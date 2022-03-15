from dataclasses import dataclass, field
from typing import List, Optional

__NAMESPACE__ = "urn:ieee:std:2030.5:ns"


@dataclass
class ActivePower:
    """The active (real) power P (in W) is the product of root-mean-square
    (RMS) voltage, RMS current, and cos(theta) where theta is the phase angle
    of current relative to voltage.

    It is the primary measure of the rate of flow of energy.

    :ivar multiplier: Specifies exponent for uom.
    :ivar value: Value in watts (uom 38)
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    multiplier: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class AmpereHour:
    """
    Available electric charge.

    :ivar multiplier: Specifies exponent of uom.
    :ivar value: Value in ampere-hours (uom 106)
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    multiplier: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class ApparentPower:
    """
    The apparent power S (in VA) is the product of root mean square (RMS)
    voltage and RMS current.

    :ivar multiplier: Specifies exponent of uom.
    :ivar value: Value in volt-amperes (uom 61)
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    multiplier: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class ApplianceLoadReduction:
    """The ApplianceLoadReduction object is used by a Demand Response service
    provider to provide signals for ENERGY STAR compliant appliances.

    See the definition of ApplianceLoadReductionType for more
    information.

    :ivar type: Indicates the type of appliance load reduction
        requested.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    type: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class AppliedTargetReduction:
    """
    Specifies the value of the TargetReduction applied by the device.

    :ivar type: Enumerated field representing the type of reduction
        requested.
    :ivar value: Indicates the requested amount of the relevant
        commodity to be reduced.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    type: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class Charge:
    """Charges contain charges on a customer bill.

    These could be items like taxes, levies, surcharges, rebates, or
    others.  This is meant to allow the HAN device to retrieve enough
    information to be able to reconstruct an estimate of what the total
    bill would look like. Providers can provide line item billing,
    including multiple charge kinds (e.g. taxes, surcharges) at whatever
    granularity desired, using as many Charges as desired during a
    billing period. There can also be any number of Charges associated
    with different ReadingTypes to distinguish between TOU tiers,
    consumption blocks, or demand charges.

    :ivar description: A description of the charge.
    :ivar kind: The type (kind) of charge.
    :ivar value: A monetary charge.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 20,
        }
    )
    kind: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class Condition:
    """
    Indicates a condition that must be satisfied for the Notification to be
    triggered.

    :ivar attribute_identifier: 0 = Reading value 1-255 = Reserved
    :ivar lower_threshold: The value of the lower threshold
    :ivar upper_threshold: The value of the upper threshold
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    attribute_identifier: Optional[int] = field(
        default=None,
        metadata={
            "name": "attributeIdentifier",
            "type": "Element",
            "required": True,
        }
    )
    lower_threshold: Optional[int] = field(
        default=None,
        metadata={
            "name": "lowerThreshold",
            "type": "Element",
            "required": True,
            "min_inclusive": -140737488355328,
            "max_inclusive": 140737488355328,
        }
    )
    upper_threshold: Optional[int] = field(
        default=None,
        metadata={
            "name": "upperThreshold",
            "type": "Element",
            "required": True,
            "min_inclusive": -140737488355328,
            "max_inclusive": 140737488355328,
        }
    )


@dataclass
class ConnectStatusType:
    """DER ConnectStatus value (bitmap):

    0 - Connected
    1 - Available
    2 - Operating
    3 - Test
    4 - Fault / Error
    All other values reserved.

    :ivar date_time: The date and time at which the state applied.
    :ivar value: The value indicating the state.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    date_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "dateTime",
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[bytes] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 1,
            "format": "base16",
        }
    )


@dataclass
class CreditTypeChange:
    """
    Specifies a change to the credit type.

    :ivar new_type: The new credit type, to take effect at the time
        specified by startTime
    :ivar start_time: The date/time when the change is to take effect.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    new_type: Optional[int] = field(
        default=None,
        metadata={
            "name": "newType",
            "type": "Element",
            "required": True,
        }
    )
    start_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "startTime",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class CurrentRms:
    """
    Average flow of charge through a conductor.

    :ivar multiplier: Specifies exponent of value.
    :ivar value: Value in amperes RMS (uom 5)
    """
    class Meta:
        name = "CurrentRMS"
        namespace = "urn:ieee:std:2030.5:ns"

    multiplier: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class CurveData:
    """
    Data point values for defining a curve or schedule.

    :ivar excitation: If yvalue is Power Factor, then this field SHALL
        be present. If yvalue is not Power Factor, then this field SHALL
        NOT be present. True when DER is absorbing reactive power
        (under-excited), false when DER is injecting reactive power
        (over-excited).
    :ivar xvalue: The data value of the X-axis (independent) variable,
        depending on the curve type. See definitions in DERControlBase
        for further information.
    :ivar yvalue: The data value of the Y-axis (dependent) variable,
        depending on the curve type. See definitions in DERControlBase
        for further information. If yvalue is Power Factor, the
        excitation field SHALL be present and yvalue SHALL be a positive
        value. If yvalue is not Power Factor, the excitation field SHALL
        NOT be present.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    excitation: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    xvalue: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    yvalue: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class DateTimeInterval:
    """
    Interval of date and time.

    :ivar duration: Duration of the interval, in seconds.
    :ivar start: Date and time of the start of the interval.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    duration: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    start: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class DutyCycle:
    """Duty cycle control is a device specific issue and is managed by the
    device.

    The duty cycle of the device under control should span the shortest
    practical time period in accordance with the nature of the device
    under control and the intent of the request for demand reduction.
    The default factory setting SHOULD be three minutes for each 10% of
    duty cycle.  This indicates that the default time period over which
    a duty cycle is applied is 30 minutes, meaning a 10% duty cycle
    would cause a device to be ON for 3 minutes.   The “off state” SHALL
    precede the “on state”.

    :ivar normal_value: Contains the maximum On state duty cycle applied
        by the end device, as a percentage of time.  The field not
        present indicates that this field has not been used by the end
        device.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    normal_value: Optional[int] = field(
        default=None,
        metadata={
            "name": "normalValue",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class EnvironmentalCost:
    """Provides alternative or secondary price information for the relevant
    RateComponent.

    Supports jurisdictions that seek to convey the environmental price
    per unit of the specified commodity not expressed in currency.
    Implementers and consumers can use this attribute to prioritize
    operations of their HAN devices (e.g., PEV charging during times of
    high availability of renewable electricity resources).

    :ivar amount: The estimated or actual environmental or other cost,
        per commodity unit defined by the ReadingType, for this
        RateComponent (e.g., grams of carbon dioxide emissions each per
        kWh).
    :ivar cost_kind: The kind of cost referred to in the amount.
    :ivar cost_level: The relative level of the amount attribute.  In
        conjunction with numCostLevels, this attribute informs a device
        of the relative scarcity of the amount attribute (e.g., a high
        or low availability of renewable generation). numCostLevels and
        costLevel values SHALL ascend in order of scarcity, where "0"
        signals the lowest relative cost and higher values signal
        increasing cost.  For example, if numCostLevels is equal to “3,”
        then if the lowest relative costLevel were equal to “0,” devices
        would assume this is the lowest relative period to operate.
        Likewise, if the costLevel in the next TimeTariffInterval
        instance is equal to “1,” then the device would assume it is
        relatively more expensive, in environmental terms, to operate
        during this TimeTariffInterval instance than the previous one.
        There is no limit to the number of relative price levels other
        than that indicated in the attribute type, but for practicality,
        service providers should strive for simplicity and recognize the
        diminishing returns derived from increasing the numCostLevel
        value greater than four.
    :ivar num_cost_levels: The number of all relative cost levels. In
        conjunction with costLevel, numCostLevels signals the relative
        scarcity of the commodity for the duration of the
        TimeTariffInterval instance (e.g., a relative indication of
        cost). This is useful in providing context for nominal cost
        signals to consumers or devices that might see a range of amount
        values from different service providres or from the same service
        provider.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    amount: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    cost_kind: Optional[int] = field(
        default=None,
        metadata={
            "name": "costKind",
            "type": "Element",
            "required": True,
        }
    )
    cost_level: Optional[int] = field(
        default=None,
        metadata={
            "name": "costLevel",
            "type": "Element",
            "required": True,
        }
    )
    num_cost_levels: Optional[int] = field(
        default=None,
        metadata={
            "name": "numCostLevels",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class Error:
    """
    Contains information about the nature of an error if a request could not be
    completed successfully.

    :ivar max_retry_duration: Contains the number of seconds the client
        SHOULD wait before retrying the request.
    :ivar reason_code: Code indicating the reason for failure. 0 -
        Invalid request format 1 - Invalid request values (e.g. invalid
        threshold values) 2 - Resource limit reached 3 - Conditional
        subscription field not supported 4 - Maximum request frequency
        exceeded All other values reserved
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    max_retry_duration: Optional[int] = field(
        default=None,
        metadata={
            "name": "maxRetryDuration",
            "type": "Element",
        }
    )
    reason_code: Optional[int] = field(
        default=None,
        metadata={
            "name": "reasonCode",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class EventStatus:
    """Current status information relevant to a specific object.

    The Status object is used to indicate the current status of an
    Event. Devices can read the containing resource (e.g. TextMessage)
    to get the most up to date status of the event.  Devices can also
    subscribe to a specific resource instance to get updates when any of
    its attributes change, including the Status object.

    :ivar current_status: Field representing the current status type. 0
        = Scheduled This status indicates that the event has been
        scheduled and the event has not yet started.  The server SHALL
        set the event to this status when the event is first scheduled
        and persist until the event has become active or has been
        cancelled.  For events with a start time less than or equal to
        the current time, this status SHALL never be indicated, the
        event SHALL start with a status of “Active”. 1 = Active This
        status indicates that the event is currently active. The server
        SHALL set the event to this status when the event reaches its
        earliest Effective Start Time. 2 = Cancelled When events are
        cancelled, the Status.dateTime attribute SHALL be set to the
        time the cancellation occurred, which cannot be in the future.
        The server is responsible for maintaining the cancelled event in
        its collection for the duration of the original event, or until
        the server has run out of space and needs to store a new event.
        Client devices SHALL be aware of Cancelled events, determine if
        the Cancelled event applies to them, and cancel the event
        immediately if applicable. 3 = Cancelled with Randomization The
        server is responsible for maintaining the cancelled event in its
        collection for the duration of the Effective Scheduled Period.
        Client devices SHALL be aware of Cancelled with Randomization
        events, determine if the Cancelled event applies to them, and
        cancel the event immediately, using the larger of (absolute
        value of randomizeStart) and (absolute value of
        randomizeDuration) as the end randomization, in seconds. This
        Status.type SHALL NOT be used with "regular" Events, only with
        specializations of RandomizableEvent. 4 = Superseded Events
        marked as Superseded by servers are events that may have been
        replaced by new events from the same program that target the
        exact same set of deviceCategory's (if applicable) AND
        DERControl controls (e.g., opModTargetW) (if applicable) and
        overlap for a given period of time. Servers SHALL mark an event
        as Superseded at the earliest Effective Start Time of the
        overlapping event. Servers are responsible for maintaining the
        Superseded event in their collection for the duration of the
        Effective Scheduled Period. Client devices encountering a
        Superseded event SHALL terminate execution of the event
        immediately and commence execution of the new event immediately,
        unless the current time is within the start randomization window
        of the superseded event, in which case the client SHALL obey the
        start randomization of the new event. This Status.type SHALL NOT
        be used with TextMessage, since multiple text messages can be
        active. All other values reserved.
    :ivar date_time: The dateTime attribute will provide a timestamp of
        when the current status was defined. dateTime MUST be set to the
        time at which the status change occurred, not a time in the
        future or past.
    :ivar potentially_superseded: Set to true by a server of this event
        if there are events that overlap this event in time and also
        overlap in some, but not all, deviceCategory's (if applicable)
        AND DERControl controls (e.g., opModTargetW) (if applicable) in
        the same function set instance.
    :ivar potentially_superseded_time: Indicates the time that the
        potentiallySuperseded flag was set.
    :ivar reason: The Reason attribute allows a Service provider to
        provide a textual explanation of the status.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    current_status: Optional[int] = field(
        default=None,
        metadata={
            "name": "currentStatus",
            "type": "Element",
            "required": True,
        }
    )
    date_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "dateTime",
            "type": "Element",
            "required": True,
        }
    )
    potentially_superseded: Optional[bool] = field(
        default=None,
        metadata={
            "name": "potentiallySuperseded",
            "type": "Element",
            "required": True,
        }
    )
    potentially_superseded_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "potentiallySupersededTime",
            "type": "Element",
        }
    )
    reason: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 192,
        }
    )


@dataclass
class FixedPointType:
    """
    Abstract type for specifying a fixed-point value without a given unit of
    measure.

    :ivar multiplier: Specifies exponent of uom.
    :ivar value: Dimensionless value
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    multiplier: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class FixedVar:
    """
    Specifies a signed setpoint for reactive power.

    :ivar ref_type: Indicates whether to interpret 'value' as %setMaxVar
        or %statVarAvail.
    :ivar value: Specify a signed setpoint for reactive power in % (see
        'refType' for context).
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    ref_type: Optional[int] = field(
        default=None,
        metadata={
            "name": "refType",
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class FreqDroopType:
    """
    Type for Frequency-Droop (Frequency-Watt) operation.

    :ivar d_bof: Frequency droop dead band for over-frequency
        conditions. In thousandths of Hz.
    :ivar d_buf: Frequency droop dead band for under-frequency
        conditions. In thousandths of Hz.
    :ivar k_of: Frequency droop per-unit frequency change for over-
        frequency conditions corresponding to 1 per-unit power output
        change. In thousandths, unitless.
    :ivar k_uf: Frequency droop per-unit frequency change for under-
        frequency conditions corresponding to 1 per-unit power output
        change. In thousandths, unitless.
    :ivar open_loop_tms: Open loop response time, the duration from a
        step change in control signal input until the output changes by
        90% of its final change before any overshoot, in hundredths of a
        second. Resolution is 1/100 sec. A value of 0 is used to mean no
        limit.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    d_bof: Optional[int] = field(
        default=None,
        metadata={
            "name": "dBOF",
            "type": "Element",
            "required": True,
        }
    )
    d_buf: Optional[int] = field(
        default=None,
        metadata={
            "name": "dBUF",
            "type": "Element",
            "required": True,
        }
    )
    k_of: Optional[int] = field(
        default=None,
        metadata={
            "name": "kOF",
            "type": "Element",
            "required": True,
        }
    )
    k_uf: Optional[int] = field(
        default=None,
        metadata={
            "name": "kUF",
            "type": "Element",
            "required": True,
        }
    )
    open_loop_tms: Optional[int] = field(
        default=None,
        metadata={
            "name": "openLoopTms",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class GpslocationType:
    """
    Specifies a GPS location, expressed in WGS 84 coordinates.

    :ivar lat: Specifies the latitude from equator. -90 (south) to +90
        (north) in decimal degrees.
    :ivar lon: Specifies the longitude from Greenwich Meridian. -180
        (west) to +180 (east) in decimal degrees.
    """
    class Meta:
        name = "GPSLocationType"
        namespace = "urn:ieee:std:2030.5:ns"

    lat: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 32,
        }
    )
    lon: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 32,
        }
    )


@dataclass
class InverterStatusType:
    """DER InverterStatus value:

    0 - N/A
    1 - off
    2 - sleeping (auto-shutdown) or DER is at low output power/voltage
    3 - starting up or ON but not producing power
    4 - tracking MPPT power point
    5 - forced power reduction/derating
    6 - shutting down
    7 - one or more faults exist
    8 - standby (service on unit) - DER may be at high output voltage/power
    9 - test mode
    10 - as defined in manufacturer status
    All other values reserved.

    :ivar date_time: The date and time at which the state applied.
    :ivar value: The value indicating the state.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    date_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "dateTime",
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class Link:
    """
    Links provide a reference, via URI, to another resource.

    :ivar href: A URI reference.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    href: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass
class LocalControlModeStatusType:
    """DER LocalControlModeStatus/value:

    0 – local control 1 – remote control All other values reserved.

    :ivar date_time: The date and time at which the state applied.
    :ivar value: The value indicating the state.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    date_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "dateTime",
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class ManufacturerStatusType:
    """
    DER ManufacturerStatus/value: String data type.

    :ivar date_time: The date and time at which the state applied.
    :ivar value: The value indicating the state.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    date_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "dateTime",
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 6,
        }
    )


@dataclass
class Offset:
    """If a temperature offset is sent that causes the heating or cooling
    temperature set point to exceed the limit boundaries that are programmed
    into the device, the device SHALL respond by setting the temperature at the
    limit.

    If an EDC is being targeted at multiple devices or to a device that
    controls multiple devices (e.g., EMS), it can provide multiple
    Offset types within one EDC. For events with multiple Offset types,
    a client SHALL select the Offset that best fits their operating
    function. Alternatively, an event with a single Offset type can be
    targeted at an EMS in order to request a percentage load reduction
    on the average energy usage of the entire premise. An EMS SHOULD use
    the Metering function set to determine the initial load in the
    premise, reduce energy consumption by controlling devices at its
    disposal, and at the conclusion of the event, once again use the
    Metering function set to determine if the desired load reduction was
    achieved.

    :ivar cooling_offset: The value change requested for the cooling
        offset, in degree C / 10. The value should be added to the
        normal set point for cooling, or if loadShiftForward is true,
        then the value should be subtracted from the normal set point.
    :ivar heating_offset: The value change requested for the heating
        offset, in degree C / 10. The value should be subtracted for
        heating, or if loadShiftForward is true, then the value should
        be added to the normal set point.
    :ivar load_adjustment_percentage_offset: The value change requested
        for the load adjustment percentage. The value should be
        subtracted from the normal setting, or if loadShiftForward is
        true, then the value should be added to the normal setting.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    cooling_offset: Optional[int] = field(
        default=None,
        metadata={
            "name": "coolingOffset",
            "type": "Element",
        }
    )
    heating_offset: Optional[int] = field(
        default=None,
        metadata={
            "name": "heatingOffset",
            "type": "Element",
        }
    )
    load_adjustment_percentage_offset: Optional[int] = field(
        default=None,
        metadata={
            "name": "loadAdjustmentPercentageOffset",
            "type": "Element",
        }
    )


@dataclass
class OperationalModeStatusType:
    """DER OperationalModeStatus value:

    0 - Not applicable / Unknown
    1 - Off
    2 - Operational mode
    3 - Test mode
    All other values reserved.

    :ivar date_time: The date and time at which the state applied.
    :ivar value: The value indicating the state.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    date_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "dateTime",
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class PowerConfiguration:
    """
    Contains configuration related to the device's power sources.

    :ivar battery_install_time: Time/Date at which battery was
        installed,
    :ivar low_charge_threshold: In context of the PowerStatus resource,
        this is the value of EstimatedTimeRemaining below which
        BatteryStatus "low" is indicated and the PS_LOW_BATTERY is
        raised.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    battery_install_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "batteryInstallTime",
            "type": "Element",
        }
    )
    low_charge_threshold: Optional[int] = field(
        default=None,
        metadata={
            "name": "lowChargeThreshold",
            "type": "Element",
        }
    )


@dataclass
class PowerFactor:
    """
    Specifies a setpoint for Displacement Power Factor, the ratio between
    apparent and active powers at the fundamental frequency (e.g. 60 Hz).

    :ivar displacement: Significand of an unsigned value of cos(theta)
        between 0 and 1.0. E.g. a value of 0.95 may be specified as a
        displacement of 950 and a multiplier of -3.
    :ivar multiplier: Specifies exponent of 'displacement'.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    displacement: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    multiplier: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class PowerFactorWithExcitation:
    """
    Specifies a setpoint for Displacement Power Factor, the ratio between
    apparent and active powers at the fundamental frequency (e.g. 60 Hz) and
    includes an excitation flag.

    :ivar displacement: Significand of an unsigned value of cos(theta)
        between 0 and 1.0. E.g. a value of 0.95 may be specified as a
        displacement of 950 and a multiplier of -3.
    :ivar excitation: True when DER is absorbing reactive power (under-
        excited), false when DER is injecting reactive power (over-
        excited).
    :ivar multiplier: Specifies exponent of 'displacement'.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    displacement: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    excitation: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    multiplier: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class ReactivePower:
    """
    The reactive power Q (in var) is the product of root mean square (RMS)
    voltage, RMS current, and sin(theta) where theta is the phase angle of
    current relative to voltage.

    :ivar multiplier: Specifies exponent of uom.
    :ivar value: Value in volt-amperes reactive (var) (uom 63)
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    multiplier: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class ReactiveSusceptance:
    """
    Reactive susceptance.

    :ivar multiplier: Specifies exponent of uom.
    :ivar value: Value in siemens (uom 53)
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    multiplier: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class RealEnergy:
    """
    Real electrical energy.

    :ivar multiplier: Multiplier for 'unit'.
    :ivar value: Value of the energy in Watt-hours. (uom 72)
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    multiplier: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_inclusive": 281474976710655,
        }
    )


@dataclass
class RequestStatus:
    """
    The RequestStatus object is used to indicate the current status of a Flow
    Reservation Request.

    :ivar date_time: The dateTime attribute will provide a timestamp of
        when the request status was set. dateTime MUST be set to the
        time at which the status change occurred, not a time in the
        future or past.
    :ivar request_status: Field representing the request status type. 0
        = Requested 1 = Cancelled All other values reserved.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    date_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "dateTime",
            "type": "Element",
            "required": True,
        }
    )
    request_status: Optional[int] = field(
        default=None,
        metadata={
            "name": "requestStatus",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class Resource:
    """
    A resource is an addressable unit of information, either a collection
    (List) or instance of an object (identifiedObject, or simply, Resource)

    :ivar href: A reference to the resource address (URI). Required in a
        response to a GET, ignored otherwise.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    href: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )


@dataclass
class ServiceChange:
    """
    Specifies a change to the service status.

    :ivar new_status: The new service status, to take effect at the time
        specified by startTime
    :ivar start_time: The date/time when the change is to take effect.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    new_status: Optional[int] = field(
        default=None,
        metadata={
            "name": "newStatus",
            "type": "Element",
            "required": True,
        }
    )
    start_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "startTime",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class SetPoint:
    """The SetPoint object is used to apply specific temperature set points to
    a temperature control device.

    The values of the heatingSetpoint and coolingSetpoint attributes SHALL be calculated as follows:
    Cooling/Heating Temperature Set Point / 100 = temperature in degrees Celsius where -273.15°C &amp;lt;= temperature &amp;lt;= 327.67°C, corresponding to a Cooling and/or Heating Temperature Set Point. The maximum resolution this format allows is 0.01°C.
    The field not present in a Response indicates that this field has not been used by the end device.
    If a temperature is sent that exceeds the temperature limit boundaries that are programmed into the device, the device SHALL respond by setting the temperature at the limit.

    :ivar cooling_setpoint: This attribute represents the cooling
        temperature set point in degrees Celsius / 100. (Hundredths of a
        degree C)
    :ivar heating_setpoint: This attribute represents the heating
        temperature set point in degrees Celsius / 100. (Hundredths of a
        degree C)
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    cooling_setpoint: Optional[int] = field(
        default=None,
        metadata={
            "name": "coolingSetpoint",
            "type": "Element",
        }
    )
    heating_setpoint: Optional[int] = field(
        default=None,
        metadata={
            "name": "heatingSetpoint",
            "type": "Element",
        }
    )


