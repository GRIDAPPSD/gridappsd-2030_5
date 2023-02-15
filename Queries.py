import sys
from pprint import pprint
from typing import Optional

import cimlab.data_profile.rc4_2021 as cim
from cimlab.loaders import ConnectionParameters, Parameter
from cimlab.loaders.blazegraph.blazegraph import BlazegraphConnection
from cimlab.models import DistributedModel
from gridappsd import GridAPPSD

# import importlib
# cim_profile = 'rc4_2021'
# cim = importlib.import_module('cimlab.data_profile.' + cim_profile)


# sort PowerElectronicsUnits
def get_inverter_buses(network_area):
    if cim.PowerElectronicsConnection in network_area.typed_catalog:
        network_area.get_all_attributes(cim.PowerElectronicsConnection)
        network_area.get_all_attributes(cim.PowerElectronicsConnectionPhase)
        network_area.get_all_attributes(cim.Terminal)
        network_area.get_all_attributes(cim.Analog)

        print('\n \n EXAMPLE 6: GET ALL INVERTER PHASES AND BUSES')
        for pec in network_area.typed_catalog[cim.PowerElectronicsConnection].values():
            print('\n name: ', pec.name, pec.mRID)
            print('p = ', pec.p, 'q = ', pec.q)
            node1 = pec.Terminals[0].ConnectivityNode
            print('bus: ', node1.name, node1.mRID)
            for pec_phs in pec.PowerElectronicsConnectionPhases:
                print('phase ', pec_phs.phase, ': ', pec_phs.mRID)

            for meas in pec.Measurements:
                print('Measurement: ', meas.name, meas.mRID)
                print('type:', meas.measurementType, 'phases:', meas.phases)


topic = "goss.gridappsd.request.data.topology"
#feeder_mrid = "_C07972A7-600D-4AA5-B254-4CAA4263560E"    # Ochre 13-node
feeder_mrid = "_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62"    # 13-node
# feeder_mrid = "_E407CBB6-8C8D-9BC9-589C-AB83FBF0826D"    # 123-node
message = {"requestType": "GET_SWITCH_AREAS", "modelID": feeder_mrid, "resultFormat": "JSON"}

gapps = GridAPPSD(username="system", password="manager")

print(gapps.query_model_names())
sys.exit()

topology_response = gapps.get_response(topic, message, timeout=30)
# Blazegraph connection for running outside the container
params = ConnectionParameters(
    [Parameter(key="url", value="http://localhost:8889/bigdata/namespace/kb/sparql")])
bg = BlazegraphConnection(params, 'rc4_2021')

# Initialize Model
feeder = cim.Feeder(mRID=feeder_mrid)
network = DistributedModel(connection=bg, feeder=feeder, topology=topology_response['feeders'])

for switch_area in network.switch_areas:
    get_inverter_buses(switch_area)
    for secondary_area in switch_area.secondary_areas:
        get_inverter_buses(secondary_area)

print(network.typed_catalog.get(cim.PowerElectronicsConnection))

# feeder = cim.Feeder(mRID=feeder_mrid)
# network = DistributedModel(connection=bg, feeder=feeder, topology=topology_response['feeders'])

sys.exit()
import atexit

from gridappsd import GridAPPSD

conn: Optional[GridAPPSD] = None


def get_conn() -> GridAPPSD:
    global conn
    if conn is None:
        conn = GridAPPSD()
        atexit.register(conn.disconnect)
    return conn


def QuerySynchronousMachine(feeder_id):
    querySynchronousMachine = """# SynchronousMachine - DistSyncMachine
    PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c:  <http://iec.ch/TC57/CIM100#>
    SELECT ?name ?bus (group_concat(distinct ?phs;separator="\\n") as ?phases) ?ratedS ?ratedU ?p ?q ?id ?fdrid WHERE {
      VALUES ?fdrid {"%s"}  # 123 bus
     ?s r:type c:SynchronousMachine.
     ?s c:IdentifiedObject.name ?name.
     ?s c:Equipment.EquipmentContainer ?fdr.
     ?fdr c:IdentifiedObject.mRID ?fdrid.
      #bind(strafter(str(?fdridraw), "_") as ?fdrid).
     ?s c:SynchronousMachine.ratedS ?ratedS.
     ?s c:SynchronousMachine.ratedU ?ratedU.
     ?s c:SynchronousMachine.p ?p.
     ?s c:SynchronousMachine.q ?q. 
     ?s c:IdentifiedObject.mRID ?id.
     #bind(strafter(str(?s),"#_") as ?id).
     OPTIONAL {?smp c:SynchronousMachinePhase.SynchronousMachine ?s.
     ?smp c:SynchronousMachinePhase.phase ?phsraw.
       bind(strafter(str(?phsraw),"SinglePhaseKind.") as ?phs) }
     ?t c:Terminal.ConductingEquipment ?s.
     ?t c:Terminal.ConnectivityNode ?cn. 
     ?cn c:IdentifiedObject.name ?bus
    }
    GROUP by ?name ?bus ?ratedS ?ratedU ?p ?q ?id ?fdrid
    ORDER by ?name
    """ % feeder_id
    results = get_conn().query_data(querySynchronousMachine)
    return results


