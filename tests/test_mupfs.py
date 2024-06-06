from typing import List, Tuple

import ieee_2030_5.models as m
from ieee_2030_5.client import IEEE2030_5_Client
from ieee_2030_5.utils import dataclass_to_xml, xml_to_dataclass

mirror_usage_points: List[m.MirrorUsagePoint] = [
    xml_to_dataclass("""
        <MirrorUsagePoint xmlns="urn:ieee:std:2030.5:ns">
        <mRID>0600006CC8</mRID>
        <description>Gas Mirroring</description>
        <roleFlags>13</roleFlags>
        <serviceCategoryKind>1</serviceCategoryKind>
        <status>1</status>
        <deviceLFDI>00</deviceLFDI>
        <MirrorMeterReading>
        <mRID>0700006CC8</mRID>
        <Reading>
        <value>125</value>
        </Reading>
        <ReadingType>
        <accumulationBehaviour>9</accumulationBehaviour>
        <commodity>7</commodity>
        <dataQualifier>0</dataQualifier>
        <flowDirection>1</flowDirection>
        <powerOfTenMultiplier>3</powerOfTenMultiplier>
        <uom>119</uom>
        </ReadingType>
        </MirrorMeterReading>
        </MirrorUsagePoint>""")
]

# mirror_usage_points: List[m.MirrorUsagePoint] = [
#     m.MirrorUsagePoint(mRID="5509D69F8B3535950000000000009182",
#                        description="DER Inverter Real Power",
#                        roleFlags=49,
#                        serviceCategoryKind=0,
#                        status=0,
#                        MirrorMeterReading=m.MirrorMeterReading(
#                            mRID="5509D69F8B3535950000000000009182",
#                            description="Real Power(W)",
#                            ReadingType=m.ReadingType(accumulationBehaviour=12,
#                                                      commodity=1,
#                                                      dataQualifier=2,
#                                                      intervalLength=300,
#                                                      powerOfTenMultiplier=0,
#                                                      uom=38)))
#     # ,
#     # m.MirrorUsagePoint(
#     #     mRID="5509D69F8B3535950000000000009184",
#     #     description="DER Inverter Reactive Power",
#     #     roleFlags=49,
#     #     serviceCategoryKind=0,
#     #     status=0,
#     #     MirrorMeterReading=m.MirrorMeterReading(
#     #         mRID="5509D69F8B3535950000000000009184",
#     #         description="Reactive Power(VAr) Set",
#     #         ReadingType=m.ReadingType(
#     #             accumulationBehaviour=12,
#     #             commodity=1,
#     #             dataQualifier=2,
#     #             intervalLength=300,
#     #             powerOfTenMultiplier=0,
#     #             uom=38
#     #         )
#     #     )
#     # )
# ]


def create_mup_list_on_server(client: IEEE2030_5_Client) -> List[Tuple[int, str]]:
    client.device_capability()

    response = []
    for mup in mirror_usage_points:
        response.append(client.create_mirror_usage_point(mup))
    return response


def create_mmr_on_server(client: IEEE2030_5_Client, mup_loc: str) -> (int, str):
    mmr = xml_to_dataclass("""<MirrorMeterReading xmlns="urn:ieee:std:2030.5:ns">
        <mRID>0800006CC8</mRID>
        <MirrorReadingSet>
        <mRID>0900006CC8</mRID>
        <timePeriod>
        <duration>86400</duration>
        <start>1341579365</start>
        </timePeriod>
        <Reading>
        <value>9</value>
        <localID>00</localID>
        </Reading>
        <Reading>
        <value>11</value>
        <localID>01</localID>
        </Reading>
        <Reading>
        <value>10</value>
        <localID>02</localID>
        </Reading>
        <Reading>
        <value>13</value>
        <localID>03</localID>
        </Reading>
        <Reading>
        <value>12</value>
        <localID>04</localID>
        </Reading>
        <Reading>
        <value>11</value>
        <localID>05</localID>
        </Reading>
        <Reading>
        <value>10</value>
        <localID>06</localID>
        </Reading>
        <Reading>
        <value>16</value>
        <localID>07</localID>
        </Reading>
        <Reading>
        <value>9</value>
        <localID>08</localID>
        </Reading>
        <Reading>
        <value>7</value>
        <localID>09</localID>
        </Reading>
        <Reading>
        <value>6</value>
        <localID>0A</localID>
        </Reading>
        <Reading>
        <value>5</value>
        <localID>0B</localID>
        </Reading>
        <Reading>
        <value>8</value>
        <localID>0C</localID>
        </Reading>
        <Reading>
        <value>9</value>
        <localID>0D</localID>
        </Reading>
        <Reading>
        <value>10</value>
        <localID>0E</localID>
        </Reading>
        <Reading>
        <value>12</value>
        <localID>0F</localID>
        </Reading>
        <Reading>
        <value>14</value>
        <localID>10</localID>
        </Reading>
        <Reading>
        <value>13</value>
        <localID>11</localID>
        </Reading>
        <Reading>
        <value>11</value>
        <localID>12</localID>
        </Reading>
        <Reading>
        <value>7</value>
        <localID>13</localID>
        </Reading>
        <Reading>
        <value>8</value>
        <localID>14</localID>
        </Reading>
        <Reading>
        <value>10</value>
        <localID>15</localID>
        </Reading>
        <Reading>
        <value>10</value>
        <localID>16</localID>
        </Reading>
        <Reading>
        <value>10</value>
        <localID>17</localID>
        </Reading>
        </MirrorReadingSet>
        </MirrorMeterReading>""")

    status, loc = client.create_mirror_meter_reading(mup_loc, mmr)

    return status, loc


