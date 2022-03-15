# GridAPPS-D IEEE 2030.5 Server

## Setup

## Running the server

```commandline
usage: __main__.py [-h] [--no-validate] [--no-create-certs] config

positional arguments:
  config             Configuration file for the server.

optional arguments:
  -h, --help         show this help message and exit
  --no-validate      Allows faster startup since the resolving of addresses is
                     not done!
  --no-create-certs  If specified certificates for for client and server will
                     not be created.
```

### Configuration

The configuration file that is passed to the main has the following format.

```yaml
# path to openssl.cnf that is in the repository
# do not change this file as it is used as a template
openssl_cnf: openssl.cnf

# binding ip address for the server
server_hostname: 0.0.0.0

# Location of certificates to be used/created with the server.
tls_repository: ~/tls

# devices that are to be registered with the 2030.5 server.  It is expedted
# that a client connects to the server using a certificate available in
# the tls_repository.
#
devices:
  # hostname is used certificate generation and management.
- hostname: 6F33B5DD-50CD-4599-8559-3299BC22D9F0
  bus: m2001-ess1  
  # Device category type is the 2030.5 DeviceCategoryType bit field mentioned
  # in documentation below.
  device_category_type: 3
  
  id: 6F33B5DD-50CD-4599-8559-3299BC22D9F0
  ip: 127.0.0.2
  ipu: '1.1111111'
  name: battery1
  p: 0.0
  phases: ''
  q: 0.0
  ratedE: 500000.0
  ratedS: 250000.0
  ratedU: 12470.0
  state: Waiting
  storedE: 500000.0
```
#### Device Category Types
```
# Bit positions SHALL be defined as follows:
# 0 - Programmable Communicating Thermostat
# 1 - Strip Heaters
# 2 - Baseboard Heaters
# 3 - Water Heater
# 4 - Pool Pump
# 5 - Sauna
# 6 - Hot Tub
# 7 - Smart Appliance
# 8 - Irrigation Pump
# 9 - Managed Commercial and Industrial (C&amp;amp;I) Loads
# 10 - Simple Misc. (Residential On/Off) Loads
# 11 - Exterior Lighting
# 12 - Interior Lighting
# 13 - Load Control Switch
# 14 - Energy Management System
# 15 - Smart Energy Module
# 16 - Electric Vehicle
# 17 - EVSE
# 18 - Virtual or Mixed DER
# 19 - Reciprocating Engine
# 20 - Fuel Cell
# 21 - Photovoltaic System
# 22 - Combined Heat and Power
# 23 - Combined PV and Storage
# 24 - Other Generation System
# 25 - Other Storage System
# All other values reserved.
```

## Client Connectivity

The server will expose an endpoint of begining with https://myserver/dcap.  From there
a client will be able to traverse and do any PUT, POST, GET, and DELETE operations specified
in the 2030.5 test procedures.
