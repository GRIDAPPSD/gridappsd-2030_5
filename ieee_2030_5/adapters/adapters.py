from dataclasses import dataclass, field
import threading
from typing import Callable, Dict, List, Union
from ieee_2030_5.data.indexer import add_href
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
import ieee_2030_5.adapters as adpt
from ieee_2030_5.adapters import Adapter, NotFoundError, ResourceListAdapter
from ieee_2030_5.config import ReturnValue

from copy import deepcopy
from datetime import datetime
import time

from blinker import Signal
import logging

_log = logging.getLogger(__name__)

DERCurveAdapter = Adapter[m.DERCurve](hrefs.curve_href(), generic_type=m.DERCurve)
DERControlAdapter = Adapter[m.DERControl]("/derc", generic_type=m.DERControl)
DERCurveAdapter = Adapter[m.DERCurve](hrefs.curve_href(), generic_type=m.DERCurve)
DERProgramAdapter = Adapter[m.DERProgram](hrefs.der_program_href(), generic_type=m.DERProgram)
FunctionSetAssignmentsAdapter = Adapter[m.FunctionSetAssignments](
    url_prefix="/fsa", generic_type=m.FunctionSetAssignments)

EndDeviceAdapter = Adapter[m.EndDevice](hrefs.get_enddevice_href(), generic_type=m.EndDevice)
DeviceCapabilityAdapter = Adapter[m.DeviceCapability]("/dcap", generic_type=m.DeviceCapability)
# Generally the href will only be in the context of an end device.
RegistrationAdapter = Adapter[m.Registration](url_prefix="/reg", generic_type=m.Registration)
DERAdapter = Adapter[m.DER](url_prefix="/der", generic_type=m.DER)
UsagePointAdapter = Adapter[m.UsagePoint](url_prefix="/upt", generic_type=m.UsagePoint)
ListAdapter = ResourceListAdapter()

def _create_or_update_reading(reading_list_href: str, reading: m.Reading) -> ReturnValue:
    updated = False

    saved_reading: m.Reading | None = None
    # Attempt to find an existing reading with the same loc
    try:
        saved_reading = adpt.ListAdapter.get_item_by_prop(reading_list_href, 'localID', reading.localID)
    except NotFoundError:
        # If not found then we add the reading to the list of readings.
        pass

    if saved_reading is None:
        saved_reading = adpt.ListAdapter.append_and_increment_href(reading_list_href, reading)
    else:
        updated = True
        adpt.ListAdapter.set(reading_list_href, int(saved_reading.href.split(hrefs.SEP)[-1]), reading)

    return ReturnValue(True, an_object=saved_reading, was_update=updated, location=saved_reading.href)



def _create_or_update_reading_set(reading_set_list_href: str, mirror_reading_set: m.MirrorReadingSet) -> ReturnValue:

    update = False
    current_mmr_reading_set: m.MirrorReadingSet | None = None

    current_mmr_reading_set = adpt.ListAdapter.get_by_mrid(mirror_reading_set.href, mirror_reading_set.mRID)

    if current_mmr_reading_set is None:
        mmr_href = reading_set_list_href.replace(hrefs.DEFAULT_UPT_ROOT, hrefs.DEFAULT_MUP_ROOT)
        current_mmr_reading_set = adpt.ListAdapter.append_and_increment_href(
            mmr_href, mirror_reading_set)
        new_rs = m.ReadingSet(description=mirror_reading_set.description,
                              timePeriod=mirror_reading_set.timePeriod,
                              version=mirror_reading_set.version)
        current_rs = adpt.ListAdapter.append_and_increment_href(reading_set_list_href, new_rs)
    else:
        update = True
        current_rs = adpt.ListAdapter.get(reading_set_list_href,
                                          key=int(mirror_reading_set.href.split(hrefs.SEP)[-1]))
        current_rs.description = mirror_reading_set.description
        current_rs.timePeriod = mirror_reading_set.timePeriod
        current_rs.version = mirror_reading_set.version
        adpt.ListAdapter.set(reading_set_list_href,
                             int(mirror_reading_set.href.split(hrefs.SEP)[-1]), current_rs)

    return ReturnValue(True, current_rs, update, current_rs.href)

    # # Update the href of the mirror reading set. so it can be referenced correctly
    # # within the list of mirror reading sets.
    # new_rs_index = adpt.ListAdapter.list_size(reading_set_list_href)
    # mirror_rs_href = hrefs.SEP.join([mirror_reading_set.href, str(new_rs_index)])
    # mirror_reading_set.href = mirror_rs_href

    # adpt.ListAdapter.append(mirror_reading_set.href), mirror_reading_set)

    # # new_rs: m.ReadingSet = m.ReadingSet(href=hrefs.SEP.join([reading_set_list_href, str(new_rs_index)]),
    # #                       description=mirror_reading_set.description,
    # #                       timePeriod=mirror_reading_set.timePeriod,
    # #                       version=mirror_reading_set.version,
    # #                       ReadingTypeLink=adpt.ListAdapter.get_single(mirror_reading_set.ReadingTypeLink,)
    # # # saved_rs: m.ReadingSet = adpt.ListAdapter.append_and_increment_href(reading_set_list_href, new_rs)

    # # # adpt.ListAdapter.append(reading_set_list_href),
    # # #                         mirror_reading_set.Reading)


