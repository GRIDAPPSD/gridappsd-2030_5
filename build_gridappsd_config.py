import argparse
import socket

from dataclasses import dataclass
from pprint import pprint
from typing import List

import yaml

from ieee_2030_5.models import DeviceCategoryType

IEEE_9500_FINAL = "_EE71F6C9-56F0-4167-A14E-7F4C71F10EAA"
#IEEE_9500_FINAL = "_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62"
IEEE_13CK_NODE = "_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62"


@dataclass
class DERDevice:
    name: str
    bus: str
    p: float
    q: float
    state: str
    id: str
    ratedE: float
    storedE: float
    ratedS: float
    ratedU: float
    phases: str
    ipu: str

    def config_dict(self):
        """
        Creates a dictionary that can be used directly
        in the configuration of the 2030.5 service.
        """
        return self.__dict__


def build_config(output_file: str, modelid: str):
    """
    This function builds a configuration file for the server
    based upon the passed model and output file.   The model
    will quiery the Batteries available in the model and write
    a configuration file that the service can use.  The service
    will generate a pki for each of the devices and the service
    itself.

    See the service documentation for that.
    """
    # Use query from gridappsd to get information that
    # we want for the system.
    from Queries import QueryAllDERGroups, QueryBattery, QuerySolar, QuerySynchronousMachine, QueryInverter

    a = QueryBattery(modelid)
    b = QuerySynchronousMachine(modelid)
    c = QuerySolar(modelid)
    d = QueryInverter(modelid)
    all_devices = set()
    set_to_check = set(
        ['_7CBFA8C8-F70E-4921-923C-E125555FDE99', '_A2B5CBC5-BFD5-495A-AB05-9CCBE2DE369B'])
    batteries = set()
    machines = set()
    solar = set()

    with open(output_file, "w") as fp:
        results = []
        # results: List[DERDevice] = []

        for data in a["data"]["results"]["bindings"]:
            if data["id"]["value"] in all_devices:
                print(f"{data['id']['value']} found {data['name']['value']} storage unit")

            if data["id"]["value"] in set_to_check:
                print(f"{data['id']['value']} is a storage unit")
            all_devices.add(data['id']['value'])
            der = dict(
                name=data["name"]["value"],
                bus=data["bus"]["value"],
                device_category_type=DeviceCategoryType.RESIDENTIAL_ENERGY_STORAGE_UNIT.name,
                p=float(data["p"]["value"]),
                q=float(data["q"]["value"]),
                state=data["state"]["value"],
                id=data["id"]["value"],
                ratedE=float(data["ratedE"]["value"]),
                storedE=float(data["storedE"]["value"]),
                ratedS=float(data["ratedS"]["value"]),
                ratedU=float(data["ratedU"]["value"]),
                phases=data["phases"]["value"],
                ipu=data["ipu"]["value"])
            batteries.add(data['id']['value'])
            results.append(der)

        for data in b["data"]["results"]["bindings"]:
            if data["id"]["value"] in all_devices:
                print(f"{data['id']['value']} found {data['name']['value']} generator")

            if data["id"]["value"] in set_to_check:
                print(f"{data['id']['value']} is a generator ")
            all_devices.add(data['id']['value'])
            der = dict(
                name=data["name"]["value"],
                bus=data["bus"]["value"],
                device_category_type=DeviceCategoryType.GENERATION_SYSTEMS.name,
                p=float(data["p"]["value"]),
                q=float(data["q"]["value"]),
                id=data["id"]["value"],
                ratedS=float(data["ratedS"]["value"]),
                ratedU=float(data["ratedU"]["value"]),
                phases=data["phases"]["value"],
            )
            machines.add(data['id']['value'])
            results.append(der)

        for data in c["data"]["results"]["bindings"]:
            if data["id"]["value"] in all_devices:
                print(f"{data['id']['value']} found {data['name']['value']} generator solar")
            if data["id"]["value"] in set_to_check:
                print(f"{data['id']['value']} is a solar gen")
            all_devices.add(data['id']['value'])
            der = dict(name=data["name"]["value"],
                       bus=data["bus"]["value"],
                       device_category_type=DeviceCategoryType.GENERATION_SYSTEMS.name,
                       p=float(data["p"]["value"]),
                       q=float(data["q"]["value"]),
                       id=data["id"]["value"],
                       ratedS=float(data["ratedS"]["value"]),
                       ratedU=float(data["ratedU"]["value"]),
                       phases=data["phases"]["value"],
                       ipu=data["ipu"]["value"])
            solar.add(data['id']['value'])
            results.append(der)

        for data in d["data"]["results"]["bindings"]:

            der = dict(
                name=data["name"]["value"],
                bus=data["bus"]["value"],
                device_category_type=DeviceCategoryType.SMART_INVERTER.name,
                p=float(data["p"]["value"]),
                q=float(data["q"]["value"]),
            # inverter mrid is pecid (PowerElectronicsConnection)
                id=data["pecid"]["value"],
                resource_id=data["id"]["value"],
            #pecid=data["pecid"]["value"],
                ratedS=float(data["ratedS"]["value"]),
                ratedU=float(data["ratedU"]["value"]),
                phases=data["phases"]["value"],
                ipu=data["ipu"]["value"])
            resource_id = data["id"]["value"]
            inverter_id = data["pecid"]["value"]
            if resource_id in solar:
                print(f"inverter: {inverter_id} contains solar resource_id {resource_id}")
            elif resource_id in machines:
                print(
                    f"inverter: {inverter_id} contains synchronous machine resource_id {resource_id}"
                )
            elif resource_id in batteries:
                print(f"inverter: {inverter_id} contains battery resource_id {resource_id}")
            else:
                print(f"inverter: {inverter_id} contains unknown resource_id {resource_id}")
            results.append(der)

        # Build the devices list with information
        # to build the system with.
        devices = []
        count = 2
        iproot = "127.0.0."
        for r in results:
            dev = {'hostname': r["id"], "ip": f"{iproot}{count}"}
            dev.update(r)
            devices.append(dev)

        output = {
            "devices": devices,
            "tls_repository": "~/tls",
            "server_hostname": socket.gethostname(),
            "server_mode": "enddevices_create_on_start",
            "openssl_cnf": "openssl.cnf"
        }
        yaml.dump(output, fp, indent=2)
        # print([x for x in results])

    # with open(output_file, "w") as fp:
    #     results: List[DERDevice] = []
    #     for data in b["data"]["results"]["bindings"]:
    #         der = DERDevice(
    #             name=data["name"]["value"],
    #             bus=data["bus"]["value"],
    #             p=float(data["p"]["value"]),
    #             q=float(data["q"]["value"]),
    #             state=data["state"]["value"],
    #             id=data["id"]["value"],
    #             ratedE=float(data["ratedE"]["value"]),
    #             storedE=float(data["storedE"]["value"]),
    #             ratedS=float(data["ratedS"]["value"]),
    #             ratedU=float(data["ratedU"]["value"]),
    #             phases=data["phases"]["value"],
    #             ipu=c["ipu"]["value"]
    #         )
    #         results.append(der)
    #
    #     # Build the devices list with information
    #     # to build the system with.
    #     devices = []
    #     count = 2
    #     iproot = "127.0.0."
    #     for r in results:
    #         dev = {'hostname': r.id, "ip": f"{iproot}{count}"}
    #         dev.update(r.config_dict())
    #         devices.append(dev)
    #
    #     output = {
    #         "devices": devices,
    #         "tls_repository": "~/tls",
    #         "server": socket.gethostname(),
    #         "openssl_cnf": "openssl.cnf"
    #     }
    #     yaml.dump(output, fp, indent=2)
    #     print([x for x in results])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("output_file")
    parser.add_argument("--modelid", default=IEEE_13CK_NODE)
    opts = parser.parse_args()

    build_config(opts.output_file, opts.modelid)