def test_no_mup_default(first_client: IEEE2030_5_Client):
    upt: m.UsagePointList = first_client.get("/upt")
    assert upt is not None
    assert isinstance(upt, m.UsagePointList)
    assert "/upt" == upt.href
    assert 0 == upt.all

    mup = first_client.get("/mup")
    assert mup is not None
    assert isinstance(mup, m.MirrorUsagePointList)
    assert "/mup" == mup.href
    assert 0 == mup.all


def test_create_mup(first_client: IEEE2030_5_Client):
    dcap: m.DeviceCapability = first_client.device_capability()

    assert dcap.MirrorUsagePointListLink is not None

    # List from conformance test, but not used here
    # active_power_type = m.ReadingType(accumulationBehaviour=12,
    #                                   commodity=1,
    #                                   flowDirection=19,
    #                                   kind=38,
    #                                   uom=38)
    # reactive_power_type = m.ReadingType(accumulationBehaviour=12,
    #                                     commodity=1,
    #                                     flowDirection=19,
    #                                     kind=37,
    #                                     uom=63)
    # voltage_type = m.ReadingType(accumulationBehaviour=12,
    #                              commodity=1,
    #                              flowDirection=1,
    #                              phase=0,
    #                              uom=29)
    # frequency_type = m.ReadingType(accumulationBehaviour=12, commodity=1, flowDirection=1, uom=33)

    # mirrormeterreadings = [
    #     m.MirrorMeterReading(mRID="5509D69F8B3535950000000000009182",
    #                          description="Real Power(W)",
    #                          ReadingType=active_power_type),
    #     m.MirrorMeterReading(mRID="5509D69F8B3535950000000000009184",
    #                          description="Reactive Power(VAr) Set",
    #                          ReadingType=reactive_power_type),
    #     m.MirrorMeterReading(mRID="5509D69F8B3535950000000000009186",
    #                          description="Voltage(V)",
    #                          ReadingType=voltage_type),
    #     m.MirrorMeterReading(mRID="5509D69F8B3535950000000000009188",
    #                          description="Frequency(Hz)",
    #                          ReadingType=frequency_type)
    # ]

    # mup_responses = []

    for mup in mirror_usage_points:

        status, loc = first_client.create_mirror_usage_point(mup)
        assert status == 201
        mup_data = first_client.get(loc)
        assert mup_data
        assert isinstance(mup_data, m.MirrorUsagePoint)
        assert loc == mup_data.href

    upt: m.UsagePointList = first_client.get(dcap.UsagePointListLink.href)
    assert upt is not None
    assert isinstance(upt, m.UsagePointList)
    assert len(mirror_usage_points) == upt.all and upt.all != 0
    for u in upt.UsagePoint:
        assert u.href is not None
        assert u.MeterReadingListLink is not None and u.MeterReadingListLink.href is not None

