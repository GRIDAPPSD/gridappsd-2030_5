import time

import gridappsd.json_extension as json
import gridappsd.topics as topics
from gridappsd import DifferenceBuilder, GridAPPSD

gapps = GridAPPSD(username="system", password="manager")

gapps.connect()
assert gapps

service_name = "IEEE_2030_5"
simulation_id = ""
send_topic = topics.application_input_topic(application_id=service_name, simulation_id=simulation_id)

builder = DifferenceBuilder()
builder.add_difference(
    object_id="_986AF5BC-D77F-439F-8704-0DD49B0732AA",
    attribute="DERControl.DERControlBase.opModTargetW",
    forward_value=dict(multiplier=5, value=25),
    reverse_value=dict(multiplier=5, value=25),
)

# builder.add_difference(object_id="_EB6BC0A1-FA4B-46CE-B26E-DD022AB62595",
#                        attribute="DERControl.description",
#                        forward_value="This is a change!",
#                        reverse_value="")

message = builder.get_message()

print(f"Sending to topic {send_topic}")
print(f"Message: {json.dumps(message, indent=2)}")

gapps.send(send_topic, message)


def gapps_results(headers, message):
    print(f"GridAPPS-D message bus {message}")


gapps.subscribe("/topic/goss.gridappsd.IEEE_2030_5.output", gapps_results)


time.sleep(2)