def _create_or_update_meter_reading(upt_list_href: str, mmr: m.MirrorMeterReading,
                          ) -> ReturnValue:
    """
    Create a MeterReading from a MirrorMeterReading and add it to the UsagePoint.

    Note: The passed mmr MUST have the uri set ot the actual mmr not the list!

    """

    saved_mr = adpt.ListAdapter.get_by_mrid(upt_list_href, mmr.mRID)

    was_updated = False
    if not saved_mr:
        # Create the new meter reading from the mirror meter reading.
        new_mr = m.MeterReading(mRID=mmr.mRID, description=mmr.description)

        saved_mr: m.MeterReading = adpt.ListAdapter.append_and_increment_href(upt_list_href, new_mr)
    else:
        was_updated = True
        saved_mr.description = mmr.description

    assert saved_mr.href.split(hrefs.SEP)[-1] == mmr.href.split(hrefs.SEP)[-1]

    return ReturnValue(True, was_update=was_updated, an_object=saved_mr, location=saved_mr.href)


    # mmr.ReadingSet is a list of MirrorReadingSet objects.
    if mmr.MirrorReadingSet is not None:
        meter_reading_set_list_href = hrefs.SEP.join([saved_mr.href, "rs"])
        for mmr_rs in mmr.MirrorReadingSet:
            stored_mmrs: m.MirrorReadingSet = adpt.ListAdapter.append_and_increment_href(
                hrefs.SEP.join([mmr.href, "rs"]), mmr_rs)
            ret = _create_or_update_reading_set(meter_reading_set_list_href, stored_mmrs)
            assert isinstance(ret.an_object, m.ReadingSet)
            myrs: m.ReadingSet = ret.an_object

            for mmr_r in mmr_rs.Reading:
                new_mmr_r_list_href = hrefs.SEP.join([stored_mmrs.href, "r"])
                saved_mmr_reading = adpt.ListAdapter.append_and_increment_href(new_mmr_r_list_href, mmr_r)

                new_r_list_href = hrefs.SEP.join([myrs.href, "r"])
                copy_of_reading = deepcopy(mmr_r)
                saved_reading = adpt.ListAdapter.append_and_increment_href(new_r_list_href, copy_of_reading)
                assert saved_mmr_reading.href.split(hrefs.SEP)[-1] == saved_reading.href.split(hrefs.SEP)[-1]




        upt_mrs_href = hrefs.SEP.join([saved_mr.href, "rs"])

        ret: ReturnValue = _create_or_update_reading_set(upt_mrs_href, stored_mmrs)
        new_rs: m.ReadingSet = ret.an_object
        saved_mr.ReadingSetListLink = m.ReadingSetListLink(href=upt_mrs_href)
        adpt.ListAdapter.set(upt_list_href, int(saved_mr.href.split(hrefs.SEP)[-1]), saved_mr)


        # rs_list: List[m.ReadingSet] | None = None
        # try:
        #     rs_list = adpt.ListAdapter.get_list(upt_mrs_href)
        # except KeyError:
        #     adpt.ListAdapter.initialize_uri(upt_mrs_href, m.ReadingSet)


        # if rs_list is None:
        #     new_rs_index = 0
        # else:
        #     new_rs_index = len(rs_list)

        # new_rs_href = hrefs.SEP.join([upt_mrs_href, str(new_rs_index)])
        # new_rs = m.ReadingSet(href=new_rs_href, description=mmr.MirrorReadingSet.description,
        #                       timePeriod=mmr.MirrorReadingSet.timePeriod, version=mmr.MirrorReadingSet.version,
        #                       ReadingListLink=m.ReadingListLink(href=hrefs.SEP.join([new_rs_href, "r"])))




        #rs = m.ReadingSet(href=upt_mrs_href, description=mmr.MirrorReadingSet.description)
        # adpt.ListAdapter.append(upt_mrs_href, ).initialize_uri(upt_mrs_href, m.ReadingSet)

        # new_mr.ReadingSetListLink = m.ReadingSetListLink(href=upt_mrs_href)


    # Create a meter reading for the usage point.
    # upt_meter_reading = m.MeterReading(href=new_mmr_href,
    #                                    mRID=mmr.mRID,
    #                                    description=mmr.description)
    # adpt.ListAdapter.append(upt.MeterReadingListLink.href, upt_meter_reading)

    # # Store the type of reading using the add_href method.
    # rt_href = hrefs.SEP.join([upt.href, "rt", str(new_mmr_index)])
    # upt_meter_reading.ReadingTypeLink = m.ReadingTypeLink(rt_href)
    # add_href(rt_href, mmr.ReadingType)

    return saved_mr