def test_post_mirror_reading_with_type(first_client: IEEE2030_5_Client):
    response: m.DeviceCapability = first_client.device_capability()

    active_power_type = m.ReadingType(accumulationBehaviour=12,
                                      commodity=1,
                                      flowDirection=19,
                                      kind=38,
                                      uom=38)
    active_power_reading = m.MirrorMeterReading(mRID="5509D69F8B353595000082",
                             description="Real Power(W)",
                             ReadingType=active_power_type),
    mup = m.MirrorUsagePoint(mRID="006CC8",
                             description="Inverter Active Power",
                                roleFlags=13,
                                serviceCategoryKind=1,
                                status=1,
                                deviceLFDI="00",
                                MirrorMeterReading=active_power_reading)
    status, loc = first_client.create_mirror_usage_point(mup)
    assert status == 201
    assert loc.startswith("/mup")

    mup_list: m.MirrorUsagePointList = first_client.get("/mup?l=1000")

    assert isinstance(mup_list, m.MirrorUsagePointList)
    assert mup_list is not None
    assert mup_list.all == 1

    mup: m.MirrorUsagePoint = first_client.get(loc)
    assert mup is not None
    assert mup.href == loc

    status, loc = first_client.create_mirror_meter_reading(loc, m.MirrorMeterReading(mRID="14772",
                                                                                     ReadingType=active_power_type,
                                                                                     Reading=[m.Reading(value=100)]))

    assert status == 201
    assert loc.startswith("/upt")

    upt_reading: m.MeterReading = first_client.get(loc)

    assert upt_reading is not None
    assert upt_reading.mRID == "14772"
    assert upt_reading.ReadingTypeLink.href is not None

    rt: m.ReadingType = first_client.get(upt_reading.ReadingTypeLink.href)
    assert rt is not None





def test_post_mirror_reading(first_client: IEEE2030_5_Client):
    response = create_mup_list_on_server(first_client)
    assert len(mirror_usage_points) == len(response)

    status, loc = create_mmr_on_server(first_client, response[0][1])
    assert 201 == status
    assert loc.startswith("/upt")

    mr_list: m.MeterReadingList = first_client.get(f"{loc}?l=1000")
    assert mr_list is not None
    assert 2 == mr_list.all
    assert 2 == mr_list.results
    assert isinstance(mr_list, m.MeterReadingList)
    assert len(mr_list.MeterReading) == 2
    mr = mr_list.MeterReading[1]
    mr_get = first_client.get(mr.href)
    assert mr_get is not None
    assert mr == mr_get

    assert mr.ReadingTypeLink.href is not None
    rt = first_client.get(mr.ReadingTypeLink.href)
    assert rt is not None
    assert isinstance(rt, m.ReadingType)

    assert mr.ReadingSetListLink is not None and mr.ReadingSetListLink.href is not None
    rs_list = first_client.get(mr.ReadingSetListLink.href)
    assert rs_list is not None
    assert isinstance(rs_list, m.ReadingSetList)

    assert rs_list.all == 1 and rs_list.results == 1
    rs = rs_list.ReadingSet[0]
    assert rs is not None
    assert isinstance(rs, m.ReadingSet)
    rs_get = first_client.get(rs.href)
    assert rs == rs_get

    assert rs.ReadingListLink is not None and rs.ReadingListLink.href is not None
    r_list = first_client.get(f"{rs.ReadingListLink.href}?l=10")
    assert r_list is not None and isinstance(r_list, m.ReadingList)
    r = r_list.Reading[0]
    assert 10 == len(r_list.Reading)
    assert r is not None and isinstance(r, m.Reading)
    r_get = first_client.get(r.href)
    assert r == r_get


def test_no_mup_default2(first_client: IEEE2030_5_Client):
    upt: m.UsagePointList = first_client.get("/upt")
    assert upt is not None
    assert isinstance(upt, m.UsagePointList)
    assert "/upt" == upt.href
    assert 0 == upt.all

    mup = first_client.get("/mup")
    assert mup is not None
    assert isinstance(mup, m.MirrorUsagePointList)
    assert "/mup" == mup.href
    assert 0 == mup.all


def test_create_update_mup(first_client: IEEE2030_5_Client):
    response = create_mup_list_on_server(first_client)
    assert len(mirror_usage_points) == len(response)

    response2 = create_mup_list_on_server(first_client)
    assert len(mirror_usage_points) == len(response2)
    assert 204, response2[0][0]

    # dcap: m.DeviceCapability = first_client.device_capability()

    # assert dcap.MirrorUsagePointListLink is not None
    # upt_loc_list: List[str] = []

    # for mup in mirror_usage_points:
    #     status, loc = first_client.create_mirror_usage_point(mup)
    #     assert status == 201
    #     mup_data = first_client.get(loc)
    #     assert mup_data
    #     upt_loc_list.append(loc)

    # for mup in mirror_usage_points:
    #     status, loc = first_client.create_mirror_usage_point(mup)
    #     assert status == 204

    # for loc in upt_loc_list:
    #     upt_loc = loc.replace('mup', 'upt')
    #     upt = first_client.get(upt_loc)
    #     assert upt
    #     assert isinstance(upt, m.UsagePoint)
    #     assert upt_loc == upt.href
