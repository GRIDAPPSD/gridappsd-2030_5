from gridappsd import GridAPPSD

conn = GridAPPSD()


def QuerySynchronousMachine(feeder_id):
    querySynchronousMachine = """# SynchronousMachine - DistSyncMachine
    PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c:  <http://iec.ch/TC57/CIM100#>
    SELECT ?name ?bus (group_concat(distinct ?phs;separator="\\n") as ?phases) ?ratedS ?ratedU ?p ?q ?id ?fdrid WHERE {
      VALUES ?fdrid {"_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62"}
     ?s r:type c:SynchronousMachine.
     ?s c:IdentifiedObject.name ?name.
     ?s c:Equipment.EquipmentContainer ?fdr.
     ?fdr c:IdentifiedObject.mRID ?fdrid.
      #bind(strafter(str(?fdridraw), "_") as ?fdrid).
     ?s c:SynchronousMachine.ratedS ?ratedS.
     ?s c:SynchronousMachine.ratedU ?ratedU.
     ?s c:SynchronousMachine.p ?p.
     ?s c:SynchronousMachine.q ?q. 
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
    """
    results = conn.query_data(querySynchronousMachine)
    return results


# # another way from dermsgui.py in gridappsd-cim-interop
# # it's slower, and the eqid and id are the same
# querySynchronousMachine="""
# PREFIX r: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
# PREFIX c: <http://iec.ch/TC57/CIM100#>
# PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
# SELECT ?name ?bus ?ratedS ?ratedU ?p ?q (group_concat(distinct ?phs;separator="\\n") as ?phases) ?eqid ?fdrid WHERE {
# 	SELECT ?name ?bus ?ratedS ?ratedU ?p ?q ?eqid ?fdrid ?phs WHERE { ?s c:Equipment.EquipmentContainer ?fdr.
#  ?fdr c:IdentifiedObject.mRID ?fdrid.
#  ?s r:type c:SynchronousMachine.
#  ?s c:IdentifiedObject.name ?name.
#  ?s c:IdentifiedObject.mRID ?eqid.
#  ?s c:SynchronousMachine.ratedS ?ratedS.
#  ?s c:SynchronousMachine.ratedU ?ratedU.
#  ?s c:SynchronousMachine.p ?p.
#  ?s c:SynchronousMachine.q ?q.
#  ?t c:Terminal.ConductingEquipment ?s.
#  ?t c:Terminal.ConnectivityNode ?cn.
#  ?cn c:IdentifiedObject.name ?bus.
#  OPTIONAL {?smp c:SynchronousMachinePhase.SynchronousMachine ?s.
#  ?smp c:SynchronousMachinePhase.phase ?phsraw.
#    bind(strafter(str(?phsraw),"SinglePhaseKind.") as ?phs) } } ORDER BY ?name ?phs
#  } GROUP BY ?name ?bus ?ratedS ?ratedU ?p ?q ?eqid ?fdrid
#  ORDER BY ?name
# """

def QuerySolar(feeder_id):
    querySolar = """# Solar - DistSolar
    PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c:  <http://iec.ch/TC57/CIM100#>
    SELECT ?name ?bus ?ratedS ?ratedU ?ipu ?p ?q ?fdrid (group_concat(distinct ?phs;separator="\\n") as ?phases) WHERE {
    ?s r:type c:PhotovoltaicUnit.
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
    GROUP by ?name ?bus ?ratedS ?ratedU ?ipu ?p ?q ?fdrid
    ORDER by ?name
    """ % feeder_id
    results = conn.query_data(querySolar)
    return results


def QuerySolar1(feeder_id):
    querySolar = """
    PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c:  <http://iec.ch/TC57/CIM100#>
    SELECT ?feeder ?fid ?station ?sid ?subregion ?sgrid ?region ?rgnid WHERE {
     ?s r:type c:Feeder.
     ?s c:IdentifiedObject.name ?feeder.
     ?s c:IdentifiedObject.mRID ?fid.
     ?s c:Feeder.NormalEnergizingSubstation ?sub.
     ?sub c:IdentifiedObject.name ?station.
     ?sub c:IdentifiedObject.mRID ?sid.
     ?sub c:Substation.Region ?sgr.
     ?sgr c:IdentifiedObject.name ?subregion.
     ?sgr c:IdentifiedObject.mRID ?sgrid.
     ?sgr c:SubGeographicalRegion.Region ?rgn.
     ?rgn c:IdentifiedObject.name ?region.
     ?rgn c:IdentifiedObject.mRID ?rgnid.
    }
    ORDER by ?station ?feeder"""

    results = conn.query_data(querySolar)
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
    #VALUES ?fdrid {"%s"}  # 123 bus
    #VALUES ?fdrid {"_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62"}  # 13 bus
    #VALUES ?fdrid {"_5B816B93-7A5F-B64C-8460-47C17D6E4B0F"}  # 13 bus assets
    #VALUES ?fdrid {"_4F76A5F9-271D-9EB8-5E31-AA362D86F2C3"}  # 8500 node
    #VALUES ?fdrid {"_67AB291F-DCCD-31B7-B499-338206B9828F"}  # J1
    #VALUES ?fdrid {"_9CE150A8-8CC5-A0F9-B67E-BBD8C79D3095"}  # R2 12.47 3
     ?pec c:Equipment.EquipmentContainer ?fdr.
     ?fdr c:IdentifiedObject.mRID ?fdridraw.
      bind(strafter(str(?fdridraw), "_") as ?fdrid).
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

    results = conn.query_data(queryBattery)
    return results


