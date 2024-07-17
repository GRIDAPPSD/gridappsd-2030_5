from __future__ import annotations

import os
from dataclasses import asdict
import json
import logging

import re
from threading import Timer

ENABLED = True
try:
    from attrs import define, field
    import gridappsd.topics as topics
    from ieee_2030_5.types_ import Lfdi
    import ieee_2030_5.models as m
    from gridappsd import GridAPPSD
    from gridappsd.field_interface.interfaces import FieldMessageBus
    from cimgraph.data_profile import CIM_PROFILE
    from gridappsd.field_interface.agents.agents import GridAPPSDMessageBus
    import cimgraph.data_profile.rc4_2021 as cim
    from cimgraph.models import FeederModel
    from cimgraph.databases.gridappsd import GridappsdConnection
    from cimgraph.databases import ConnectionParameters

except ImportError:
    ENABLED = False

if ENABLED:
    _log = logging.getLogger("ieee_2030_5.gridappsd.adapter")
    from ieee_2030_5.certs import TLSRepository
    from ieee_2030_5.config import DeviceConfiguration, GridappsdConfiguration
    import ieee_2030_5.adapters as adpt

    @define
    class HouseLookup:
        mRID: str
        name: str
        lfdi: Lfdi


    class PublishTimer(Timer):
        # def __init__(self, interval: float, function, adapter: GridAPPSDAdapter):
        #     self.adapter = adapter
        #     super().__init__(interval=interval, function=function)
        def run(self):
            while not self.finished.wait(self.interval):
                self.function(*self.args, **self.kwargs)


    @define
    class GridAPPSDAdapter:
        gapps: GridAPPSD
        gridappsd_configuration: dict | GridappsdConfiguration
        tls: TLSRepository

        _publish_interval_seconds: int = 3
        _default_pin: str | None = None
        _inverters: list[HouseLookup] | None = None
        _model_dict_file: str | None = None
        _model_id: str | None = None
        _model_name: str | None = None
        _devices: list[DeviceConfiguration] | None = None
        _power_electronic_connections: list[cim.PowerElectronicsConnection] | None = None
        _timer: PublishTimer | None = None
        __field_bus_connection__: FieldMessageBus | None = None

        def get_message_bus(self) -> FieldMessageBus:
            if self.__field_bus_connection__ is None:
                # TODO Use factory class here!
                self.__field_bus_connection__ = GridAPPSDMessageBus(self.gridappsd_configuration.field_bus_def)
                # TODO Hack to make sure the gridappsd is actually able to connect.
                self.__field_bus_connection__.gridappsd_obj = GridAPPSD(username=self.gridappsd_configuration.username,
                                                                        password=self.gridappsd_configuration.password)
                # TODO Use the interface instead of this, however the gridappsdmessagebus doesn't implement it!
                assert self.__field_bus_connection__.gridappsd_obj.connected
            return self.__field_bus_connection__

        def use_houses_as_inverters(self) -> bool:
            return (self.gridappsd_configuration.house_named_inverters_regex is not None or
                    self.gridappsd_configuration.utility_named_inverters_regex is not None)

        def __attrs_post_init__(self):
            if self.gridappsd_configuration is not None and not isinstance(self.gridappsd_configuration,
                                                                           GridappsdConfiguration):
                self.gridappsd_configuration = GridappsdConfiguration(**self.gridappsd_configuration)

            if not self.gridappsd_configuration:
                raise ValueError("Missing GridAPPSD configuration, but it is required.")

            self._model_name = self.gridappsd_configuration.model_name
            self._default_pin = self.gridappsd_configuration.default_pin

            _log.debug("Creating timer now")
            self._timer = PublishTimer(self._publish_interval_seconds, self.publish_house_aggregates)
            self._timer.start()

        # power_electronic_connections: list[cim.PowerElectronicsConnection] = []

        def get_model_id_from_name(self) -> str:
            models = self.gapps.query_model_info()
            for m in models['data']['models']:
                if m['modelName'] == self._model_name:
                    return m['modelId']
            raise ValueError(f"Model {self._model_name} not found")

        def get_house_and_utility_inverters(self) -> list[HouseLookup]:
            """
            This function uses the GridAPPSD API to get the list of energy consumers.

            This method should only be called with the `house_named_inverters_regex` or `utility_named_inverters_regex`
            properties set on the `GridappsdConfiguration object.  If set then the function searches for energy
            consumers that match the regular expression and returns them as a list of HouseLookup objects.
            In the case of utility regular expression it will return 3 HouseLookup objects for each phase of the
            utility inverter.  The name of the phase (a b c, A B C, 1 2 3, etc) is determined by the
            response from the server in the querying of the model.

            :return: list of HouseLookup objects
            :rtype: list[HouseLookup]
            """

            if self._inverters is not None:
                return self._inverters

            self._inverters = []

            if self._model_dict_file is None:

                if self._model_id is None:
                    self._model_id = self.get_model_id_from_name()

                response = self.gapps.get_response(topic='goss.gridappsd.process.request.config',
                                                   message={"configurationType": "CIM Dictionary",
                                                            "parameters": {"model_id": f"{self._model_id}"}})

                # Should have returned only a single feeder
                feeder = response['data']['feeders'][0]
            else:

                with open(self.model_dict_file, 'r') as f:
                    feeder = json.load(f)['feeders'][0]

            re_houses = re.compile(self.gridappsd_configuration.house_named_inverters_regex)
            re_utility = re.compile(self.gridappsd_configuration.utility_named_inverters_regex)

            # Based upon the energyconsumers create matches to the houses and utilities
            # and add them to the list.
            for ec in feeder['energyconsumers']:
                if match_house := re.match(re_houses, ec['name']):
                    self._inverters.append(HouseLookup(mRID=ec['mRID'],
                                                       name=match_house.group(0),
                                                       lfdi=self.tls.lfdi(ec['mRID'])))
                elif match_utility := re.match(re_utility, ec['name']):
                    for phase in ec['phases']:
                        self._inverters.append(HouseLookup(mRID=ec['mRID'],
                                                           name=match_utility.group(0) + f"_{phase}",
                                                           lfdi=self.tls.lfdi(ec['mRID'])))
            return self._inverters

        def get_power_electronic_connections(self) -> list[cim.PowerElectronicsConnection]:
            if self._power_electronic_connections is not None:
                return self._power_electronic_connections

            self._power_electronic_connections = []

            models = self.gapps.query_model_info()
            for m in models['data']['models']:
                if m['modelName'] == self._model_name:
                    self._model_id = m['modelId']
                    break
            if not self._model_id:
                raise ValueError(f"Model {self._model_name} not found")

            cim_profile = CIM_PROFILE.RC4_2021.value
            iec = 7
            params = ConnectionParameters(cim_profile=cim_profile, iec61970_301=iec)

            conn = GridappsdConnection(params)
            conn.cim_profile = cim_profile
            feeder = cim.Feeder(mRID=self._model_id)

            network = FeederModel(connection=conn, container=feeder, distributed=False)

            network.get_all_edges(cim.PowerElectronicsConnection)

            self._power_electronic_connections = network.graph[cim.PowerElectronicsConnection].values()
            return self._power_electronic_connections

        def _build_device_configurations(self):
            self._devices = []
            if self.use_houses_as_inverters():
                for inv in self.get_house_and_utility_inverters():
                    dev = DeviceConfiguration(id=inv.mRID,
                                              pin=int(self._default_pin),
                                              lfdi=self.tls.lfdi(inv.mRID))
                    dev.ders = [dict(description=inv.name)]
                    self._devices.append(dev)
            else:
                for inv in self.get_power_electronic_connections():
                    dev = DeviceConfiguration(
                        id=inv.mRID,
                        pin=int(self._default_pin),
                        lfdi=self.tls.lfdi(inv.mRID)
                    )
                    dev.ders = [dict(description=inv.mRID)]
                    self._devices.append(dev)

        def get_device_configurations(self) -> list[DeviceConfiguration]:
            if not self._devices:
                self._build_device_configurations()
            return self._devices

        def get_message_for_bus(self) -> dict:
            import random
            msg = {}

            # TODO Get from list adapter for each house.
            # TODO This might not be the right way to do this
            # Filter for availability
            # for dev in self._devices:
            #     if inverter := next(filter(lambda x: x.lfdi == dev.lfdi, self._inverters):

            der_status_uris = adpt.ListAdapter.filter_single_dict(lambda k: k.endswith('ders'))

            for uri in der_status_uris:
                _log.debug(f"Testing uri: {uri}")

                meta_data = adpt.ListAdapter.get_single_meta_data(uri)
                status: m.DERStatus = adpt.ListAdapter.get_single(meta_data['uri'])

                inverter: HouseLookup | None = None

                _log.debug(f"Status is: {status}")
                if status:
                    _log.debug(f"Status found: {status}")
                    for x in self._devices:
                        if x.lfdi == meta_data['lfdi']:
                            inverter = x
                            _log.debug(f"Found inverter: {inverter}")
                            break

                    if inverter:

                        msg[inverter.mRID] = dict(mrid=inverter.mRID, name=inverter.name)

                        msg[inverter.mRID].update(asdict(status))


            # for inv in self._inverters:
            #     adpt.ListAdapter.get_single_meta_data(())
            #     try:
            #         # TODO we need to make sure we have the right mRID for the inverters this doesn't guarantee it.
            #         uri = next(der_status_uris)
            #         data = adpt.ListAdapter.get_single(uri)
            #         msg[inv.mRID] = dict(mrid=inv.mRID, name=inv.name)
            #         for k, v in data.__dict__.items():
            #             if v is not None:
            #                 msg[inv.mRID][k] = v
            #
            #     except StopIteration:
            #         pass

            return msg

        def create_2030_5_device_certificates_and_configurations(self) -> list[DeviceConfiguration]:

            self._devices = []
            if self.use_houses_as_inverters():
                for house in self.get_house_and_utility_inverters():
                    self.tls.create_cert(house.mRID)
            else:
                for inv in self.get_power_electronic_connections():
                    self.tls.create_cert(inv.mRID)
            self._build_device_configurations()
            return self._devices

        def publish_house_aggregates(self):
            from pprint import pformat

            mb = self.get_message_bus()

            if field_bus := self.gridappsd_configuration.field_bus_def.id:
                ...

            if simulation_id := os.environ.get("GRIDAPPSD_SIMULATION_ID"):
                pass
            if service_name := os.environ.get("GRIDAPPSD_SERVICE_NAME"):
                pass

            output_topic = topics.application_output_topic(application_id=service_name, simulation_id=simulation_id)
            # # TODO: the output topic goes to the field bus manager regardless of the message_bus_id for some reason.
            # output_topic = topics.field_output_topic(message_bus_id=field_bus)

            message = self.get_message_for_bus()

            _log.debug(f"Output: {output_topic}\n{pformat(message, 2)}")
            mb.send(topic=output_topic, message=message)