@dataclass
class SignedRealEnergy:
    """
    Real electrical energy, signed.

    :ivar multiplier: Multiplier for 'unit'.
    :ivar value: Value of the energy in Watt-hours. (uom 72)
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    multiplier: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "min_inclusive": -140737488355328,
            "max_inclusive": 140737488355328,
        }
    )


@dataclass
class StateOfChargeStatusType:
    """
    DER StateOfChargeStatus value: Percent data type.

    :ivar date_time: The date and time at which the state applied.
    :ivar value: The value indicating the state.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    date_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "dateTime",
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class StorageModeStatusType:
    """DER StorageModeStatus value:

    0 – storage charging 1 – storage discharging 2 – storage holding All
    other values reserved.

    :ivar date_time: The date and time at which the state applied.
    :ivar value: The value indicating the state.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    date_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "dateTime",
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class TargetReduction:
    """The TargetReduction object is used by a Demand Response service provider
    to provide a RECOMMENDED threshold that a device/premises should maintain
    its consumption below.

    For example, a service provider can provide a RECOMMENDED threshold
    of some kWh for a 3-hour event. This means that the device/premises
    would maintain its consumption below the specified limit for the
    specified period.

    :ivar type: Indicates the type of reduction requested.
    :ivar value: Indicates the requested amount of the relevant
        commodity to be reduced.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    type: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class Temperature:
    """
    Specification of a temperature.

    :ivar multiplier: Multiplier for 'unit'.
    :ivar subject: The subject of the temperature measurement 0 -
        Enclosure 1 - Transformer 2 - HeatSink
    :ivar value: Value in Degrees Celsius (uom 23).
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    multiplier: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    subject: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class TimeConfiguration:
    """
    Contains attributes related to the configuration of the time service.

    :ivar dst_end_rule: Rule to calculate end of daylight savings time
        in the current year.  Result of dstEndRule must be greater than
        result of dstStartRule.
    :ivar dst_offset: Daylight savings time offset from local standard
        time.
    :ivar dst_start_rule: Rule to calculate start of daylight savings
        time in the current year. Result of dstEndRule must be greater
        than result of dstStartRule.
    :ivar tz_offset: Local time zone offset from UTCTime. Does not
        include any daylight savings time offsets.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    dst_end_rule: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "dstEndRule",
            "type": "Element",
            "required": True,
            "max_length": 4,
            "format": "base16",
        }
    )
    dst_offset: Optional[int] = field(
        default=None,
        metadata={
            "name": "dstOffset",
            "type": "Element",
            "required": True,
        }
    )
    dst_start_rule: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "dstStartRule",
            "type": "Element",
            "required": True,
            "max_length": 4,
            "format": "base16",
        }
    )
    tz_offset: Optional[int] = field(
        default=None,
        metadata={
            "name": "tzOffset",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class UnitValueType:
    """
    Type for specification of a specific value, with units and power of ten
    multiplier.

    :ivar multiplier: Multiplier for 'unit'.
    :ivar unit: Unit in symbol
    :ivar value: Value in units specified
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    multiplier: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    unit: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class UnsignedFixedPointType:
    """
    Abstract type for specifying an unsigned fixed-point value without a given
    unit of measure.

    :ivar multiplier: Specifies exponent of uom.
    :ivar value: Dimensionless value
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    multiplier: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class VoltageRms:
    """
    Average electric potential difference between two points.

    :ivar multiplier: Specifies exponent of uom.
    :ivar value: Value in volts RMS (uom 29)
    """
    class Meta:
        name = "VoltageRMS"
        namespace = "urn:ieee:std:2030.5:ns"

    multiplier: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class WattHour:
    """
    Active (real) energy.

    :ivar multiplier: Specifies exponent of uom.
    :ivar value: Value in watt-hours (uom 72)
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    multiplier: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class LoWpan:
    """
    Contains information specific to 6LoWPAN.

    :ivar octets_rx: Number of Bytes received
    :ivar octets_tx: Number of Bytes transmitted
    :ivar packets_rx: Number of packets received
    :ivar packets_tx: Number of packets transmitted
    :ivar rx_frag_error: Number of errors receiving fragments
    """
    class Meta:
        name = "loWPAN"
        namespace = "urn:ieee:std:2030.5:ns"

    octets_rx: Optional[int] = field(
        default=None,
        metadata={
            "name": "octetsRx",
            "type": "Element",
        }
    )
    octets_tx: Optional[int] = field(
        default=None,
        metadata={
            "name": "octetsTx",
            "type": "Element",
        }
    )
    packets_rx: Optional[int] = field(
        default=None,
        metadata={
            "name": "packetsRx",
            "type": "Element",
            "required": True,
        }
    )
    packets_tx: Optional[int] = field(
        default=None,
        metadata={
            "name": "packetsTx",
            "type": "Element",
            "required": True,
        }
    )
    rx_frag_error: Optional[int] = field(
        default=None,
        metadata={
            "name": "rxFragError",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class AccountBalanceLink(Link):
    """
    SHALL contain a Link to an instance of AccountBalance.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class AccountingUnit:
    """
    Unit for accounting; use either 'energyUnit' or 'currencyUnit' to specify
    the unit for 'value'.

    :ivar energy_unit: Unit of service.
    :ivar monetary_unit: Unit of currency.
    :ivar multiplier: Multiplier for the 'energyUnit' or 'monetaryUnit'.
    :ivar value: Value of the monetary aspect
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    energy_unit: Optional[RealEnergy] = field(
        default=None,
        metadata={
            "name": "energyUnit",
            "type": "Element",
        }
    )
    monetary_unit: Optional[int] = field(
        default=None,
        metadata={
            "name": "monetaryUnit",
            "type": "Element",
            "required": True,
        }
    )
    multiplier: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class AssociatedUsagePointLink(Link):
    """SHALL contain a Link to an instance of UsagePoint.

    If present, this is the submeter that monitors the DER output.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class BillingPeriod(Resource):
    """A Billing Period relates to the period of time on which a customer is
    billed.

    As an example the billing period interval for a particular customer
    might be 31 days starting on July 1, 2011. The start date and
    interval can change on each billing period. There may also be
    multiple billing periods related to a customer agreement to support
    different tariff structures.

    :ivar bill_last_period: The amount of the bill for the previous
        billing period.
    :ivar bill_to_date: The bill amount related to the billing period as
        of the statusTimeStamp.
    :ivar interval: The time interval for this billing period.
    :ivar status_time_stamp: The date / time of the last update of this
        resource.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    bill_last_period: Optional[int] = field(
        default=None,
        metadata={
            "name": "billLastPeriod",
            "type": "Element",
            "min_inclusive": -140737488355328,
            "max_inclusive": 140737488355328,
        }
    )
    bill_to_date: Optional[int] = field(
        default=None,
        metadata={
            "name": "billToDate",
            "type": "Element",
            "min_inclusive": -140737488355328,
            "max_inclusive": 140737488355328,
        }
    )
    interval: Optional[DateTimeInterval] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    status_time_stamp: Optional[int] = field(
        default=None,
        metadata={
            "name": "statusTimeStamp",
            "type": "Element",
        }
    )


@dataclass
class ConfigurationLink(Link):
    """
    SHALL contain a Link to an instance of Configuration.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class ConsumptionTariffInterval(Resource):
    """One of a sequence of thresholds defined in terms of consumption quantity
    of a service such as electricity, water, gas, etc.

    It defines the steps or blocks in a step tariff structure, where
    startValue simultaneously defines the entry value of this step and
    the closing value of the previous step. Where consumption is greater
    than startValue, it falls within this block and where consumption is
    less than or equal to startValue, it falls within one of the
    previous blocks.

    :ivar consumption_block: Indicates the consumption block related to
        the reading. If not specified, is assumed to be "0 - N/A".
    :ivar environmental_cost:
    :ivar price: The charge for this rate component, per unit of measure
        defined by the associated ReadingType, in currency specified in
        TariffProfile. The Pricing service provider determines the
        appropriate price attribute value based on its applicable
        regulatory rules. For example, price could be net or inclusive
        of applicable taxes, fees, or levies. The Billing function set
        provides the ability to represent billing information in a more
        detailed manner.
    :ivar start_value: The lowest level of consumption that defines the
        starting point of this consumption step or block. Thresholds
        start at zero for each billing period. If specified, the first
        ConsumptionTariffInterval.startValue for a TimeTariffInteral
        instance SHALL begin at "0." Subsequent
        ConsumptionTariffInterval.startValue elements SHALL be greater
        than the previous one.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    consumption_block: Optional[int] = field(
        default=None,
        metadata={
            "name": "consumptionBlock",
            "type": "Element",
            "required": True,
        }
    )
    environmental_cost: List[EnvironmentalCost] = field(
        default_factory=list,
        metadata={
            "name": "EnvironmentalCost",
            "type": "Element",
        }
    )
    price: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    start_value: Optional[int] = field(
        default=None,
        metadata={
            "name": "startValue",
            "type": "Element",
            "required": True,
            "max_inclusive": 281474976710655,
        }
    )


@dataclass
class CurrentDerprogramLink(Link):
    """SHALL contain a Link to an instance of DERProgram.

    If present, this is the DERProgram containing the currently active
    DERControl.
    """
    class Meta:
        name = "CurrentDERProgramLink"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class CustomerAccountLink(Link):
    """
    SHALL contain a Link to an instance of CustomerAccount.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DeravailabilityLink(Link):
    """
    SHALL contain a Link to an instance of DERAvailability.
    """
    class Meta:
        name = "DERAvailabilityLink"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class Dercapability(Resource):
    """
    Distributed energy resource type and nameplate ratings.

    :ivar modes_supported: Bitmap indicating the DER Controls
        implemented by the device. See DERControlType for values.
    :ivar rtg_abnormal_category: Abnormal operating performance category
        as defined by IEEE 1547-2018. One of: 0 - not specified 1 -
        Category I 2 - Category II 3 - Category III All other values
        reserved.
    :ivar rtg_max_a: Maximum continuous AC current capability of the
        DER, in Amperes (RMS).
    :ivar rtg_max_ah: Usable energy storage capacity of the DER, in
        AmpHours.
    :ivar rtg_max_charge_rate_va: Maximum apparent power charge rating
        in Volt-Amperes. May differ from the maximum apparent power
        rating.
    :ivar rtg_max_charge_rate_w: Maximum rate of energy transfer
        received by the storage DER, in Watts.
    :ivar rtg_max_discharge_rate_va: Maximum apparent power discharge
        rating in Volt-Amperes. May differ from the maximum apparent
        power rating.
    :ivar rtg_max_discharge_rate_w: Maximum rate of energy transfer
        delivered by the storage DER, in Watts. Required for combined
        generation/storage DERs (e.g. DERType == 83).
    :ivar rtg_max_v: AC voltage maximum rating.
    :ivar rtg_max_va: Maximum continuous apparent power output
        capability of the DER, in VA.
    :ivar rtg_max_var: Maximum continuous reactive power delivered by
        the DER, in var.
    :ivar rtg_max_var_neg: Maximum continuous reactive power received by
        the DER, in var.  If absent, defaults to negative rtgMaxVar.
    :ivar rtg_max_w: Maximum continuous active power output capability
        of the DER, in watts. Represents combined generation plus
        storage output if DERType == 83.
    :ivar rtg_max_wh: Maximum energy storage capacity of the DER, in
        WattHours.
    :ivar rtg_min_pfover_excited: Minimum Power Factor displacement
        capability of the DER when injecting reactive power (over-
        excited); SHALL be a positive value between 0.0 (typically
        &amp;gt; 0.7) and 1.0. If absent, defaults to unity.
    :ivar rtg_min_pfunder_excited: Minimum Power Factor displacement
        capability of the DER when absorbing reactive power (under-
        excited); SHALL be a positive value between 0.0 (typically
        &amp;gt; 0.7) and 0.9999.  If absent, defaults to
        rtgMinPFOverExcited.
    :ivar rtg_min_v: AC voltage minimum rating.
    :ivar rtg_normal_category: Normal operating performance category as
        defined by IEEE 1547-2018. One of: 0 - not specified 1 -
        Category A 2 - Category B All other values reserved.
    :ivar rtg_over_excited_pf: Specified over-excited power factor.
    :ivar rtg_over_excited_w: Active power rating in Watts at specified
        over-excited power factor (rtgOverExcitedPF). If present,
        rtgOverExcitedPF SHALL be present.
    :ivar rtg_reactive_susceptance: Reactive susceptance that remains
        connected to the Area EPS in the cease to energize and trip
        state.
    :ivar rtg_under_excited_pf: Specified under-excited power factor.
    :ivar rtg_under_excited_w: Active power rating in Watts at specified
        under-excited power factor (rtgUnderExcitedPF). If present,
        rtgUnderExcitedPF SHALL be present.
    :ivar rtg_vnom: AC voltage nominal rating.
    :ivar type: Type of DER; see DERType object
    """
    class Meta:
        name = "DERCapability"
        namespace = "urn:ieee:std:2030.5:ns"

    modes_supported: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "modesSupported",
            "type": "Element",
            "required": True,
            "max_length": 4,
            "format": "base16",
        }
    )
    rtg_abnormal_category: Optional[int] = field(
        default=None,
        metadata={
            "name": "rtgAbnormalCategory",
            "type": "Element",
        }
    )
    rtg_max_a: Optional[CurrentRms] = field(
        default=None,
        metadata={
            "name": "rtgMaxA",
            "type": "Element",
        }
    )
    rtg_max_ah: Optional[AmpereHour] = field(
        default=None,
        metadata={
            "name": "rtgMaxAh",
            "type": "Element",
        }
    )
    rtg_max_charge_rate_va: Optional[ApparentPower] = field(
        default=None,
        metadata={
            "name": "rtgMaxChargeRateVA",
            "type": "Element",
        }
    )
    rtg_max_charge_rate_w: Optional[ActivePower] = field(
        default=None,
        metadata={
            "name": "rtgMaxChargeRateW",
            "type": "Element",
        }
    )
    rtg_max_discharge_rate_va: Optional[ApparentPower] = field(
        default=None,
        metadata={
            "name": "rtgMaxDischargeRateVA",
            "type": "Element",
        }
    )
    rtg_max_discharge_rate_w: Optional[ActivePower] = field(
        default=None,
        metadata={
            "name": "rtgMaxDischargeRateW",
            "type": "Element",
        }
    )
    rtg_max_v: Optional[VoltageRms] = field(
        default=None,
        metadata={
            "name": "rtgMaxV",
            "type": "Element",
        }
    )
    rtg_max_va: Optional[ApparentPower] = field(
        default=None,
        metadata={
            "name": "rtgMaxVA",
            "type": "Element",
        }
    )
    rtg_max_var: Optional[ReactivePower] = field(
        default=None,
        metadata={
            "name": "rtgMaxVar",
            "type": "Element",
        }
    )
    rtg_max_var_neg: Optional[ReactivePower] = field(
        default=None,
        metadata={
            "name": "rtgMaxVarNeg",
            "type": "Element",
        }
    )
    rtg_max_w: Optional[ActivePower] = field(
        default=None,
        metadata={
            "name": "rtgMaxW",
            "type": "Element",
            "required": True,
        }
    )
    rtg_max_wh: Optional[WattHour] = field(
        default=None,
        metadata={
            "name": "rtgMaxWh",
            "type": "Element",
        }
    )
    rtg_min_pfover_excited: Optional[PowerFactor] = field(
        default=None,
        metadata={
            "name": "rtgMinPFOverExcited",
            "type": "Element",
        }
    )
    rtg_min_pfunder_excited: Optional[PowerFactor] = field(
        default=None,
        metadata={
            "name": "rtgMinPFUnderExcited",
            "type": "Element",
        }
    )
    rtg_min_v: Optional[VoltageRms] = field(
        default=None,
        metadata={
            "name": "rtgMinV",
            "type": "Element",
        }
    )
    rtg_normal_category: Optional[int] = field(
        default=None,
        metadata={
            "name": "rtgNormalCategory",
            "type": "Element",
        }
    )
    rtg_over_excited_pf: Optional[PowerFactor] = field(
        default=None,
        metadata={
            "name": "rtgOverExcitedPF",
            "type": "Element",
        }
    )
    rtg_over_excited_w: Optional[ActivePower] = field(
        default=None,
        metadata={
            "name": "rtgOverExcitedW",
            "type": "Element",
        }
    )
    rtg_reactive_susceptance: Optional[ReactiveSusceptance] = field(
        default=None,
        metadata={
            "name": "rtgReactiveSusceptance",
            "type": "Element",
        }
    )
    rtg_under_excited_pf: Optional[PowerFactor] = field(
        default=None,
        metadata={
            "name": "rtgUnderExcitedPF",
            "type": "Element",
        }
    )
    rtg_under_excited_w: Optional[ActivePower] = field(
        default=None,
        metadata={
            "name": "rtgUnderExcitedW",
            "type": "Element",
        }
    )
    rtg_vnom: Optional[VoltageRms] = field(
        default=None,
        metadata={
            "name": "rtgVNom",
            "type": "Element",
        }
    )
    type: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class DercapabilityLink(Link):
    """
    SHALL contain a Link to an instance of DERCapability.
    """
    class Meta:
        name = "DERCapabilityLink"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DercurveLink(Link):
    """
    SHALL contain a Link to an instance of DERCurve.
    """
    class Meta:
        name = "DERCurveLink"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class Derlink(Link):
    """
    SHALL contain a Link to an instance of DER.
    """
    class Meta:
        name = "DERLink"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DerprogramLink(Link):
    """
    SHALL contain a Link to an instance of DERProgram.
    """
    class Meta:
        name = "DERProgramLink"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DersettingsLink(Link):
    """
    SHALL contain a Link to an instance of DERSettings.
    """
    class Meta:
        name = "DERSettingsLink"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DerstatusLink(Link):
    """
    SHALL contain a Link to an instance of DERStatus.
    """
    class Meta:
        name = "DERStatusLink"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class Drlccapabilities:
    """
    Contains information about the static capabilities of the device, to allow
    service providers to know what types of functions are supported, what the
    normal operating ranges and limits are, and other similar information, in
    order to provide better suggestions of applicable programs to receive the
    maximum benefit.

    :ivar average_energy: The average hourly energy usage when in normal
        operating mode.
    :ivar max_demand: The maximum demand rating of this end device.
    :ivar options_implemented: Bitmap indicating the DRLC options
        implemented by the device. 0 - Target reduction (kWh) 1 - Target
        reduction (kW) 2 - Target reduction (Watts) 3 - Target reduction
        (Cubic Meters) 4 - Target reduction (Cubic Feet) 5 - Target
        reduction (US Gallons) 6 - Target reduction (Imperial Gallons) 7
        - Target reduction (BTUs) 8 - Target reduction (Liters) 9 -
        Target reduction (kPA (gauge)) 10 - Target reduction (kPA
        (absolute)) 11 - Target reduction (Mega Joule) 12 - Target
        reduction (Unitless) 13-15 - Reserved 16 - Temperature set point
        17 - Temperature offset 18 - Duty cycle 19 - Load adjustment
        percentage 20 - Appliance load reduction 21-31 - Reserved
    """
    class Meta:
        name = "DRLCCapabilities"
        namespace = "urn:ieee:std:2030.5:ns"

    average_energy: Optional[RealEnergy] = field(
        default=None,
        metadata={
            "name": "averageEnergy",
            "type": "Element",
            "required": True,
        }
    )
    max_demand: Optional[ActivePower] = field(
        default=None,
        metadata={
            "name": "maxDemand",
            "type": "Element",
            "required": True,
        }
    )
    options_implemented: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "optionsImplemented",
            "type": "Element",
            "required": True,
            "max_length": 4,
            "format": "base16",
        }
    )


@dataclass
class DefaultDercontrolLink(Link):
    """SHALL contain a Link to an instance of DefaultDERControl.

    This is the default mode of the DER which MAY be overridden by
    DERControl events.
    """
    class Meta:
        name = "DefaultDERControlLink"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DemandResponseProgramLink(Link):
    """
    SHALL contain a Link to an instance of DemandResponseProgram.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DeviceCapabilityLink(Link):
    """
    SHALL contain a Link to an instance of DeviceCapability.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DeviceInformationLink(Link):
    """
    SHALL contain a Link to an instance of DeviceInformation.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DeviceStatusLink(Link):
    """
    SHALL contain a Link to an instance of DeviceStatus.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class EndDeviceLink(Link):
    """
    SHALL contain a Link to an instance of EndDevice.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class File(Resource):
    """This resource contains various meta-data describing a file's
    characteristics.

    The meta-data provides general file information and also is used to
    support filtered queries of file lists

    :ivar activate_time: This element MUST be set to the date/time at
        which this file is activated. If the activation time is less
        than or equal to current time, the LD MUST immediately place the
        file into the activated state (in the case of a firmware file,
        the file is now the running image).  If the activation time is
        greater than the current time, the LD MUST wait until the
        specified activation time is reached, then MUST place the file
        into the activated state. Omission of this element means that
        the LD MUST NOT take any action to activate the file until a
        subsequent GET to this File resource provides an activateTime.
    :ivar file_uri: This element MUST be set to the URI location of the
        file binary artifact.  This is the BLOB (binary large object)
        that is actually loaded by the LD
    :ivar l_fdi: This element MUST be set to the LFDI of the device for
        which this file in targeted.
    :ivar mf_hw_ver: This element MUST be set to the hardware version
        for which this file is targeted.
    :ivar mf_id: This element MUST be set to the manufacturer's Private
        Enterprise Number (assigned by IANA).
    :ivar mf_model: This element MUST be set to the manufacturer model
        number for which this file is targeted. The syntax and semantics
        are left to the manufacturer.
    :ivar mf_ser_num: This element MUST be set to the manufacturer
        serial number for which this file is targeted. The syntax and
        semantics are left to the manufacturer.
    :ivar mf_ver: This element MUST be set to the software version
        information for this file. The syntax and semantics are left to
        the manufacturer.
    :ivar size: This element MUST be set to the total size (in bytes) of
        the file referenced by fileURI.
    :ivar type: A value indicating the type of the file.  MUST be one of
        the following values: 00 = Software Image 01 = Security
        Credential 02 = Configuration 03 = Log 04–7FFF = reserved
        8000-FFFF = Manufacturer defined
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    activate_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "activateTime",
            "type": "Element",
        }
    )
    file_uri: Optional[str] = field(
        default=None,
        metadata={
            "name": "fileURI",
            "type": "Element",
            "required": True,
        }
    )
    l_fdi: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "lFDI",
            "type": "Element",
            "max_length": 20,
            "format": "base16",
        }
    )
    mf_hw_ver: Optional[str] = field(
        default=None,
        metadata={
            "name": "mfHwVer",
            "type": "Element",
            "max_length": 32,
        }
    )
    mf_id: Optional[int] = field(
        default=None,
        metadata={
            "name": "mfID",
            "type": "Element",
            "required": True,
        }
    )
    mf_model: Optional[str] = field(
        default=None,
        metadata={
            "name": "mfModel",
            "type": "Element",
            "required": True,
            "max_length": 32,
        }
    )
    mf_ser_num: Optional[str] = field(
        default=None,
        metadata={
            "name": "mfSerNum",
            "type": "Element",
            "max_length": 32,
        }
    )
    mf_ver: Optional[str] = field(
        default=None,
        metadata={
            "name": "mfVer",
            "type": "Element",
            "required": True,
            "max_length": 16,
        }
    )
    size: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    type: Optional[bytes] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 2,
            "format": "base16",
        }
    )


@dataclass
class FileLink(Link):
    """This element MUST be set to the URI of the most recent File being
    loaded/activated by the LD.

    In the case of file status 0, this element MUST be omitted.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class FileStatusLink(Link):
    """
    SHALL contain a Link to an instance of FileStatus.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class IdentifiedObject(Resource):
    """
    This is a root class to provide common naming attributes for all classes
    needing naming attributes.

    :ivar m_rid: The global identifier of the object.
    :ivar description: The description is a human readable text
        describing or naming the object.
    :ivar version: Contains the version number of the object. See the
        type definition for details.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    m_rid: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "mRID",
            "type": "Element",
            "required": True,
            "max_length": 16,
            "format": "base16",
        }
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 32,
        }
    )
    version: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class ListType(Resource):
    """Container to hold a collection of object instances or references.

    See Design Pattern section for additional details.

    :ivar all: The number specifying "all" of the items in the list.
        Required on a response to a GET, ignored otherwise.
    :ivar results: Indicates the number of items in this page of
        results.
    """
    class Meta:
        name = "List"
        namespace = "urn:ieee:std:2030.5:ns"

    all: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
    results: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass
class ListLink(Link):
    """
    ListLinks provide a reference, via URI, to a List.

    :ivar all: Indicates the total number of items in the referenced
        list. This attribute SHALL be present if the href is a local or
        relative URI. This attribute SHOULD NOT be present if the href
        is a remote or absolute URI, as the server may be unaware of
        changes to the value.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    all: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
        }
    )


