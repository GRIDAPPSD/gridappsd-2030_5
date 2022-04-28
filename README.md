# GridAPPS-D IEEE 2030.5 Server

## Overview

The GridAPPS-D IEEE 2030.5 Server implements the Common Smart Inverter Profile (CSIP).  The server
can work in both in-band and out-of-band registration models detailed in  CCIP Implementation Guide v2 
section 6.1.3 and 6.1.4 respectively.  

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
  #
  # An enumeration has been created at ieee_2030_5/models/device_category.py for you to
  # enter the types of devices supported.
  device_category_type: WATER_HEATER
  
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

## Client Connectivity

The server will expose an endpoint of beginning with https://myserver/dcap.  From there
a client will be able to traverse and do any PUT, POST, GET, and DELETE operations specified
in the 2030.5 test procedures.