def QuerySolar(feeder_id):
    querySolar = """# Solar - DistSolar
    PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c:  <http://iec.ch/TC57/CIM100#>
    SELECT ?name ?bus ?ratedS ?ratedU ?ipu ?p ?q ?fdrid ?id (group_concat(distinct ?phs;separator="\\n") as ?phases) WHERE {
    ?s r:type c:PhotovoltaicUnit.
    ?s c:IdentifiedObject.name ?name.
    ?s c:IdentifiedObject.mRID ?id.
    ?pec c:PowerElectronicsConnection.PowerElectronicsUnit ?s.
    # feeder selection options - if all commented out, query matches all feeders
    VALUES ?fdrid {"%s"}  # 123 bus
    #VALUES ?fdrid {"_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62"}  # 13 bus
    #VALUES ?fdrid {"_5B816B93-7A5F-B64C-8460-47C17D6E4B0F"}  # 13 bus assets
    #VALUES ?fdrid {"_4F76A5F9-271D-9EB8-5E31-AA362D86F2C3"}  # 8500 node
    #VALUES ?fdrid {"_67AB291F-DCCD-31B7-B499-338206B9828F"}  # J1
    #VALUES ?fdrid {"_9CE150A8-8CC5-A0F9-B67E-BBD8C79D3095"}  # R2 12.47 3
     ?pec c:Equipment.EquipmentContainer ?fdr.
     ?fdr c:IdentifiedObject.mRID ?fdrid.
     #?pec c:IdentifiedObject.mRID ?id.
      #bind(strafter(str(?fdridraw), "_") as ?fdrid).
     ?pec c:PowerElectronicsConnection.ratedS ?ratedS.
     ?pec c:PowerElectronicsConnection.ratedU ?ratedU.
     ?pec c:PowerElectronicsConnection.maxIFault ?ipu.
     ?pec c:PowerElectronicsConnection.p ?p.
     ?pec c:PowerElectronicsConnection.q ?q.
     OPTIONAL {?pecp c:PowerElectronicsConnectionPhase.PowerElectronicsConnection ?pec.
     ?pecp c:PowerElectronicsConnectionPhase.phase ?phsraw.
       bind(strafter(str(?phsraw),"SinglePhaseKind.") as ?phs) }
     #bind(strafter(str(?s),"#_") as ?id).
     ?t c:Terminal.ConductingEquipment ?pec.
     ?t c:Terminal.ConnectivityNode ?cn. 
     ?cn c:IdentifiedObject.name ?bus
    }
    GROUP by ?name ?bus ?ratedS ?ratedU ?ipu ?p ?q ?fdrid ?id
    ORDER by ?name
    """ % feeder_id
    results = get_conn().query_data(querySolar)
    print(results)
    return results


def QueryBattery(feeder_id):
    queryBattery = """# Storage - DistStorage
    PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c:  <http://iec.ch/TC57/CIM100#>
    SELECT ?name ?bus ?ratedS ?ratedU ?ipu ?ratedE ?storedE ?state ?p ?q ?id ?fdrid (group_concat(distinct ?phs;separator="\\n") as ?phases) WHERE {
     ?s r:type c:BatteryUnit.
     ?s c:IdentifiedObject.name ?name.
     ?pec c:PowerElectronicsConnection.PowerElectronicsUnit ?s.
    # feeder selection options - if all commented out, query matches all feeders
    VALUES ?fdrid {"%s"}  # 123 bus
    #VALUES ?fdrid {"_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62"}  # 13 bus
    #VALUES ?fdrid {"_5B816B93-7A5F-B64C-8460-47C17D6E4B0F"}  # 13 bus assets
    #VALUES ?fdrid {"_4F76A5F9-271D-9EB8-5E31-AA362D86F2C3"}  # 8500 node
    #VALUES ?fdrid {"_67AB291F-DCCD-31B7-B499-338206B9828F"}  # J1
    #VALUES ?fdrid {"_9CE150A8-8CC5-A0F9-B67E-BBD8C79D3095"}  # R2 12.47 3
     ?pec c:Equipment.EquipmentContainer ?fdr.
     ?fdr c:IdentifiedObject.mRID ?fdrid.
      #bind(strafter(str(?fdridraw), "_") as ?fdrid).
     ?pec c:PowerElectronicsConnection.ratedS ?ratedS.
     ?pec c:PowerElectronicsConnection.ratedU ?ratedU.
     ?pec c:PowerElectronicsConnection.maxIFault ?ipu.
     ?s c:BatteryUnit.ratedE ?ratedE.
     ?s c:BatteryUnit.storedE ?storedE.
     ?s c:BatteryUnit.batteryState ?stateraw.
       bind(strafter(str(?stateraw),"BatteryState.") as ?state)
     ?pec c:PowerElectronicsConnection.p ?p.
     ?pec c:PowerElectronicsConnection.q ?q. 
     OPTIONAL {?pecp c:PowerElectronicsConnectionPhase.PowerElectronicsConnection ?pec.
     ?pecp c:PowerElectronicsConnectionPhase.phase ?phsraw.
       bind(strafter(str(?phsraw),"SinglePhaseKind.") as ?phs) }
     bind(strafter(str(?s),"#_") as ?id).
     ?t c:Terminal.ConductingEquipment ?pec.
     ?t c:Terminal.ConnectivityNode ?cn. 
     ?cn c:IdentifiedObject.name ?bus
    }
    GROUP by ?name ?bus ?ratedS ?ratedU ?ipu ?ratedE ?storedE ?state ?p ?q ?id ?fdrid
    ORDER by ?name
    """ % feeder_id

    results = get_conn().query_data(queryBattery)
    return results