def create_or_update_meter_reading(mup_href: str,
                                mmr_input: Union[m.MirrorMeterReading, m.MirrorMeterReadingList],
                                ) -> ReturnValue:

    if isinstance(mmr_input, m.MirrorMeterReadingList):
        raise NotImplemented()

    mup: m.MirrorUsagePoint = adpt.ListAdapter.get(hrefs.DEFAULT_MUP_ROOT,
                                                   mup_href.split(hrefs.SEP)[-1])
    assert isinstance(mup, m.MirrorUsagePoint)

    upt: m.UsagePoint = adpt.ListAdapter.get(hrefs.DEFAULT_UPT_ROOT,
                                             mup_href.split(hrefs.SEP)[-1])

    assert isinstance(upt, m.UsagePoint)

    was_updated = False
    location = None

    if isinstance(mmr_input, m.MirrorMeterReadingList):
        return ReturnValue(False, "Not Implemented")

    elif isinstance(mmr_input, m.MirrorMeterReading):

        # Attempt to find an existing mirror meter reading with the same mrid.
        # If found then we need to replace it with this new meter reading.
        mmr_list_href = hrefs.SEP.join([mup_href, "mr"])
        upt_list_href = mmr_list_href.replace("mup", "upt")

        mmr_current: m.MirrorMeterReading = adpt.ListAdapter.get_by_mrid(mmr_list_href,
                                                                         mmr_input.mRID)

        # Each of the following will only create a single level and then return.  The return
        # object will be the last object created.
        #
        # if not found then we add the mmr to the list of mmrs.
        if mmr_current is None:
            # Store the new mirror meter reading.
            saved_mmr = adpt.ListAdapter.append_and_increment_href(mmr_list_href, mmr_input)
        else:
            saved_mmr = mmr_current

        # Create a meter reading for the usage point from the mirror meter reading.
        meter_reading_result = _create_or_update_meter_reading(upt_list_href, saved_mmr)
        meter_reading = meter_reading_result.an_object

        if mmr_input.ReadingType is not None:
            rt_href = hrefs.SEP.join([meter_reading.href, "rt"])
            adpt.ListAdapter.set_single(rt_href, mmr_input.ReadingType)
            meter_reading.ReadingTypeLink = m.ReadingTypeLink(href=rt_href)

        if mmr_input.Reading is not None:
            upt_r_href = hrefs.SEP.join([meter_reading.href, "r"])
            meter_reading.ReadingListLink = m.ReadingListLink(href=upt_r_href)
            reading_result = _create_or_update_reading(upt_r_href, mmr_input.Reading)

        # Use the meter_reading_results object
        if mmr_input.MirrorReadingSet is not None:
            upt_rs_href = hrefs.SEP.join([meter_reading_result.an_object.href, "rs"])
            meter_reading.ReadingSetListLink = m.ReadingSetListLink(href=upt_rs_href)

            for mmr_rs in mmr_input.MirrorReadingSet:
                ret = _create_or_update_reading_set(upt_rs_href, mmr_rs)
                assert isinstance(ret.an_object, m.ReadingSet)
                myrs: m.ReadingSet = ret.an_object

                upt_r_href = hrefs.SEP.join([ret.an_object.href, "r"])
                myrs.ReadingListLink = m.ReadingListLink(href=upt_r_href)
                for mmr_r in mmr_rs.Reading:
                    reading_result = _create_or_update_reading(upt_r_href, mmr_r)


        adpt.ListAdapter.store()
        # The over all result of this call!
        return meter_reading_result


        # new_mmr_index = adpt.ListAdapter.list_size(mmr_list_href)
        # new_mmr_href = hrefs.SEP.join([mmr_list_href, str(new_mmr_index)])
        # mmr_input.href = new_mmr_href

        # upt_meter_reading = _create_or_update_meter_reading(upt, mmr_input)





        # if mmr_input.MirrorReadingSet is not None:
        #     return_value = _create_or_update_reading_set(mup, mmr_input.MirrorReadingSet, internal_ref_transform)

    #     # Attempt to find an existing mup with the same mrid.  If found then we need to replace
    #     # the data with the new data etc.  If not found then we add the mmr to the list of mmrs.
    #     mmr_list_href = hrefs.SEP.join([mup_href, "mr"])
    #     upt_list_href = mmr_list_href.replace("mup", "upt")
    #     mmr_item = adpt.ListAdapter.get_by_mrid(mmr_list_href), mmr_input.mRID)


    #     if mmr_item:
    #         mmr_index = adpt.ListAdapter.get_list(mmr_list_href)).index(mmr_item)
    #         was_updated = True
    #     else:
    #         # This is a new mirror meter reading index.
    #         new_mmr_index = adpt.ListAdapter.list_size(mmr_list_href))

    #         # Initialize the url for the mirror meter reading list.
    #         mmr_input.href = hrefs.SEP.join([mmr_list_href, str(new_mmr_index)])



    #         adpt.ListAdapter.initialize_uri(upt_list_href), m.ReadingList)
    #         # Add a new mirror meter reading to the list of mirror meter readings.
    #         mmr_input.href = hrefs.SEP.join([mmr_list_href, str(new_mmr_index)])

    #         # If this is a List of MirrorMeterReadings then we need to add each one to the list. And
    #         # initialize the types of readings.
    #         if mup.MirrorMeterReading:
    #             for mup_mr in mup.MirrorMeterReading:
    #                 mmr_input.ReadingType = mup_mr.ReadingType
    #                 mmr_input.description = mup_mr.description
    #                 mmr_input.lastUpdateTime = mup_mr.lastUpdateTime

    #             ListAdapter.append(mmr_list_href), mmr_input)
    #             location = mmr_input.href

    #         if mmr_input.Reading is not None and mmr_input.ReadingType is not None:
    #             stored_mirror_reading = adpt.ListAdapter.get_by_mrid(mmr_list_href), mmr_input.mRID)

    #             # If we found it, then replace with new reading
    #             if stored_mirror_reading:
    #                 mirror_reading_indx = adpt.ListAdapter.get_list(mmr_list_href)).index(stored_mirror_reading)

    #                 # Replace MirrorMeterReading with new data
    #                 adpt.ListAdapter.set(mmr_list_href), mirror_reading_indx, mmr_input)

    #                 adpt.ListAdapter.set(upt_list_href), mirror_reading_indx, mmr_input.Reading)
    #                 was_updated = True
    #             else:
    #                 reading_index = adpt.ListAdapter.list_size(mmr_list_href))
    #                 mmr_input.Reading.href = hrefs.SEP.join([mmr_input.href, "r"])
    #                 ListAdapter.append(mmr_list_href), mmr_input)
    #                 ListAdapter.set(upt_list_href), reading_index, mmr_input)
    #                 location = mmr_input.href

    #             # ListAdapter.set_single(mmr_list_href), mmr_input)
    #             # upt_input = deepcopy(mmr_input)
    #             # upt_input.href = upt_input.href.replace("mup", "upt")
    #             # ListAdapter.set_single(upt_list_href), upt_input)
    #             # location = upt_list_href

    #     return ReturnValue(True, mmr_input, was_updated, location)

    #     try:
    #         # Check to see if the meter reading already exists based upon the passed mRID.
    #         mmr_item = adpt.ListAdapter.get_by_mrid(mmr_list_href), mmr_input.mRID)
    #         new_mmr_index = adpt.ListAdapter.get_list(mmr_list_href)).index(mmr_item)
    #         was_updated = True
    #     except NotFoundError:
    #         new_mmr_index = adpt.ListAdapter.list_size(mmr_list_href))
    #         mmr_input.href = hrefs.SEP.join([mmr_list_href, str(new_mmr_index)])

    #         # This is a singleton reading here.
    #         if mmr_input.ReadingType is not None and mmr_input.Reading is not None:
    #             ListAdapter.set_single(mmr_list_href), mmr_input)

    #         for mup_mr in mup.MirrorMeterReading:
    #             mmr_input.ReadingType = mup_mr.ReadingType
    #             mmr_input.description = mup_mr.description
    #             mmr_input.lastUpdateTime = mup_mr.lastUpdateTime
    #         ListAdapter.append(mmr_list_href), mmr_input)
    #         mmr_item = mmr_input

    #     try:
    #         mr = adpt.ListAdapter.get(upt_list_href), new_mmr_index)
    #     except NotFoundError:
    #         # This shouldn't happen if it does then there is something wrong with our code.
    #         if was_updated:
    #             raise ValueError("Unable to find meter reading for updated mirror meter reading")
    #         rt_href = hrefs.SEP.join([upt_list_href, str(new_mmr_index), "rt"])
    #         mmr_item.ReadingType.href = rt_href
    #         mr = m.MeterReading(href=hrefs.SEP.join([upt_list_href, str(new_mmr_index)]),
    #                             mRID=mmr_item.mRID,
    #                             description=mmr_item.description,
    #                             ReadingTypeLink=m.ReadingTypeLink(rt_href))
    #         add_href(rt_href, mmr_item.ReadingType)
    #         ListAdapter.append(upt_list_href), mr)
    #     location = upt_list_href

    #     # Current instantanious values.
    #     if mmr_input.Reading is not None:
    #         mmr_item.Reading.href = hrefs.SEP.join([mmr_item.href, "r"])
    #         mmr_item.Reading.href = mmr_item.Reading.href.replace("mup", "upt")
    #         add_href(mmr_item.Reading.href, mmr_item.Reading)
    #         mr.ReadingLink = m.ReadingLink(mmr_item.Reading.href)

    #     # Mirror reading sets
    #     if mmr_input.MirrorReadingSet:

    #         mrs_list_href = hrefs.SEP.join([mmr_item.href, "rs"])
    #         rs_list_href = hrefs.SEP.join([mmr_item.href, "rs"]).replace("mup", "upt")
    #         mr.ReadingSetListLink = m.ReadingSetListLink(href=rs_list_href)
    #         ListAdapter.initialize_uri(mr.ReadingSetListLink.href), m.ReadingSet)

    #         for mrs in mmr_input.MirrorReadingSet:
    #             found_rs = False
    #             try:
    #                 mrs_item = ListAdapter.get_by_mrid(mrs_list_href), mrs.mRID)
    #                 mrs_item_index = ListAdapter.get_list(mrs_list_href).index(mrs_item)
    #                 found_rs = True
    #             except NotFoundError:
    #                 mrs_item = mrs
    #                 mrs_item_index = ListAdapter.list_size(mrs_list_href))
    #                 mrs_item.href = hrefs.SEP.join([mrs_list_href, str(mrs_item_index)])
    #                 ListAdapter.append(mrs_list_href), mrs_item)

    #             if found_rs:
    #                 rs_item = ListAdapter.get(rs_list_href), mrs_item_index)
    #                 rs_item.description = mrs_item.description
    #                 rs_item.timePeriod = mrs_item.timePeriod
    #                 rs_item.version = mrs_item.version
    #             else:
    #                 rs_item = m.ReadingSet(href=hrefs.SEP.join([rs_list_href,
    #                                                             str(mrs_item_index)]),
    #                                        description=mrs_item.description,
    #                                        timePeriod=mrs_item.timePeriod,
    #                                        version=mrs_item.version)
    #                 ListAdapter.append(rs_list_href), rs_item)

    #             reading_list_href = hrefs.SEP.join([rs_item.href, "r"])
    #             rs_item.ReadingListLink = m.ReadingListLink(href=reading_list_href)
    #             for reading_index, reading in enumerate(mrs_item.Reading):
    #                 reading.href = hrefs.SEP.join([reading_list_href, str(reading_index)])
    #                 ListAdapter.append(reading_list_href), reading)

    # ListAdapter.store()

    return ReturnValue(True, mmr_item, was_updated, location)


