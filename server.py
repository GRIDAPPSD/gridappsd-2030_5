
import argparse
import json
import pprint
import Queries
import logging
import time

# from lxml import etree
from gridappsd import GridAPPSD
from gridappsd import topics as t

conn = GridAPPSD()


def get_DERM_devices(feeder_id):
    # payload = conn._build_query_payload('QUERY', queryString=Queries.querySynchronousMachine)
    # request_topic = '.'.join((t.REQUEST_DATA, "powergridmodel"))
    # results = conn.get_response(request_topic, json.dumps(payload), timeout=30)
    # pprint.pprint(results)
    #
    # payload = conn._build_query_payload('QUERY', queryString=Queries.querySolar )
    # request_topic = '.'.join((t.REQUEST_DATA, "powergridmodel"))
    # results = conn.get_response(request_topic, json.dumps(payload), timeout=30)
    # pprint.pprint(results)
    #
    # payload = conn._build_query_payload('QUERY', queryString=Queries.queryBattery )
    # request_topic = '.'.join((t.REQUEST_DATA, "powergridmodel"))
    # results = conn.get_response(request_topic, json.dumps(payload), timeout=30)
    # pprint.pprint(results)

    # results = conn.query_data(Queries.querySynchronousMachine(feeder_id))
    # pprint.pprint(results)
    # results = Queries.QuerySolar(feeder_id)
    results = Queries.QuerySynchronousMachine(feeder_id)
    pprint.pprint(results)
    # results = conn.query_data(Queries.queryBattery(feeder_id)
    # pprint.pprint(results)


def _main():

    print("Service starting!!!-------------------------------------------------------")
    parser = argparse.ArgumentParser()
    parser.add_argument("simulation_id",
                        help="Simulation id to use for responses on the message bus.")
    parser.add_argument("request",
                        help="Query Request")
    opts = parser.parse_args()
    sim_request = json.loads(opts.request.replace("\'", ""))
    feeder_id = sim_request["power_system_config"]["Line_name"]
    get_DERM_devices(feeder_id)


if __name__ == "__main__":
    _main()
