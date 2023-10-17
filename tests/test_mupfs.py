from typing import List

import ieee_2030_5.models as m
from ieee_2030_5.client import IEEE2030_5_Client

mirror_usage_points: List[m.MirrorUsagePoint] = [
    m.MirrorUsagePoint(mRID="5509D69F8B3535950000000000009182",
                       description="DER Inverter Real Power",
                       roleFlags=49,
                       serviceCategoryKind=0,
                       status=0,
                       MirrorMeterReading=m.MirrorMeterReading(
                           mRID="5509D69F8B3535950000000000009182",
                           description="Real Power(W)",
                           ReadingType=m.ReadingType(accumulationBehaviour=12,
                                                     commodity=1,
                                                     dataQualifier=2,
                                                     intervalLength=300,
                                                     powerOfTenMultiplier=0,
                                                     uom=38)))
    # ,
    # m.MirrorUsagePoint(
    #     mRID="5509D69F8B3535950000000000009184",
    #     description="DER Inverter Reactive Power",
    #     roleFlags=49,
    #     serviceCategoryKind=0,
    #     status=0,
    #     MirrorMeterReading=m.MirrorMeterReading(
    #         mRID="5509D69F8B3535950000000000009184",
    #         description="Reactive Power(VAr) Set",
    #         ReadingType=m.ReadingType(
    #             accumulationBehaviour=12,
    #             commodity=1,
    #             dataQualifier=2,
    #             intervalLength=300,
    #             powerOfTenMultiplier=0,
    #             uom=38
    #         )
    #     )
    # )
]


def test_create_update_mup(first_client: IEEE2030_5_Client):

    dcap: m.DeviceCapability = first_client.device_capability()

    assert dcap.MirrorUsagePointListLink is not None
    upt_loc_list: List[str] = []

    for mup in mirror_usage_points:
        status, loc = first_client.create_mirror_usage_point(mup)
        assert status == 201
        mup_data = first_client.get(loc)
        assert mup_data
        upt_loc_list.append(loc)

    for mup in mirror_usage_points:
        status, loc = first_client.create_mirror_usage_point(mup)
        assert status == 204

    for loc in upt_loc_list:
        upt_loc = loc.replace('mup', 'upt')
        upt = first_client.get(upt_loc)
        assert upt
        assert isinstance(upt, m.UsagePoint)
        assert upt_loc == upt.href