def QueryInverter(feeder_id):
    queryInverter = """
    PREFIX r: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c: <http://iec.ch/TC57/CIM100#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT ?name ?bus ?ratedS ?ratedU ?ipu ?p ?q ?fdrid ?id ?pecid (group_concat(distinct ?phs;separator="\\n") as ?phases)  WHERE {
    VALUES ?fdrid {"%s"}
    #?s r:type c:PhotovoltaicUnit.
    #?s r:type c:BatteryUnit.
    ?s c:IdentifiedObject.name ?name.
    ?s c:IdentifiedObject.mRID ?id.
    ?pec c:PowerElectronicsConnection.PowerElectronicsUnit ?s.
    ?pec c:IdentifiedObject.mRID ?pecid.
    ?pec c:Equipment.EquipmentContainer ?fdr.
    ?fdr c:IdentifiedObject.mRID ?fdrid.
    ?pec c:PowerElectronicsConnection.ratedS ?ratedS.
    ?pec c:PowerElectronicsConnection.ratedU ?ratedU.
    ?pec c:PowerElectronicsConnection.maxIFault ?ipu.
    ?pec c:PowerElectronicsConnection.p ?p.
    ?pec c:PowerElectronicsConnection.q ?q.
    OPTIONAL {?pecp c:PowerElectronicsConnectionPhase.PowerElectronicsConnection ?pec.
    ?pecp c:PowerElectronicsConnectionPhase.phase ?phsraw.
    bind(strafter(str(?phsraw),"SinglePhaseKind.") as ?phs) }
    ?t c:Terminal.ConductingEquipment ?pec.
    ?t c:Terminal.ConnectivityNode ?cn.
    ?cn c:IdentifiedObject.name ?bus
    }
    GROUP by ?name ?bus ?ratedS ?ratedU ?ipu ?p ?q ?fdrid ?id ?pecid
    ORDER by ?name
    """ % feeder_id

    results = get_conn().query_data(queryInverter)
    return results


def QueryAllDERGroups(feeder_id):
    queryAllDERGroups = """#get all EndDeviceGroup
    PREFIX  xsd:  <http://www.w3.org/2001/XMLSchema#>
    PREFIX  r:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX  c:    <http://iec.ch/TC57/CIM100#>
    select ?mRID ?description (group_concat(distinct ?name;separator="\\n") as ?names) 
                              (group_concat(distinct ?device;separator="\\n") as ?devices)
                              (group_concat(distinct ?func;separator="\\n") as ?funcs) 
    VALUES ?fdrid {"%s"}
    where {
      ?q1 a c:EndDeviceGroup .
      ?q1 c:IdentifiedObject.mRID ?mRIDraw .
        bind(strafter(str(?mRIDraw), "_") as ?mRID).
      ?q1 c:IdentifiedObject.name ?name .
      ?q1 c:IdentifiedObject.description ?description .
      Optional{
        ?q1 c:EndDeviceGroup.EndDevice ?deviceobj .
        ?deviceobj c:IdentifiedObject.mRID ?deviceID .
        ?deviceobj c:IdentifiedObject.name ?deviceName .
        ?deviceobj c:EndDevice.isSmartInverter ?isSmart .
        bind(concat(strafter(str(?deviceID), "_"), ",", str(?deviceName), ",", str(?isSmart)) as ?device)
      }
      ?q1 c:DERFunction ?derFunc .
      ?derFunc ?pfunc ?vfuc .
      Filter(?pfunc !=r:type)
        bind(concat(strafter(str(?pfunc), "DERFunction."), ",", str(?vfuc)) as ?func)
    }
    Group by ?mRID ?description
    Order by ?mRID
    """ % feeder_id

    results = get_conn().query_data(queryAllDERGroups)
    return results
