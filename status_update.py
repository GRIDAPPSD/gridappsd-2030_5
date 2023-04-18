import json

line1 = { "GUID": 308022149380, "ts": 1654281015, "txid": 4, "type": 2, 
         "metering": {},
         "capability": {"nomV":240 , "maxW": 10000}}

line2 = { "GUID": 308022149380, "ts": 1654281015, "txid": 5, "type": 2, 
         "metering": {"voltage":321, "activePower":93, "reactivePower": 12},
         "capability": {}, "settings": {}}

line3 = { "GUID": 308022149380, "ts": 1654281015, "txid": 6, "type": 2, 
         "metering": {}, "capability": {}, "settings": {"maxV": 250, "minV":209}}

with open("/var/tmp/status_resp_file.inp", "w") as f:
     json.dump(line1, f)
     f.write("\n")
     json.dump(line2, f)
     f.write("\n")
     json.dump(line3, f)
     f.write("\n")

