# Server Configuration

The server configuration is made up of several configuration files.  The first of which is the main
configuration file.  The main configuration file will hold links to other configurations for the
server.

## Main Configuration File

The main configuration file holds information related to the current devices available and whether they
are created before registering or not.  It also holds the main ip address of the server and a proxy
if necessary for keeping traffic alive.  The final thing for the main configuraiton is the location
of a repository of private and public certificataes for the server.  Clients should be given the
server certificate and client certificate for connecting to the server via https.

```yaml
---
#server_hostname: 127.0.0.1:8070
#proxy_hostname: 0.0.0.0:7443
server_hostname: 0.0.0.0:7443

tls_repository: "~/tls"
openssl_cnf: "openssl.cnf"

server_mode: enddevices_register_access_only
# server_mode: enddevices_create_on_start

debug_device: dev1

DERControlListFile: DERControlList.yml
DERProgramListFile: DERProgramList.yml
DERCurveListFile: DERCurveList.yml

# Device names available for control
devices:
  - id: dev2
    device_category_type: FUEL_CELL
    pin: 12345

```

## DERControlLists.yml Configuration

Controlling DER assets from the utility server is based upon a standard set of control
parameters.  The DERControlLists.yml file is where lists of these parameters are stored.  There
can be multiple lists specified in this file.  The following are a full list of the codes
available for each of the lists.  Following the list of all of them is an example with default
der control and 

```yaml
# 
- DERControlName: AllProperties
  opModConnect: true
  opModEnergize: false
  opModFixedPFAbsorbW:
  opModFixedPFInjectW:
  opModFixedVar:
  opModFixedW:
  opModFreqDroop:
  opModFreqWatt:
  opModHFRTMayTrip:
  opModHFRTMustTrip:
  opModHVRTMayTrip:
  opModHVRTMomentaryCessation:
  opModHVRTMustTrip:
  opModLFRTMayTrip:
  opModLFRTMustTrip:
  opModLVRTMayTrip:
  opModLVRTMomentaryCessation:
  opModLVRTMustTrip:
  opModMaxLimW:
  opModTargetVar:
  opModTargetW:
  opModVoltVar:
  opModVoltWatt:
  opModWattPF:
  opModWattVar:
  rampTms: 
```

As a "real world" example of the DERControlLists.yml file I have contrived the following
with a DefaultDERControl and 3 other lists that can be used for programs. 

```yaml
# The default is used when a DER is not being controlled by any program
default: DefaultDERControl
# List of controls
DERControls:
  # First DERControl is the default, because the DERControlName matches the default.
  # It does not have to be first in the list.
  - DERControlName: DefaultDERControl
    description: "Default DER Control"
    opModConnect: true
    opModEnergize: false
  # Second DERControl
  - DERControlName: energized
    description: "An Energized DER ready to run"
    opModConnect: true
    opModEnergize: true
  # Third DERControl
  - DERControlName: 
```