@dataclass
class LogEvent(Resource):
    """
    A time stamped instance of a significant event detected by the device.

    :ivar created_date_time: The date and time that the event occurred.
    :ivar details: Human readable text that MAY be used to transmit
        additional details about the event. A host MAY remove this field
        when received.
    :ivar extended_data: May be used to transmit additional details
        about the event.
    :ivar function_set: If the profileID indicates this is IEEE 2030.5,
        the functionSet is defined by IEEE 2030.5 and SHALL be one of
        the values from the table below (IEEE 2030.5 function set
        identifiers). If the profileID is anything else, the functionSet
        is defined by the identified profile. 0       General (not
        specific to a function set) 1       Publish and Subscribe 2
        End Device 3       Function Set Assignment 4       Response 5
        Demand Response and Load Control 6       Metering 7
        Pricing 8       Messaging 9       Billing 10      Prepayment 11
        Distributed Energy Resources 12      Time 13      Software
        Download 14      Device Information 15      Power Status 16
        Network Status 17      Log Event List 18      Configuration 19
        Security All other values are reserved.
    :ivar log_event_code: An 8 bit unsigned integer. logEventCodes are
        scoped to a profile and a function set. If the profile is IEEE
        2030.5, the logEventCode is defined by IEEE 2030.5 within one of
        the function sets of IEEE 2030.5. If the profile is anything
        else, the logEventCode is defined by the specified profile.
    :ivar log_event_id: This 16-bit value, combined with
        createdDateTime, profileID, and logEventPEN, should provide a
        reasonable level of uniqueness.
    :ivar log_event_pen: The Private Enterprise Number(PEN) of the
        entity that defined the profileID, functionSet, and logEventCode
        of the logEvent. IEEE 2030.5-assigned logEventCodes SHALL use
        the IEEE 2030.5 PEN.  Combinations of profileID, functionSet,
        and logEventCode SHALL have unique meaning within a logEventPEN
        and are defined by the owner of the PEN.
    :ivar profile_id: The profileID identifies which profile (HA, BA,
        SE, etc) defines the following event information. 0       Not
        profile specific. 1       Vendor Defined 2       IEEE 2030.5 3
        Home Automation 4       Building Automation All other values are
        reserved.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    created_date_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "createdDateTime",
            "type": "Element",
            "required": True,
        }
    )
    details: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 32,
        }
    )
    extended_data: Optional[int] = field(
        default=None,
        metadata={
            "name": "extendedData",
            "type": "Element",
        }
    )
    function_set: Optional[int] = field(
        default=None,
        metadata={
            "name": "functionSet",
            "type": "Element",
            "required": True,
        }
    )
    log_event_code: Optional[int] = field(
        default=None,
        metadata={
            "name": "logEventCode",
            "type": "Element",
            "required": True,
        }
    )
    log_event_id: Optional[int] = field(
        default=None,
        metadata={
            "name": "logEventID",
            "type": "Element",
            "required": True,
        }
    )
    log_event_pen: Optional[int] = field(
        default=None,
        metadata={
            "name": "logEventPEN",
            "type": "Element",
            "required": True,
        }
    )
    profile_id: Optional[int] = field(
        default=None,
        metadata={
            "name": "profileID",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class MeterReadingLink(Link):
    """
    SHALL contain a Link to an instance of MeterReading.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class Neighbor(Resource):
    """
    Contains 802.15.4 link layer specific attributes.

    :ivar is_child: True if the neighbor is a child.
    :ivar link_quality: The quality of the link, as defined by 802.15.4
    :ivar short_address: As defined by IEEE 802.15.4
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    is_child: Optional[bool] = field(
        default=None,
        metadata={
            "name": "isChild",
            "type": "Element",
            "required": True,
        }
    )
    link_quality: Optional[int] = field(
        default=None,
        metadata={
            "name": "linkQuality",
            "type": "Element",
            "required": True,
        }
    )
    short_address: Optional[int] = field(
        default=None,
        metadata={
            "name": "shortAddress",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class Pevinfo:
    """
    Contains attributes that can be exposed by PEVs and other devices that have
    charging requirements.

    :ivar charging_power_now: This is the actual power flow in or out of
        the charger or inverter. This is calculated by the vehicle based
        on actual measurements. This number is positive for charging.
    :ivar energy_request_now: This is the amount of energy that must be
        transferred from the grid to EVSE and PEV to achieve the target
        state of charge allowing for charger efficiency and any vehicle
        and EVSE parasitic loads. This is calculated by the vehicle and
        changes throughout the connection as forward or reverse power
        flow change the battery state of charge.  This number is
        positive for charging.
    :ivar max_forward_power: This is maximum power transfer capability
        that could be used for charging the PEV to perform the requested
        energy transfer.  It is the lower of the vehicle or EVSE
        physical power limitations. It is not based on economic
        considerations. The vehicle may draw less power than this value
        based on its charging cycle. The vehicle defines this parameter.
        This number is positive for charging power flow.
    :ivar minimum_charging_duration: This is computed by the PEV based
        on the charging profile to complete the energy transfer if the
        maximum power is authorized.  The value will never be smaller
        than the ratio of the energy request to the power request
        because the charging profile may not allow the maximum power to
        be used throughout the transfer.   This is a critical parameter
        for determining whether any slack time exists in the charging
        cycle between the current time and the TCIN.
    :ivar target_state_of_charge: This is the target state of charge
        that is to be achieved during charging before the time of
        departure (TCIN).  The default value is 100%. The value cannot
        be set to a value less than the actual state of charge.
    :ivar time_charge_is_needed: Time Charge is Needed (TCIN) is the
        time that the PEV is expected to depart. The value is manually
        entered using controls and displays in the vehicle or on the
        EVSE or using a mobile device.  It is authenticated and saved by
        the PEV.  This value may be updated during a charging session.
    :ivar time_charging_status_pev: This is the time that the parameters
        are updated, except for changes to TCIN.
    """
    class Meta:
        name = "PEVInfo"
        namespace = "urn:ieee:std:2030.5:ns"

    charging_power_now: Optional[ActivePower] = field(
        default=None,
        metadata={
            "name": "chargingPowerNow",
            "type": "Element",
            "required": True,
        }
    )
    energy_request_now: Optional[RealEnergy] = field(
        default=None,
        metadata={
            "name": "energyRequestNow",
            "type": "Element",
            "required": True,
        }
    )
    max_forward_power: Optional[ActivePower] = field(
        default=None,
        metadata={
            "name": "maxForwardPower",
            "type": "Element",
            "required": True,
        }
    )
    minimum_charging_duration: Optional[int] = field(
        default=None,
        metadata={
            "name": "minimumChargingDuration",
            "type": "Element",
            "required": True,
        }
    )
    target_state_of_charge: Optional[int] = field(
        default=None,
        metadata={
            "name": "targetStateOfCharge",
            "type": "Element",
            "required": True,
        }
    )
    time_charge_is_needed: Optional[int] = field(
        default=None,
        metadata={
            "name": "timeChargeIsNeeded",
            "type": "Element",
            "required": True,
        }
    )
    time_charging_status_pev: Optional[int] = field(
        default=None,
        metadata={
            "name": "timeChargingStatusPEV",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class PowerStatusLink(Link):
    """
    SHALL contain a Link to an instance of PowerStatus.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class PrepayOperationStatus(Resource):
    """
    PrepayOperationStatus describes the status of the service or commodity
    being conditionally controlled by the Prepayment function set.

    :ivar credit_type_change: CreditTypeChange is used to define a
        pending change of creditTypeInUse, which will activate at a
        specified time.
    :ivar credit_type_in_use: CreditTypeInUse identifies whether the
        present mode of operation is consuming regular credit or
        emergency credit.
    :ivar service_change: ServiceChange is used to define a pending
        change of serviceStatus, which will activate at a specified
        time.
    :ivar service_status: ServiceStatus identifies whether the service
        is connected or disconnected, or armed for connection or
        disconnection.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    credit_type_change: Optional[CreditTypeChange] = field(
        default=None,
        metadata={
            "name": "creditTypeChange",
            "type": "Element",
        }
    )
    credit_type_in_use: Optional[int] = field(
        default=None,
        metadata={
            "name": "creditTypeInUse",
            "type": "Element",
        }
    )
    service_change: Optional[ServiceChange] = field(
        default=None,
        metadata={
            "name": "serviceChange",
            "type": "Element",
        }
    )
    service_status: Optional[int] = field(
        default=None,
        metadata={
            "name": "serviceStatus",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class PrepayOperationStatusLink(Link):
    """
    SHALL contain a Link to an instance of PrepayOperationStatus.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class PrepaymentLink(Link):
    """
    SHALL contain a Link to an instance of Prepayment.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class RplsourceRoutes(Resource):
    """
    A RPL source routes object.

    :ivar dest_address: See [RFC 6554].
    :ivar source_route: See [RFC 6554].
    """
    class Meta:
        name = "RPLSourceRoutes"
        namespace = "urn:ieee:std:2030.5:ns"

    dest_address: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "DestAddress",
            "type": "Element",
            "required": True,
            "max_length": 16,
            "format": "base16",
        }
    )
    source_route: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "SourceRoute",
            "type": "Element",
            "required": True,
            "max_length": 16,
            "format": "base16",
        }
    )


@dataclass
class RateComponentLink(Link):
    """
    SHALL contain a Link to an instance of RateComponent.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class ReadingBase(Resource):
    """Specific value measured by a meter or other asset.

    ReadingBase is abstract, used to define the elements common to
    Reading and IntervalReading.

    :ivar consumption_block: Indicates the consumption block related to
        the reading. REQUIRED if ReadingType numberOfConsumptionBlocks
        is non-zero. If not specified, is assumed to be "0 - N/A".
    :ivar quality_flags: List of codes indicating the quality of the
        reading, using specification: Bit 0 - valid: data that has gone
        through all required validation checks and either passed them
        all or has been verified Bit 1 - manually edited: Replaced or
        approved by a human Bit 2 - estimated using reference day: data
        value was replaced by a machine computed value based on analysis
        of historical data using the same type of measurement. Bit 3 -
        estimated using linear interpolation: data value was computed
        using linear interpolation based on the readings before and
        after it Bit 4 - questionable: data that has failed one or more
        checks Bit 5 - derived: data that has been calculated (using
        logic or mathematical operations), not necessarily measured
        directly Bit 6 - projected (forecast): data that has been
        calculated as a projection or forecast of future readings
    :ivar time_period: The time interval associated with the reading. If
        not specified, then defaults to the intervalLength specified in
        the associated ReadingType.
    :ivar tou_tier: Indicates the time of use tier related to the
        reading. REQUIRED if ReadingType numberOfTouTiers is non-zero.
        If not specified, is assumed to be "0 - N/A".
    :ivar value: Value in units specified by ReadingType
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    consumption_block: Optional[int] = field(
        default=None,
        metadata={
            "name": "consumptionBlock",
            "type": "Element",
        }
    )
    quality_flags: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "qualityFlags",
            "type": "Element",
            "max_length": 2,
            "format": "base16",
        }
    )
    time_period: Optional[DateTimeInterval] = field(
        default=None,
        metadata={
            "name": "timePeriod",
            "type": "Element",
        }
    )
    tou_tier: Optional[int] = field(
        default=None,
        metadata={
            "name": "touTier",
            "type": "Element",
        }
    )
    value: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "min_inclusive": -140737488355328,
            "max_inclusive": 140737488355328,
        }
    )


@dataclass
class ReadingLink(Link):
    """
    A Link to a Reading.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class ReadingType(Resource):
    """Type of data conveyed by a specific Reading.

    See IEC 61968 Part 9 Annex C for full definitions of these values.

    :ivar accumulation_behaviour: The “accumulation behaviour” indicates
        how the value is represented to accumulate over time.
    :ivar calorific_value: The amount of heat generated when a given
        mass of fuel is completely burned. The CalorificValue is used to
        convert the measured volume or mass of gas into kWh. The
        CalorificValue attribute represents the current active value.
    :ivar commodity: Indicates the commodity applicable to this
        ReadingType.
    :ivar conversion_factor: Accounts for changes in the volume of gas
        based on temperature and pressure. The ConversionFactor
        attribute represents the current active value. The
        ConversionFactor is dimensionless. The default value for the
        ConversionFactor is 1, which means no conversion is applied. A
        price server can advertise a new/different value at any time.
    :ivar data_qualifier: The data type can be used to describe a
        salient attribute of the data. Possible values are average,
        absolute, and etc.
    :ivar flow_direction: Anything involving current might have a flow
        direction. Possible values include forward and reverse.
    :ivar interval_length: Default interval length specified in seconds.
    :ivar kind: Compound class that contains kindCategory and kindIndex
    :ivar max_number_of_intervals: To be populated for mirrors of
        interval data to set the expected number of intervals per
        ReadingSet. Servers may discard intervals received that exceed
        this number.
    :ivar number_of_consumption_blocks: Number of consumption blocks. 0
        means not applicable, and is the default if not specified. The
        value needs to be at least 1 if any actual prices are provided.
    :ivar number_of_tou_tiers: The number of TOU tiers that can be used
        by any resource configured by this ReadingType. Servers SHALL
        populate this value with the largest touTier value that will
        &lt;i&gt;ever&lt;/i&gt; be used while this ReadingType is in
        effect. Servers SHALL set numberOfTouTiers equal to the number
        of standard TOU tiers plus the number of CPP tiers that may be
        used while this ReadingType is in effect. Servers SHALL specify
        a value between 0 and 255 (inclusive) for numberOfTouTiers
        (servers providing flat rate pricing SHOULD set numberOfTouTiers
        to 0, as in practice there is no difference between having no
        tiers and having one tier).
    :ivar phase: Contains phase information associated with the type.
    :ivar power_of_ten_multiplier: Indicates the power of ten multiplier
        applicable to the unit of measure of this ReadingType.
    :ivar sub_interval_length: Default sub-interval length specified in
        seconds for Readings of ReadingType. Some demand calculations
        are done over a number of smaller intervals. For example, in a
        rolling demand calculation, the demand value is defined as the
        rolling sum of smaller intervals over the intervalLength. The
        subintervalLength is the length of the smaller interval in this
        calculation. It SHALL be an integral division of the
        intervalLength. The number of sub-intervals can be calculated by
        dividing the intervalLength by the subintervalLength.
    :ivar supply_limit: Reflects the supply limit set in the meter. This
        value can be compared to the Reading value to understand if
        limits are being approached or exceeded. Units follow the same
        definition as in this ReadingType.
    :ivar tiered_consumption_blocks: Specifies whether or not the
        consumption blocks are differentiated by TOUTier or not. Default
        is false, if not specified. true = consumption accumulated over
        individual tiers false = consumption accumulated over all tiers
    :ivar uom: Indicates the measurement type for the units of measure
        for the readings of this type.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    accumulation_behaviour: Optional[int] = field(
        default=None,
        metadata={
            "name": "accumulationBehaviour",
            "type": "Element",
        }
    )
    calorific_value: Optional[UnitValueType] = field(
        default=None,
        metadata={
            "name": "calorificValue",
            "type": "Element",
        }
    )
    commodity: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    conversion_factor: Optional[UnitValueType] = field(
        default=None,
        metadata={
            "name": "conversionFactor",
            "type": "Element",
        }
    )
    data_qualifier: Optional[int] = field(
        default=None,
        metadata={
            "name": "dataQualifier",
            "type": "Element",
        }
    )
    flow_direction: Optional[int] = field(
        default=None,
        metadata={
            "name": "flowDirection",
            "type": "Element",
        }
    )
    interval_length: Optional[int] = field(
        default=None,
        metadata={
            "name": "intervalLength",
            "type": "Element",
        }
    )
    kind: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    max_number_of_intervals: Optional[int] = field(
        default=None,
        metadata={
            "name": "maxNumberOfIntervals",
            "type": "Element",
        }
    )
    number_of_consumption_blocks: Optional[int] = field(
        default=None,
        metadata={
            "name": "numberOfConsumptionBlocks",
            "type": "Element",
        }
    )
    number_of_tou_tiers: Optional[int] = field(
        default=None,
        metadata={
            "name": "numberOfTouTiers",
            "type": "Element",
        }
    )
    phase: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    power_of_ten_multiplier: Optional[int] = field(
        default=None,
        metadata={
            "name": "powerOfTenMultiplier",
            "type": "Element",
        }
    )
    sub_interval_length: Optional[int] = field(
        default=None,
        metadata={
            "name": "subIntervalLength",
            "type": "Element",
        }
    )
    supply_limit: Optional[int] = field(
        default=None,
        metadata={
            "name": "supplyLimit",
            "type": "Element",
            "max_inclusive": 281474976710655,
        }
    )
    tiered_consumption_blocks: Optional[bool] = field(
        default=None,
        metadata={
            "name": "tieredConsumptionBlocks",
            "type": "Element",
        }
    )
    uom: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class ReadingTypeLink(Link):
    """
    SHALL contain a Link to an instance of ReadingType.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class Registration(Resource):
    """
    Registration represents an authorization to access the resources on a host.

    :ivar date_time_registered: Contains the time at which this
        registration was created, by which clients MAY prioritize
        information providers with the most recent registrations, when
        no additional direction from the consumer is available.
    :ivar p_in: Contains the registration PIN number associated with the
        device, including the checksum digit.
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    date_time_registered: Optional[int] = field(
        default=None,
        metadata={
            "name": "dateTimeRegistered",
            "type": "Element",
            "required": True,
        }
    )
    p_in: Optional[int] = field(
        default=None,
        metadata={
            "name": "pIN",
            "type": "Element",
            "required": True,
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class RegistrationLink(Link):
    """
    SHALL contain a Link to an instance of Registration.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class RespondableResource(Resource):
    """
    A Resource to which a Response can be requested.

    :ivar reply_to: A reference to the response resource address (URI).
        Required on a response to a GET if responseRequired is "true".
    :ivar response_required: Indicates whether or not a response is
        required upon receipt, creation or update of this resource.
        Responses shall be posted to the collection specified in
        "replyTo". If the resource has a deviceCategory field, devices
        that match one or more of the device types indicated in
        deviceCategory SHALL respond according to the rules listed
        below.  If the category does not match, the device SHALL NOT
        respond. If the resource does not have a deviceCategory field, a
        device receiving the resource SHALL respond according to the
        rules listed below. Value encoded as hex according to the
        following bit assignments, any combination is possible. See
        Table 27 for the list of appropriate Response status codes to be
        sent for these purposes. 0 - End device shall indicate that
        message was received 1 - End device shall indicate specific
        response. 2 - End user / customer response is required. All
        other values reserved.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    reply_to: Optional[str] = field(
        default=None,
        metadata={
            "name": "replyTo",
            "type": "Attribute",
        }
    )
    response_required: bytes = field(
        default=b"\x00",
        metadata={
            "name": "responseRequired",
            "type": "Attribute",
            "max_length": 1,
            "format": "base16",
        }
    )


@dataclass
class Response(Resource):
    """
    The Response object is the generic response data repository which is
    extended for specific function sets.

    :ivar created_date_time: The createdDateTime field contains the date
        and time when the acknowledgement/status occurred in the client.
        The client will provide the timestamp to ensure the proper time
        is captured in case the response is delayed in reaching the
        server (server receipt time would not be the same as the actual
        confirmation time). The time reported from the client should be
        relative to the time server indicated by the
        FunctionSetAssignment that also indicated the event resource; if
        no FunctionSetAssignment exists, the time of the server where
        the event resource was hosted.
    :ivar end_device_lfdi: Contains the LFDI of the device providing the
        response.
    :ivar status: The status field contains the acknowledgement or
        status. Each event type (DRLC, DER, Price, or Text) can return
        different status information (e.g. an Acknowledge will be
        returned for a Price event where a DRLC event can return Event
        Received, Event Started, and Event Completed). The Status field
        value definitions are defined in Table 27: Response Types by
        Function Set.
    :ivar subject: The subject field provides a method to match the
        response with the originating event. It is populated with the
        mRID of the original object.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    created_date_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "createdDateTime",
            "type": "Element",
        }
    )
    end_device_lfdi: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "endDeviceLFDI",
            "type": "Element",
            "required": True,
            "max_length": 20,
            "format": "base16",
        }
    )
    status: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    subject: Optional[bytes] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 16,
            "format": "base16",
        }
    )


@dataclass
class SelfDeviceLink(Link):
    """
    SHALL contain a Link to an instance of SelfDevice.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class ServiceSupplierLink(Link):
    """
    SHALL contain a Link to an instance of ServiceSupplier.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class SubscribableResource(Resource):
    """
    A Resource to which a Subscription can be requested.

    :ivar subscribable: Indicates whether or not subscriptions are
        supported for this resource, and whether or not conditional
        (thresholds) are supported. If not specified, is "not
        subscribable" (0).
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    subscribable: int = field(
        default=0,
        metadata={
            "type": "Attribute",
        }
    )


@dataclass
class SubscriptionBase(Resource):
    """Holds the information related to a client subscription to receive
    updates to a resource automatically.

    The actual resources may be passed in the Notification by specifying
    a specific xsi:type for the Resource and passing the full
    representation.

    :ivar subscribed_resource: The resource for which the subscription
        applies. Query string parameters SHALL NOT be specified when
        subscribing to list resources.  Should a query string parameter
        be specified, servers SHALL ignore them.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    subscribed_resource: Optional[str] = field(
        default=None,
        metadata={
            "name": "subscribedResource",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class SupplyInterruptionOverride(Resource):
    """SupplyInterruptionOverride: There may be periods of time when social, regulatory or other concerns mean that service should not be interrupted, even when available credit has been exhausted. Each Prepayment instance links to a List of SupplyInterruptionOverride instances. Each SupplyInterruptionOverride defines a contiguous period of time during which supply SHALL NOT be interrupted.

    :ivar description: The description is a human readable text
        describing or naming the object.
    :ivar interval: Interval defines the period of time during which
        supply should not be interrupted.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 32,
        }
    )
    interval: Optional[DateTimeInterval] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class SupportedLocale(Resource):
    """
    Specifies a locale that is supported.

    :ivar locale: The code for a locale that is supported
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    locale: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 42,
        }
    )


@dataclass
class TariffProfileLink(Link):
    """
    SHALL contain a Link to an instance of TariffProfile.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class Time(Resource):
    """
    Contains the representation of time, constantly updated.

    :ivar current_time: The current time, in the format defined by
        TimeType.
    :ivar dst_end_time: Time at which daylight savings ends (dstOffset
        no longer applied).  Result of dstEndRule calculation.
    :ivar dst_offset: Daylight savings time offset from local standard
        time. A typical practice is advancing clocks one hour when
        daylight savings time is in effect, which would result in a
        positive dstOffset.
    :ivar dst_start_time: Time at which daylight savings begins (apply
        dstOffset).  Result of dstStartRule calculation.
    :ivar local_time: Local time: localTime = currentTime + tzOffset (+
        dstOffset when in effect).
    :ivar quality: Metric indicating the quality of the time source from
        which the service acquired time. Lower (smaller) quality
        enumeration values are assumed to be more accurate. 3 - time
        obtained from external authoritative source such as NTP 4 - time
        obtained from level 3 source 5 - time manually set or obtained
        from level 4 source 6 - time obtained from level 5 source 7 -
        time intentionally uncoordinated All other values are reserved
        for future use.
    :ivar tz_offset: Local time zone offset from currentTime. Does not
        include any daylight savings time offsets. For American time
        zones, a negative tzOffset SHALL be used (eg, EST = GMT-5 which
        is -18000).
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    current_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "currentTime",
            "type": "Element",
            "required": True,
        }
    )
    dst_end_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "dstEndTime",
            "type": "Element",
            "required": True,
        }
    )
    dst_offset: Optional[int] = field(
        default=None,
        metadata={
            "name": "dstOffset",
            "type": "Element",
            "required": True,
        }
    )
    dst_start_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "dstStartTime",
            "type": "Element",
            "required": True,
        }
    )
    local_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "localTime",
            "type": "Element",
        }
    )
    quality: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    tz_offset: Optional[int] = field(
        default=None,
        metadata={
            "name": "tzOffset",
            "type": "Element",
            "required": True,
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class TimeLink(Link):
    """
    SHALL contain a Link to an instance of Time.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class UsagePointLink(Link):
    """
    SHALL contain a Link to an instance of UsagePoint.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class AccountBalance(Resource):
    """AccountBalance contains the regular credit and emergency credit balance
    for this given service or commodity prepay instance.

    It may also contain status information concerning the balance data.

    :ivar available_credit: AvailableCredit shows the balance of the sum
        of credits minus the sum of charges. In a Central Wallet mode
        this value may be passed down to the Prepayment server via an
        out-of-band mechanism. In Local or ESI modes, this value may be
        calculated based upon summation of CreditRegister transactions
        minus consumption charges calculated using Metering (and
        possibly Pricing) function set data. This value may be negative;
        for instance, if disconnection is prevented due to a Supply
        Interruption Override.
    :ivar credit_status: CreditStatus identifies whether the present
        value of availableCredit is considered OK, low, exhausted, or
        negative.
    :ivar emergency_credit: EmergencyCredit is the amount of credit
        still available for the given service or commodity prepayment
        instance. If both availableCredit and emergyCredit are
        exhausted, then service will typically be disconnected.
    :ivar emergency_credit_status: EmergencyCreditStatus identifies
        whether the present value of emergencyCredit is considered OK,
        low, exhausted, or negative.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    available_credit: Optional[AccountingUnit] = field(
        default=None,
        metadata={
            "name": "availableCredit",
            "type": "Element",
            "required": True,
        }
    )
    credit_status: Optional[int] = field(
        default=None,
        metadata={
            "name": "creditStatus",
            "type": "Element",
        }
    )
    emergency_credit: Optional[AccountingUnit] = field(
        default=None,
        metadata={
            "name": "emergencyCredit",
            "type": "Element",
        }
    )
    emergency_credit_status: Optional[int] = field(
        default=None,
        metadata={
            "name": "emergencyCreditStatus",
            "type": "Element",
        }
    )


@dataclass
class ActiveBillingPeriodListLink(ListLink):
    """
    SHALL contain a Link to a List of active BillingPeriod instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class ActiveCreditRegisterListLink(ListLink):
    """
    SHALL contain a Link to a List of active CreditRegister instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class ActiveDercontrolListLink(ListLink):
    """
    SHALL contain a Link to a List of active DERControl instances.
    """
    class Meta:
        name = "ActiveDERControlListLink"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class ActiveEndDeviceControlListLink(ListLink):
    """
    SHALL contain a Link to a List of active EndDeviceControl instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class ActiveFlowReservationListLink(ListLink):
    """
    SHALL contain a Link to a List of active FlowReservation instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class ActiveProjectionReadingListLink(ListLink):
    """
    SHALL contain a Link to a List of active ProjectionReading instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class ActiveSupplyInterruptionOverrideListLink(ListLink):
    """
    SHALL contain a Link to a List of active SupplyInterruptionOverride
    instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class ActiveTargetReadingListLink(ListLink):
    """
    SHALL contain a Link to a List of active TargetReading instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class ActiveTextMessageListLink(ListLink):
    """
    SHALL contain a Link to a List of active TextMessage instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class ActiveTimeTariffIntervalListLink(ListLink):
    """
    SHALL contain a Link to a List of active TimeTariffInterval instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class AssociatedDerprogramListLink(ListLink):
    """
    SHALL contain a Link to a List of DERPrograms having the DERControl(s) for
    this DER.
    """
    class Meta:
        name = "AssociatedDERProgramListLink"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class BillingPeriodListLink(ListLink):
    """
    SHALL contain a Link to a List of BillingPeriod instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class BillingReading(ReadingBase):
    """Data captured at regular intervals of time.

    Interval data could be captured as incremental data, absolute data,
    or relative data. The source for the data is usually a tariff
    quantity or an engineering quantity. Data is typically captured in
    time-tagged, uniform, fixed-length intervals of 5 min, 10 min, 15
    min, 30 min, or 60 min. However, consumption aggregations can also
    be represented with this class.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    charge: List[Charge] = field(
        default_factory=list,
        metadata={
            "name": "Charge",
            "type": "Element",
        }
    )


@dataclass
class BillingReadingListLink(ListLink):
    """
    SHALL contain a Link to a List of BillingReading instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class BillingReadingSetListLink(ListLink):
    """
    SHALL contain a Link to a List of BillingReadingSet instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class ConsumptionTariffIntervalList(ListType):
    """
    A List element to hold ConsumptionTariffInterval objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    consumption_tariff_interval: List[ConsumptionTariffInterval] = field(
        default_factory=list,
        metadata={
            "name": "ConsumptionTariffInterval",
            "type": "Element",
        }
    )


@dataclass
class ConsumptionTariffIntervalListLink(ListLink):
    """
    SHALL contain a Link to a List of ConsumptionTariffInterval instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class CreditRegister(IdentifiedObject):
    """CreditRegister instances define a credit-modifying transaction.

    Typically this would be a credit-adding transaction, but may be a
    subtracting transaction (perhaps in response to an out-of-band debt
    signal).

    :ivar credit_amount: CreditAmount is the amount of credit being
        added by a particular CreditRegister transaction. Negative
        values indicate that credit is being subtracted.
    :ivar credit_type: CreditType indicates whether the credit
        transaction applies to regular or emergency credit.
    :ivar effective_time: EffectiveTime identifies the time at which the
        credit transaction goes into effect. For credit addition
        transactions, this is typically the moment at which the
        transaction takes place. For credit subtraction transactions,
        (e.g., non-fuel debt recovery transactions initiated from a
        back-haul or ESI) this may be a future time at which credit is
        deducted.
    :ivar token: Token is security data that authenticates the
        legitimacy of the transaction. The details of this token are not
        defined by IEEE 2030.5. How a Prepayment server handles this
        field is left as vendor specific implementation or will be
        defined by one or more other standards.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    credit_amount: Optional[AccountingUnit] = field(
        default=None,
        metadata={
            "name": "creditAmount",
            "type": "Element",
            "required": True,
        }
    )
    credit_type: Optional[int] = field(
        default=None,
        metadata={
            "name": "creditType",
            "type": "Element",
        }
    )
    effective_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "effectiveTime",
            "type": "Element",
            "required": True,
        }
    )
    token: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 32,
        }
    )


@dataclass
class CreditRegisterListLink(ListLink):
    """
    SHALL contain a Link to a List of CreditRegister instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class CustomerAccountListLink(ListLink):
    """
    SHALL contain a Link to a List of CustomerAccount instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class CustomerAgreementListLink(ListLink):
    """
    SHALL contain a Link to a List of CustomerAgreement instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class Deravailability(SubscribableResource):
    """
    Indicates current reserve generation status.

    :ivar availability_duration: Indicates number of seconds the DER
        will be able to deliver active power at the reservePercent
        level.
    :ivar max_charge_duration: Indicates number of seconds the DER will
        be able to receive active power at the reserveChargePercent
        level.
    :ivar reading_time: The timestamp when the DER availability was last
        updated.
    :ivar reserve_charge_percent: Percent of continuous received active
        power (%setMaxChargeRateW) that is estimated to be available in
        reserve.
    :ivar reserve_percent: Percent of continuous delivered active power
        (%setMaxW) that is estimated to be available in reserve.
    :ivar stat_var_avail: Estimated reserve reactive power, in var.
        Represents the lesser of received or delivered reactive power.
    :ivar stat_wavail: Estimated reserve active power, in watts.
    """
    class Meta:
        name = "DERAvailability"
        namespace = "urn:ieee:std:2030.5:ns"

    availability_duration: Optional[int] = field(
        default=None,
        metadata={
            "name": "availabilityDuration",
            "type": "Element",
        }
    )
    max_charge_duration: Optional[int] = field(
        default=None,
        metadata={
            "name": "maxChargeDuration",
            "type": "Element",
        }
    )
    reading_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "readingTime",
            "type": "Element",
            "required": True,
        }
    )
    reserve_charge_percent: Optional[int] = field(
        default=None,
        metadata={
            "name": "reserveChargePercent",
            "type": "Element",
        }
    )
    reserve_percent: Optional[int] = field(
        default=None,
        metadata={
            "name": "reservePercent",
            "type": "Element",
        }
    )
    stat_var_avail: Optional[ReactivePower] = field(
        default=None,
        metadata={
            "name": "statVarAvail",
            "type": "Element",
        }
    )
    stat_wavail: Optional[ActivePower] = field(
        default=None,
        metadata={
            "name": "statWAvail",
            "type": "Element",
        }
    )


