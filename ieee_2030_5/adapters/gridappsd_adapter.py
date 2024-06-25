import json

ENABLED = True
try:
    from attrs import define, field
    from gridappsd import GridAPPSD
    from cimgraph.data_profile import CIM_PROFILE
    import cimgraph.data_profile.rc4_2021 as cim
    from cimgraph.models import FeederModel
    from cimgraph.databases.gridappsd import GridappsdConnection
    from cimgraph.databases import ConnectionParameters
except ImportError:
    ENABLED = False

from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.config import DeviceConfiguration


if ENABLED:
    @define
    class OcherHouse:
        mrid: str
        name: str

    @define
    class GridAPPSDAdapter:
        gapps: GridAPPSD
        model_name: str
        default_pin: str
        ocher_houses_as_inverters: bool = False
        model_dict_file: str | None = None
        model_id: str | None = None
        devices: list[DeviceConfiguration] | None = None
        power_electronic_connections: list[cim.PowerElectronicsConnection] | None = None
        ocher_houses: list[OcherHouse] | None = None
        # power_electronic_connections: list[cim.PowerElectronicsConnection] = []

        def _get_model_id_from_name(self) -> str:
            models = self.gapps.query_model_info()
            for m in models['data']['models']:
                if m['modelName'] == self.model_name:
                    return m['modelId']
            raise ValueError(f"Model {self.model_name} not found")

        def _get_ocher_house_and_utility_inverters(self) -> list[OcherHouse]:
            """
            This function uses the GridAPPSD API to get the list of energy consumers.  The list is then filtered to
            include only the names that are in the format t1_house* and utility_*.  From this the name t1_ is removed
            from the name and the mrid is used for the inverter mrid.

            :return: list of OcherHouse objects
            :rtype: list[OcherHouse]
            """

            if self.ocher_houses is not None:
                return self.ocher_houses

            self.ocher_houses = []

            if self.model_dict_file is None:

                if self.model_id is None:
                    self.model_id = self._get_model_id_from_name()

                response = self.gapps.get_response(topic='goss.gridappsd.process.request.config',
                                                message={"configurationType":"CIM Dictionary","parameters":{"model_id":f"{self.model_id}"}})

                # Should have returned only a single feeder
                feeder = response['data']['feeders'][0]
            else:

                with open(self.model_dict_file, 'r') as f:
                    feeder = json.load(f)['feeders'][0]

            for ec in feeder['energyconsumers']:
                name = ec['name']
                if name.startswith("tl_house"):
                    mrid = ec['mRID']
                    name = ec['name'][3:]
                    #inv_mrid = ec['eqContainer']
                    self.ocher_houses.append(OcherHouse(mrid, name))
                elif name.startswith("utility_"):
                    mrid = ec['mRID']
                    for phase in ec['phases']:
                        name = ec['name'] + f"_{phase}"
                        mrid = ec['mRID'] + f"{phase}"
                        self.ocher_houses.append(OcherHouse(mrid, name))

                    # name = ec['name']
                    # self.ocher_houses.append(OcherHouse(mrid, name, inv_mrid))
            return self.ocher_houses

        def _get_power_electronic_connections(self) -> list[cim.PowerElectronicsConnection]:
            if self.power_electronic_connections is not None:
                return self.power_electronic_connections

            self.power_electronic_connections = []

            models = self.gapps.query_model_info()
            for m in models['data']['models']:
                if m['modelName'] == self.model_name:
                    self.model_id = m['modelId']
                    break
            if not self.model_id:
                raise ValueError(f"Model {self.model_name} not found")

            cim_profile = CIM_PROFILE.RC4_2021.value
            iec = 7
            params = ConnectionParameters(cim_profile=cim_profile, iec61970_301=iec)

            conn = GridappsdConnection(params)
            conn.cim_profile = cim_profile
            feeder = cim.Feeder(mRID=self.model_id)

            network = FeederModel(connection=conn, container=feeder, distributed=False)

            network.get_all_edges(cim.PowerElectronicsConnection)

            self.power_electronic_connections = network.graph[cim.PowerElectronicsConnection].values()
            return self.power_electronic_connections

        def _build_device_configurations(self):
            self.devices = []
            if self.ocher_houses_as_inverters:
                for ocr in self._get_ocher_house_and_utility_inverters():
                    dev = DeviceConfiguration(id=ocr.mrid,
                                              pin=self.default_pin)
                    self.devices.append(dev)
            else:
                for inv in self._get_power_electronic_connections():
                    dev = DeviceConfiguration(
                        id=inv.mRID,
                        pin=self.default_pin
                    )
                    self.devices.append(dev)

        def get_device_configurations(self) -> list[DeviceConfiguration]:
            if not self.devices:
                self._build_device_configurations()
            return self.devices

        def create_2030_5_device_certificates_and_configurations(self, tls: TLSRepository) -> list[DeviceConfiguration]:

            self.devices = []
            if self.ocher_houses_as_inverters:
                for house in self._get_ocher_house_and_utility_inverters():
                    tls.create_cert(house.mrid)
            else:
                for inv in self.power_electronic_connections:
                    tls.create_cert(inv.mRID)
            self._build_device_configurations()
            return self.devices
