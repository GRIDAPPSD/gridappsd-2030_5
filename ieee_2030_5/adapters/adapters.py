from dataclasses import dataclass, field
import threading
from typing import Callable, Dict, List, Union
from ieee_2030_5.data.indexer import add_href
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
import ieee_2030_5.adapters as adpt
from ieee_2030_5.adapters import Adapter, NotFoundError, ResourceListAdapter
from ieee_2030_5.config import ReturnValue

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
MirrorUsagePointAdapter = Adapter[m.MirrorUsagePoint](url_prefix="/mup",
                                                      generic_type=m.MirrorUsagePoint)
MirrorMeterReadingAdapter = Adapter[m.MirrorMeterReading](url_prefix="/mr",
                                                          generic_type=m.MirrorMeterReading)
MirrorReadingSetAdapter = Adapter[m.MirrorReadingSet](url_prefix="/rs",
                                                      generic_type=m.MirrorReadingSet)
UsagePointAdapter = Adapter[m.UsagePoint](url_prefix="/upt", generic_type=m.UsagePoint)
ListAdapter = ResourceListAdapter()


def create_mirror_meter_reading(
        mup_href: str, mmr_input: Union[m.MirrorMeterReading,
                                        m.MirrorMeterReadingList]) -> ReturnValue:

    if isinstance(mmr_input, m.MirrorMeterReadingList):
        raise NotImplemented()

    mup: m.MirrorUsagePoint = adpt.ListAdapter.get(hrefs.DEFAULT_MUP_ROOT,
                                                   mup_href.split(hrefs.SEP)[-1])
    assert isinstance(mup, m.MirrorUsagePoint)
    assert len(mup.MirrorMeterReading) == 1

    was_updated = False
    location = None
    if isinstance(mmr_input, m.MirrorMeterReading):
        # Attempt to find an existing mup with the same mrid.  If found then we need to replace
        # the data with the new data etc.  If not found then we add the mmr to the list of mmrs.
        mmr_list_href = hrefs.SEP.join([mup_href, "mr"])
        mr_list_href = mmr_list_href.replace("mup", "upt")
        try:
            mmr = adpt.ListAdapter.get_by_mrid(mmr_list_href, mmr_input.mRID)
            mmr_index = adpt.ListAdapter.get_list(mmr_list_href).index(mmr)
            was_updated = True
        except NotFoundError:
            mmr_index = adpt.ListAdapter.list_size(mmr_list_href)
            mmr_input.href = hrefs.SEP.join([mmr_list_href, str(mmr_index)])

            for mup_mr in mup.MirrorMeterReading:
                mmr_input.ReadingType = mup_mr.ReadingType
                mmr_input.description = mup_mr.description
                mmr_input.lastUpdateTime = mup_mr.lastUpdateTime
            ListAdapter.append(mmr_list_href, mmr_input)
            mmr = mmr_input

        try:
            mr = adpt.ListAdapter.get(mr_list_href, mmr_index)
        except NotFoundError:
            # This shouldn't happen if it does then there is something wrong with our code.
            if was_updated:
                raise ValueError("Unable to find meter reading for updated mirror meter reading")
            rt_href = hrefs.SEP.join([mr_list_href, str(mmr_index), "rt"])
            mmr.ReadingType.href = rt_href
            mr = m.MeterReading(href=hrefs.SEP.join([mr_list_href, str(mmr_index)]),
                                mRID=mmr.mRID,
                                description=mmr.description,
                                ReadingTypeLink=m.ReadingTypeLink(rt_href))
            add_href(rt_href, mmr.ReadingType)
            ListAdapter.append(mr_list_href, mr)
        location = mr_list_href

        # Current instantanious values.
        if mmr_input.Reading is not None:
            mmr.Reading.href = hrefs.SEP.join([mmr.href, "r"])
            mmr.Reading.href = mmr.Reading.href.replace("mup", "upt")
            add_href(mmr.Reading.href, mmr.Reading)
            mr.ReadingLink = m.ReadingLink(mmr.Reading.href)

        # Mirror reading sets
        if mmr_input.MirrorReadingSet:

            mrs_list_href = hrefs.SEP.join([mmr.href, "rs"])
            rs_list_href = hrefs.SEP.join([mmr.href, "rs"]).replace("mup", "upt")
            mr.ReadingSetListLink = m.ReadingSetListLink(href=rs_list_href)
            ListAdapter.initialize_uri(mr.ReadingSetListLink.href, m.ReadingSet)

            for mrs in mmr_input.MirrorReadingSet:
                found_rs = False
                try:
                    mrs_item = ListAdapter.get_by_mrid(mrs_list_href, mrs.mRID)
                    mrs_item_index = ListAdapter.get_list(mrs_list_href).index(mrs_item)
                    found_rs = True
                except NotFoundError:
                    mrs_item = mrs
                    mrs_item_index = ListAdapter.list_size(mrs_list_href)
                    mrs_item.href = hrefs.SEP.join([mrs_list_href, str(mrs_item_index)])
                    ListAdapter.append(mrs_list_href, mrs_item)

                if found_rs:
                    rs_item = ListAdapter.get(rs_list_href, mrs_item_index)
                    rs_item.description = mrs_item.description
                    rs_item.timePeriod = mrs_item.timePeriod
                    rs_item.version = mrs_item.version
                else:
                    rs_item = m.ReadingSet(href=hrefs.SEP.join([rs_list_href,
                                                                str(mrs_item_index)]),
                                           description=mrs_item.description,
                                           timePeriod=mrs_item.timePeriod,
                                           version=mrs_item.version)
                    ListAdapter.append(rs_list_href, rs_item)

                reading_list_href = hrefs.SEP.join([rs_item.href, "r"])
                rs_item.ReadingListLink = m.ReadingListLink(href=reading_list_href)
                for reading_index, reading in enumerate(mrs_item.Reading):
                    reading.href = hrefs.SEP.join([reading_list_href, str(reading_index)])
                    ListAdapter.append(reading_list_href, reading)

    ListAdapter.store()

    return ReturnValue(True, mmr, was_updated, location)


def create_mirror_usage_point(mup: m.MirrorUsagePoint) -> ReturnValue:
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
        upt.MeterReadingListLink = m.MeterReadingListLink(href=hrefs.SEP.join([upt.href, "mr"]))
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