@dataclass
class DercontrolBase:
    """
    Distributed Energy Resource (DER) control values.

    :ivar op_mod_connect: Set DER as connected (true) or disconnected
        (false). Used in conjunction with ramp rate when re-connecting.
        Implies galvanic isolation.
    :ivar op_mod_energize: Set DER as energized (true) or de-energized
        (false). Used in conjunction with ramp rate when re-energizing.
    :ivar op_mod_fixed_pfabsorb_w: The opModFixedPFAbsorbW function
        specifies a requested fixed Power Factor (PF) setting for when
        active power is being absorbed. The actual displacement SHALL be
        within the limits established by setMinPFOverExcited and
        setMinPFUnderExcited. If issued simultaneously with other
        reactive power controls (e.g. opModFixedVar) the control
        resulting in least var magnitude SHOULD take precedence.
    :ivar op_mod_fixed_pfinject_w: The opModFixedPFInjectW function
        specifies a requested fixed Power Factor (PF) setting for when
        active power is being injected. The actual displacement SHALL be
        within the limits established by setMinPFOverExcited and
        setMinPFUnderExcited. If issued simultaneously with other
        reactive power controls (e.g. opModFixedVar) the control
        resulting in least var magnitude SHOULD take precedence.
    :ivar op_mod_fixed_var: The opModFixedVar function specifies the
        delivered or received reactive power setpoint.  The context for
        the setpoint value is determined by refType and SHALL be one of
        %setMaxW, %setMaxVar, or %statVarAvail.  If issued
        simultaneously with other reactive power controls (e.g.
        opModFixedPFInjectW) the control resulting in least var
        magnitude SHOULD take precedence.
    :ivar op_mod_fixed_w: The opModFixedW function specifies a requested
        charge or discharge mode setpoint, in %setMaxChargeRateW if
        negative value or %setMaxW or %setMaxDischargeRateW if positive
        value (in hundredths).
    :ivar op_mod_freq_droop: Specifies a frequency-watt operation. This
        operation limits active power generation or consumption when the
        line frequency deviates from nominal by a specified amount.
    :ivar op_mod_freq_watt: Specify DERCurveLink for curveType == 0.
        The Frequency-Watt function limits active power generation or
        consumption when the line frequency deviates from nominal by a
        specified amount. The Frequency-Watt curve is specified as an
        array of Frequency-Watt pairs that are interpolated into a
        piecewise linear function with hysteresis.  The x value of each
        pair specifies a frequency in Hz. The y value specifies a
        corresponding active power output in %setMaxW.
    :ivar op_mod_hfrtmay_trip: Specify DERCurveLink for curveType == 1.
        The High Frequency Ride-Through (HFRT) function is specified by
        one or two duration-frequency curves that define the operating
        region under high frequency conditions. Each HFRT curve is
        specified by an array of duration-frequency pairs that will be
        interpolated into a piecewise linear function that defines an
        operating region. The x value of each pair specifies a duration
        (time at a given frequency in seconds). The y value of each pair
        specifies a frequency, in Hz. This control specifies the "may
        trip" region.
    :ivar op_mod_hfrtmust_trip: Specify DERCurveLink for curveType == 2.
        The High Frequency Ride-Through (HFRT) function is specified by
        a duration-frequency curve that defines the operating region
        under high frequency conditions.  Each HFRT curve is specified
        by an array of duration-frequency pairs that will be
        interpolated into a piecewise linear function that defines an
        operating region.  The x value of each pair specifies a duration
        (time at a given frequency in seconds). The y value of each pair
        specifies a frequency, in Hz. This control specifies the "must
        trip" region.
    :ivar op_mod_hvrtmay_trip: Specify DERCurveLink for curveType == 3.
        The High Voltage Ride-Through (HVRT) function is specified by
        one, two, or three duration-volt curves that define the
        operating region under high voltage conditions. Each HVRT curve
        is specified by an array of duration-volt pairs that will be
        interpolated into a piecewise linear function that defines an
        operating region. The x value of each pair specifies a duration
        (time at a given voltage in seconds). The y value of each pair
        specifies an effective percentage voltage, defined as ((locally
        measured voltage - setVRefOfs / setVRef). This control specifies
        the "may trip" region.
    :ivar op_mod_hvrtmomentary_cessation: Specify DERCurveLink for
        curveType == 4.  The High Voltage Ride-Through (HVRT) function
        is specified by duration-volt curves that define the operating
        region under high voltage conditions.  Each HVRT curve is
        specified by an array of duration-volt pairs that will be
        interpolated into a piecewise linear function that defines an
        operating region.  The x value of each pair specifies a duration
        (time at a given voltage in seconds). The y value of each pair
        specifies an effective percent voltage, defined as ((locally
        measured voltage - setVRefOfs) / setVRef). This control
        specifies the "momentary cessation" region.
    :ivar op_mod_hvrtmust_trip: Specify DERCurveLink for curveType == 5.
        The High Voltage Ride-Through (HVRT) function is specified by
        duration-volt curves that define the operating region under high
        voltage conditions.  Each HVRT curve is specified by an array of
        duration-volt pairs that will be interpolated into a piecewise
        linear function that defines an operating region.  The x value
        of each pair specifies a duration (time at a given voltage in
        seconds). The y value of each pair specifies an effective
        percent voltage, defined as ((locally measured voltage -
        setVRefOfs) / setVRef). This control specifies the "must trip"
        region.
    :ivar op_mod_lfrtmay_trip: Specify DERCurveLink for curveType == 6.
        The Low Frequency Ride-Through (LFRT) function is specified by
        one or two duration-frequency curves that define the operating
        region under low frequency conditions. Each LFRT curve is
        specified by an array of duration-frequency pairs that will be
        interpolated into a piecewise linear function that defines an
        operating region. The x value of each pair specifies a duration
        (time at a given frequency in seconds). The y value of each pair
        specifies a frequency, in Hz. This control specifies the "may
        trip" region.
    :ivar op_mod_lfrtmust_trip: Specify DERCurveLink for curveType == 7.
        The Low Frequency Ride-Through (LFRT) function is specified by a
        duration-frequency curve that defines the operating region under
        low frequency conditions.  Each LFRT curve is specified by an
        array of duration-frequency pairs that will be interpolated into
        a piecewise linear function that defines an operating region.
        The x value of each pair specifies a duration (time at a given
        frequency in seconds). The y value of each pair specifies a
        frequency, in Hz. This control specifies the "must trip" region.
    :ivar op_mod_lvrtmay_trip: Specify DERCurveLink for curveType == 8.
        The Low Voltage Ride-Through (LVRT) function is specified by
        one, two, or three duration-volt curves that define the
        operating region under low voltage conditions. Each LVRT curve
        is specified by an array of duration-volt pairs that will be
        interpolated into a piecewise linear function that defines an
        operating region. The x value of each pair specifies a duration
        (time at a given voltage in seconds). The y value of each pair
        specifies an effective percent voltage, defined as ((locally
        measured voltage - setVRefOfs) / setVRef). This control
        specifies the "may trip" region.
    :ivar op_mod_lvrtmomentary_cessation: Specify DERCurveLink for
        curveType == 9.  The Low Voltage Ride-Through (LVRT) function is
        specified by duration-volt curves that define the operating
        region under low voltage conditions.  Each LVRT curve is
        specified by an array of duration-volt pairs that will be
        interpolated into a piecewise linear function that defines an
        operating region.  The x value of each pair specifies a duration
        (time at a given voltage in seconds). The y value of each pair
        specifies an effective percent voltage, defined as ((locally
        measured voltage - setVRefOfs) / setVRef). This control
        specifies the "momentary cessation" region.
    :ivar op_mod_lvrtmust_trip: Specify DERCurveLink for curveType ==
        10.  The Low Voltage Ride-Through (LVRT) function is specified
        by duration-volt curves that define the operating region under
        low voltage conditions.  Each LVRT curve is specified by an
        array of duration-volt pairs that will be interpolated into a
        piecewise linear function that defines an operating region.  The
        x value of each pair specifies a duration (time at a given
        voltage in seconds). The y value of each pair specifies an
        effective percent voltage, defined as ((locally measured voltage
        - setVRefOfs) / setVRef). This control specifies the "must trip"
        region.
    :ivar op_mod_max_lim_w: The opModMaxLimW function sets the maximum
        active power generation level at the electrical coupling point
        as a percentage of set capacity (%setMaxW, in hundredths). This
        limitation may be met e.g. by reducing PV output or by using
        excess PV output to charge associated storage.
    :ivar op_mod_target_var: Target reactive power, in var. This control
        is likely to be more useful for aggregators, as individual DERs
        may not be able to maintain a target setting.
    :ivar op_mod_target_w: Target output power, in Watts. This control
        is likely to be more useful for aggregators, as individual DERs
        may not be able to maintain a target setting.
    :ivar op_mod_volt_var: Specify DERCurveLink for curveType == 11.
        The static volt-var function provides over- or under-excited var
        compensation as a function of measured voltage. The volt-var
        curve is specified as an array of volt-var pairs that are
        interpolated into a piecewise linear function with hysteresis.
        The x value of each pair specifies an effective percent voltage,
        defined as ((locally measured voltage - setVRefOfs) / setVRef)
        and SHOULD support a domain of at least 0 - 135. If VRef is
        present in DERCurve, then the x value of each pair is
        additionally multiplied by (VRef / 10000). The y value specifies
        a target var output interpreted as a signed percentage (-100 to
        100). The meaning of the y value is determined by yRefType and
        must be one of %setMaxW, %setMaxVar, or %statVarAvail.
    :ivar op_mod_volt_watt: Specify DERCurveLink for curveType == 12.
        The Volt-Watt reduces active power output as a function of
        measured voltage. The Volt-Watt curve is specified as an array
        of Volt-Watt pairs that are interpolated into a piecewise linear
        function with hysteresis. The x value of each pair specifies an
        effective percent voltage, defined as ((locally measured voltage
        - setVRefOfs) / setVRef) and SHOULD support a domain of at least
        0 - 135. The y value specifies an active power output
        interpreted as a percentage (0 - 100). The meaning of the y
        value is determined by yRefType and must be one of %setMaxW or
        %statWAvail.
    :ivar op_mod_watt_pf: Specify DERCurveLink for curveType == 13.  The
        Watt-PF function varies Power Factor (PF) as a function of
        delivered active power. The Watt-PF curve is specified as an
        array of Watt-PF coordinates that are interpolated into a
        piecewise linear function with hysteresis.  The x value of each
        pair specifies a watt setting in %setMaxW, (0 - 100). The PF
        output setting is a signed displacement in y value (PF sign
        SHALL be interpreted according to the EEI convention, where
        unity PF is considered unsigned). These settings are not
        expected to be updated very often during the life of the
        installation, therefore only a single curve is required.  If
        issued simultaneously with other reactive power controls (e.g.
        opModFixedPFInjectW) the control resulting in least var
        magnitude SHOULD take precedence.
    :ivar op_mod_watt_var: Specify DERCurveLink for curveType == 14. The
        Watt-Var function varies vars as a function of delivered active
        power. The Watt-Var curve is specified as an array of Watt-Var
        pairs that are interpolated into a piecewise linear function
        with hysteresis. The x value of each pair specifies a watt
        setting in %setMaxW, (0-100). The y value specifies a target var
        output interpreted as a signed percentage (-100 to 100). The
        meaning of the y value is determined by yRefType and must be one
        of %setMaxW, %setMaxVar, or %statVarAvail.
    :ivar ramp_tms: Requested ramp time, in hundredths of a second, for
        the device to transition from the current DERControl  mode
        setting(s) to the new mode setting(s). If absent, use default
        ramp rate (setGradW).  Resolution is 1/100 sec.
    """
    class Meta:
        name = "DERControlBase"
        namespace = "urn:ieee:std:2030.5:ns"

    op_mod_connect: Optional[bool] = field(
        default=None,
        metadata={
            "name": "opModConnect",
            "type": "Element",
        }
    )
    op_mod_energize: Optional[bool] = field(
        default=None,
        metadata={
            "name": "opModEnergize",
            "type": "Element",
        }
    )
    op_mod_fixed_pfabsorb_w: Optional[PowerFactorWithExcitation] = field(
        default=None,
        metadata={
            "name": "opModFixedPFAbsorbW",
            "type": "Element",
        }
    )
    op_mod_fixed_pfinject_w: Optional[PowerFactorWithExcitation] = field(
        default=None,
        metadata={
            "name": "opModFixedPFInjectW",
            "type": "Element",
        }
    )
    op_mod_fixed_var: Optional[FixedVar] = field(
        default=None,
        metadata={
            "name": "opModFixedVar",
            "type": "Element",
        }
    )
    op_mod_fixed_w: Optional[int] = field(
        default=None,
        metadata={
            "name": "opModFixedW",
            "type": "Element",
        }
    )
    op_mod_freq_droop: Optional[FreqDroopType] = field(
        default=None,
        metadata={
            "name": "opModFreqDroop",
            "type": "Element",
        }
    )
    op_mod_freq_watt: Optional[DercurveLink] = field(
        default=None,
        metadata={
            "name": "opModFreqWatt",
            "type": "Element",
        }
    )
    op_mod_hfrtmay_trip: Optional[DercurveLink] = field(
        default=None,
        metadata={
            "name": "opModHFRTMayTrip",
            "type": "Element",
        }
    )
    op_mod_hfrtmust_trip: Optional[DercurveLink] = field(
        default=None,
        metadata={
            "name": "opModHFRTMustTrip",
            "type": "Element",
        }
    )
    op_mod_hvrtmay_trip: Optional[DercurveLink] = field(
        default=None,
        metadata={
            "name": "opModHVRTMayTrip",
            "type": "Element",
        }
    )
    op_mod_hvrtmomentary_cessation: Optional[DercurveLink] = field(
        default=None,
        metadata={
            "name": "opModHVRTMomentaryCessation",
            "type": "Element",
        }
    )
    op_mod_hvrtmust_trip: Optional[DercurveLink] = field(
        default=None,
        metadata={
            "name": "opModHVRTMustTrip",
            "type": "Element",
        }
    )
    op_mod_lfrtmay_trip: Optional[DercurveLink] = field(
        default=None,
        metadata={
            "name": "opModLFRTMayTrip",
            "type": "Element",
        }
    )
    op_mod_lfrtmust_trip: Optional[DercurveLink] = field(
        default=None,
        metadata={
            "name": "opModLFRTMustTrip",
            "type": "Element",
        }
    )
    op_mod_lvrtmay_trip: Optional[DercurveLink] = field(
        default=None,
        metadata={
            "name": "opModLVRTMayTrip",
            "type": "Element",
        }
    )
    op_mod_lvrtmomentary_cessation: Optional[DercurveLink] = field(
        default=None,
        metadata={
            "name": "opModLVRTMomentaryCessation",
            "type": "Element",
        }
    )
    op_mod_lvrtmust_trip: Optional[DercurveLink] = field(
        default=None,
        metadata={
            "name": "opModLVRTMustTrip",
            "type": "Element",
        }
    )
    op_mod_max_lim_w: Optional[int] = field(
        default=None,
        metadata={
            "name": "opModMaxLimW",
            "type": "Element",
        }
    )
    op_mod_target_var: Optional[ReactivePower] = field(
        default=None,
        metadata={
            "name": "opModTargetVar",
            "type": "Element",
        }
    )
    op_mod_target_w: Optional[ActivePower] = field(
        default=None,
        metadata={
            "name": "opModTargetW",
            "type": "Element",
        }
    )
    op_mod_volt_var: Optional[DercurveLink] = field(
        default=None,
        metadata={
            "name": "opModVoltVar",
            "type": "Element",
        }
    )
    op_mod_volt_watt: Optional[DercurveLink] = field(
        default=None,
        metadata={
            "name": "opModVoltWatt",
            "type": "Element",
        }
    )
    op_mod_watt_pf: Optional[DercurveLink] = field(
        default=None,
        metadata={
            "name": "opModWattPF",
            "type": "Element",
        }
    )
    op_mod_watt_var: Optional[DercurveLink] = field(
        default=None,
        metadata={
            "name": "opModWattVar",
            "type": "Element",
        }
    )
    ramp_tms: Optional[int] = field(
        default=None,
        metadata={
            "name": "rampTms",
            "type": "Element",
        }
    )


@dataclass
class DercontrolListLink(ListLink):
    """
    SHALL contain a Link to a List of DERControl instances.
    """
    class Meta:
        name = "DERControlListLink"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DercontrolResponse(Response):
    """
    A response to a DERControl.
    """
    class Meta:
        name = "DERControlResponse"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class Dercurve(IdentifiedObject):
    """DER related curves such as Volt-Var mode curves.

    Relationship between an independent variable (X-axis) and a
    dependent variable (Y-axis).

    :ivar autonomous_vref_enable: If the curveType is opModVoltVar, then
        this field MAY be present. If the curveType is not opModVoltVar,
        then this field SHALL NOT be present. Enable/disable autonomous
        vRef adjustment. When enabled, the Volt-Var curve characteristic
        SHALL be adjusted autonomously as vRef changes and
        autonomousVRefTimeConstant SHALL be present. If a DER is able to
        support Volt-Var mode but is unable to support autonomous vRef
        adjustment, then the DER SHALL execute the curve without
        autonomous vRef adjustment. If not specified, then the value is
        false.
    :ivar autonomous_vref_time_constant: If the curveType is
        opModVoltVar, then this field MAY be present. If the curveType
        is not opModVoltVar, then this field SHALL NOT be present.
        Adjustment range for vRef time constant, in hundredths of a
        second.
    :ivar creation_time: The time at which the object was created.
    :ivar curve_data:
    :ivar curve_type: Specifies the associated curve-based control mode.
    :ivar open_loop_tms: Open loop response time, the time to ramp up to
        90% of the new target in response to the change in voltage, in
        hundredths of a second. Resolution is 1/100 sec. A value of 0 is
        used to mean no limit. When not present, the device SHOULD
        follow its default behavior.
    :ivar ramp_dec_tms: Decreasing ramp rate, interpreted as a
        percentage change in output capability limit per second (e.g.
        %setMaxW / sec).  Resolution is in hundredths of a
        percent/second. A value of 0 means there is no limit. If absent,
        ramp rate defaults to setGradW.
    :ivar ramp_inc_tms: Increasing ramp rate, interpreted as a
        percentage change in output capability limit per second (e.g.
        %setMaxW / sec).  Resolution is in hundredths of a
        percent/second. A value of 0 means there is no limit. If absent,
        ramp rate defaults to rampDecTms.
    :ivar ramp_pt1_tms: The configuration parameter for a low-pass
        filter, PT1 is a time, in hundredths of a second, in which the
        filter will settle to 95% of a step change in the input value.
        Resolution is 1/100 sec.
    :ivar v_ref: If the curveType is opModVoltVar, then this field MAY
        be present. If the curveType is not opModVoltVar, then this
        field SHALL NOT be present. The nominal AC voltage (RMS)
        adjustment to the voltage curve points for Volt-Var curves.
    :ivar x_multiplier: Exponent for X-axis value.
    :ivar y_multiplier: Exponent for Y-axis value.
    :ivar y_ref_type: The Y-axis units context.
    """
    class Meta:
        name = "DERCurve"
        namespace = "urn:ieee:std:2030.5:ns"

    autonomous_vref_enable: Optional[bool] = field(
        default=None,
        metadata={
            "name": "autonomousVRefEnable",
            "type": "Element",
        }
    )
    autonomous_vref_time_constant: Optional[int] = field(
        default=None,
        metadata={
            "name": "autonomousVRefTimeConstant",
            "type": "Element",
        }
    )
    creation_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "creationTime",
            "type": "Element",
            "required": True,
        }
    )
    curve_data: List[CurveData] = field(
        default_factory=list,
        metadata={
            "name": "CurveData",
            "type": "Element",
            "min_occurs": 1,
            "max_occurs": 10,
        }
    )
    curve_type: Optional[int] = field(
        default=None,
        metadata={
            "name": "curveType",
            "type": "Element",
            "required": True,
        }
    )
    open_loop_tms: Optional[int] = field(
        default=None,
        metadata={
            "name": "openLoopTms",
            "type": "Element",
        }
    )
    ramp_dec_tms: Optional[int] = field(
        default=None,
        metadata={
            "name": "rampDecTms",
            "type": "Element",
        }
    )
    ramp_inc_tms: Optional[int] = field(
        default=None,
        metadata={
            "name": "rampIncTms",
            "type": "Element",
        }
    )
    ramp_pt1_tms: Optional[int] = field(
        default=None,
        metadata={
            "name": "rampPT1Tms",
            "type": "Element",
        }
    )
    v_ref: Optional[int] = field(
        default=None,
        metadata={
            "name": "vRef",
            "type": "Element",
        }
    )
    x_multiplier: Optional[int] = field(
        default=None,
        metadata={
            "name": "xMultiplier",
            "type": "Element",
            "required": True,
        }
    )
    y_multiplier: Optional[int] = field(
        default=None,
        metadata={
            "name": "yMultiplier",
            "type": "Element",
            "required": True,
        }
    )
    y_ref_type: Optional[int] = field(
        default=None,
        metadata={
            "name": "yRefType",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class DercurveListLink(ListLink):
    """
    SHALL contain a Link to a List of DERCurve instances.
    """
    class Meta:
        name = "DERCurveListLink"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DerlistLink(ListLink):
    """
    SHALL contain a Link to a List of DER instances.
    """
    class Meta:
        name = "DERListLink"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DerprogramListLink(ListLink):
    """
    SHALL contain a Link to a List of DERProgram instances.
    """
    class Meta:
        name = "DERProgramListLink"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class Dersettings(SubscribableResource):
    """
    Distributed energy resource settings.

    :ivar modes_enabled: Bitmap indicating the DER Controls enabled on
        the device. See DERControlType for values. If a control is
        supported (see DERCapability::modesSupported), but not enabled,
        the control will not be executed if encountered.
    :ivar set_esdelay: Enter service delay, in hundredths of a second.
    :ivar set_eshigh_freq: Enter service frequency high. Specified in
        hundredths of Hz.
    :ivar set_eshigh_volt: Enter service voltage high. Specified as an
        effective percent voltage, defined as (100% * (locally measured
        voltage - setVRefOfs) / setVRef), in hundredths of a percent.
    :ivar set_eslow_freq: Enter service frequency low. Specified in
        hundredths of Hz.
    :ivar set_eslow_volt: Enter service voltage low. Specified as an
        effective percent voltage, defined as (100% * (locally measured
        voltage - setVRefOfs) / setVRef), in hundredths of a percent.
    :ivar set_esramp_tms: Enter service ramp time, in hundredths of a
        second.
    :ivar set_esrandom_delay: Enter service randomized delay, in
        hundredths of a second.
    :ivar set_grad_w: Set default rate of change (ramp rate) of active
        power output due to command or internal action, defined in
        %setWMax / second.  Resolution is in hundredths of a
        percent/second. A value of 0 means there is no limit.
        Interpreted as a percentage change in output capability limit
        per second when used as a default ramp rate.
    :ivar set_max_a: AC current maximum. Maximum AC current in RMS
        Amperes.
    :ivar set_max_ah: Maximum usable energy storage capacity of the DER,
        in AmpHours. Note: this may be different from physical
        capability.
    :ivar set_max_charge_rate_va: Apparent power charge maximum. Maximum
        apparent power the DER can absorb from the grid in Volt-Amperes.
        May differ from the apparent power maximum (setMaxVA).
    :ivar set_max_charge_rate_w: Maximum rate of energy transfer
        received by the storage device, in Watts. Defaults to
        rtgMaxChargeRateW.
    :ivar set_max_discharge_rate_va: Apparent power discharge maximum.
        Maximum apparent power the DER can deliver to the grid in Volt-
        Amperes. May differ from the apparent power maximum (setMaxVA).
    :ivar set_max_discharge_rate_w: Maximum rate of energy transfer
        delivered by the storage device, in Watts. Defaults to
        rtgMaxDischargeRateW.
    :ivar set_max_v: AC voltage maximum setting.
    :ivar set_max_va: Set limit for maximum apparent power capability of
        the DER (in VA). Defaults to rtgMaxVA.
    :ivar set_max_var: Set limit for maximum reactive power delivered by
        the DER (in var). SHALL be a positive value &amp;lt;= rtgMaxVar
        (default).
    :ivar set_max_var_neg: Set limit for maximum reactive power received
        by the DER (in var). If present, SHALL be a negative value
        &amp;gt;= rtgMaxVarNeg (default). If absent, defaults to
        negative setMaxVar.
    :ivar set_max_w: Set limit for maximum active power capability of
        the DER (in W). Defaults to rtgMaxW.
    :ivar set_max_wh: Maximum energy storage capacity of the DER, in
        WattHours. Note: this may be different from physical capability.
    :ivar set_min_pfover_excited: Set minimum Power Factor displacement
        limit of the DER when injecting reactive power (over-excited);
        SHALL be a positive value between 0.0 (typically &amp;gt; 0.7)
        and 1.0.  SHALL be &amp;gt;= rtgMinPFOverExcited (default).
    :ivar set_min_pfunder_excited: Set minimum Power Factor displacement
        limit of the DER when absorbing reactive power (under-excited);
        SHALL be a positive value between 0.0 (typically &amp;gt; 0.7)
        and 0.9999.  If present, SHALL be &amp;gt;= rtgMinPFUnderExcited
        (default).  If absent, defaults to setMinPFOverExcited.
    :ivar set_min_v: AC voltage minimum setting.
    :ivar set_soft_grad_w: Set soft-start rate of change (soft-start
        ramp rate) of active power output due to command or internal
        action, defined in %setWMax / second.  Resolution is in
        hundredths of a percent/second. A value of 0 means there is no
        limit. Interpreted as a percentage change in output capability
        limit per second when used as a ramp rate.
    :ivar set_vnom: AC voltage nominal setting.
    :ivar set_vref: The nominal AC voltage (RMS) at the utility's point
        of common coupling.
    :ivar set_vref_ofs: The nominal AC voltage (RMS) offset between the
        DER's electrical connection point and the utility's point of
        common coupling.
    :ivar updated_time: Specifies the time at which the DER information
        was last updated.
    """
    class Meta:
        name = "DERSettings"
        namespace = "urn:ieee:std:2030.5:ns"

    modes_enabled: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "modesEnabled",
            "type": "Element",
            "max_length": 4,
            "format": "base16",
        }
    )
    set_esdelay: Optional[int] = field(
        default=None,
        metadata={
            "name": "setESDelay",
            "type": "Element",
        }
    )
    set_eshigh_freq: Optional[int] = field(
        default=None,
        metadata={
            "name": "setESHighFreq",
            "type": "Element",
        }
    )
    set_eshigh_volt: Optional[int] = field(
        default=None,
        metadata={
            "name": "setESHighVolt",
            "type": "Element",
        }
    )
    set_eslow_freq: Optional[int] = field(
        default=None,
        metadata={
            "name": "setESLowFreq",
            "type": "Element",
        }
    )
    set_eslow_volt: Optional[int] = field(
        default=None,
        metadata={
            "name": "setESLowVolt",
            "type": "Element",
        }
    )
    set_esramp_tms: Optional[int] = field(
        default=None,
        metadata={
            "name": "setESRampTms",
            "type": "Element",
        }
    )
    set_esrandom_delay: Optional[int] = field(
        default=None,
        metadata={
            "name": "setESRandomDelay",
            "type": "Element",
        }
    )
    set_grad_w: Optional[int] = field(
        default=None,
        metadata={
            "name": "setGradW",
            "type": "Element",
            "required": True,
        }
    )
    set_max_a: Optional[CurrentRms] = field(
        default=None,
        metadata={
            "name": "setMaxA",
            "type": "Element",
        }
    )
    set_max_ah: Optional[AmpereHour] = field(
        default=None,
        metadata={
            "name": "setMaxAh",
            "type": "Element",
        }
    )
    set_max_charge_rate_va: Optional[ApparentPower] = field(
        default=None,
        metadata={
            "name": "setMaxChargeRateVA",
            "type": "Element",
        }
    )
    set_max_charge_rate_w: Optional[ActivePower] = field(
        default=None,
        metadata={
            "name": "setMaxChargeRateW",
            "type": "Element",
        }
    )
    set_max_discharge_rate_va: Optional[ApparentPower] = field(
        default=None,
        metadata={
            "name": "setMaxDischargeRateVA",
            "type": "Element",
        }
    )
    set_max_discharge_rate_w: Optional[ActivePower] = field(
        default=None,
        metadata={
            "name": "setMaxDischargeRateW",
            "type": "Element",
        }
    )
    set_max_v: Optional[VoltageRms] = field(
        default=None,
        metadata={
            "name": "setMaxV",
            "type": "Element",
        }
    )
    set_max_va: Optional[ApparentPower] = field(
        default=None,
        metadata={
            "name": "setMaxVA",
            "type": "Element",
        }
    )
    set_max_var: Optional[ReactivePower] = field(
        default=None,
        metadata={
            "name": "setMaxVar",
            "type": "Element",
        }
    )
    set_max_var_neg: Optional[ReactivePower] = field(
        default=None,
        metadata={
            "name": "setMaxVarNeg",
            "type": "Element",
        }
    )
    set_max_w: Optional[ActivePower] = field(
        default=None,
        metadata={
            "name": "setMaxW",
            "type": "Element",
            "required": True,
        }
    )
    set_max_wh: Optional[WattHour] = field(
        default=None,
        metadata={
            "name": "setMaxWh",
            "type": "Element",
        }
    )
    set_min_pfover_excited: Optional[PowerFactor] = field(
        default=None,
        metadata={
            "name": "setMinPFOverExcited",
            "type": "Element",
        }
    )
    set_min_pfunder_excited: Optional[PowerFactor] = field(
        default=None,
        metadata={
            "name": "setMinPFUnderExcited",
            "type": "Element",
        }
    )
    set_min_v: Optional[VoltageRms] = field(
        default=None,
        metadata={
            "name": "setMinV",
            "type": "Element",
        }
    )
    set_soft_grad_w: Optional[int] = field(
        default=None,
        metadata={
            "name": "setSoftGradW",
            "type": "Element",
        }
    )
    set_vnom: Optional[VoltageRms] = field(
        default=None,
        metadata={
            "name": "setVNom",
            "type": "Element",
        }
    )
    set_vref: Optional[VoltageRms] = field(
        default=None,
        metadata={
            "name": "setVRef",
            "type": "Element",
        }
    )
    set_vref_ofs: Optional[VoltageRms] = field(
        default=None,
        metadata={
            "name": "setVRefOfs",
            "type": "Element",
        }
    )
    updated_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "updatedTime",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class Derstatus(SubscribableResource):
    """
    DER status information.

    :ivar alarm_status: Bitmap indicating the status of DER alarms (see
        DER LogEvents for more details). 0 - DER_FAULT_OVER_CURRENT 1 -
        DER_FAULT_OVER_VOLTAGE 2 - DER_FAULT_UNDER_VOLTAGE 3 -
        DER_FAULT_OVER_FREQUENCY 4 - DER_FAULT_UNDER_FREQUENCY 5 -
        DER_FAULT_VOLTAGE_IMBALANCE 6 - DER_FAULT_CURRENT_IMBALANCE 7 -
        DER_FAULT_EMERGENCY_LOCAL 8 - DER_FAULT_EMERGENCY_REMOTE 9 -
        DER_FAULT_LOW_POWER_INPUT 10 - DER_FAULT_PHASE_ROTATION 11-31 -
        Reserved
    :ivar gen_connect_status: Connect/status value for generator DER.
        See ConnectStatusType for values.
    :ivar inverter_status: DER InverterStatus/value. See
        InverterStatusType for values.
    :ivar local_control_mode_status: The local control mode status. See
        LocalControlModeStatusType for values.
    :ivar manufacturer_status: Manufacturer status code.
    :ivar operational_mode_status: Operational mode currently in use.
        See OperationalModeStatusType for values.
    :ivar reading_time: The timestamp when the current status was last
        updated.
    :ivar state_of_charge_status: State of charge status. See
        StateOfChargeStatusType for values.
    :ivar storage_mode_status: Storage mode status. See
        StorageModeStatusType for values.
    :ivar stor_connect_status: Connect/status value for storage DER. See
        ConnectStatusType for values.
    """
    class Meta:
        name = "DERStatus"
        namespace = "urn:ieee:std:2030.5:ns"

    alarm_status: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "alarmStatus",
            "type": "Element",
            "max_length": 4,
            "format": "base16",
        }
    )
    gen_connect_status: Optional[ConnectStatusType] = field(
        default=None,
        metadata={
            "name": "genConnectStatus",
            "type": "Element",
        }
    )
    inverter_status: Optional[InverterStatusType] = field(
        default=None,
        metadata={
            "name": "inverterStatus",
            "type": "Element",
        }
    )
    local_control_mode_status: Optional[LocalControlModeStatusType] = field(
        default=None,
        metadata={
            "name": "localControlModeStatus",
            "type": "Element",
        }
    )
    manufacturer_status: Optional[ManufacturerStatusType] = field(
        default=None,
        metadata={
            "name": "manufacturerStatus",
            "type": "Element",
        }
    )
    operational_mode_status: Optional[OperationalModeStatusType] = field(
        default=None,
        metadata={
            "name": "operationalModeStatus",
            "type": "Element",
        }
    )
    reading_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "readingTime",
            "type": "Element",
            "required": True,
        }
    )
    state_of_charge_status: Optional[StateOfChargeStatusType] = field(
        default=None,
        metadata={
            "name": "stateOfChargeStatus",
            "type": "Element",
        }
    )
    storage_mode_status: Optional[StorageModeStatusType] = field(
        default=None,
        metadata={
            "name": "storageModeStatus",
            "type": "Element",
        }
    )
    stor_connect_status: Optional[ConnectStatusType] = field(
        default=None,
        metadata={
            "name": "storConnectStatus",
            "type": "Element",
        }
    )


