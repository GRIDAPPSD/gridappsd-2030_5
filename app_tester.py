import json
import logging
import os
import random
import sys
import time
from pprint import pformat

from gridappsd import DifferenceBuilder, GridAPPSD, topics

DEFAULT_MESSAGE_PERIOD = 30
import csv

# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
#                     format="%(asctime)s - %(name)s;%(levelname)s|%(message)s",
#                     datefmt="%Y-%m-%d %H:%M:%S")
# Only log errors to the stomp logger.
logging.getLogger("stomp.py").setLevel(logging.ERROR)

_log = logging.getLogger(__name__)


class IEEE2030_5:
    """A simple class that handles publishing forward and reverse differences

    The object should be used as a callback from a GridAPPSD object so that the
    on_message function will get called each time a message from the simulator.  During
    the execution of on_meessage the `CapacitorToggler` object will publish a
    message to the simulation_input_topic with the forward and reverse difference specified.
    """

    def __init__(self, gridappsd_obj):
        """Create a ``CapacitorToggler`` object

        This object should be used as a subscription callback from a ``GridAPPSD``
        object.  This class will toggle the capacitors passed to the constructor
        off and on every five messages that are received on the ``fncs_output_topic``.

        Note
        ----
        This class does not subscribe only publishes.

        Parameters
        ----------
        simulation_id: str
            The simulation_id to use for publishing to a topic.
        gridappsd_obj: GridAPPSD
            An instatiated object that is connected to the gridappsd message bus
            usually this should be the same object which subscribes, but that
            isn't required.
        capacitor_list: list(str)
            A list of capacitors mrids to turn on/off
        """
        self._gapps = gridappsd_obj

    def on_message(self, headers, message):
        """Handle incoming messages on the simulation_output_topic for the simulation_id

        Parameters
        ----------
        headers: dict
            A dictionary of headers that could be used to determine topic of origin and
            other attributes.
        message: object
            A data structure following the protocol defined in the message structure
            of ``GridAPPSD``.  Most message payloads will be serialized dictionaries, but that is
            not a requirement.
        """

        if type(message) == str:
            message = json.loads(message)
        # print(f'message {message}')
        if message:
            # for v in message.values():
            #   print(f' v {v}')
            # Transform dictionary into required format
            # transformed_data = {v['name']: {
            #         'time stamp': v['timeStamp'],
            #         'SOC': v['value'] / 10000,
            #         'mRID': v['mRID']
            #     } for v in message.values()}

            transformed_data = {
                v["name"]: {
                    "time stamp": v["timeStamp"],
                    "SOC": (v["value"] if v["value"] is not None else 0) / 10000,
                    "mRID": v["mRID"],
                }
                for v in message.values()
            }

            _log.debug(f"IEEE 2030.5 server  ... transformed_data\n{pformat(transformed_data)}")

            # Specify the CSV file name
            csv_filename = "IEEE_2030_5_clients_house_data.csv"
            # Convert data into a DataFrame formatted for CSV output
            # Flatten the dictionary
            flattened_data = {
                f"{outer_key}_{inner_key}": inner_value
                for outer_key, inner_dict in transformed_data.items()
                for inner_key, inner_value in inner_dict.items()
            }

            # Check if file exists and clear it if it does
            if os.path.exists(csv_filename):
                open(csv_filename, "w").close()  # Empty the file before writing

            # Write the flattened data to CSV
            with open(csv_filename, mode="a", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=flattened_data.keys())

                # Write header if file is empty
                if file.tell() == 0:
                    writer.writeheader()

                # Write row data
                writer.writerow(flattened_data)

            # Some demo for understanding object and measurement mrids. Print the status of several switches
            # timestamp = message["message"] ["timestamp"]
            # meas_value = message['message']['measurements']

            # print(f'meas_value received by the IEEE 2030.5 server  ... timestamp {timestamp} .... meas value {meas_value}')

            service_name = "IEEE_2030_5"
            simulation_id = ""
            send_topic = topics.application_input_topic(application_id=service_name, simulation_id=simulation_id)
            builder = DifferenceBuilder()
            for key, value in transformed_data.items():
                # print(f' key {key}')
                # print(f' value {value}')
                value_imp = int(random.uniform(600, 7000))
                builder.add_difference(
                    object_id=value["mRID"],
                    attribute="DERControl.DERControlBase.opModTargetW",
                    forward_value=dict(multiplier=1, value=value_imp),
                    reverse_value=dict(multiplier=1, value=value_imp),
                )

            message = builder.get_message()

            # #print(f"Sending to topic {send_topic}")
            # #print(f"Message: {json.dumps(message, indent=2)}")
            _log.debug(f"Sending to topic {send_topic}")
            _log.debug(f"Message: {pformat(message)}")

            self._gapps.send(send_topic, message)


def _main():
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s;%(levelname)s|%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("stomp.py").setLevel(logging.ERROR)
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    _log.debug("Starting application")
    print("Application #starting!!!-------------------------------------------------------")

    gapps = GridAPPSD(username="system", password="manager")
    gapps.connect()

    app_2030_5 = IEEE2030_5(gapps)
    gapps.subscribe("/topic/goss.gridappsd.IEEE_2030_5.output", app_2030_5)

    while True:
        time.sleep(0.1)


if __name__ == "__main__":
    _main()
