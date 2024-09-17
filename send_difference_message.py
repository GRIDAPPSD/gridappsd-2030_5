import time

import gridappsd.topics as topics
import gridappsd.json_extension as json
from gridappsd import GridAPPSD
from gridappsd import DifferenceBuilder

gapps = GridAPPSD(username='system', password='manager')

gapps.connect()
assert gapps

service_name = "IEEE_2030_5"
simulation_id = ""
send_topic = topics.application_input_topic(application_id=service_name, simulation_id=simulation_id)

builder = DifferenceBuilder()
builder.add_difference(object_id="_4C4846A8-312B-4D03-BFF8-BCB58CAB4366",
                       attribute="DERControl.DERControlBase.opModTargetW",
                       forward_value=dict(multiplier=5, value=1),
                       reverse_value=dict(multiplier=1, value=1))

# builder.add_difference(object_id="_EB6BC0A1-FA4B-46CE-B26E-DD022AB62595",
#                        attribute="DERControl.description",
#                        forward_value="This is a change!",
#                        reverse_value="")

message = builder.get_message()

print(f"Sending to topic {send_topic}")
print(f"Message: {json.dumps(message, indent=2)}")

gapps.send(send_topic, message)

time.sleep(2)