@dataclass
class DemandResponseProgramListLink(ListLink):
    """
    SHALL contain a Link to a List of DemandResponseProgram instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DeviceStatus(Resource):
    """
    Status of device.

    :ivar changed_time: The time at which the reported values were
        recorded.
    :ivar on_count: The number of times that the device has been turned
        on: Count of "device on" times, since the last time the counter
        was reset
    :ivar op_state: Device operational state: 0 - Not applicable /
        Unknown 1 - Not operating 2 - Operating 3 - Starting up 4 -
        Shutting down 5 - At disconnect level 6 - kW ramping 7 - kVar
        ramping
    :ivar op_time: Total time device has operated: re-settable:
        Accumulated time in seconds since the last time the counter was
        reset.
    :ivar temperature:
    :ivar time_link:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    changed_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "changedTime",
            "type": "Element",
            "required": True,
        }
    )
    on_count: Optional[int] = field(
        default=None,
        metadata={
            "name": "onCount",
            "type": "Element",
        }
    )
    op_state: Optional[int] = field(
        default=None,
        metadata={
            "name": "opState",
            "type": "Element",
        }
    )
    op_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "opTime",
            "type": "Element",
        }
    )
    temperature: List[Temperature] = field(
        default_factory=list,
        metadata={
            "name": "Temperature",
            "type": "Element",
        }
    )
    time_link: Optional[TimeLink] = field(
        default=None,
        metadata={
            "name": "TimeLink",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class DrResponse(Response):
    """
    A response to a Demand Response Load Control (EndDeviceControl) message.

    :ivar appliance_load_reduction:
    :ivar applied_target_reduction:
    :ivar duty_cycle:
    :ivar offset:
    :ivar override_duration: Indicates the amount of time, in seconds,
        that the client partially opts-out during the demand response
        event. When overriding within the allowed override duration, the
        client SHALL send a partial opt-out (Response status code 8) for
        partial opt-out upon completion, with the total time the event
        was overridden (this attribute) populated. The client SHALL send
        a no participation status response (status type 10) if the user
        partially opts-out for longer than
        EndDeviceControl.overrideDuration.
    :ivar set_point:
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    appliance_load_reduction: Optional[ApplianceLoadReduction] = field(
        default=None,
        metadata={
            "name": "ApplianceLoadReduction",
            "type": "Element",
        }
    )
    applied_target_reduction: Optional[AppliedTargetReduction] = field(
        default=None,
        metadata={
            "name": "AppliedTargetReduction",
            "type": "Element",
        }
    )
    duty_cycle: Optional[DutyCycle] = field(
        default=None,
        metadata={
            "name": "DutyCycle",
            "type": "Element",
        }
    )
    offset: Optional[Offset] = field(
        default=None,
        metadata={
            "name": "Offset",
            "type": "Element",
        }
    )
    override_duration: Optional[int] = field(
        default=None,
        metadata={
            "name": "overrideDuration",
            "type": "Element",
        }
    )
    set_point: Optional[SetPoint] = field(
        default=None,
        metadata={
            "name": "SetPoint",
            "type": "Element",
        }
    )


@dataclass
class EndDeviceControlListLink(ListLink):
    """
    SHALL contain a Link to a List of EndDeviceControl instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class EndDeviceListLink(ListLink):
    """
    SHALL contain a Link to a List of EndDevice instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class FileList(ListType):
    """
    A List element to hold File objects.

    :ivar file:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    file: List[File] = field(
        default_factory=list,
        metadata={
            "name": "File",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class FileListLink(ListLink):
    """
    SHALL contain a Link to a List of File instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class FileStatus(Resource):
    """
    This object provides status of device file load and activation operations.

    :ivar activate_time: Date/time at which this File, referred to by
        FileLink, will be activated. Omission of or presence and value
        of this element MUST exactly match omission or presence and
        value of the activateTime element from the File resource.
    :ivar file_link:
    :ivar load_percent: This element MUST be set to the percentage of
        the file, indicated by FileLink, that was loaded during the
        latest load attempt. This value MUST be reset to 0 each time a
        load attempt is started for the File indicated by FileLink. This
        value MUST be increased when an LD receives HTTP response
        containing file content. This value MUST be set to 100 when the
        full content of the file has been received by the LD
    :ivar next_request_attempt: This element MUST be set to the time at
        which the LD will issue its next GET request for file content
        from the File indicated by FileLink
    :ivar request503_count: This value MUST be reset to 0 when FileLink
        is first pointed at a new File. This value MUST be incremented
        each time an LD receives a 503 error from the FS.
    :ivar request_fail_count: This value MUST be reset to 0 when
        FileLink is first pointed at a new File. This value MUST be
        incremented each time a GET request for file content failed. 503
        errors MUST be excluded from this counter.
    :ivar status: Current loading status of the file indicated by
        FileLink. This element MUST be set to one of the following
        values: 0 - No load operation in progress 1 - File load in
        progress (first request for file content has been issued by LD)
        2 - File load failed 3 - File loaded successfully (full content
        of file has been received by the LD), signature verification in
        progress 4 - File signature verification failed 5 - File
        signature verified, waiting to activate file. 6 - File
        activation failed 7 - File activation in progress 8 - File
        activated successfully (this state may not be reached/persisted
        through an image activation) 9-255 - Reserved for future use.
    :ivar status_time: This element MUST be set to the time at which
        file status transitioned to the value indicated in the status
        element.
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    activate_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "activateTime",
            "type": "Element",
        }
    )
    file_link: Optional[FileLink] = field(
        default=None,
        metadata={
            "name": "FileLink",
            "type": "Element",
        }
    )
    load_percent: Optional[int] = field(
        default=None,
        metadata={
            "name": "loadPercent",
            "type": "Element",
            "required": True,
        }
    )
    next_request_attempt: Optional[int] = field(
        default=None,
        metadata={
            "name": "nextRequestAttempt",
            "type": "Element",
            "required": True,
        }
    )
    request503_count: Optional[int] = field(
        default=None,
        metadata={
            "name": "request503Count",
            "type": "Element",
            "required": True,
        }
    )
    request_fail_count: Optional[int] = field(
        default=None,
        metadata={
            "name": "requestFailCount",
            "type": "Element",
            "required": True,
        }
    )
    status: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    status_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "statusTime",
            "type": "Element",
            "required": True,
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class FlowReservationRequest(IdentifiedObject):
    """Used to request flow transactions.

    Client EndDevices submit a request for charging or discharging from
    the server. The server creates an associated FlowReservationResponse
    containing the charging parameters and interval to provide a lower
    aggregated demand at the premises, or within a larger part of the
    distribution system.

    :ivar creation_time: The time at which the request was created.
    :ivar duration_requested: A value that is calculated by the storage
        device that defines the minimum duration, in seconds, that it
        will take to complete the actual flow transaction, including any
        ramp times and conditioning times, if applicable.
    :ivar energy_requested: Indicates the total amount of energy, in
        Watt-Hours, requested to be transferred between the storage
        device and the electric power system. Positive values indicate
        charging and negative values indicate discharging. This sign
        convention is different than for the DER function where
        discharging is positive.  Note that the energyRequestNow
        attribute in the PowerStatus Object must always represent a
        charging solution and it is not allowed to have a negative
        value.
    :ivar interval_requested: The time window during which the flow
        reservation is needed. For example, if an electric vehicle is
        set with a 7:00 AM time charge is needed, and price drops to the
        lowest tier at 11:00 PM, then this window would likely be from
        11:00 PM until 7:00 AM.
    :ivar power_requested: Indicates the sustained level of power, in
        Watts, that is requested. For charging this is calculated by the
        storage device and it represents the charging system capability
        (which for an electric vehicle must also account for any power
        limitations due to the EVSE control pilot). For discharging, a
        lower value than the inverter capability can be used as a
        target.
    :ivar request_status:
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    creation_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "creationTime",
            "type": "Element",
            "required": True,
        }
    )
    duration_requested: Optional[int] = field(
        default=None,
        metadata={
            "name": "durationRequested",
            "type": "Element",
        }
    )
    energy_requested: Optional[SignedRealEnergy] = field(
        default=None,
        metadata={
            "name": "energyRequested",
            "type": "Element",
            "required": True,
        }
    )
    interval_requested: Optional[DateTimeInterval] = field(
        default=None,
        metadata={
            "name": "intervalRequested",
            "type": "Element",
            "required": True,
        }
    )
    power_requested: Optional[ActivePower] = field(
        default=None,
        metadata={
            "name": "powerRequested",
            "type": "Element",
            "required": True,
        }
    )
    request_status: Optional[RequestStatus] = field(
        default=None,
        metadata={
            "name": "RequestStatus",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class FlowReservationRequestListLink(ListLink):
    """
    SHALL contain a Link to a List of FlowReservationRequest instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class FlowReservationResponseListLink(ListLink):
    """
    SHALL contain a Link to a List of FlowReservationResponse instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class FlowReservationResponseResponse(Response):
    """
    A response to a FlowReservationResponse.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class FunctionSetAssignmentsListLink(ListLink):
    """
    SHALL contain a Link to a List of FunctionSetAssignments instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class HistoricalReadingListLink(ListLink):
    """
    SHALL contain a Link to a List of HistoricalReading instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class IpaddrListLink(ListLink):
    """
    SHALL contain a Link to a List of IPAddr instances.
    """
    class Meta:
        name = "IPAddrListLink"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class IpinterfaceListLink(ListLink):
    """
    SHALL contain a Link to a List of IPInterface instances.
    """
    class Meta:
        name = "IPInterfaceListLink"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class LlinterfaceListLink(ListLink):
    """
    SHALL contain a Link to a List of LLInterface instances.
    """
    class Meta:
        name = "LLInterfaceListLink"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class LoadShedAvailability(Resource):
    """
    Indicates current consumption status and ability to shed load.

    :ivar availability_duration: Indicates for how many seconds the
        consuming device will be able to reduce consumption at the
        maximum response level.
    :ivar demand_response_program_link:
    :ivar sheddable_percent: Maximum percent of current operating load
        that is estimated to be sheddable.
    :ivar sheddable_power: Maximum amount of current operating load that
        is estimated to be sheddable, in Watts.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    availability_duration: Optional[int] = field(
        default=None,
        metadata={
            "name": "availabilityDuration",
            "type": "Element",
        }
    )
    demand_response_program_link: Optional[DemandResponseProgramLink] = field(
        default=None,
        metadata={
            "name": "DemandResponseProgramLink",
            "type": "Element",
        }
    )
    sheddable_percent: Optional[int] = field(
        default=None,
        metadata={
            "name": "sheddablePercent",
            "type": "Element",
        }
    )
    sheddable_power: Optional[ActivePower] = field(
        default=None,
        metadata={
            "name": "sheddablePower",
            "type": "Element",
        }
    )


@dataclass
class LoadShedAvailabilityListLink(ListLink):
    """
    SHALL contain a Link to a List of LoadShedAvailability instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class LogEventListLink(ListLink):
    """
    SHALL contain a Link to a List of LogEvent instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class MessagingProgramListLink(ListLink):
    """
    SHALL contain a Link to a List of MessagingProgram instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class MeterReadingBase(IdentifiedObject):
    """
    A container for associating ReadingType, Readings and ReadingSets.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class MeterReadingListLink(ListLink):
    """
    SHALL contain a Link to a List of MeterReading instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class MirrorUsagePointListLink(ListLink):
    """
    SHALL contain a Link to a List of MirrorUsagePoint instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class NeighborList(ListType):
    """
    List of 15.4 neighbors.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    neighbor: List[Neighbor] = field(
        default_factory=list,
        metadata={
            "name": "Neighbor",
            "type": "Element",
        }
    )


@dataclass
class NeighborListLink(ListLink):
    """
    SHALL contain a Link to a List of Neighbor instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class Notification(SubscriptionBase):
    """Holds the information related to a client subscription to receive
    updates to a resource automatically.

    The actual resources may be passed in the Notification by specifying
    a specific xsi:type for the Resource and passing the full
    representation.

    :ivar new_resource_uri: The new location of the resource, if moved.
        This attribute SHALL be a fully-qualified absolute URI, not a
        relative reference.
    :ivar resource:
    :ivar status: 0 = Default Status 1 = Subscription canceled, no
        additional information 2 = Subscription canceled, resource moved
        3 = Subscription canceled, resource definition changed (e.g., a
        new version of IEEE 2030.5) 4 = Subscription canceled, resource
        deleted All other values reserved.
    :ivar subscription_uri: The subscription from which this
        notification was triggered. This attribute SHALL be a fully-
        qualified absolute URI, not a relative reference.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    new_resource_uri: Optional[str] = field(
        default=None,
        metadata={
            "name": "newResourceURI",
            "type": "Element",
        }
    )
    resource: Optional[Resource] = field(
        default=None,
        metadata={
            "name": "Resource",
            "type": "Element",
        }
    )
    status: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    subscription_uri: Optional[str] = field(
        default=None,
        metadata={
            "name": "subscriptionURI",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class NotificationListLink(ListLink):
    """
    SHALL contain a Link to a List of Notification instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class PowerStatus(Resource):
    """
    Contains the status of the device's power sources.

    :ivar battery_status: Battery system status 0 = unknown 1 = normal
        (more than LowChargeThreshold remaining) 2 = low (less than
        LowChargeThreshold remaining) 3 = depleted (0% charge remaining)
        4 = not applicable (mains powered only)
    :ivar changed_time: The time at which the reported values were
        recorded.
    :ivar current_power_source: This value will be fixed for devices
        powered by a single source.  This value may change for devices
        able to transition between multiple power sources (mains to
        battery backup, etc.).
    :ivar estimated_charge_remaining: Estimate of remaining battery
        charge as a percent of full charge.
    :ivar estimated_time_remaining: Estimated time (in seconds) to total
        battery charge depletion (under current load)
    :ivar pevinfo:
    :ivar session_time_on_battery: If the device has a battery, this is
        the time since the device last switched to battery power, or the
        time since the device was restarted, whichever is less, in
        seconds.
    :ivar total_time_on_battery: If the device has a battery, this is
        the total time the device has been on battery power, in seconds.
        It may be reset when the battery is replaced.
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    battery_status: Optional[int] = field(
        default=None,
        metadata={
            "name": "batteryStatus",
            "type": "Element",
            "required": True,
        }
    )
    changed_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "changedTime",
            "type": "Element",
            "required": True,
        }
    )
    current_power_source: Optional[int] = field(
        default=None,
        metadata={
            "name": "currentPowerSource",
            "type": "Element",
            "required": True,
        }
    )
    estimated_charge_remaining: Optional[int] = field(
        default=None,
        metadata={
            "name": "estimatedChargeRemaining",
            "type": "Element",
        }
    )
    estimated_time_remaining: Optional[int] = field(
        default=None,
        metadata={
            "name": "estimatedTimeRemaining",
            "type": "Element",
        }
    )
    pevinfo: Optional[Pevinfo] = field(
        default=None,
        metadata={
            "name": "PEVInfo",
            "type": "Element",
        }
    )
    session_time_on_battery: Optional[int] = field(
        default=None,
        metadata={
            "name": "sessionTimeOnBattery",
            "type": "Element",
        }
    )
    total_time_on_battery: Optional[int] = field(
        default=None,
        metadata={
            "name": "totalTimeOnBattery",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class PrepaymentListLink(ListLink):
    """
    SHALL contain a Link to a List of Prepayment instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class PriceResponse(Response):
    """
    A response related to a price message.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class PriceResponseCfg(Resource):
    """
    Configuration data that specifies how price responsive devices SHOULD
    respond to price changes while acting upon a given RateComponent.

    :ivar consume_threshold: Price responsive clients acting upon the
        associated RateComponent SHOULD consume the associated commodity
        while the price is less than this threshold.
    :ivar max_reduction_threshold: Price responsive clients acting upon
        the associated RateComponent SHOULD reduce consumption to the
        maximum extent possible while the price is greater than this
        threshold.
    :ivar rate_component_link:
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    consume_threshold: Optional[int] = field(
        default=None,
        metadata={
            "name": "consumeThreshold",
            "type": "Element",
            "required": True,
        }
    )
    max_reduction_threshold: Optional[int] = field(
        default=None,
        metadata={
            "name": "maxReductionThreshold",
            "type": "Element",
            "required": True,
        }
    )
    rate_component_link: Optional[RateComponentLink] = field(
        default=None,
        metadata={
            "name": "RateComponentLink",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class PriceResponseCfgListLink(ListLink):
    """
    SHALL contain a Link to a List of PriceResponseCfg instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class ProjectionReadingListLink(ListLink):
    """
    SHALL contain a Link to a List of ProjectionReading instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class RplinstanceListLink(ListLink):
    """
    SHALL contain a Link to a List of RPLInterface instances.
    """
    class Meta:
        name = "RPLInstanceListLink"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class RplsourceRoutesList(ListType):
    """
    List or RPL source routes if the hosting device is the DODAGroot.
    """
    class Meta:
        name = "RPLSourceRoutesList"
        namespace = "urn:ieee:std:2030.5:ns"

    rplsource_routes: List[RplsourceRoutes] = field(
        default_factory=list,
        metadata={
            "name": "RPLSourceRoutes",
            "type": "Element",
        }
    )


@dataclass
class RplsourceRoutesListLink(ListLink):
    """
    SHALL contain a Link to a List of RPLSourceRoutes instances.
    """
    class Meta:
        name = "RPLSourceRoutesListLink"
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class RateComponentListLink(ListLink):
    """
    SHALL contain a Link to a List of RateComponent instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class Reading(ReadingBase):
    """
    Specific value measured by a meter or other asset.

    :ivar local_id: The local identifier for this reading within the
        reading set. localIDs are assigned in order of creation time.
        For interval data, this value SHALL increase with each interval
        time, and for block/tier readings, localID SHALL not be
        specified.
    :ivar subscribable: Indicates whether or not subscriptions are
        supported for this resource, and whether or not conditional
        (thresholds) are supported. If not specified, is "not
        subscribable" (0).
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    local_id: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "localID",
            "type": "Element",
            "max_length": 2,
            "format": "base16",
        }
    )
    subscribable: int = field(
        default=0,
        metadata={
            "type": "Attribute",
        }
    )


@dataclass
class ReadingListLink(ListLink):
    """
    SHALL contain a Link to a List of Reading instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class ReadingSetBase(IdentifiedObject):
    """A set of Readings of the ReadingType indicated by the parent
    MeterReading.

    ReadingBase is abstract, used to define the elements common to
    ReadingSet and IntervalBlock.

    :ivar time_period: Specifies the time range during which the
        contained readings were taken.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    time_period: Optional[DateTimeInterval] = field(
        default=None,
        metadata={
            "name": "timePeriod",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class ReadingSetListLink(ListLink):
    """
    SHALL contain a Link to a List of ReadingSet instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class RespondableIdentifiedObject(RespondableResource):
    """
    An IdentifiedObject to which a Response can be requested.

    :ivar m_rid: The global identifier of the object.
    :ivar description: The description is a human readable text
        describing or naming the object.
    :ivar version: Contains the version number of the object. See the
        type definition for details.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    m_rid: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "mRID",
            "type": "Element",
            "required": True,
            "max_length": 16,
            "format": "base16",
        }
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 32,
        }
    )
    version: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class RespondableSubscribableIdentifiedObject(RespondableResource):
    """
    An IdentifiedObject to which a Response can be requested.

    :ivar m_rid: The global identifier of the object.
    :ivar description: The description is a human readable text
        describing or naming the object.
    :ivar version: Contains the version number of the object. See the
        type definition for details.
    :ivar subscribable: Indicates whether or not subscriptions are
        supported for this resource, and whether or not conditional
        (thresholds) are supported. If not specified, is "not
        subscribable" (0).
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    m_rid: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "mRID",
            "type": "Element",
            "required": True,
            "max_length": 16,
            "format": "base16",
        }
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 32,
        }
    )
    version: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    subscribable: int = field(
        default=0,
        metadata={
            "type": "Attribute",
        }
    )


@dataclass
class ResponseList(ListType):
    """
    A List element to hold Response objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    response: List[Response] = field(
        default_factory=list,
        metadata={
            "name": "Response",
            "type": "Element",
        }
    )


@dataclass
class ResponseListLink(ListLink):
    """
    SHALL contain a Link to a List of Response instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class ResponseSetListLink(ListLink):
    """
    SHALL contain a Link to a List of ResponseSet instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class ServiceSupplier(IdentifiedObject):
    """
    Organisation that provides services to Customers.

    :ivar email: E-mail address for this service supplier.
    :ivar phone: Human-readable phone number for this service supplier.
    :ivar provider_id: Contains the IANA PEN for the commodity provider.
    :ivar web: Website URI address for this service supplier.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    email: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 32,
        }
    )
    phone: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 20,
        }
    )
    provider_id: Optional[int] = field(
        default=None,
        metadata={
            "name": "providerID",
            "type": "Element",
        }
    )
    web: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 42,
        }
    )