def QueryAllDERGroups(feeder_id):
    queryAllDERGroups = """#get all EndDeviceGroup
    PREFIX  xsd:  <http://www.w3.org/2001/XMLSchema#>
    PREFIX  r:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX  c:    <http://iec.ch/TC57/CIM100#>
    select ?mRID ?description (group_concat(distinct ?name;separator="\\n") as ?names) 
                              (group_concat(distinct ?device;separator="\\n") as ?devices)
                              (group_concat(distinct ?func;separator="\\n") as ?funcs) 
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
    """% feeder_id

    results = conn.query_data(queryAllDERGroups)
    return results


queryDERGroupsByName = """#get all EndDeviceGroup
PREFIX  xsd:  <http://www.w3.org/2001/XMLSchema#>
PREFIX  r:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX  c:    <http://iec.ch/TC57/CIM100#>
select ?mRID ?description (group_concat(distinct ?name;separator="\\n") as ?names) 
 						  (group_concat(distinct ?device;separator="\\n") as ?devices)
 						  (group_concat(distinct ?func;separator="\\n") as ?funcs) 
where {{
  ?q1 a c:EndDeviceGroup .
  ?q1 c:IdentifiedObject.mRID ?mRIDraw .
    bind(strafter(str(?mRIDraw), "_") as ?mRID).
  ?q1 c:IdentifiedObject.name ?name .
  VALUES ?name {{{groupnames}}}
  ?q1 c:IdentifiedObject.description ?description .
  Optional{{
  	?q1 c:EndDeviceGroup.EndDevice ?deviceobj .
    ?deviceobj c:IdentifiedObject.mRID ?deviceID .
    ?deviceobj c:IdentifiedObject.name ?deviceName .
    ?deviceobj c:EndDevice.isSmartInverter ?isSmart .
    bind(concat(strafter(str(?deviceID), "_"), ",", str(?deviceName), ",", str(?isSmart)) as ?device)
  }}
  ?q1 c:DERFunction ?derFunc .
  ?derFunc ?pfunc ?vfuc .
  Filter(?pfunc !=r:type)
    bind(concat(strafter(str(?pfunc), "DERFunction."), ",", str(?vfuc)) as ?func)
}}
Group by ?mRID ?description
Order by ?mRID
"""

queryDERGroupsBymRID = """#get all EndDeviceGroup
PREFIX  xsd:  <http://www.w3.org/2001/XMLSchema#>
PREFIX  r:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX  c:    <http://iec.ch/TC57/CIM100#>
select ?mRID ?description (group_concat(distinct ?name;separator="\\n") as ?names) 
 						  (group_concat(distinct ?device;separator="\\n") as ?devices)
 						  (group_concat(distinct ?func;separator="\\n") as ?funcs) 
where {{
  ?q1 a c:EndDeviceGroup .
  ?q1 c:IdentifiedObject.mRID ?mRIDraw .
    bind(strafter(str(?mRIDraw), "_") as ?mRID).
  VALUES ?mRID {{{mRIDs}}}
  ?q1 c:IdentifiedObject.name ?name .
  ?q1 c:IdentifiedObject.description ?description .
  Optional{{
  	?q1 c:EndDeviceGroup.EndDevice ?deviceobj .
    ?deviceobj c:IdentifiedObject.mRID ?deviceID .
    ?deviceobj c:IdentifiedObject.name ?deviceName .
    ?deviceobj c:EndDevice.isSmartInverter ?isSmart .
    bind(concat(strafter(str(?deviceID), "_"), ",", str(?deviceName), ",", str(?isSmart)) as ?device)
  }}
  ?q1 c:DERFunction ?derFunc .
  ?derFunc ?pfunc ?vfuc .
  Filter(?pfunc !=r:type)
    bind(concat(strafter(str(?pfunc), "DERFunction."), ",", str(?vfuc)) as ?func)
}}
Group by ?mRID ?description
Order by ?mRID
"""


def QueryEndDevices(feeder_id):
    queryEndDevices = """
    PREFIX r: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c: <http://iec.ch/TC57/CIM100#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT ?name ?mrid ?issmart ?upoint #?upoint
    WHERE {
      ?s a c:EndDevice .
      ?s c:IdentifiedObject.name ?name .
      ?s c:IdentifiedObject.mRID ?rawmrid .
        bind(strafter(str(?rawmrid),"_") as ?mrid)
      ?s c:EndDevice.isSmartInverter ?issmart .
      ?s c:EndDevice.UsagePoint ?upraw .
        bind(strafter(str(?upraw),"#_") as ?upoint)
      #?upraw c:IdentifiedObject.name ?upointName .
      #?upraw c:IdentifiedObject.mRID ?upointID .
      #  bind(strafter(str(?upointID),"_") as ?upoint2)
    }
    ORDER by ?name
    """% feeder_id

    results = conn.query_data(queryAllDERGroups)
    return results

