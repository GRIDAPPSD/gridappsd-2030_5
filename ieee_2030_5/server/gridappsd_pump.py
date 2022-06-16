import json
import atexit
import os
import sys
import time
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from pprint import pprint, pformat

from gridappsd.field_interface import MessageBusDefinition, ContextManager
from gridappsd.field_interface.agents import FeederAgent, SecondaryAreaAgent

from Queries import QueryAllDERGroups, QueryBattery, QuerySolar, QueryInverter
from ieee_2030_5.models import Resource, PowerStatus, DERCapability, UsagePoint
from ieee_2030_5.models.end_devices import EndDevices


class DataPumpFeederAgent(FeederAgent):

    def __init__(self, upstream_message_bus_def: MessageBusDefinition,
                 downstream_message_bus_def: MessageBusDefinition = None,
                 feeder_dict=None, simulation_id=None):
        super().__init__(upstream_message_bus_def, downstream_message_bus_def, feeder_dict, simulation_id)
    #TODO remove first four
    def on_measurement(self, peer, sender, bus, topic, headers, message):
        # with open("feeder.txt", "a") as fp:
        #     fp.write(json.dumps(message))
        print("Feeder!")
        print(message)

class DataPumperAgent(SecondaryAreaAgent):
    def __init__(self, upstream_message_bus_def: MessageBusDefinition, downstream_message_bus_def: MessageBusDefinition,
                 secondary_area_dict=None, simulation_id=None):
        super().__init__(upstream_message_bus_def, downstream_message_bus_def, secondary_area_dict, simulation_id)

    def on_measurement(self, peer, sender, bus, topic, headers, message):
        # with open("secondary.txt", "a") as fp:
        #     if "_4c491539-dfc1-4fda-9841-3bf10348e2fa" in json.dumps(message):
        #         print("Woot found it!")
        #         sys.exit()
        #     fp.write(json.dumps(message))
        print("Secondary Area")
        print(message)

def start_data_pump(msg_bus_def: MessageBusDefinition, end_devices: EndDevices):

    atexit.register(stop_data_pump)

def stop_data_pump():
    pass


if __name__ == '__main__':
    os.environ["GRIDAPPSD_USER"] = "system"
    os.environ["GRIDAPPSD_PASSWORD"] = "manager"
    os.environ["GRIDAPPSD_ADDRESS"] = "gridappsd"
    os.environ["GRIDAPPSD_PORT"] = "61613"

    config_file = """
connections:
  id: _49AD8E07-3BF9-A4E2-CB8F-C3722F837B62
  is_ot_bus: true
  connection_type: CONNECTION_TYPE_GRIDAPPSD
  connection_args:
    GRIDAPPSD_ADDRESS: tcp://gridappsd:61613
    GRIDAPPSD_USER: system
    GRIDAPPSD_PASSWORD: manager
"""
    Path("tmp.file.yml").write_text(config_file)
    system_bus_def = MessageBusDefinition.load("tmp.file.yml")
    feeder_id = "_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62"
    simulation_id = "1160276262"

    ieee_resources = []
    inverters = QueryInverter(feeder_id)


    # Power status of a resource contains

    context = ContextManager.get_context_by_feeder(feeder_id)
    bus_refs = defaultdict(list)

    for switch_area in context['data']['switch_areas']:
        for secondary_area in switch_area['secondary_areas']:
            for binding in inverters['data']['results']['bindings']:

                # TODO: Change to use id later...Topo processor is using pecid for now.
                pprint(binding['pecid']['value'])
                mrid = binding['pecid']['value']
                other_mrid = binding['id']['value']
                ieee_resources.append(
                    UsagePoint(mRID=mrid)
                )
                if mrid in secondary_area['addressable_equipment']:
                    new_area = deepcopy(secondary_area)
                    new_area['addressable_equipment'] = [mrid, other_mrid]
                    new_area['unaddressable_equipment'] = []

                    bus_refs[secondary_area['message_bus_id']].append(new_area)

    pprint(bus_refs)
    feeder = context['data']
    Path("data.dump.json").write_text(pformat(context['data'], indent=2))
    data = Path("data.dump.json").read_text()
    for p in ieee_resources:
        if p.mRID in data:
            print(f"Found: {p.mRID}")
        else:
            print(f"Not found: {p.mRID}")
    # feeder_agent = DataPumpFeederAgent(upstream_message_bus_def=system_bus_def,
    #                                    feeder_dict=feeder,
    #                                    simulation_id=simulation_id)
    # feeder_agent.connect()
    for bus_id, secondary_area in bus_refs.items():
        bus_def = deepcopy(system_bus_def)
        bus_def.id = bus_id
        for area in secondary_area:
            dpa = DataPumperAgent(system_bus_def, downstream_message_bus_def=bus_def, secondary_area_dict=area,
                                  simulation_id=simulation_id)
            dpa.connect()

    while True:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            print("Exiting sample")
            break
    #         break
    # coordinating_agent.spawn_distributed_agent(feeder_agent)
    # addressable = context["addressable_equipment"]
    # print(addressable)