@dataclass
class SubscribableIdentifiedObject(SubscribableResource):
    """
    An IdentifiedObject to which a Subscription can be requested.

    :ivar m_rid: The global identifier of the object.
    :ivar description: The description is a human readable text
        describing or naming the object.
    :ivar version: Contains the version number of the object. See the
        type definition for details.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    m_rid: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "mRID",
            "type": "Element",
            "required": True,
            "max_length": 16,
            "format": "base16",
        }
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 32,
        }
    )
    version: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )


@dataclass
class SubscribableList(SubscribableResource):
    """
    A List to which a Subscription can be requested.

    :ivar all: The number specifying "all" of the items in the list.
        Required on GET, ignored otherwise.
    :ivar results: Indicates the number of items in this page of
        results.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    all: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )
    results: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        }
    )


@dataclass
class Subscription(SubscriptionBase):
    """
    Holds the information related to a client subscription to receive updates
    to a resource automatically.

    :ivar condition:
    :ivar encoding: 0 - application/sep+xml 1 - application/sep-exi
        2-255 - reserved
    :ivar level: Contains the preferred schema and extensibility level
        indication such as "+S1"
    :ivar limit: This element is used to indicate the maximum number of
        list items that should be included in a notification when the
        subscribed resource changes. This limit is meant to be
        functionally equivalent to the ‘limit’ query string parameter,
        but applies to both list resources as well as other resources.
        For list resources, if a limit of ‘0’ is specified, then
        notifications SHALL contain a list resource with results=’0’
        (equivalent to a simple change notification).  For list
        resources, if a limit greater than ‘0’ is specified, then
        notifications SHALL contain a list resource with results equal
        to the limit specified (or less, should the list contain fewer
        items than the limit specified or should the server be unable to
        provide the requested number of items for any reason) and follow
        the same rules for list resources (e.g., ordering).  For non-
        list resources, if a limit of ‘0’ is specified, then
        notifications SHALL NOT contain a resource representation
        (equivalent to a simple change notification).  For non-list
        resources, if a limit greater than ‘0’ is specified, then
        notifications SHALL contain the representation of the changed
        resource.
    :ivar notification_uri: The resource to which to post the
        notifications about the requested subscribed resource. Because
        this URI will exist on a server other than the one being POSTed
        to, this attribute SHALL be a fully-qualified absolute URI, not
        a relative reference.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    condition: Optional[Condition] = field(
        default=None,
        metadata={
            "name": "Condition",
            "type": "Element",
        }
    )
    encoding: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    level: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 16,
        }
    )
    limit: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    notification_uri: Optional[str] = field(
        default=None,
        metadata={
            "name": "notificationURI",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class SubscriptionListLink(ListLink):
    """
    SHALL contain a Link to a List of Subscription instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class SupplyInterruptionOverrideList(ListType):
    """
    A List element to hold SupplyInterruptionOverride objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    supply_interruption_override: List[SupplyInterruptionOverride] = field(
        default_factory=list,
        metadata={
            "name": "SupplyInterruptionOverride",
            "type": "Element",
        }
    )


@dataclass
class SupplyInterruptionOverrideListLink(ListLink):
    """
    SHALL contain a Link to a List of SupplyInterruptionOverride instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class SupportedLocaleList(ListType):
    """
    A List element to hold SupportedLocale objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    supported_locale: List[SupportedLocale] = field(
        default_factory=list,
        metadata={
            "name": "SupportedLocale",
            "type": "Element",
        }
    )


@dataclass
class SupportedLocaleListLink(ListLink):
    """
    SHALL contain a Link to a List of SupportedLocale instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class TargetReadingListLink(ListLink):
    """
    SHALL contain a Link to a List of TargetReading instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class TariffProfileListLink(ListLink):
    """
    SHALL contain a Link to a List of TariffProfile instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class TextMessageListLink(ListLink):
    """
    SHALL contain a Link to a List of TextMessage instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class TextResponse(Response):
    """
    A response to a text message.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class TimeTariffIntervalListLink(ListLink):
    """
    SHALL contain a Link to a List of TimeTariffInterval instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class UsagePointBase(IdentifiedObject):
    """Logical point on a network at which consumption or production is either
    physically measured (e.g. metered) or estimated (e.g. unmetered street
    lights).

    A container for associating ReadingType, Readings and ReadingSets.

    :ivar role_flags: Specifies the roles that apply to the usage point.
    :ivar service_category_kind: The kind of service provided by this
        usage point.
    :ivar status: Specifies the current status of the service at this
        usage point. 0 = off 1 = on
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    role_flags: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "roleFlags",
            "type": "Element",
            "required": True,
            "max_length": 2,
            "format": "base16",
        }
    )
    service_category_kind: Optional[int] = field(
        default=None,
        metadata={
            "name": "serviceCategoryKind",
            "type": "Element",
            "required": True,
        }
    )
    status: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class UsagePointListLink(ListLink):
    """
    SHALL contain a Link to a List of UsagePoint instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class AbstractDevice(SubscribableResource):
    """
    The EndDevice providing the resources available within the
    DeviceCapabilities.

    :ivar configuration_link:
    :ivar derlist_link:
    :ivar device_category: This field is for use in devices that can
        adjust energy usage (e.g., demand response, distributed energy
        resources).  For devices that do not respond to
        EndDeviceControls or DERControls (for instance, an ESI), this
        field should not have any bits set.
    :ivar device_information_link:
    :ivar device_status_link:
    :ivar file_status_link:
    :ivar ipinterface_list_link:
    :ivar l_fdi: Long form of device identifier. See the Security
        section for additional details.
    :ivar load_shed_availability_list_link:
    :ivar log_event_list_link:
    :ivar power_status_link:
    :ivar s_fdi: Short form of device identifier, WITH the checksum
        digit. See the Security section for additional details.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    configuration_link: Optional[ConfigurationLink] = field(
        default=None,
        metadata={
            "name": "ConfigurationLink",
            "type": "Element",
        }
    )
    derlist_link: Optional[DerlistLink] = field(
        default=None,
        metadata={
            "name": "DERListLink",
            "type": "Element",
        }
    )
    device_category: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "deviceCategory",
            "type": "Element",
            "max_length": 4,
            "format": "base16",
        }
    )
    device_information_link: Optional[DeviceInformationLink] = field(
        default=None,
        metadata={
            "name": "DeviceInformationLink",
            "type": "Element",
        }
    )
    device_status_link: Optional[DeviceStatusLink] = field(
        default=None,
        metadata={
            "name": "DeviceStatusLink",
            "type": "Element",
        }
    )
    file_status_link: Optional[FileStatusLink] = field(
        default=None,
        metadata={
            "name": "FileStatusLink",
            "type": "Element",
        }
    )
    ipinterface_list_link: Optional[IpinterfaceListLink] = field(
        default=None,
        metadata={
            "name": "IPInterfaceListLink",
            "type": "Element",
        }
    )
    l_fdi: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "lFDI",
            "type": "Element",
            "max_length": 20,
            "format": "base16",
        }
    )
    load_shed_availability_list_link: Optional[LoadShedAvailabilityListLink] = field(
        default=None,
        metadata={
            "name": "LoadShedAvailabilityListLink",
            "type": "Element",
        }
    )
    log_event_list_link: Optional[LogEventListLink] = field(
        default=None,
        metadata={
            "name": "LogEventListLink",
            "type": "Element",
        }
    )
    power_status_link: Optional[PowerStatusLink] = field(
        default=None,
        metadata={
            "name": "PowerStatusLink",
            "type": "Element",
        }
    )
    s_fdi: Optional[int] = field(
        default=None,
        metadata={
            "name": "sFDI",
            "type": "Element",
            "required": True,
            "max_inclusive": 281474976710655,
        }
    )


@dataclass
class BillingMeterReadingBase(MeterReadingBase):
    """
    Contains historical, target, and projection readings of various types,
    possibly associated with charges.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    billing_reading_set_list_link: Optional[BillingReadingSetListLink] = field(
        default=None,
        metadata={
            "name": "BillingReadingSetListLink",
            "type": "Element",
        }
    )
    reading_type_link: Optional[ReadingTypeLink] = field(
        default=None,
        metadata={
            "name": "ReadingTypeLink",
            "type": "Element",
        }
    )


@dataclass
class BillingPeriodList(SubscribableList):
    """
    A List element to hold BillingPeriod objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    billing_period: List[BillingPeriod] = field(
        default_factory=list,
        metadata={
            "name": "BillingPeriod",
            "type": "Element",
        }
    )


@dataclass
class BillingReadingList(ListType):
    """
    A List element to hold BillingReading objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    billing_reading: List[BillingReading] = field(
        default_factory=list,
        metadata={
            "name": "BillingReading",
            "type": "Element",
        }
    )


@dataclass
class BillingReadingSet(ReadingSetBase):
    """
    Time sequence of readings of the same reading type.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    billing_reading_list_link: Optional[BillingReadingListLink] = field(
        default=None,
        metadata={
            "name": "BillingReadingListLink",
            "type": "Element",
        }
    )


@dataclass
class Configuration(SubscribableResource):
    """
    This resource contains various settings to control the operation of the
    device.

    :ivar current_locale: [RFC 4646] identifier of the language-region
        currently in use.
    :ivar power_configuration:
    :ivar price_response_cfg_list_link:
    :ivar time_configuration:
    :ivar user_device_name: User assigned, convenience name used for
        network browsing displays, etc.  Example "My Thermostat"
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    current_locale: Optional[str] = field(
        default=None,
        metadata={
            "name": "currentLocale",
            "type": "Element",
            "required": True,
            "max_length": 42,
        }
    )
    power_configuration: Optional[PowerConfiguration] = field(
        default=None,
        metadata={
            "name": "PowerConfiguration",
            "type": "Element",
        }
    )
    price_response_cfg_list_link: Optional[PriceResponseCfgListLink] = field(
        default=None,
        metadata={
            "name": "PriceResponseCfgListLink",
            "type": "Element",
        }
    )
    time_configuration: Optional[TimeConfiguration] = field(
        default=None,
        metadata={
            "name": "TimeConfiguration",
            "type": "Element",
        }
    )
    user_device_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "userDeviceName",
            "type": "Element",
            "required": True,
            "max_length": 32,
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class CreditRegisterList(ListType):
    """
    A List element to hold CreditRegister objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    credit_register: List[CreditRegister] = field(
        default_factory=list,
        metadata={
            "name": "CreditRegister",
            "type": "Element",
        }
    )


@dataclass
class CustomerAccount(IdentifiedObject):
    """Assignment of a group of products and services purchased by the Customer
    through a CustomerAgreement, used as a mechanism for customer billing and
    payment.

    It contains common information from the various types of
    CustomerAgreements to register billings (invoices) for a Customer and
    receive payment.

    :ivar currency: The ISO 4217 code indicating the currency applicable
        to the bill amounts in the summary. See list at
        http://www.unece.org/cefact/recommendations/rec09/rec09_ecetrd203.pdf
    :ivar customer_account: The account number for the customer (if
        applicable).
    :ivar customer_agreement_list_link:
    :ivar customer_name: The name of the customer.
    :ivar price_power_of_ten_multiplier: Indicates the power of ten
        multiplier for the prices in this function set.
    :ivar service_supplier_link:
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    currency: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    customer_account: Optional[str] = field(
        default=None,
        metadata={
            "name": "customerAccount",
            "type": "Element",
            "max_length": 42,
        }
    )
    customer_agreement_list_link: Optional[CustomerAgreementListLink] = field(
        default=None,
        metadata={
            "name": "CustomerAgreementListLink",
            "type": "Element",
        }
    )
    customer_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "customerName",
            "type": "Element",
            "max_length": 42,
        }
    )
    price_power_of_ten_multiplier: Optional[int] = field(
        default=None,
        metadata={
            "name": "pricePowerOfTenMultiplier",
            "type": "Element",
            "required": True,
        }
    )
    service_supplier_link: Optional[ServiceSupplierLink] = field(
        default=None,
        metadata={
            "name": "ServiceSupplierLink",
            "type": "Element",
        }
    )


@dataclass
class CustomerAgreement(IdentifiedObject):
    """Agreement between the customer and the service supplier to pay for
    service at a specific service location.

    It records certain billing information about the type of service
    provided at the service location and is used during charge creation
    to determine the type of service.

    :ivar active_billing_period_list_link:
    :ivar active_projection_reading_list_link:
    :ivar active_target_reading_list_link:
    :ivar billing_period_list_link:
    :ivar historical_reading_list_link:
    :ivar prepayment_link:
    :ivar projection_reading_list_link:
    :ivar service_account: The account number of the service account (if
        applicable).
    :ivar service_location: The address or textual description of the
        service location.
    :ivar target_reading_list_link:
    :ivar tariff_profile_link:
    :ivar usage_point_link:
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    active_billing_period_list_link: Optional[ActiveBillingPeriodListLink] = field(
        default=None,
        metadata={
            "name": "ActiveBillingPeriodListLink",
            "type": "Element",
        }
    )
    active_projection_reading_list_link: Optional[ActiveProjectionReadingListLink] = field(
        default=None,
        metadata={
            "name": "ActiveProjectionReadingListLink",
            "type": "Element",
        }
    )
    active_target_reading_list_link: Optional[ActiveTargetReadingListLink] = field(
        default=None,
        metadata={
            "name": "ActiveTargetReadingListLink",
            "type": "Element",
        }
    )
    billing_period_list_link: Optional[BillingPeriodListLink] = field(
        default=None,
        metadata={
            "name": "BillingPeriodListLink",
            "type": "Element",
        }
    )
    historical_reading_list_link: Optional[HistoricalReadingListLink] = field(
        default=None,
        metadata={
            "name": "HistoricalReadingListLink",
            "type": "Element",
        }
    )
    prepayment_link: Optional[PrepaymentLink] = field(
        default=None,
        metadata={
            "name": "PrepaymentLink",
            "type": "Element",
        }
    )
    projection_reading_list_link: Optional[ProjectionReadingListLink] = field(
        default=None,
        metadata={
            "name": "ProjectionReadingListLink",
            "type": "Element",
        }
    )
    service_account: Optional[str] = field(
        default=None,
        metadata={
            "name": "serviceAccount",
            "type": "Element",
            "max_length": 42,
        }
    )
    service_location: Optional[str] = field(
        default=None,
        metadata={
            "name": "serviceLocation",
            "type": "Element",
            "max_length": 42,
        }
    )
    target_reading_list_link: Optional[TargetReadingListLink] = field(
        default=None,
        metadata={
            "name": "TargetReadingListLink",
            "type": "Element",
        }
    )
    tariff_profile_link: Optional[TariffProfileLink] = field(
        default=None,
        metadata={
            "name": "TariffProfileLink",
            "type": "Element",
        }
    )
    usage_point_link: Optional[UsagePointLink] = field(
        default=None,
        metadata={
            "name": "UsagePointLink",
            "type": "Element",
        }
    )


@dataclass
class Der(SubscribableResource):
    """
    Contains links to DER resources.
    """
    class Meta:
        name = "DER"
        namespace = "urn:ieee:std:2030.5:ns"

    associated_derprogram_list_link: Optional[AssociatedDerprogramListLink] = field(
        default=None,
        metadata={
            "name": "AssociatedDERProgramListLink",
            "type": "Element",
        }
    )
    associated_usage_point_link: Optional[AssociatedUsagePointLink] = field(
        default=None,
        metadata={
            "name": "AssociatedUsagePointLink",
            "type": "Element",
        }
    )
    current_derprogram_link: Optional[CurrentDerprogramLink] = field(
        default=None,
        metadata={
            "name": "CurrentDERProgramLink",
            "type": "Element",
        }
    )
    deravailability_link: Optional[DeravailabilityLink] = field(
        default=None,
        metadata={
            "name": "DERAvailabilityLink",
            "type": "Element",
        }
    )
    dercapability_link: Optional[DercapabilityLink] = field(
        default=None,
        metadata={
            "name": "DERCapabilityLink",
            "type": "Element",
        }
    )
    dersettings_link: Optional[DersettingsLink] = field(
        default=None,
        metadata={
            "name": "DERSettingsLink",
            "type": "Element",
        }
    )
    derstatus_link: Optional[DerstatusLink] = field(
        default=None,
        metadata={
            "name": "DERStatusLink",
            "type": "Element",
        }
    )


@dataclass
class DercurveList(ListType):
    """
    A List element to hold DERCurve objects.
    """
    class Meta:
        name = "DERCurveList"
        namespace = "urn:ieee:std:2030.5:ns"

    dercurve: List[Dercurve] = field(
        default_factory=list,
        metadata={
            "name": "DERCurve",
            "type": "Element",
        }
    )


@dataclass
class Derprogram(SubscribableIdentifiedObject):
    """
    Distributed Energy Resource program.

    :ivar active_dercontrol_list_link:
    :ivar default_dercontrol_link:
    :ivar dercontrol_list_link:
    :ivar dercurve_list_link:
    :ivar primacy: Indicates the relative primacy of the provider of
        this Program.
    """
    class Meta:
        name = "DERProgram"
        namespace = "urn:ieee:std:2030.5:ns"

    active_dercontrol_list_link: Optional[ActiveDercontrolListLink] = field(
        default=None,
        metadata={
            "name": "ActiveDERControlListLink",
            "type": "Element",
        }
    )
    default_dercontrol_link: Optional[DefaultDercontrolLink] = field(
        default=None,
        metadata={
            "name": "DefaultDERControlLink",
            "type": "Element",
        }
    )
    dercontrol_list_link: Optional[DercontrolListLink] = field(
        default=None,
        metadata={
            "name": "DERControlListLink",
            "type": "Element",
        }
    )
    dercurve_list_link: Optional[DercurveListLink] = field(
        default=None,
        metadata={
            "name": "DERCurveListLink",
            "type": "Element",
        }
    )
    primacy: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class DefaultDercontrol(SubscribableIdentifiedObject):
    """
    Contains control mode information to be used if no active DERControl is
    found.

    :ivar dercontrol_base:
    :ivar set_esdelay: Enter service delay, in hundredths of a second.
        When present, this value SHALL update the value of the
        corresponding setting (DERSettings::setESDelay).
    :ivar set_eshigh_freq: Enter service frequency high. Specified in
        hundredths of Hz. When present, this value SHALL update the
        value of the corresponding setting (DERSettings::setESHighFreq).
    :ivar set_eshigh_volt: Enter service voltage high. Specified as an
        effective percent voltage, defined as (100% * (locally measured
        voltage - setVRefOfs) / setVRef), in hundredths of a percent.
        When present, this value SHALL update the value of the
        corresponding setting (DERSettings::setESHighVolt).
    :ivar set_eslow_freq: Enter service frequency low. Specified in
        hundredths of Hz. When present, this value SHALL update the
        value of the corresponding setting (DERSettings::setESLowFreq).
    :ivar set_eslow_volt: Enter service voltage low. Specified as an
        effective percent voltage, defined as (100% * (locally measured
        voltage - setVRefOfs) / setVRef), in hundredths of a percent.
        When present, this value SHALL update the value of the
        corresponding setting (DERSettings::setESLowVolt).
    :ivar set_esramp_tms: Enter service ramp time, in hundredths of a
        second. When present, this value SHALL update the value of the
        corresponding setting (DERSettings::setESRampTms).
    :ivar set_esrandom_delay: Enter service randomized delay, in
        hundredths of a second. When present, this value SHALL update
        the value of the corresponding setting
        (DERSettings::setESRandomDelay).
    :ivar set_grad_w: Set default rate of change (ramp rate) of active
        power output due to command or internal action, defined in
        %setWMax / second.  Resolution is in hundredths of a
        percent/second. A value of 0 means there is no limit.
        Interpreted as a percentage change in output capability limit
        per second when used as a default ramp rate. When present, this
        value SHALL update the value of the corresponding setting
        (DERSettings::setGradW).
    :ivar set_soft_grad_w: Set soft-start rate of change (soft-start
        ramp rate) of active power output due to command or internal
        action, defined in %setWMax / second.  Resolution is in
        hundredths of a percent/second. A value of 0 means there is no
        limit. Interpreted as a percentage change in output capability
        limit per second when used as a ramp rate. When present, this
        value SHALL update the value of the corresponding setting
        (DERSettings::setSoftGradW).
    """
    class Meta:
        name = "DefaultDERControl"
        namespace = "urn:ieee:std:2030.5:ns"

    dercontrol_base: Optional[DercontrolBase] = field(
        default=None,
        metadata={
            "name": "DERControlBase",
            "type": "Element",
            "required": True,
        }
    )
    set_esdelay: Optional[int] = field(
        default=None,
        metadata={
            "name": "setESDelay",
            "type": "Element",
        }
    )
    set_eshigh_freq: Optional[int] = field(
        default=None,
        metadata={
            "name": "setESHighFreq",
            "type": "Element",
        }
    )
    set_eshigh_volt: Optional[int] = field(
        default=None,
        metadata={
            "name": "setESHighVolt",
            "type": "Element",
        }
    )
    set_eslow_freq: Optional[int] = field(
        default=None,
        metadata={
            "name": "setESLowFreq",
            "type": "Element",
        }
    )
    set_eslow_volt: Optional[int] = field(
        default=None,
        metadata={
            "name": "setESLowVolt",
            "type": "Element",
        }
    )
    set_esramp_tms: Optional[int] = field(
        default=None,
        metadata={
            "name": "setESRampTms",
            "type": "Element",
        }
    )
    set_esrandom_delay: Optional[int] = field(
        default=None,
        metadata={
            "name": "setESRandomDelay",
            "type": "Element",
        }
    )
    set_grad_w: Optional[int] = field(
        default=None,
        metadata={
            "name": "setGradW",
            "type": "Element",
        }
    )
    set_soft_grad_w: Optional[int] = field(
        default=None,
        metadata={
            "name": "setSoftGradW",
            "type": "Element",
        }
    )