def create_mirror_usage_point(mup: m.MirrorUsagePoint,
                              ) -> ReturnValue:
    """Creates a MirrorUsagePoint and associated UsagePoint and adds them to their adapters.
    """

    # Attempt to find an existing mup with the same mrid.  If found then we need to replace
    # it with the new data etc.
    found_with_mrid = None
    if adpt.ListAdapter.list_size(hrefs.DEFAULT_MUP_ROOT) > 0:
        try:
            found_with_mrid = adpt.ListAdapter.get_by_mrid(hrefs.DEFAULT_MUP_ROOT, mup.mRID)
        except NotFoundError:
            ...

    update = False
    if not found_with_mrid:
        # Creating a new allocation of resources for the mup. And then copy the data from the
        # mup resources into the usage point resources allocating new data as needed.
        upt_href = hrefs.UsagePointHref()

        # Both the usage point and mirror usage point will have the same point index.
        point_index = adpt.ListAdapter.list_size(hrefs.DEFAULT_MUP_ROOT)
        mup.href = hrefs.SEP.join([hrefs.DEFAULT_MUP_ROOT, str(point_index)])
        # Add the mirror usage point to the list of mirror usage points.
        adpt.ListAdapter.append(hrefs.DEFAULT_MUP_ROOT, mup)

        # Create a usage point with the same index as the mirror usage point.
        upt = m.UsagePoint(href=hrefs.SEP.join([hrefs.DEFAULT_UPT_ROOT,
                                                str(point_index)]),
                           description=mup.description,
                           deviceLFDI=mup.deviceLFDI,
                           serviceCategoryKind=mup.serviceCategoryKind,
                           mRID=mup.mRID,
                           roleFlags=mup.roleFlags,
                           status=mup.status)
        upt.MeterReadingListLink = m.MeterReadingListLink(href=hrefs.SEP.join([upt.href, "mr"]), all=0)
        adpt.ListAdapter.append(hrefs.DEFAULT_UPT_ROOT, upt)

        # Initialize the url for the mirror meter reading list.
        mmr_list_href = hrefs.SEP.join([mup.href, "mr"])
        adpt.ListAdapter.initialize_uri(mmr_list_href, m.MirrorMeterReading)

        # Initialize the url for the meter reading list.
        mr_list_href = hrefs.SEP.join([upt.href, "mr"])
        adpt.ListAdapter.initialize_uri(mr_list_href, m.MeterReading)

        for index_for_readings, mirror_meter_reading in enumerate(mup.MirrorMeterReading):
            # Validate the the reading has a reading type associated with it.
            if not mirror_meter_reading.ReadingType:
                return ReturnValue(
                    False,
                    f"Invalid Reading Type for Mirror Meter Reading {mirror_meter_reading.mRID}")

            # Update the mirror meter reading href and then add it to the list of mirror meter readings.
            mirror_meter_reading.href = hrefs.SEP.join([mmr_list_href, str(index_for_readings)])
            adpt.ListAdapter.append(mmr_list_href, mirror_meter_reading)

            # Create a meter reading for the usage point.
            meter_reading = m.MeterReading(href=hrefs.SEP.join(
                [mr_list_href, str(index_for_readings)]),
                                           mRID=mirror_meter_reading.mRID,
                                           description=mirror_meter_reading.description)
            adpt.ListAdapter.append(mr_list_href, meter_reading)

            # Store the type of reading using the add_href method.
            rt_href = hrefs.SEP.join([upt.href, "rt", str(index_for_readings)])
            meter_reading.ReadingTypeLink = m.ReadingTypeLink(rt_href)

            adpt.ListAdapter.set_single(rt_href, mirror_meter_reading.ReadingType)
            add_href(rt_href, mirror_meter_reading.ReadingType)

    else:
        # TODO Update all properties with new items from mup
        mup.href = found_with_mrid.href
        found_with_mrid.description = mup.description
        found_with_mrid.deviceLFDI = mup.deviceLFDI
        found_with_mrid.serviceCategoryKind = mup.serviceCategoryKind
        found_with_mrid.mRID = mup.mRID
        found_with_mrid.roleFlags = mup.roleFlags
        found_with_mrid.status = mup.status
        update = True
        adpt.ListAdapter.store()

    return ReturnValue(True, mup, update, mup.href)


