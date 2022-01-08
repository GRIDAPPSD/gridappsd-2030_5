import argparse
import socket

from dataclasses import dataclass
from typing import List

import yaml


IEEE_9500_FINAL = "_EE71F6C9-56F0-4167-A14E-7F4C71F10EAA"

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
    a configuration file that the service can use.  The servcie
    will generate a pki for each of the devices and the service
    itself.

    See the service documentation for that.
    """
    # Use query from gridappsd to get information that
    # we want for the system.
    from Queries import QueryAllDERGroups, QueryBattery

    a = QueryBattery(modelid)

    with open(output_file, "w") as fp:
        results: List[DERDevice] = []
        for data in a["data"]["results"]["bindings"]:
            der = DERDevice(
                name=data["name"]["value"],
                bus=data["bus"]["value"],
                p=float(data["p"]["value"]),
                q=float(data["q"]["value"]),
                state=data["state"]["value"],
                id=data["id"]["value"],
                ratedE=float(data["ratedE"]["value"]),
                storedE=float(data["storedE"]["value"]),
                ratedS=float(data["ratedS"]["value"]),
                ratedU=float(data["ratedU"]["value"]),
                phases=data["phases"]["value"],
                ipu=data["ipu"]["value"]
            )
            results.append(der)

        # Build the devices list with information
        # to build the system with.
        devices = []
        count = 2
        iproot = "127.0.0."
        for r in results:
            dev = {'hostname': r.id, "ip": f"{iproot}{count}"}
            dev.update(r.config_dict())
            devices.append(dev)

        output = {
            "devices": devices,
            "tls_repository": "~/tls",
            "server": socket.gethostname(),
            "openssl_cnf": "openssl.cnf"
        }
        yaml.dump(output, fp, indent=2)
        print([x for x in results])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("output_file")
    parser.add_argument("--modelid", default=IEEE_9500_FINAL)
    opts = parser.parse_args()

    build_config(opts.output_file, opts.modelid)