@dataclass
class DemandResponseProgram(IdentifiedObject):
    """
    Demand response program.

    :ivar active_end_device_control_list_link:
    :ivar availability_update_percent_change_threshold: This attribute
        allows program providers to specify the requested granularity of
        updates to LoadShedAvailability sheddablePercent. If not
        present, or set to 0, then updates to LoadShedAvailability SHALL
        NOT be provided. If present and greater than zero, then clients
        SHALL provide their LoadShedAvailability if it has not
        previously been provided, and thereafter if the difference
        between the previously provided value and the current value of
        LoadShedAvailability sheddablePercent is greater than
        availabilityUpdatePercentChangeThreshold.
    :ivar availability_update_power_change_threshold: This attribute
        allows program providers to specify the requested granularity of
        updates to LoadShedAvailability sheddablePower. If not present,
        or set to 0, then updates to LoadShedAvailability SHALL NOT be
        provided. If present and greater than zero, then clients SHALL
        provide their LoadShedAvailability if it has not previously been
        provided, and thereafter if the difference between the
        previously provided value and the current value of
        LoadShedAvailability sheddablePower is greater than
        availabilityUpdatePowerChangeThreshold.
    :ivar end_device_control_list_link:
    :ivar primacy: Indicates the relative primacy of the provider of
        this program.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    active_end_device_control_list_link: Optional[ActiveEndDeviceControlListLink] = field(
        default=None,
        metadata={
            "name": "ActiveEndDeviceControlListLink",
            "type": "Element",
        }
    )
    availability_update_percent_change_threshold: Optional[int] = field(
        default=None,
        metadata={
            "name": "availabilityUpdatePercentChangeThreshold",
            "type": "Element",
        }
    )
    availability_update_power_change_threshold: Optional[ActivePower] = field(
        default=None,
        metadata={
            "name": "availabilityUpdatePowerChangeThreshold",
            "type": "Element",
        }
    )
    end_device_control_list_link: Optional[EndDeviceControlListLink] = field(
        default=None,
        metadata={
            "name": "EndDeviceControlListLink",
            "type": "Element",
        }
    )
    primacy: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class DeviceInformation(Resource):
    """
    Contains identification and other information about the device that changes
    very infrequently, typically only when updates are applied, if ever.

    :ivar drlccapabilities:
    :ivar functions_implemented: Bitmap indicating the function sets
        used by the device as a client. 0 - Device Capability 1 - Self
        Device Resource 2 - End Device Resource 3 - Function Set
        Assignments 4 - Subscription/Notification Mechanism 5 - Response
        6 - Time 7 - Device Information 8 - Power Status 9 - Network
        Status 10 - Log Event 11 - Configuration Resource 12 - Software
        Download 13 - DRLC 14 - Metering 15 - Pricing 16 - Messaging 17
        - Billing 18 - Prepayment 19 - Flow Reservation 20 - DER Control
    :ivar gps_location: GPS location of this device.
    :ivar l_fdi: Long form device identifier. See the Security section
        for full details.
    :ivar mf_date: Date/time of manufacture
    :ivar mf_hw_ver: Manufacturer hardware version
    :ivar mf_id: The manufacturer's IANA Enterprise Number.
    :ivar mf_info: Manufacturer dependent information related to the
        manufacture of this device
    :ivar mf_model: Manufacturer's model number
    :ivar mf_ser_num: Manufacturer assigned serial number
    :ivar primary_power: Primary source of power.
    :ivar secondary_power: Secondary source of power
    :ivar supported_locale_list_link:
    :ivar sw_act_time: Activation date/time of currently running
        software
    :ivar sw_ver: Currently running software version
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    drlccapabilities: Optional[Drlccapabilities] = field(
        default=None,
        metadata={
            "name": "DRLCCapabilities",
            "type": "Element",
        }
    )
    functions_implemented: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "functionsImplemented",
            "type": "Element",
            "max_length": 8,
            "format": "base16",
        }
    )
    gps_location: Optional[GpslocationType] = field(
        default=None,
        metadata={
            "name": "gpsLocation",
            "type": "Element",
        }
    )
    l_fdi: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "lFDI",
            "type": "Element",
            "required": True,
            "max_length": 20,
            "format": "base16",
        }
    )
    mf_date: Optional[int] = field(
        default=None,
        metadata={
            "name": "mfDate",
            "type": "Element",
            "required": True,
        }
    )
    mf_hw_ver: Optional[str] = field(
        default=None,
        metadata={
            "name": "mfHwVer",
            "type": "Element",
            "required": True,
            "max_length": 32,
        }
    )
    mf_id: Optional[int] = field(
        default=None,
        metadata={
            "name": "mfID",
            "type": "Element",
            "required": True,
        }
    )
    mf_info: Optional[str] = field(
        default=None,
        metadata={
            "name": "mfInfo",
            "type": "Element",
            "max_length": 32,
        }
    )
    mf_model: Optional[str] = field(
        default=None,
        metadata={
            "name": "mfModel",
            "type": "Element",
            "required": True,
            "max_length": 32,
        }
    )
    mf_ser_num: Optional[str] = field(
        default=None,
        metadata={
            "name": "mfSerNum",
            "type": "Element",
            "required": True,
            "max_length": 32,
        }
    )
    primary_power: Optional[int] = field(
        default=None,
        metadata={
            "name": "primaryPower",
            "type": "Element",
            "required": True,
        }
    )
    secondary_power: Optional[int] = field(
        default=None,
        metadata={
            "name": "secondaryPower",
            "type": "Element",
            "required": True,
        }
    )
    supported_locale_list_link: Optional[SupportedLocaleListLink] = field(
        default=None,
        metadata={
            "name": "SupportedLocaleListLink",
            "type": "Element",
        }
    )
    sw_act_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "swActTime",
            "type": "Element",
            "required": True,
        }
    )
    sw_ver: Optional[str] = field(
        default=None,
        metadata={
            "name": "swVer",
            "type": "Element",
            "required": True,
            "max_length": 32,
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class Event(RespondableSubscribableIdentifiedObject):
    """An Event indicates information that applies to a particular period of
    time.

    Events SHALL be executed relative to the time of the server, as
    described in the Time function set section 11.1.

    :ivar creation_time: The time at which the Event was created.
    :ivar event_status:
    :ivar interval: The period during which the Event applies.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    creation_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "creationTime",
            "type": "Element",
            "required": True,
        }
    )
    event_status: Optional[EventStatus] = field(
        default=None,
        metadata={
            "name": "EventStatus",
            "type": "Element",
            "required": True,
        }
    )
    interval: Optional[DateTimeInterval] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class FlowReservationRequestList(ListType):
    """
    A List element to hold FlowReservationRequest objects.

    :ivar flow_reservation_request:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    flow_reservation_request: List[FlowReservationRequest] = field(
        default_factory=list,
        metadata={
            "name": "FlowReservationRequest",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class FunctionSetAssignmentsBase(Resource):
    """
    Defines a collection of function set instances that are to be used by one
    or more devices as indicated by the EndDevice object(s) of the server.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    customer_account_list_link: Optional[CustomerAccountListLink] = field(
        default=None,
        metadata={
            "name": "CustomerAccountListLink",
            "type": "Element",
        }
    )
    demand_response_program_list_link: Optional[DemandResponseProgramListLink] = field(
        default=None,
        metadata={
            "name": "DemandResponseProgramListLink",
            "type": "Element",
        }
    )
    derprogram_list_link: Optional[DerprogramListLink] = field(
        default=None,
        metadata={
            "name": "DERProgramListLink",
            "type": "Element",
        }
    )
    file_list_link: Optional[FileListLink] = field(
        default=None,
        metadata={
            "name": "FileListLink",
            "type": "Element",
        }
    )
    messaging_program_list_link: Optional[MessagingProgramListLink] = field(
        default=None,
        metadata={
            "name": "MessagingProgramListLink",
            "type": "Element",
        }
    )
    prepayment_list_link: Optional[PrepaymentListLink] = field(
        default=None,
        metadata={
            "name": "PrepaymentListLink",
            "type": "Element",
        }
    )
    response_set_list_link: Optional[ResponseSetListLink] = field(
        default=None,
        metadata={
            "name": "ResponseSetListLink",
            "type": "Element",
        }
    )
    tariff_profile_list_link: Optional[TariffProfileListLink] = field(
        default=None,
        metadata={
            "name": "TariffProfileListLink",
            "type": "Element",
        }
    )
    time_link: Optional[TimeLink] = field(
        default=None,
        metadata={
            "name": "TimeLink",
            "type": "Element",
        }
    )
    usage_point_list_link: Optional[UsagePointListLink] = field(
        default=None,
        metadata={
            "name": "UsagePointListLink",
            "type": "Element",
        }
    )


@dataclass
class Ieee802154:
    """
    Contains 802.15.4 link layer specific attributes.

    :ivar capability_info: As defined by IEEE 802.15.4
    :ivar neighbor_list_link:
    :ivar short_address: As defined by IEEE 802.15.4
    """
    class Meta:
        name = "IEEE_802_15_4"
        namespace = "urn:ieee:std:2030.5:ns"

    capability_info: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "capabilityInfo",
            "type": "Element",
            "required": True,
            "max_length": 1,
            "format": "base16",
        }
    )
    neighbor_list_link: Optional[NeighborListLink] = field(
        default=None,
        metadata={
            "name": "NeighborListLink",
            "type": "Element",
        }
    )
    short_address: Optional[int] = field(
        default=None,
        metadata={
            "name": "shortAddress",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class Ipaddr(Resource):
    """
    An Internet Protocol address object.

    :ivar address: An IP address value.
    :ivar rplinstance_list_link:
    """
    class Meta:
        name = "IPAddr"
        namespace = "urn:ieee:std:2030.5:ns"

    address: Optional[bytes] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 16,
            "format": "base16",
        }
    )
    rplinstance_list_link: Optional[RplinstanceListLink] = field(
        default=None,
        metadata={
            "name": "RPLInstanceListLink",
            "type": "Element",
        }
    )


@dataclass
class Ipinterface(Resource):
    """Specific IPInterface resource.

    This resource may be thought of as network status information for a
    specific network (IP) layer interface.

    :ivar if_descr: Use rules from [RFC 2863].
    :ivar if_high_speed: Use rules from [RFC 2863].
    :ivar if_in_broadcast_pkts: Use rules from [RFC 2863].
    :ivar if_index: Use rules from [RFC 2863].
    :ivar if_in_discards: Use rules from [RFC 2863]. Can be thought of
        as Input Datagrams Discarded.
    :ivar if_in_errors: Use rules from [RFC 2863].
    :ivar if_in_multicast_pkts: Use rules from [RFC 2863]. Can be
        thought of as Multicast Datagrams Received.
    :ivar if_in_octets: Use rules from [RFC 2863]. Can be thought of as
        Bytes Received.
    :ivar if_in_ucast_pkts: Use rules from [RFC 2863]. Can be thought of
        as Datagrams Received.
    :ivar if_in_unknown_protos: Use rules from [RFC 2863]. Can be
        thought of as Datagrams with Unknown Protocol Received.
    :ivar if_mtu: Use rules from [RFC 2863].
    :ivar if_name: Use rules from [RFC 2863].
    :ivar if_oper_status: Use rules and assignments from [RFC 2863].
    :ivar if_out_broadcast_pkts: Use rules from [RFC 2863]. Can be
        thought of as Broadcast Datagrams Sent.
    :ivar if_out_discards: Use rules from [RFC 2863]. Can be thought of
        as Output Datagrams Discarded.
    :ivar if_out_errors: Use rules from [RFC 2863].
    :ivar if_out_multicast_pkts: Use rules from [RFC 2863]. Can be
        thought of as Multicast Datagrams Sent.
    :ivar if_out_octets: Use rules from [RFC 2863]. Can be thought of as
        Bytes Sent.
    :ivar if_out_ucast_pkts: Use rules from [RFC 2863]. Can be thought
        of as Datagrams Sent.
    :ivar if_promiscuous_mode: Use rules from [RFC 2863].
    :ivar if_speed: Use rules from [RFC 2863].
    :ivar if_type: Use rules and assignments from [RFC 2863].
    :ivar ipaddr_list_link:
    :ivar last_reset_time: Similar to ifLastChange in [RFC 2863].
    :ivar last_updated_time: The date/time of the reported status.
    :ivar llinterface_list_link:
    """
    class Meta:
        name = "IPInterface"
        namespace = "urn:ieee:std:2030.5:ns"

    if_descr: Optional[str] = field(
        default=None,
        metadata={
            "name": "ifDescr",
            "type": "Element",
            "max_length": 192,
        }
    )
    if_high_speed: Optional[int] = field(
        default=None,
        metadata={
            "name": "ifHighSpeed",
            "type": "Element",
        }
    )
    if_in_broadcast_pkts: Optional[int] = field(
        default=None,
        metadata={
            "name": "ifInBroadcastPkts",
            "type": "Element",
        }
    )
    if_index: Optional[int] = field(
        default=None,
        metadata={
            "name": "ifIndex",
            "type": "Element",
        }
    )
    if_in_discards: Optional[int] = field(
        default=None,
        metadata={
            "name": "ifInDiscards",
            "type": "Element",
        }
    )
    if_in_errors: Optional[int] = field(
        default=None,
        metadata={
            "name": "ifInErrors",
            "type": "Element",
        }
    )
    if_in_multicast_pkts: Optional[int] = field(
        default=None,
        metadata={
            "name": "ifInMulticastPkts",
            "type": "Element",
        }
    )
    if_in_octets: Optional[int] = field(
        default=None,
        metadata={
            "name": "ifInOctets",
            "type": "Element",
        }
    )
    if_in_ucast_pkts: Optional[int] = field(
        default=None,
        metadata={
            "name": "ifInUcastPkts",
            "type": "Element",
        }
    )
    if_in_unknown_protos: Optional[int] = field(
        default=None,
        metadata={
            "name": "ifInUnknownProtos",
            "type": "Element",
        }
    )
    if_mtu: Optional[int] = field(
        default=None,
        metadata={
            "name": "ifMtu",
            "type": "Element",
        }
    )
    if_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "ifName",
            "type": "Element",
            "max_length": 16,
        }
    )
    if_oper_status: Optional[int] = field(
        default=None,
        metadata={
            "name": "ifOperStatus",
            "type": "Element",
        }
    )
    if_out_broadcast_pkts: Optional[int] = field(
        default=None,
        metadata={
            "name": "ifOutBroadcastPkts",
            "type": "Element",
        }
    )
    if_out_discards: Optional[int] = field(
        default=None,
        metadata={
            "name": "ifOutDiscards",
            "type": "Element",
        }
    )
    if_out_errors: Optional[int] = field(
        default=None,
        metadata={
            "name": "ifOutErrors",
            "type": "Element",
        }
    )
    if_out_multicast_pkts: Optional[int] = field(
        default=None,
        metadata={
            "name": "ifOutMulticastPkts",
            "type": "Element",
        }
    )
    if_out_octets: Optional[int] = field(
        default=None,
        metadata={
            "name": "ifOutOctets",
            "type": "Element",
        }
    )
    if_out_ucast_pkts: Optional[int] = field(
        default=None,
        metadata={
            "name": "ifOutUcastPkts",
            "type": "Element",
        }
    )
    if_promiscuous_mode: Optional[bool] = field(
        default=None,
        metadata={
            "name": "ifPromiscuousMode",
            "type": "Element",
        }
    )
    if_speed: Optional[int] = field(
        default=None,
        metadata={
            "name": "ifSpeed",
            "type": "Element",
        }
    )
    if_type: Optional[int] = field(
        default=None,
        metadata={
            "name": "ifType",
            "type": "Element",
        }
    )
    ipaddr_list_link: Optional[IpaddrListLink] = field(
        default=None,
        metadata={
            "name": "IPAddrListLink",
            "type": "Element",
        }
    )
    last_reset_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "lastResetTime",
            "type": "Element",
        }
    )
    last_updated_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "lastUpdatedTime",
            "type": "Element",
        }
    )
    llinterface_list_link: Optional[LlinterfaceListLink] = field(
        default=None,
        metadata={
            "name": "LLInterfaceListLink",
            "type": "Element",
        }
    )


@dataclass
class LoadShedAvailabilityList(ListType):
    """
    A List element to hold LoadShedAvailability objects.

    :ivar load_shed_availability:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    load_shed_availability: List[LoadShedAvailability] = field(
        default_factory=list,
        metadata={
            "name": "LoadShedAvailability",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class LogEventList(SubscribableList):
    """
    A List element to hold LogEvent objects.

    :ivar log_event:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    log_event: List[LogEvent] = field(
        default_factory=list,
        metadata={
            "name": "LogEvent",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class MessagingProgram(SubscribableIdentifiedObject):
    """
    Provides a container for collections of text messages.

    :ivar active_text_message_list_link:
    :ivar locale: Indicates the language and region of the messages in
        this collection.
    :ivar primacy: Indicates the relative primacy of the provider of
        this program.
    :ivar text_message_list_link:
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    active_text_message_list_link: Optional[ActiveTextMessageListLink] = field(
        default=None,
        metadata={
            "name": "ActiveTextMessageListLink",
            "type": "Element",
        }
    )
    locale: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 42,
        }
    )
    primacy: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    text_message_list_link: Optional[TextMessageListLink] = field(
        default=None,
        metadata={
            "name": "TextMessageListLink",
            "type": "Element",
        }
    )


@dataclass
class MeterReading(MeterReadingBase):
    """
    Set of values obtained from the meter.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    rate_component_list_link: Optional[RateComponentListLink] = field(
        default=None,
        metadata={
            "name": "RateComponentListLink",
            "type": "Element",
        }
    )
    reading_link: Optional[ReadingLink] = field(
        default=None,
        metadata={
            "name": "ReadingLink",
            "type": "Element",
        }
    )
    reading_set_list_link: Optional[ReadingSetListLink] = field(
        default=None,
        metadata={
            "name": "ReadingSetListLink",
            "type": "Element",
        }
    )
    reading_type_link: Optional[ReadingTypeLink] = field(
        default=None,
        metadata={
            "name": "ReadingTypeLink",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class MirrorReadingSet(ReadingSetBase):
    """
    A set of Readings of the ReadingType indicated by the parent MeterReading.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    reading: List[Reading] = field(
        default_factory=list,
        metadata={
            "name": "Reading",
            "type": "Element",
        }
    )


@dataclass
class NotificationList(ListType):
    """
    A List element to hold Notification objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    notification: List[Notification] = field(
        default_factory=list,
        metadata={
            "name": "Notification",
            "type": "Element",
        }
    )


@dataclass
class PriceResponseCfgList(ListType):
    """
    A List element to hold PriceResponseCfg objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    price_response_cfg: List[PriceResponseCfg] = field(
        default_factory=list,
        metadata={
            "name": "PriceResponseCfg",
            "type": "Element",
        }
    )


@dataclass
class Rplinstance(Resource):
    """Specific RPLInstance resource.

    This resource may be thought of as network status information for a
    specific RPL instance associated with IPInterface.

    :ivar dodagid: See [RFC 6550].
    :ivar dodagroot: See [RFC 6550].
    :ivar flags: See [RFC 6550].
    :ivar grounded_flag: See [RFC 6550].
    :ivar mop: See [RFC 6550].
    :ivar prf: See [RFC 6550].
    :ivar rank: See [RFC 6550].
    :ivar rplinstance_id: See [RFC 6550].
    :ivar rplsource_routes_list_link:
    :ivar version_number: See [RFC 6550].
    """
    class Meta:
        name = "RPLInstance"
        namespace = "urn:ieee:std:2030.5:ns"

    dodagid: Optional[int] = field(
        default=None,
        metadata={
            "name": "DODAGid",
            "type": "Element",
            "required": True,
        }
    )
    dodagroot: Optional[bool] = field(
        default=None,
        metadata={
            "name": "DODAGroot",
            "type": "Element",
            "required": True,
        }
    )
    flags: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    grounded_flag: Optional[bool] = field(
        default=None,
        metadata={
            "name": "groundedFlag",
            "type": "Element",
            "required": True,
        }
    )
    mop: Optional[int] = field(
        default=None,
        metadata={
            "name": "MOP",
            "type": "Element",
            "required": True,
        }
    )
    prf: Optional[int] = field(
        default=None,
        metadata={
            "name": "PRF",
            "type": "Element",
            "required": True,
        }
    )
    rank: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    rplinstance_id: Optional[int] = field(
        default=None,
        metadata={
            "name": "RPLInstanceID",
            "type": "Element",
            "required": True,
        }
    )
    rplsource_routes_list_link: Optional[RplsourceRoutesListLink] = field(
        default=None,
        metadata={
            "name": "RPLSourceRoutesListLink",
            "type": "Element",
        }
    )
    version_number: Optional[int] = field(
        default=None,
        metadata={
            "name": "versionNumber",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class RateComponent(IdentifiedObject):
    """
    Specifies the applicable charges for a single component of the rate, which
    could be generation price or consumption price, for example.

    :ivar active_time_tariff_interval_list_link:
    :ivar flow_rate_end_limit: Specifies the maximum flow rate (e.g. kW
        for electricity) for which this RateComponent applies, for the
        usage point and given rate / tariff. In combination with
        flowRateStartLimit, allows a service provider to define the
        demand or output characteristics for the particular tariff
        design.  If a server includes the flowRateEndLimit attribute,
        then it SHALL also include flowRateStartLimit attribute. For
        example, a service provider’s tariff limits customers to 20 kWs
        of demand for the given rate structure.  Above this threshold
        (from 20-50 kWs), there are different demand charges per unit of
        consumption.  The service provider can use flowRateStartLimit
        and flowRateEndLimit to describe the demand characteristics of
        the different rates.  Similarly, these attributes can be used to
        describe limits on premises DERs that might be producing a
        commodity and sending it back into the distribution network.
        Note: At the time of writing, service provider tariffs with
        demand-based components were not originally identified as being
        in scope, and service provider tariffs vary widely in their use
        of demand components and the method for computing charges.  It
        is expected that industry groups (e.g., OpenSG) will document
        requirements in the future that the IEEE 2030.5 community can
        then use as source material for the next version of IEEE 2030.5.
    :ivar flow_rate_start_limit: Specifies the minimum flow rate (e.g.,
        kW for electricity) for which this RateComponent applies, for
        the usage point and given rate / tariff. In combination with
        flowRateEndLimit, allows a service provider to define the demand
        or output characteristics for the particular tariff design.  If
        a server includes the flowRateStartLimit attribute, then it
        SHALL also include flowRateEndLimit attribute.
    :ivar reading_type_link: Provides indication of the ReadingType with
        which this price is associated.
    :ivar role_flags: Specifies the roles that this usage point has been
        assigned.
    :ivar time_tariff_interval_list_link:
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    active_time_tariff_interval_list_link: Optional[ActiveTimeTariffIntervalListLink] = field(
        default=None,
        metadata={
            "name": "ActiveTimeTariffIntervalListLink",
            "type": "Element",
        }
    )
    flow_rate_end_limit: Optional[UnitValueType] = field(
        default=None,
        metadata={
            "name": "flowRateEndLimit",
            "type": "Element",
        }
    )
    flow_rate_start_limit: Optional[UnitValueType] = field(
        default=None,
        metadata={
            "name": "flowRateStartLimit",
            "type": "Element",
        }
    )
    reading_type_link: Optional[ReadingTypeLink] = field(
        default=None,
        metadata={
            "name": "ReadingTypeLink",
            "type": "Element",
            "required": True,
        }
    )
    role_flags: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "roleFlags",
            "type": "Element",
            "required": True,
            "max_length": 2,
            "format": "base16",
        }
    )
    time_tariff_interval_list_link: Optional[TimeTariffIntervalListLink] = field(
        default=None,
        metadata={
            "name": "TimeTariffIntervalListLink",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class ReadingList(SubscribableList):
    """
    A List element to hold Reading objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    reading: List[Reading] = field(
        default_factory=list,
        metadata={
            "name": "Reading",
            "type": "Element",
        }
    )


@dataclass
class ReadingSet(ReadingSetBase):
    """
    A set of Readings of the ReadingType indicated by the parent MeterReading.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    reading_list_link: Optional[ReadingListLink] = field(
        default=None,
        metadata={
            "name": "ReadingListLink",
            "type": "Element",
        }
    )


@dataclass
class ResponseSet(IdentifiedObject):
    """
    A container for a ResponseList.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    response_list_link: Optional[ResponseListLink] = field(
        default=None,
        metadata={
            "name": "ResponseListLink",
            "type": "Element",
        }
    )


@dataclass
class ServiceSupplierList(ListType):
    """
    A List element to hold ServiceSupplier objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    service_supplier: List[ServiceSupplier] = field(
        default_factory=list,
        metadata={
            "name": "ServiceSupplier",
            "type": "Element",
        }
    )


@dataclass
class SubscriptionList(ListType):
    """
    A List element to hold Subscription objects.

    :ivar subscription:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    subscription: List[Subscription] = field(
        default_factory=list,
        metadata={
            "name": "Subscription",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class TariffProfile(IdentifiedObject):
    """
    A schedule of charges; structure that allows the definition of tariff
    structures such as step (block) and time of use (tier) when used in
    conjunction with TimeTariffInterval and ConsumptionTariffInterval.

    :ivar currency: The currency code indicating the currency for this
        TariffProfile.
    :ivar price_power_of_ten_multiplier: Indicates the power of ten
        multiplier for the price attribute.
    :ivar primacy: Indicates the relative primacy of the provider of
        this program.
    :ivar rate_code: The rate code for this tariff profile.  Provided by
        the Pricing service provider per its internal business needs and
        practices and provides a method to identify the specific rate
        code for the TariffProfile instance.  This would typically not
        be communicated to the user except to facilitate troubleshooting
        due to its service provider-specific technical nature.
    :ivar rate_component_list_link:
    :ivar service_category_kind: The kind of service provided by this
        usage point.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    currency: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    price_power_of_ten_multiplier: Optional[int] = field(
        default=None,
        metadata={
            "name": "pricePowerOfTenMultiplier",
            "type": "Element",
        }
    )
    primacy: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    rate_code: Optional[str] = field(
        default=None,
        metadata={
            "name": "rateCode",
            "type": "Element",
            "max_length": 20,
        }
    )
    rate_component_list_link: Optional[RateComponentListLink] = field(
        default=None,
        metadata={
            "name": "RateComponentListLink",
            "type": "Element",
        }
    )
    service_category_kind: Optional[int] = field(
        default=None,
        metadata={
            "name": "serviceCategoryKind",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class UsagePoint(UsagePointBase):
    """
    Logical point on a network at which consumption or production is either
    physically measured (e.g. metered) or estimated (e.g. unmetered street
    lights).

    :ivar device_lfdi: The LFDI of the source device. This attribute
        SHALL be present when mirroring.
    :ivar meter_reading_list_link:
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    device_lfdi: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "deviceLFDI",
            "type": "Element",
            "max_length": 20,
            "format": "base16",
        }
    )
    meter_reading_list_link: Optional[MeterReadingListLink] = field(
        default=None,
        metadata={
            "name": "MeterReadingListLink",
            "type": "Element",
        }
    )


@dataclass
class BillingReadingSetList(SubscribableList):
    """
    A List element to hold BillingReadingSet objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    billing_reading_set: List[BillingReadingSet] = field(
        default_factory=list,
        metadata={
            "name": "BillingReadingSet",
            "type": "Element",
        }
    )


@dataclass
class CustomerAccountList(SubscribableList):
    """
    A List element to hold CustomerAccount objects.

    :ivar customer_account:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    customer_account: List[CustomerAccount] = field(
        default_factory=list,
        metadata={
            "name": "CustomerAccount",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class CustomerAgreementList(SubscribableList):
    """
    A List element to hold CustomerAgreement objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    customer_agreement: List[CustomerAgreement] = field(
        default_factory=list,
        metadata={
            "name": "CustomerAgreement",
            "type": "Element",
        }
    )


@dataclass
class Derlist(ListType):
    """
    A List element to hold DER objects.

    :ivar der:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        name = "DERList"
        namespace = "urn:ieee:std:2030.5:ns"

    der: List[Der] = field(
        default_factory=list,
        metadata={
            "name": "DER",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class DerprogramList(SubscribableList):
    """
    A List element to hold DERProgram objects.

    :ivar derprogram:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        name = "DERProgramList"
        namespace = "urn:ieee:std:2030.5:ns"

    derprogram: List[Derprogram] = field(
        default_factory=list,
        metadata={
            "name": "DERProgram",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class DemandResponseProgramList(SubscribableList):
    """
    A List element to hold DemandResponseProgram objects.

    :ivar demand_response_program:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    demand_response_program: List[DemandResponseProgram] = field(
        default_factory=list,
        metadata={
            "name": "DemandResponseProgram",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class DeviceCapability(FunctionSetAssignmentsBase):
    """
    Returned by the URI provided by DNS-SD, to allow clients to find the URIs
    to the resources in which they are interested.

    :ivar end_device_list_link:
    :ivar mirror_usage_point_list_link:
    :ivar self_device_link:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    end_device_list_link: Optional[EndDeviceListLink] = field(
        default=None,
        metadata={
            "name": "EndDeviceListLink",
            "type": "Element",
        }
    )
    mirror_usage_point_list_link: Optional[MirrorUsagePointListLink] = field(
        default=None,
        metadata={
            "name": "MirrorUsagePointListLink",
            "type": "Element",
        }
    )
    self_device_link: Optional[SelfDeviceLink] = field(
        default=None,
        metadata={
            "name": "SelfDeviceLink",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class EndDevice(AbstractDevice):
    """Asset container that performs one or more end device functions.

    Contains information about individual devices in the network.

    :ivar changed_time: The time at which this resource was last
        modified or created.
    :ivar enabled: This attribute indicates whether or not an EndDevice
        is enabled, or registered, on the server. If a server sets this
        attribute to false, the device is no longer registered. It
        should be noted that servers can delete EndDevice instances, but
        using this attribute for some time is more convenient for
        clients.
    :ivar flow_reservation_request_list_link:
    :ivar flow_reservation_response_list_link:
    :ivar function_set_assignments_list_link:
    :ivar post_rate: POST rate, or how often EndDevice and subordinate
        resources should be POSTed, in seconds. A client MAY indicate a
        preferred postRate when POSTing EndDevice. A server MAY add or
        modify postRate to indicate its preferred posting rate.
    :ivar registration_link:
    :ivar subscription_list_link:
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    changed_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "changedTime",
            "type": "Element",
            "required": True,
        }
    )
    enabled: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    flow_reservation_request_list_link: Optional[FlowReservationRequestListLink] = field(
        default=None,
        metadata={
            "name": "FlowReservationRequestListLink",
            "type": "Element",
        }
    )
    flow_reservation_response_list_link: Optional[FlowReservationResponseListLink] = field(
        default=None,
        metadata={
            "name": "FlowReservationResponseListLink",
            "type": "Element",
        }
    )
    function_set_assignments_list_link: Optional[FunctionSetAssignmentsListLink] = field(
        default=None,
        metadata={
            "name": "FunctionSetAssignmentsListLink",
            "type": "Element",
        }
    )
    post_rate: Optional[int] = field(
        default=None,
        metadata={
            "name": "postRate",
            "type": "Element",
        }
    )
    registration_link: Optional[RegistrationLink] = field(
        default=None,
        metadata={
            "name": "RegistrationLink",
            "type": "Element",
        }
    )
    subscription_list_link: Optional[SubscriptionListLink] = field(
        default=None,
        metadata={
            "name": "SubscriptionListLink",
            "type": "Element",
        }
    )


@dataclass
class FlowReservationResponse(Event):
    """
    The server may modify the charging or discharging parameters and interval
    to provide a lower aggregated demand at the premises, or within a larger
    part of the distribution system.

    :ivar energy_available: Indicates the amount of energy available.
    :ivar power_available: Indicates the amount of power available.
    :ivar subject: The subject field provides a method to match the
        response with the originating event. It is populated with the
        mRID of the corresponding FlowReservationRequest object.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    energy_available: Optional[SignedRealEnergy] = field(
        default=None,
        metadata={
            "name": "energyAvailable",
            "type": "Element",
            "required": True,
        }
    )
    power_available: Optional[ActivePower] = field(
        default=None,
        metadata={
            "name": "powerAvailable",
            "type": "Element",
            "required": True,
        }
    )
    subject: Optional[bytes] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 16,
            "format": "base16",
        }
    )


@dataclass
class FunctionSetAssignments(FunctionSetAssignmentsBase):
    """
    Provides an identifiable, subscribable collection of resources for a
    particular device to consume.

    :ivar m_rid: The global identifier of the object.
    :ivar description: The description is a human readable text
        describing or naming the object.
    :ivar version: Contains the version number of the object. See the
        type definition for details.
    :ivar subscribable: Indicates whether or not subscriptions are
        supported for this resource, and whether or not conditional
        (thresholds) are supported. If not specified, is "not
        subscribable" (0).
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    m_rid: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "mRID",
            "type": "Element",
            "required": True,
            "max_length": 16,
            "format": "base16",
        }
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 32,
        }
    )
    version: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
        }
    )
    subscribable: int = field(
        default=0,
        metadata={
            "type": "Attribute",
        }
    )


@dataclass
class HistoricalReading(BillingMeterReadingBase):
    """To be used to present readings that have been processed and possibly
    corrected (as allowed, due to missing or incorrect data) by backend
    systems.

    This includes quality codes valid, verified, estimated, and derived
    / corrected.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class IpaddrList(ListType):
    """
    List of IPAddr instances.
    """
    class Meta:
        name = "IPAddrList"
        namespace = "urn:ieee:std:2030.5:ns"

    ipaddr: List[Ipaddr] = field(
        default_factory=list,
        metadata={
            "name": "IPAddr",
            "type": "Element",
        }
    )


@dataclass
class IpinterfaceList(ListType):
    """
    List of IPInterface instances.

    :ivar ipinterface:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        name = "IPInterfaceList"
        namespace = "urn:ieee:std:2030.5:ns"

    ipinterface: List[Ipinterface] = field(
        default_factory=list,
        metadata={
            "name": "IPInterface",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class Llinterface(Resource):
    """
    A link-layer interface object.

    :ivar crcerrors: Contains the number of CRC errors since reset.
    :ivar eui64: Contains the EUI-64 of the link layer interface. 48 bit
        MAC addresses SHALL be changed into an EUI-64 using the method
        defined in [RFC 4291], Appendix A. (The method is to insert
        "0xFFFE" as described in the reference.)
    :ivar ieee_802_15_4:
    :ivar link_layer_type: Specifies the type of link layer interface
        associated with the IPInterface. Values are below. 0 =
        Unspecified 1 = IEEE 802.3 (Ethernet) 2 = IEEE 802.11 (WLAN) 3 =
        IEEE 802.15 (PAN) 4 = IEEE 1901 (PLC) All other values reserved.
    :ivar llack_not_rx: Number of times an ACK was not received for a
        frame transmitted (when ACK was requested).
    :ivar llcsmafail: Number of times CSMA failed.
    :ivar llframes_drop_rx: Number of dropped receive frames.
    :ivar llframes_drop_tx: Number of dropped transmit frames.
    :ivar llframes_rx: Number of link layer frames received.
    :ivar llframes_tx: Number of link layer frames transmitted.
    :ivar llmedia_access_fail: Number of times access to media failed.
    :ivar lloctets_rx: Number of Bytes received.
    :ivar lloctets_tx: Number of Bytes transmitted.
    :ivar llretry_count: Number of MAC transmit retries.
    :ivar llsecurity_error_rx: Number of receive security errors.
    :ivar lo_wpan:
    """
    class Meta:
        name = "LLInterface"
        namespace = "urn:ieee:std:2030.5:ns"

    crcerrors: Optional[int] = field(
        default=None,
        metadata={
            "name": "CRCerrors",
            "type": "Element",
            "required": True,
        }
    )
    eui64: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "EUI64",
            "type": "Element",
            "required": True,
            "max_length": 8,
            "format": "base16",
        }
    )
    ieee_802_15_4: Optional[Ieee802154] = field(
        default=None,
        metadata={
            "name": "IEEE_802_15_4",
            "type": "Element",
        }
    )
    link_layer_type: Optional[int] = field(
        default=None,
        metadata={
            "name": "linkLayerType",
            "type": "Element",
            "required": True,
        }
    )
    llack_not_rx: Optional[int] = field(
        default=None,
        metadata={
            "name": "LLAckNotRx",
            "type": "Element",
        }
    )
    llcsmafail: Optional[int] = field(
        default=None,
        metadata={
            "name": "LLCSMAFail",
            "type": "Element",
        }
    )
    llframes_drop_rx: Optional[int] = field(
        default=None,
        metadata={
            "name": "LLFramesDropRx",
            "type": "Element",
        }
    )
    llframes_drop_tx: Optional[int] = field(
        default=None,
        metadata={
            "name": "LLFramesDropTx",
            "type": "Element",
        }
    )
    llframes_rx: Optional[int] = field(
        default=None,
        metadata={
            "name": "LLFramesRx",
            "type": "Element",
        }
    )
    llframes_tx: Optional[int] = field(
        default=None,
        metadata={
            "name": "LLFramesTx",
            "type": "Element",
        }
    )
    llmedia_access_fail: Optional[int] = field(
        default=None,
        metadata={
            "name": "LLMediaAccessFail",
            "type": "Element",
        }
    )
    lloctets_rx: Optional[int] = field(
        default=None,
        metadata={
            "name": "LLOctetsRx",
            "type": "Element",
        }
    )
    lloctets_tx: Optional[int] = field(
        default=None,
        metadata={
            "name": "LLOctetsTx",
            "type": "Element",
        }
    )
    llretry_count: Optional[int] = field(
        default=None,
        metadata={
            "name": "LLRetryCount",
            "type": "Element",
        }
    )
    llsecurity_error_rx: Optional[int] = field(
        default=None,
        metadata={
            "name": "LLSecurityErrorRx",
            "type": "Element",
        }
    )
    lo_wpan: Optional[LoWpan] = field(
        default=None,
        metadata={
            "name": "loWPAN",
            "type": "Element",
        }
    )


@dataclass
class MessagingProgramList(SubscribableList):
    """
    A List element to hold MessagingProgram objects.

    :ivar messaging_program:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    messaging_program: List[MessagingProgram] = field(
        default_factory=list,
        metadata={
            "name": "MessagingProgram",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class MeterReadingList(SubscribableList):
    """
    A List element to hold MeterReading objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    meter_reading: List[MeterReading] = field(
        default_factory=list,
        metadata={
            "name": "MeterReading",
            "type": "Element",
        }
    )


@dataclass
class MirrorMeterReading(MeterReadingBase):
    """
    Mimic of MeterReading used for managing mirrors.

    :ivar last_update_time: The date and time of the last update.
    :ivar mirror_reading_set:
    :ivar next_update_time: The date and time of the next planned
        update.
    :ivar reading:
    :ivar reading_type:
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    last_update_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "lastUpdateTime",
            "type": "Element",
        }
    )
    mirror_reading_set: List[MirrorReadingSet] = field(
        default_factory=list,
        metadata={
            "name": "MirrorReadingSet",
            "type": "Element",
        }
    )
    next_update_time: Optional[int] = field(
        default=None,
        metadata={
            "name": "nextUpdateTime",
            "type": "Element",
        }
    )
    reading: Optional[Reading] = field(
        default=None,
        metadata={
            "name": "Reading",
            "type": "Element",
        }
    )
    reading_type: Optional[ReadingType] = field(
        default=None,
        metadata={
            "name": "ReadingType",
            "type": "Element",
        }
    )


@dataclass
class Prepayment(IdentifiedObject):
    """
    Prepayment (inherited from CIM SDPAccountingFunction)

    :ivar account_balance_link:
    :ivar active_credit_register_list_link:
    :ivar active_supply_interruption_override_list_link:
    :ivar credit_expiry_level: CreditExpiryLevel is the set point for
        availableCredit at which the service level may be changed. The
        typical value for this attribute is 0, regardless of whether the
        account balance is measured in a monetary or commodity basis.
        The units for this attribute SHALL match the units used for
        availableCredit.
    :ivar credit_register_list_link:
    :ivar low_credit_warning_level: LowCreditWarningLevel is the set
        point for availableCredit at which the creditStatus attribute in
        the AccountBalance resource SHALL indicate that available credit
        is low. The units for this attribute SHALL match the units used
        for availableCredit. Typically, this value is set by the service
        provider.
    :ivar low_emergency_credit_warning_level:
        LowEmergencyCreditWarningLevel is the set point for
        emergencyCredit at which the creditStatus attribute in the
        AccountBalance resource SHALL indicate that emergencycredit is
        low. The units for this attribute SHALL match the units used for
        availableCredit. Typically, this value is set by the service
        provider.
    :ivar prepay_mode: PrepayMode specifies whether the given Prepayment
        instance is operating in Credit, Central Wallet, ESI, or Local
        prepayment mode. The Credit mode indicates that prepayment is
        not presently in effect. The other modes are described in the
        Overview Section above.
    :ivar prepay_operation_status_link:
    :ivar supply_interruption_override_list_link:
    :ivar usage_point:
    :ivar usage_point_link:
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    account_balance_link: Optional[AccountBalanceLink] = field(
        default=None,
        metadata={
            "name": "AccountBalanceLink",
            "type": "Element",
            "required": True,
        }
    )
    active_credit_register_list_link: Optional[ActiveCreditRegisterListLink] = field(
        default=None,
        metadata={
            "name": "ActiveCreditRegisterListLink",
            "type": "Element",
        }
    )
    active_supply_interruption_override_list_link: Optional[ActiveSupplyInterruptionOverrideListLink] = field(
        default=None,
        metadata={
            "name": "ActiveSupplyInterruptionOverrideListLink",
            "type": "Element",
        }
    )
    credit_expiry_level: Optional[AccountingUnit] = field(
        default=None,
        metadata={
            "name": "creditExpiryLevel",
            "type": "Element",
        }
    )
    credit_register_list_link: Optional[CreditRegisterListLink] = field(
        default=None,
        metadata={
            "name": "CreditRegisterListLink",
            "type": "Element",
            "required": True,
        }
    )
    low_credit_warning_level: Optional[AccountingUnit] = field(
        default=None,
        metadata={
            "name": "lowCreditWarningLevel",
            "type": "Element",
        }
    )
    low_emergency_credit_warning_level: Optional[AccountingUnit] = field(
        default=None,
        metadata={
            "name": "lowEmergencyCreditWarningLevel",
            "type": "Element",
        }
    )
    prepay_mode: Optional[int] = field(
        default=None,
        metadata={
            "name": "prepayMode",
            "type": "Element",
            "required": True,
        }
    )
    prepay_operation_status_link: Optional[PrepayOperationStatusLink] = field(
        default=None,
        metadata={
            "name": "PrepayOperationStatusLink",
            "type": "Element",
            "required": True,
        }
    )
    supply_interruption_override_list_link: Optional[SupplyInterruptionOverrideListLink] = field(
        default=None,
        metadata={
            "name": "SupplyInterruptionOverrideListLink",
            "type": "Element",
            "required": True,
        }
    )
    usage_point: List[UsagePoint] = field(
        default_factory=list,
        metadata={
            "name": "UsagePoint",
            "type": "Element",
        }
    )
    usage_point_link: Optional[UsagePointLink] = field(
        default=None,
        metadata={
            "name": "UsagePointLink",
            "type": "Element",
        }
    )


@dataclass
class ProjectionReading(BillingMeterReadingBase):
    """
    Contains values that forecast a future reading for the time or interval
    specified.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class RplinstanceList(ListType):
    """
    List of RPLInstances associated with the IPinterface.
    """
    class Meta:
        name = "RPLInstanceList"
        namespace = "urn:ieee:std:2030.5:ns"

    rplinstance: List[Rplinstance] = field(
        default_factory=list,
        metadata={
            "name": "RPLInstance",
            "type": "Element",
        }
    )


@dataclass
class RandomizableEvent(Event):
    """
    An Event that can indicate time ranges over which the start time and
    duration SHALL be randomized.

    :ivar randomize_duration: Number of seconds boundary inside which a
        random value must be selected to be applied to the associated
        interval duration, to avoid sudden synchronized demand changes.
        If related to price level changes, sign may be ignored. Valid
        range is -3600 to 3600. If not specified, 0 is the default.
    :ivar randomize_start: Number of seconds boundary inside which a
        random value must be selected to be applied to the associated
        interval start time, to avoid sudden synchronized demand
        changes. If related to price level changes, sign may be ignored.
        Valid range is -3600 to 3600. If not specified, 0 is the
        default.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    randomize_duration: Optional[int] = field(
        default=None,
        metadata={
            "name": "randomizeDuration",
            "type": "Element",
        }
    )
    randomize_start: Optional[int] = field(
        default=None,
        metadata={
            "name": "randomizeStart",
            "type": "Element",
        }
    )


@dataclass
class RateComponentList(ListType):
    """
    A List element to hold RateComponent objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    rate_component: List[RateComponent] = field(
        default_factory=list,
        metadata={
            "name": "RateComponent",
            "type": "Element",
        }
    )


@dataclass
class ReadingSetList(SubscribableList):
    """
    A List element to hold ReadingSet objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    reading_set: List[ReadingSet] = field(
        default_factory=list,
        metadata={
            "name": "ReadingSet",
            "type": "Element",
        }
    )


@dataclass
class ResponseSetList(ListType):
    """
    A List element to hold ResponseSet objects.

    :ivar response_set:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    response_set: List[ResponseSet] = field(
        default_factory=list,
        metadata={
            "name": "ResponseSet",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class SelfDevice(AbstractDevice):
    """
    The EndDevice providing the resources available within the
    DeviceCapabilities.

    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class TargetReading(BillingMeterReadingBase):
    """
    Contains readings that specify a target or goal, such as a consumption
    target, to which billing incentives or other contractual ramifications may
    be associated.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class TariffProfileList(SubscribableList):
    """
    A List element to hold TariffProfile objects.

    :ivar tariff_profile:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    tariff_profile: List[TariffProfile] = field(
        default_factory=list,
        metadata={
            "name": "TariffProfile",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class TextMessage(Event):
    """
    Text message such as a notification.

    :ivar originator: Indicates the human-readable name of the publisher
        of the message
    :ivar priority: The priority is used to inform the client of the
        priority of the particular message.  Devices with constrained or
        limited resources for displaying Messages should use this
        attribute to determine how to handle displaying currently active
        Messages (e.g. if a device uses a scrolling method with a single
        Message viewable at a time it MAY want to push a low priority
        Message to the background and bring a newly received higher
        priority Message to the foreground).
    :ivar text_message: The textMessage attribute contains the actual
        UTF-8 encoded text to be displayed in conjunction with the
        messageLength attribute which contains the overall length of the
        textMessage attribute.  Clients and servers SHALL support a
        reception of a Message of 100 bytes in length.  Messages that
        exceed the clients display size will be left to the client to
        choose what method to handle the message (truncation, scrolling,
        etc.).
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    originator: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 20,
        }
    )
    priority: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )
    text_message: Optional[str] = field(
        default=None,
        metadata={
            "name": "textMessage",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class UsagePointList(SubscribableList):
    """
    A List element to hold UsagePoint objects.

    :ivar usage_point:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    usage_point: List[UsagePoint] = field(
        default_factory=list,
        metadata={
            "name": "UsagePoint",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class Dercontrol(RandomizableEvent):
    """
    Distributed Energy Resource (DER) time/event-based control.

    :ivar dercontrol_base:
    :ivar device_category: Specifies the bitmap indicating  the
        categories of devices that SHOULD respond. Devices SHOULD ignore
        events that do not indicate their device category. If not
        present, all devices SHOULD respond.
    """
    class Meta:
        name = "DERControl"
        namespace = "urn:ieee:std:2030.5:ns"

    dercontrol_base: Optional[DercontrolBase] = field(
        default=None,
        metadata={
            "name": "DERControlBase",
            "type": "Element",
            "required": True,
        }
    )
    device_category: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "deviceCategory",
            "type": "Element",
            "max_length": 4,
            "format": "base16",
        }
    )


@dataclass
class EndDeviceControl(RandomizableEvent):
    """
    Instructs an EndDevice to perform a specified action.

    :ivar appliance_load_reduction:
    :ivar device_category: Specifies the bitmap indicating  the
        categories of devices that SHOULD respond. Devices SHOULD ignore
        events that do not indicate their device category.
    :ivar dr_program_mandatory: A flag to indicate if the
        EndDeviceControl is considered a mandatory event as defined by
        the service provider issuing the EndDeviceControl. The
        drProgramMandatory flag alerts the client/user that they will be
        subject to penalty or ineligibility based on the service
        provider’s program rules for that deviceCategory.
    :ivar duty_cycle:
    :ivar load_shift_forward: Indicates that the event intends to
        increase consumption. A value of true indicates the intention to
        increase usage value, and a value of false indicates the
        intention to decrease usage.
    :ivar offset:
    :ivar override_duration: The overrideDuration attribute provides a
        duration, in seconds, for which a client device is allowed to
        override this EndDeviceControl and still meet the contractual
        agreement with a service provider without opting out. If
        overrideDuration is not specified, then it SHALL default to 0.
    :ivar set_point:
    :ivar target_reduction:
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    appliance_load_reduction: Optional[ApplianceLoadReduction] = field(
        default=None,
        metadata={
            "name": "ApplianceLoadReduction",
            "type": "Element",
        }
    )
    device_category: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "deviceCategory",
            "type": "Element",
            "required": True,
            "max_length": 4,
            "format": "base16",
        }
    )
    dr_program_mandatory: Optional[bool] = field(
        default=None,
        metadata={
            "name": "drProgramMandatory",
            "type": "Element",
            "required": True,
        }
    )
    duty_cycle: Optional[DutyCycle] = field(
        default=None,
        metadata={
            "name": "DutyCycle",
            "type": "Element",
        }
    )
    load_shift_forward: Optional[bool] = field(
        default=None,
        metadata={
            "name": "loadShiftForward",
            "type": "Element",
            "required": True,
        }
    )
    offset: Optional[Offset] = field(
        default=None,
        metadata={
            "name": "Offset",
            "type": "Element",
        }
    )
    override_duration: Optional[int] = field(
        default=None,
        metadata={
            "name": "overrideDuration",
            "type": "Element",
        }
    )
    set_point: Optional[SetPoint] = field(
        default=None,
        metadata={
            "name": "SetPoint",
            "type": "Element",
        }
    )
    target_reduction: Optional[TargetReduction] = field(
        default=None,
        metadata={
            "name": "TargetReduction",
            "type": "Element",
        }
    )


@dataclass
class EndDeviceList(SubscribableList):
    """
    A List element to hold EndDevice objects.

    :ivar end_device:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    end_device: List[EndDevice] = field(
        default_factory=list,
        metadata={
            "name": "EndDevice",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class FlowReservationResponseList(SubscribableList):
    """
    A List element to hold FlowReservationResponse objects.

    :ivar flow_reservation_response:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    flow_reservation_response: List[FlowReservationResponse] = field(
        default_factory=list,
        metadata={
            "name": "FlowReservationResponse",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class FunctionSetAssignmentsList(SubscribableList):
    """
    A List element to hold FunctionSetAssignments objects.

    :ivar function_set_assignments:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    function_set_assignments: List[FunctionSetAssignments] = field(
        default_factory=list,
        metadata={
            "name": "FunctionSetAssignments",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class HistoricalReadingList(ListType):
    """
    A List element to hold HistoricalReading objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    historical_reading: List[HistoricalReading] = field(
        default_factory=list,
        metadata={
            "name": "HistoricalReading",
            "type": "Element",
        }
    )


@dataclass
class LlinterfaceList(ListType):
    """
    List of LLInterface instances.
    """
    class Meta:
        name = "LLInterfaceList"
        namespace = "urn:ieee:std:2030.5:ns"

    llinterface: List[Llinterface] = field(
        default_factory=list,
        metadata={
            "name": "LLInterface",
            "type": "Element",
        }
    )


@dataclass
class MirrorMeterReadingList(ListType):
    """
    A List of MirrorMeterReading instances.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    mirror_meter_reading: List[MirrorMeterReading] = field(
        default_factory=list,
        metadata={
            "name": "MirrorMeterReading",
            "type": "Element",
        }
    )


@dataclass
class MirrorUsagePoint(UsagePointBase):
    """
    A parallel to UsagePoint to support mirroring.

    :ivar device_lfdi: The LFDI of the device being mirrored.
    :ivar mirror_meter_reading:
    :ivar post_rate: POST rate, or how often mirrored data should be
        POSTed, in seconds. A client MAY indicate a preferred postRate
        when POSTing MirrorUsagePoint. A server MAY add or modify
        postRate to indicate its preferred posting rate.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    device_lfdi: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "deviceLFDI",
            "type": "Element",
            "required": True,
            "max_length": 20,
            "format": "base16",
        }
    )
    mirror_meter_reading: List[MirrorMeterReading] = field(
        default_factory=list,
        metadata={
            "name": "MirrorMeterReading",
            "type": "Element",
        }
    )
    post_rate: Optional[int] = field(
        default=None,
        metadata={
            "name": "postRate",
            "type": "Element",
        }
    )


@dataclass
class PrepaymentList(SubscribableList):
    """
    A List element to hold Prepayment objects.

    :ivar prepayment:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    prepayment: List[Prepayment] = field(
        default_factory=list,
        metadata={
            "name": "Prepayment",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class ProjectionReadingList(ListType):
    """
    A List element to hold ProjectionReading objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    projection_reading: List[ProjectionReading] = field(
        default_factory=list,
        metadata={
            "name": "ProjectionReading",
            "type": "Element",
        }
    )


@dataclass
class TargetReadingList(ListType):
    """
    A List element to hold TargetReading objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    target_reading: List[TargetReading] = field(
        default_factory=list,
        metadata={
            "name": "TargetReading",
            "type": "Element",
        }
    )


@dataclass
class TextMessageList(SubscribableList):
    """
    A List element to hold TextMessage objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    text_message: List[TextMessage] = field(
        default_factory=list,
        metadata={
            "name": "TextMessage",
            "type": "Element",
        }
    )


@dataclass
class TimeTariffInterval(RandomizableEvent):
    """
    Describes the time-differentiated portion of the RateComponent, if
    applicable, and provides the ability to specify multiple time intervals,
    each with its own consumption-based components and other attributes.

    :ivar consumption_tariff_interval_list_link:
    :ivar tou_tier: Indicates the time of use tier related to the
        reading. If not specified, is assumed to be "0 - N/A".
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    consumption_tariff_interval_list_link: Optional[ConsumptionTariffIntervalListLink] = field(
        default=None,
        metadata={
            "name": "ConsumptionTariffIntervalListLink",
            "type": "Element",
        }
    )
    tou_tier: Optional[int] = field(
        default=None,
        metadata={
            "name": "touTier",
            "type": "Element",
            "required": True,
        }
    )


@dataclass
class DercontrolList(SubscribableList):
    """
    A List element to hold DERControl objects.
    """
    class Meta:
        name = "DERControlList"
        namespace = "urn:ieee:std:2030.5:ns"

    dercontrol: List[Dercontrol] = field(
        default_factory=list,
        metadata={
            "name": "DERControl",
            "type": "Element",
        }
    )


@dataclass
class EndDeviceControlList(SubscribableList):
    """
    A List element to hold EndDeviceControl objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    end_device_control: List[EndDeviceControl] = field(
        default_factory=list,
        metadata={
            "name": "EndDeviceControl",
            "type": "Element",
        }
    )


@dataclass
class MirrorUsagePointList(ListType):
    """
    A List of MirrorUsagePoint instances.

    :ivar mirror_usage_point:
    :ivar poll_rate: The default polling rate for this function set
        (this resource and all resources below), in seconds. If not
        specified, a default of 900 seconds (15 minutes) is used. It is
        RECOMMENDED a client poll the resources of this function set
        every pollRate seconds.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    mirror_usage_point: List[MirrorUsagePoint] = field(
        default_factory=list,
        metadata={
            "name": "MirrorUsagePoint",
            "type": "Element",
        }
    )
    poll_rate: int = field(
        default=900,
        metadata={
            "name": "pollRate",
            "type": "Attribute",
        }
    )


@dataclass
class TimeTariffIntervalList(SubscribableList):
    """
    A List element to hold TimeTariffInterval objects.
    """
    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    time_tariff_interval: List[TimeTariffInterval] = field(
        default_factory=list,
        metadata={
            "name": "TimeTariffInterval",
            "type": "Element",
        }
    )