@dataclass
class TimerSpec:
    trigger_after_seconds: int
    fn: Callable
    args: List = field(default_factory=list)
    kwargs: Dict = field(default_factory=dict)
    enabled: bool = True
    trigger_count: int = 0
    last_trigger_time: int = int(time.mktime(datetime.utcnow().timetuple()))

    def disable(self):
        self.enabled = False

    def enable(self):
        self.enabled = True

    def reset_count(self):
        self.trigger_count = 0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TimerSpec):
            raise NotImplementedError(
                f"Comparison between {self.__class__.__name__} and {type(other)} not implemented")
        return self.fn is other.fn

    def trigger(self, current_time: int):
        if self.last_trigger_time + self.trigger_after_seconds < current_time:
            if self.args and self.kwargs:
                self.fn(args=self.args, kwargs=self.kwargs)
            elif self.args:
                self.fn(args=self.args)
            else:
                self.fn()
            self.trigger_count += 1
            self.last_trigger_time = current_time


class _TimeAdapter(threading.Thread):
    tick = Signal("tick")
    event_started = Signal("event_started")
    event_ended = Signal("event_endend")
    event_scheduled = Signal("event_scheduled")
    events: Dict[str, m.Event] = {}
    current_tick: int = 0
    looping: bool = False

    @staticmethod
    def user_readable(timestamp: int) -> str:
        dt = datetime.fromtimestamp(timestamp)
        return dt.isoformat()    # .strftime("%m/%d/%Y, %H:%M:%S")

    @staticmethod
    def from_iso(iso_fmt_date: str) -> int:
        dt = datetime.strptime(iso_fmt_date, "%Y-%m-%dT%H:%M:%S")
        return int(time.mktime(dt.timetuple()))

    @staticmethod
    def add_event(evnt: m.Event):
        time_now = _TimeAdapter.current_tick
        if evnt.EventStatus is None:
            evnt.EventStatus = m.EventStatus()
        if evnt.href not in _TimeAdapter.events:
            while _TimeAdapter.looping:
                time.sleep(0.1)
            _TimeAdapter.events[evnt.href] = evnt

    def run(self) -> None:

        while True:
            _TimeAdapter.current_tick = int(time.mktime(datetime.utcnow().timetuple()))
            _TimeAdapter.tick.send(self.current_tick)
            _TimeAdapter.looping = True
            time_now = _TimeAdapter.current_tick
            for href, evnt in _TimeAdapter.events.items():
                if time_now < evnt.interval.start and evnt.EventStatus.currentStatus is None:
                    evnt.EventStatus.dateTime = time_now
                    evnt.EventStatus.currentStatus = 0
                    _log.debug(f"{'='*20}Event Scheduled {evnt.href}")
                    _TimeAdapter.event_scheduled.send(evnt)
                elif evnt.interval.start < time_now and time_now < evnt.interval.start + evnt.interval.duration:
                    if evnt.EventStatus.currentStatus != 1:
                        evnt.EventStatus.currentStatus = 1
                        evnt.EventStatus.dateTime = time_now
                        _log.debug(f"{'='*20}Event Started {evnt.href}")
                        _TimeAdapter.event_started.send(evnt)
                elif time_now > evnt.interval.start + evnt.interval.duration and evnt.EventStatus.currentStatus == 1:
                    evnt.EventStatus.currentStatus = 5
                    evnt.EventStatus.dateTime = time_now
                    _log.debug(f"{'='*20}Event Complete {evnt.href}")
                    _TimeAdapter.event_ended.send(evnt)

            _TimeAdapter.looping = False
            time.sleep(1)


TimeAdapter = _TimeAdapter()
TimeAdapter.daemon = True
TimeAdapter.start()
