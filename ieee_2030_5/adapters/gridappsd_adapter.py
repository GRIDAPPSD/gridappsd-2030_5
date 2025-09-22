from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import asdict
from threading import RLock, Timer

_log = logging.getLogger(__name__)
ENABLED = True
try:
    import cimgraph.data_profile.rc4_2021 as cim
    import gridappsd.topics as topics
    from attrs import define, field
    from cimgraph.data_profile import CIM_PROFILE
    from cimgraph.databases import ConnectionParameters
    from cimgraph.databases.gridappsd import GridappsdConnection
    from cimgraph.models import FeederModel
    from gridappsd import GridAPPSD
    from gridappsd.field_interface.agents.agents import GridAPPSDMessageBus
    from gridappsd.field_interface.interfaces import FieldMessageBus

    import ieee_2030_5.adapters as adpt
    import ieee_2030_5.hrefs as hrefs
    import ieee_2030_5.models as m
    from ieee_2030_5.types_ import Lfdi

except ImportError:
    ENABLED = False

if ENABLED:
    import ieee_2030_5.adapters as adpt
    from ieee_2030_5.certs import TLSRepository
    from ieee_2030_5.config import DeviceConfiguration, GridappsdConfiguration

    @define
    class HouseLookup:
        mRID: str
        name: str
        lfdi: Lfdi | None = None


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
        _model_dict_file: str | None = None
        _model_id: str | None = None
        _model_name: str | None = None
        _inverters: list[HouseLookup] | None = None
        _devices: list[DeviceConfiguration] | None = None
        _power_electronic_connections: list[cim.PowerElectronicsConnection] | None = None
        _timer: PublishTimer | None = None
        __field_bus_connection__: FieldMessageBus | None = None
        _lock: RLock = field(default=RLock(), init=False)


        def start_publishing(self):
            if self._timer is None:
                _log.debug("Creating timer now")
                self._timer = PublishTimer(self._publish_interval_seconds,
                                           self.publish_house_aggregates)
                self._timer.start()

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

            assert self.gapps.connected, "Gridappsd passed is not connected."

            # Get environment variables for simulation and service IDs
            simulation_id = os.environ.get("GRIDAPPSD_SIMULATION_ID")
            service_id = os.environ.get("GRIDAPPSD_SERVICE_NAME")

            if self.gridappsd_configuration.publish_interval_seconds:
                self._publish_interval_seconds = self.gridappsd_configuration.publish_interval_seconds

            _log.debug("Subscribing to topic: %s",
                   topics.application_input_topic(application_id=service_id, simulation_id=simulation_id))

            self.gapps.subscribe(topics.application_input_topic(application_id=service_id,
                                                                simulation_id=simulation_id), callback=self._input_detected)



        def _input_detected(self, _header: dict | None, message: dict | None):
            _log.info("=== GridAPPS-D Input Detected ===")
            _log.info("Header: %s", _header)
            _log.info("Full message structure: %s", message)
            _log.info("Debugging global registry mrids")
            _log.info("Note: Full registry contents scanning not implemented - use debug_mrid_lookup() for specific mRIDs")

            forward_diffs = message['input']['message']['forward_differences']
            _log.info("Processing %d forward_differences", len(forward_diffs))
            # rev_diffs not used currently

            import ieee_2030_5.hrefs as hrefs

            for i, item in enumerate(forward_diffs):
                _log.info("--- Processing forward_diff item %d ---", i)
                _log.info("Item contents: %s", item)

                if not item.get('attribute'):
                    _log.error(f"INVALID attribute detected!")
                    continue

                if not item['attribute'].startswith('DERControl'):
                    _log.error(f"INVALID attribute.  Must start with DERControl but was {item['attribute']}")
                    continue

                # Test the attribute object and object_id because we could have either.  Not sure why
                # but I have seen it both ways in the docs so handle it
                if item.get('object'):
                    object_key = 'object'
                    _log.info("Item %d: Using 'object' key", i)
                elif item.get('object_id'):
                    object_key = 'object_id'
                    _log.info("Item %d: Using 'object_id' key", i)
                else:
                    _log.error("INVALID object_id in item %d. The 'object_id' field must be set in order to use this function.", i)
                    continue

                object_id_value = item[object_key]
                _log.info("Item %d: Looking up %s='%s' directly in database", i, object_key, object_id_value)
                
                # Get the mRID location from GlobalMRIDs
                mrid_location = adpt.get_global_mrids().get_location(object_id_value)
                _log.info("Item %d: mRID %s points to location: %s", i, object_id_value, mrid_location)
                
                # Debug: also try direct database lookup with prefix to see if data exists
                mrid_key = f"mrid:{object_id_value}"
                direct_db_data = adpt.get_list_adapter()._db.get_point(mrid_key)
                if direct_db_data:
                    try:
                        direct_value = direct_db_data.decode('utf-8')
                        _log.info("Item %d: Direct DB lookup found: %s -> %s", i, mrid_key, direct_value)
                    except UnicodeDecodeError:
                        _log.error("Item %d: Direct DB lookup found BINARY DATA at %s (len=%d)", i, mrid_key, len(direct_db_data))
                else:
                    _log.info("Item %d: Direct DB lookup found nothing at %s", i, mrid_key)
                
                # Try to retrieve directly from database using the location
                obj = None
                if mrid_location:
                    try:
                        # Use the database directly instead of GlobalMRIDs cache
                        db_data = adpt.get_list_adapter()._db.get_point(mrid_location)
                        if db_data:
                            import pickle
                            obj = pickle.loads(db_data)
                            _log.debug("Item %d: Retrieved object from database at location %s", i, mrid_location)
                        else:
                            _log.warning("Item %d: No data found in database at location %s", i, mrid_location)
                    except Exception as e:
                        _log.error("Item %d: Failed to retrieve from database location %s: %s", i, mrid_location, e)
                else:
                    _log.warning("Item %d: No mRID location found for %s", i, object_id_value)

                # Note: The EndDevice should now be indexed by certificate CN during device creation

                if obj is None:
                    _log.error("Item %d: Couldn't find any object with %s='%s' in GlobalmRIDs registry", i, object_key, object_id_value)
                    # Debug: show detailed mRID lookup information
                    adpt.get_global_mrids().debug_mrid_lookup(object_id_value)

                    # Check if this is due to a stale mRID registration pointing to wrong location
                    if mrid_location and mrid_location.startswith('single:'):
                        # Try to find the corresponding enddevice location
                        href_path = mrid_location.replace('single:', '')
                        # Extract device index from href (e.g., /edev_53036 -> 53036)
                        if hrefs.SEP in href_path:
                            device_index = href_path.split(hrefs.SEP)[-1]
                            enddevice_key = f"enddevice:{device_index}"
                            # Check if the EndDevice exists at the correct location
                            if adpt.get_list_adapter()._db.exists(enddevice_key):
                                _log.info("Item %d: Found EndDevice at correct location %s, updating mRID registration", i, enddevice_key)
                                # Update mRID to point to correct location
                                adpt.get_global_mrids().register_mrid(object_id_value, enddevice_key, "EndDevice")
                                # Retry lookup
                                obj = adpt.get_global_mrids().get_item(object_id_value)
                                if obj is not None:
                                    _log.info("Item %d: Successfully retrieved EndDevice after fixing mRID registration", i)

                    if obj is None:
                        # CRITICAL ERROR: Equipment not found in database - initialization failed
                        _log.error("="*80)
                        _log.error("CRITICAL: Equipment %s='%s' NOT FOUND in database!", object_key, object_id_value)
                        _log.error("This indicates that the server initialization did not properly discover")
                        _log.error("and register this equipment from GridAPPS-D. This equipment should have")
                        _log.error("been registered during the create_2030_5_device_certificates_and_configurations")
                        _log.error("process or during energy consumer certificate copying.")
                        _log.error("="*80)
                        _log.error("SKIPPING this control message item - FIX INITIALIZATION!")
                        _log.error("="*80)
                        continue

                _log.info("Item %d: Found object of type %s for %s='%s'", i, type(obj), object_key, object_id_value)

                if not isinstance(obj, m.EndDevice):
                    _log.error("Item %d: Object with %s='%s' is not an EndDevice, got %s instead.", i, object_key, object_id_value, type(obj))
                    continue

                _log.info("Item %d: Confirmed EndDevice found, proceeding with DER control processing", i)
                _log.debug("Item %d: EndDevice details - href=%s, DERListLink=%s", i, obj.href, obj.DERListLink)
                _log.debug("Item %d: Retrieved EndDevice DERListLink type=%s, href=%s", i, type(obj.DERListLink), obj.DERListLink.href if obj.DERListLink else 'N/A')

                if isinstance(obj, m.EndDevice):
                    # Get the specific DER (NOTE we are only getting the first one)
                    # Handle multiple DERs in the future
                    _log.info("Item %d: Getting DER list from href: %s", i, obj.DERListLink.href)
                    der_list = adpt.ListAdapter.get_resource_list(obj.DERListLink.href)
                    if not der_list or not hasattr(der_list, 'DER') or not der_list.DER:
                        _log.error("Item %d: No DER found for EndDevice %s at href %s", i, getattr(obj, 'mRID', 'unknown'), obj.DERListLink.href)
                        continue

                    _log.info("Item %d: Found %d DER(s) for EndDevice %s", i, len(der_list.DER), getattr(obj, 'mRID', 'unknown'))
                    der: m.DER = der_list.DER[0]
                    _log.info("Item %d: Using DER with href: %s for processing %s='%s'", i, der.href, object_key, object_id_value)

                    # Verify this DER matches the one receiving DERStatus updates in debug.log
                    expected_der_path = f"/der{hrefs.SEP}{obj.href.split(hrefs.SEP)[1]}{hrefs.SEP}der{hrefs.SEP}0" if hrefs.SEP in obj.href else "unknown"
                    if der.href != expected_der_path:
                        _log.warning("Item %d: DER href mismatch! Expected %s, got %s", i, expected_der_path, der.href)

                    # Find the DER program - retrieve directly from database
                    _log.info("Item %d: Retrieving DER programs directly from database", i)
                    try:
                        db_data = adpt.get_list_adapter()._db.get_point(f"list:{hrefs.DEFAULT_DERP_ROOT}")
                        if not db_data:
                            _log.error("Item %d: No DER program list data found in database at list:%s", i, hrefs.DEFAULT_DERP_ROOT)
                            continue
                        
                        import pickle
                        der_program_list = pickle.loads(db_data)
                        _log.info("Item %d: Retrieved %d DER programs from database", i, len(der_program_list))
                        
                    except Exception as e:
                        _log.error("Item %d: Failed to retrieve DER programs from database: %s", i, e)
                        continue

                    # Find matching program for this DER
                    if not der.CurrentDERProgramLink:
                        _log.error("Item %d: DER %s has no CurrentDERProgramLink", i, getattr(der, 'mRID', der.href))
                        continue

                    program = None
                    for p in der_program_list:
                        if p.href == der.CurrentDERProgramLink.href:
                            program = p
                            break

                    if not program:
                        _log.error("Item %d: No matching program found for DER %s, looking for program %s", i, getattr(der, 'mRID', der.href), der.CurrentDERProgramLink.href)
                        _log.debug("Item %d: Available programs: %s", i, [p.href for p in der_program_list])
                        continue

                    _log.info("Item %d: Found program %s for DER %s", i, program.href, der.href)
                    _log.debug("Item %d: Program DefaultDERControlLink: %s", i, program.DefaultDERControlLink)

                    # Ensure program has DefaultDERControlLink - create if missing
                    if not program.DefaultDERControlLink:
                        _log.warning("Program %s has no DefaultDERControlLink, creating one", getattr(program, 'mRID', program.href))
                        # Create DefaultDERControlLink using proper href structure
                        import ieee_2030_5.hrefs as hrefs
                        program_index = int(program.href.split(hrefs.SEP)[1]) if hrefs.SEP in program.href else 0
                        program_hrefs = hrefs.DERProgramHref(program_index)
                        program.DefaultDERControlLink = m.DefaultDERControlLink(program_hrefs.default_control_href)

                        # Create the DefaultDERControl object and store it
                        default_der_control = m.DefaultDERControl(
                            href=program.DefaultDERControlLink.href,
                            mRID=adpt.get_global_mrids().new_mrid(),
                            DERControlBase=m.DERControlBase(
                                opModConnect=True,
                                opModEnergize=True
                            )
                        )
                        adpt.ListAdapter.set_single(uri=program.DefaultDERControlLink.href, obj=default_der_control)
                        
                        # Store in href indexer for immediate access
                        from ieee_2030_5.data.indexer import add_href
                        add_href(program.DefaultDERControlLink.href, default_der_control)

                        # Update the program in the database with the new DefaultDERControlLink
                        program_list = adpt.ListAdapter.get_list(hrefs.DEFAULT_DERP_ROOT)
                        for idx, existing_program in enumerate(program_list):
                            if existing_program.href == program.href:
                                program_list[idx] = program
                                adpt.ListAdapter.set_list(hrefs.DEFAULT_DERP_ROOT, program_list)
                                break

                        _log.info("Created DefaultDERControlLink and DefaultDERControl for program %s at %s", program.href, program.DefaultDERControlLink.href)

                    # Get the default DER control directly from database for debugging
                    _log.info("Item %d: Looking up DefaultDERControl '%s' directly in database", i, program.DefaultDERControlLink.href)
                    try:
                        db_data = adpt.get_list_adapter()._db.get_point(program.DefaultDERControlLink.href)
                        if db_data:
                            import pickle
                            stored_obj = pickle.loads(db_data)
                            # Check if it's an Index object or raw data
                            if hasattr(stored_obj, 'item'):
                                dderc = stored_obj.item
                            else:
                                dderc = stored_obj
                            _log.info("Item %d: Successfully retrieved DefaultDERControl from database", i)
                        else:
                            _log.error("No default DER control found in database at href %s for program %s", program.DefaultDERControlLink.href, getattr(program, 'mRID', program.href))
                            continue
                    except Exception as e:
                        _log.error("Failed to get default DER control from database href %s for program %s: %s", program.DefaultDERControlLink.href, getattr(program, 'mRID', program.href), e)
                        continue
                    # Should be something like ['DERControl', 'DERControlBase', 'opModTargetW']
                    obj_path = item['attribute'].split('.')

                    _log.debug("Updating dderc mrid: %s", dderc.mRID)
                    # Depending on whether we are controlling the outer default control or the inner base control
                    # this will be set so we can use hasattr and setattr on it.
                    controller = dderc
                    prop = obj_path[1]
                    if obj_path[1] == 'DERControlBase' and len(obj_path) == 3:
                        controller = dderc.DERControlBase
                        prop = obj_path[2]

                    if not hasattr(controller, prop):
                        _log.error("Property %s is not on obj type %s", prop, type(controller))
                        continue

                    _log.debug("Before %s Setting property %s with value: %s", der.href, prop, getattr(controller, prop))

                    # Handle value based on property type
                    if prop == 'opModTargetW' and isinstance(item['value'], dict):
                        # Convert to ActivePower object for proper typing
                        active_power = m.ActivePower(**item['value'])
                        setattr(controller, prop, active_power)
                        _log.debug("After %s Setting property %s with value: %s", der.href, prop, active_power)
                    else:
                        # Set directly for other property types
                        setattr(controller, prop, item['value'])
                        _log.debug("After %s Setting property %s with value: %s", der.href, prop, item['value'])

                    # Store the updated controller (DefaultDERControl) back to database
                    adpt.ListAdapter.set_single(uri=program.DefaultDERControlLink.href, obj=dderc)
                    _log.debug("Stored updated DefaultDERControl with %s=%s to database at %s", prop, getattr(controller, prop), program.DefaultDERControlLink.href)



        # power_electronic_connections: list[cim.PowerElectronicsConnection] = []

        def get_model_id_from_name(self) -> str:
            models = self.gapps.query_model_info()
            for model in models['data']['models']:
                if model['modelName'] == self._model_name:
                    return model['modelId']
            raise ValueError(f"Model {self._model_name} not found")

        def get_all_equipment_from_gridappsd(self) -> dict[str, str]:
            """Get all equipment IDs and their mRIDs from GridAPPS-D for initialization.
            
            Returns:
                dict: Mapping of equipment_id -> mRID for all equipment in the model
            """
            try:
                if self.gapps is None:
                    _log.warning("GridAPPS-D connection not available for equipment discovery")
                    return {}

                # Query GridAPPS-D for equipment information
                if self._model_id is None:
                    self._model_id = self.get_model_id_from_name()

                response = self.gapps.get_response(
                    topic='goss.gridappsd.process.request.config',
                    message={
                        "configurationType": "CIM Dictionary",
                        "parameters": {"model_id": f"{self._model_id}"}
                    }
                )

                feeder = response['data']['feeders'][0]
                equipment_map = {}

                # Collect equipment from all categories
                for category in ['measurements', 'energyconsumers', 'powerelectronicsconnections']:
                    if category in feeder:
                        for item in feeder[category]:
                            equipment_id = item.get('mRID')
                            if equipment_id:
                                equipment_map[equipment_id] = equipment_id  # Equipment ID is the mRID
                            
                            # Also map by name if different
                            name = item.get('name')
                            if name and name != equipment_id:
                                equipment_map[name] = equipment_id

                _log.info(f"Retrieved {len(equipment_map)} equipment entries from GridAPPS-D")
                return equipment_map

            except Exception as e:
                _log.error(f"Failed to get equipment list from GridAPPS-D: {e}")
                return {}

        def get_equipment_mrid_from_gridappsd(self, equipment_id: str) -> str | None:
            """Query GridAPPS-D to get the mRID for a given equipment ID.

            Args:
                equipment_id: GridAPPS-D equipment identifier

            Returns:
                str | None: Equipment mRID if found, None otherwise
            """
            try:
                if self.gapps is None:
                    _log.warning("GridAPPS-D connection not available for mRID lookup")
                    return None

                # Query GridAPPS-D for equipment information
                if self._model_id is None:
                    self._model_id = self.get_model_id_from_name()

                response = self.gapps.get_response(
                    topic='goss.gridappsd.process.request.config',
                    message={
                        "configurationType": "CIM Dictionary",
                        "parameters": {"model_id": f"{self._model_id}"}
                    }
                )

                feeder = response['data']['feeders'][0]

                # Look for equipment in different categories
                for category in ['measurements', 'energyconsumers', 'powerelectronicsconnections']:
                    if category in feeder:
                        for item in feeder[category]:
                            # Check if this item matches our equipment ID
                            if item.get('mRID') == equipment_id:
                                return equipment_id  # Equipment ID is the mRID
                            elif item.get('name') == equipment_id:
                                return item.get('mRID')  # Return the mRID for this equipment

                _log.warning(f"Equipment {equipment_id} not found in GridAPPS-D model")
                return None

            except Exception as e:
                _log.error(f"Failed to query GridAPPS-D for equipment {equipment_id}: {e}")
                return None

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

                with open(self._model_dict_file, 'r', encoding='utf-8') as f:
                    feeder = json.load(f)['feeders'][0]

            re_houses = re.compile(self.gridappsd_configuration.house_named_inverters_regex)
            re_utility = re.compile(self.gridappsd_configuration.utility_named_inverters_regex)

            # Based upon the energyconsumers create matches to the houses and utilities
            # and add them to the list.
            for ec in feeder['energyconsumers']:
                if match_house := re.match(re_houses, ec['name']):
                    try:
                        lfdi=self.tls.lfdi(ec['mRID'])
                    except FileNotFoundError:
                        lfdi = None
                    self._inverters.append(
                        HouseLookup(mRID=ec['mRID'], name=match_house.group(0), lfdi=lfdi))
                elif match_utility := re.match(re_utility, ec['name']):
                    #lfdi=self.tls.lfdi(ec['mRID'])
                    try:
                        lfdi=self.tls.lfdi(ec['mRID'])
                    except FileNotFoundError:
                        lfdi = None
                    self._inverters.append(
                        HouseLookup(mRID=ec['mRID'], name=match_utility.group(0), lfdi=lfdi))

            return self._inverters

        def get_power_electronic_connections(self) -> list[cim.PowerElectronicsConnection]:
            if self._power_electronic_connections is not None:
                return self._power_electronic_connections

            self._power_electronic_connections = []

            models = self.gapps.query_model_info()
            for model in models['data']['models']:
                if model['modelName'] == self._model_name:
                    self._model_id = model['modelId']
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
                    dev.ders = [inv.name]
                    dev.fsas = ["fsa0"]
                    self._devices.append(dev)
            else:
                for inv in self.get_power_electronic_connections():
                    dev = DeviceConfiguration(
                        id=inv.mRID,
                        pin=int(self._default_pin),
                        lfdi=self.tls.lfdi(inv.mRID)
                    )
                    dev.ders = [inv.mRID]
                    dev.fsas = ["fsa0"]
                    self._devices.append(dev)

        def get_device_configurations(self) -> list[DeviceConfiguration]:
            if not self._devices:
                self._build_device_configurations()
            return self._devices

        def get_message_for_bus(self) -> dict:
            import ieee_2030_5.models.output as mo
            msg = {}
            _log.debug("=== GET_MESSAGE_FOR_BUS ENTRY ===")

            def detect(v):
                if v:
                    return v.endswith("ders")
                return False

            try:
                # Database reads are already thread-safe - no adapter lock needed
                _log.debug("About to call filter_single_dict...")

                # Debug: Get ALL URIs first to see what's in the database
                try:
                    all_uris = adpt.ListAdapter.get_all_keys()
                    _log.debug("Database contains %d total URIs", len(all_uris))
                    if len(all_uris) > 0:
                        _log.debug("Sample URIs: %s", all_uris[:5])
                        ders_uris = [uri for uri in all_uris if "ders" in uri]
                        _log.debug("URIs containing 'ders': %s", ders_uris)
                        der_uris = [uri for uri in all_uris if "/der" in uri]
                        _log.debug("URIs containing '/der': %s", der_uris[:10])
                except Exception as debug_e:
                    _log.warning("Debug URI listing failed: %s", debug_e)

                der_status_uris = adpt.ListAdapter.filter_single_dict(detect)
                _log.debug("filter_single_dict returned %d URIs: %s", len(der_status_uris), der_status_uris)

                # Take a snapshot of inverters to avoid holding lock during database reads
                current_inverters = self._inverters[:] if self._inverters else []
                _log.debug("Using %d inverters for LFDI mapping", len(current_inverters))

                for uri in der_status_uris:
                    _log.debug("Testing uri: %s", uri)

                    try:
                        _log.debug("Getting metadata for URI: %s", uri)
                        meta_data = adpt.ListAdapter.get_single_meta_data(uri)
                        _log.debug("Metadata: %s", meta_data)

                        _log.debug("Getting status from URI: %s", meta_data['uri'])
                        status: m.DERStatus = adpt.ListAdapter.get_single(meta_data['uri'])
                        _log.debug("Retrieved status: %s", status)
                        inverter: HouseLookup | None = None

                        _log.debug("Status is: %s", status)
                        _log.debug("Meta_data LFDI: %s", meta_data.get('lfdi'))

                        if status and meta_data.get('lfdi') and current_inverters:
                            _log.debug("Status found: %s", status)
                            _log.debug("Looking for: %s", meta_data['lfdi'])

                            for x in current_inverters:
                                if x.lfdi == meta_data['lfdi']:
                                    inverter = x
                                    _log.debug("Found inverter: %s", inverter)
                                    break

                            if inverter:
                                # Convert to cim object measurement as analog value.
                                analog_value = mo.AnalogValue(mRID=inverter.mRID, name=inverter.name)

                                if status.readingTime is not None:
                                    analog_value.timeStamp = status.readingTime

                                if status.stateOfChargeStatus is not None:
                                    if status.stateOfChargeStatus.value is not None:
                                        analog_value.value = status.stateOfChargeStatus.value

                                msg[inverter.mRID] = asdict(analog_value)
                    except Exception as e:
                        _log.warning(f"Error processing URI {uri}: {e}")
                        continue

            except Exception as e:
                _log.error("Error in get_message_for_bus: %s", e)

            _log.debug("=== GET_MESSAGE_FOR_BUS EXIT === Final message: %s", msg)
            return msg
        def _copy_certificates_for_energy_consumers(self):
            """
            Copy certificates from conducting equipment to their related energy consumers.
            This ensures LFDI matching works for both main house mRIDs and energy consumer mRIDs.
            """
            _log.info("Copying certificates for energy consumers...")

            # Get the CIM dictionary data
            if self._model_dict_file is None:
                if self._model_id is None:
                    self._model_id = self.get_model_id_from_name()
                response = self.gapps.get_response(topic='goss.gridappsd.process.request.config',
                                                   message={"configurationType": "CIM Dictionary",
                                                            "parameters": {"model_id": f"{self._model_id}"}})
                feeder = response['data']['feeders'][0]
            else:
                with open(self._model_dict_file, 'r', encoding='utf-8') as f:
                    feeder = json.load(f)['feeders'][0]

            # Find all energy consumers with ConductingEquipment_mRID
            conducting_equipment_map = {}
            for measurement in feeder.get('measurements', []):
                if ('EnergyConsumer_' in measurement.get('name', '') and
                    'ConductingEquipment_mRID' in measurement):

                    conducting_eq_mrid = measurement['ConductingEquipment_mRID']
                    energy_consumer_mrid = measurement['mRID']

                    if conducting_eq_mrid not in conducting_equipment_map:
                        conducting_equipment_map[conducting_eq_mrid] = []
                    conducting_equipment_map[conducting_eq_mrid].append(energy_consumer_mrid)

            # Copy certificates from conducting equipment to energy consumers AND register them
            cert_copies_count = 0
            registered_consumers = 0
            
            for conducting_mrid, consumer_mrids in conducting_equipment_map.items():
                # Check if conducting equipment certificate files exist (using direct path construction)
                cert_file = self.tls._certs_dir / f"{conducting_mrid}.crt"
                combined_file = self.tls._combined_dir / f"{conducting_mrid}-combined.pem"

                if cert_file.exists() or combined_file.exists():
                    _log.debug(f"Copying certificate from {conducting_mrid} to {len(consumer_mrids)} energy consumers")

                    for consumer_mrid in consumer_mrids:
                        try:
                            # Copy the certificate files
                            self.tls.copy_certificate(conducting_mrid, consumer_mrid)
                            cert_copies_count += 1
                            _log.debug(f"  Copied certificate to {consumer_mrid}")
                            
                            # IMPORTANT: Also register this energy consumer mRID for message routing
                            # This allows GridAPPS-D messages referencing energy consumer mRIDs to be routed correctly
                            # We need access to the adapter to register - get it from context
                            import ieee_2030_5.adapters as adpt
                            if hasattr(adpt, '_initialized') and adpt._initialized:
                                # Map the energy consumer mRID to the same EndDevice as the conducting equipment
                                conducting_location = adpt.get_global_mrids().get_location(conducting_mrid)
                                if conducting_location:
                                    adpt.get_global_mrids().register_mrid(consumer_mrid, conducting_location)
                                    registered_consumers += 1
                                    _log.debug(f"  Registered energy consumer {consumer_mrid} -> {conducting_location}")
                                else:
                                    _log.warning(f"  Could not find location for conducting equipment {conducting_mrid}")
                                    
                        except Exception as e:
                            _log.warning(f"Failed to copy certificate from {conducting_mrid} to {consumer_mrid}: {e}")
                else:
                    _log.debug(f"No certificate found for conducting equipment {conducting_mrid}")

            _log.info(f"Completed certificate copying: {cert_copies_count} certificates copied, {registered_consumers} energy consumers registered")

        def create_2030_5_device_certificates_and_configurations(self) -> list[DeviceConfiguration]:
            _log.error("DEBUG: create_2030_5_device_certificates_and_configurations() CALLED")

            self._devices = []
            discovered_devices = []
            
            if self.use_houses_as_inverters():
                houses = self.get_house_and_utility_inverters()
                _log.info(f"Discovered {len(houses)} house/utility inverters from GridAPPS-D")
                for house in houses:
                    _log.debug(f"Processing house device: {house.mRID}")
                    discovered_devices.append(house.mRID)
                    self.tls.create_cert(house.mRID)
                    if house.lfdi is None:
                        house.lfdi = self.tls.lfdi(house.mRID)

                # Copy certificates to energy consumers after creating main certificates
                self._copy_certificates_for_energy_consumers()
            else:
                invs = self.get_power_electronic_connections()
                _log.info(f"Discovered {len(invs)} power electronic connections from GridAPPS-D")
                for inv in invs:
                    _log.debug(f"Processing inverter device: {inv.mRID}")
                    discovered_devices.append(inv.mRID)
                    self.tls.create_cert(inv.mRID)

                # Copy certificates to energy consumers after creating main certificates
                self._copy_certificates_for_energy_consumers()

            _log.info(f"Total devices discovered from GridAPPS-D: {discovered_devices}")
            
            # DEBUG: Check if our problem equipment ID is in any GridAPPS-D data
            _log.info("DEBUG: Checking if problem equipment IDs are in GridAPPS-D data...")
            problem_equipment = ["_EB6BC0A1-FA4B-46CE-B26E-DD022AB62595", "_CA0A0024-DA79-4395-9B05-6A7B9DE0AED9"]
            for eq_id in problem_equipment:
                if eq_id in discovered_devices:
                    _log.info(f"DEBUG: {eq_id} WAS discovered as main device")
                else:
                    _log.warning(f"DEBUG: {eq_id} NOT discovered as main device, checking energy consumers...")
                    
                    # Check if it's in the energy consumer data
                    try:
                        # Get the CIM dictionary to check energy consumers
                        if self._model_dict_file is None:
                            if self._model_id is None:
                                self._model_id = self.get_model_id_from_name()
                            response = self.gapps.get_response(
                                topic='goss.gridappsd.process.request.config',
                                message={
                                    "configurationType": "CIM Dictionary",
                                    "parameters": {"model_id": f"{self._model_id}"}
                                }
                            )
                            feeder = response['data']['feeders'][0]
                        else:
                            import json
                            with open(self._model_dict_file, 'r', encoding='utf-8') as f:
                                feeder = json.load(f)['feeders'][0]
                        
                        # Check measurements for energy consumers
                        found_in_measurements = False
                        for measurement in feeder.get('measurements', []):
                            if eq_id in [measurement.get('mRID'), measurement.get('name')]:
                                _log.info(f"DEBUG: {eq_id} FOUND in measurements: {measurement}")
                                found_in_measurements = True
                                break
                                
                        if not found_in_measurements:
                            # Check other categories
                            for category in ['energyconsumers', 'powerelectronicsconnections']:
                                if category in feeder:
                                    for item in feeder[category]:
                                        if eq_id in [item.get('mRID'), item.get('name')]:
                                            _log.info(f"DEBUG: {eq_id} FOUND in {category}: {item}")
                                            found_in_measurements = True
                                            break
                                if found_in_measurements:
                                    break
                                    
                        if not found_in_measurements:
                            _log.error(f"DEBUG: {eq_id} NOT FOUND anywhere in GridAPPS-D CIM data!")
                            
                    except Exception as e:
                        _log.error(f"DEBUG: Failed to check GridAPPS-D data for {eq_id}: {e}")
            
            self._build_device_configurations()
            return self._devices

        def publish_house_aggregates(self):
            from pprint import pformat

            mb = self.get_message_bus()

            # Get environment variables needed for topic construction
            simulation_id = os.environ.get("GRIDAPPSD_SIMULATION_ID")
            service_name = os.environ.get("GRIDAPPSD_SERVICE_NAME")

            output_topic = topics.application_output_topic(application_id=service_name, simulation_id=simulation_id)
            # # The output topic goes to the field bus manager regardless of the message_bus_id for some reason.
            # output_topic = topics.field_output_topic(message_bus_id=field_bus)

            message = self.get_message_for_bus()

            # Write detailed output to file for debugging
            import datetime
            from pathlib import Path
            debug_file = Path("gridappsd_adapter_output.log")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                with open(debug_file, "a") as f:
                    f.write(f"\n{'='*80}\n")
                    f.write(f"TIMESTAMP: {timestamp}\n")
                    f.write(f"TOPIC: {output_topic}\n")
                    f.write(f"MESSAGE: {pformat(message, 2)}\n")
                    f.write(f"MESSAGE SIZE: {len(str(message))} chars\n")
                    f.write(f"MESSAGE EMPTY: {message == {}}\n")
                    f.write(f"{'='*80}\n")
            except Exception as e:
                _log.warning(f"Failed to write debug file: {e}")

            _log.debug(f"Output: {output_topic}\n{pformat(message, 2)}")
            mb.send(topic=output_topic, message=message)
