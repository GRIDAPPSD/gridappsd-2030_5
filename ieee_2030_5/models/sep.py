from __future__ import annotations

from dataclasses import dataclass, field

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

    multiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    multiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    multiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    type: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    type: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    description: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 20,
        },
    )
    kind: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class Condition:
    """
    Indicates a condition that must be satisfied for the Notification to be
    triggered.

    :ivar attributeIdentifier: 0 = Reading value 1-255 = Reserved
    :ivar lowerThreshold: The value of the lower threshold
    :ivar upperThreshold: The value of the upper threshold
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    attributeIdentifier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    lowerThreshold: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "min_inclusive": -140737488355328,
            "max_inclusive": 140737488355328,
        },
    )
    upperThreshold: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "min_inclusive": -140737488355328,
            "max_inclusive": 140737488355328,
        },
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

    :ivar dateTime: The date and time at which the state applied.
    :ivar value: The value indicating the state.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    dateTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 1,
            "format": "base16",
        },
    )


@dataclass
class CreditTypeChange:
    """
    Specifies a change to the credit type.

    :ivar newType: The new credit type, to take effect at the time
        specified by startTime
    :ivar startTime: The date/time when the change is to take effect.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    newType: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    startTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class CurrentRMS:
    """
    Average flow of charge through a conductor.

    :ivar multiplier: Specifies exponent of value.
    :ivar value: Value in amperes RMS (uom 5)
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    multiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    excitation: bool | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    xvalue: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    yvalue: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    duration: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    start: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    :ivar normalValue: Contains the maximum On state duty cycle applied
        by the end device, as a percentage of time.  The field not
        present indicates that this field has not been used by the end
        device.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    normalValue: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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
    :ivar costKind: The kind of cost referred to in the amount.
    :ivar costLevel: The relative level of the amount attribute.  In
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
    :ivar numCostLevels: The number of all relative cost levels. In
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

    amount: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    costKind: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    costLevel: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    numCostLevels: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class Error:
    """
    Contains information about the nature of an error if a request could not be
    completed successfully.

    :ivar maxRetryDuration: Contains the number of seconds the client
        SHOULD wait before retrying the request.
    :ivar reasonCode: Code indicating the reason for failure. 0 -
        Invalid request format 1 - Invalid request values (e.g. invalid
        threshold values) 2 - Resource limit reached 3 - Conditional
        subscription field not supported 4 - Maximum request frequency
        exceeded All other values reserved
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    maxRetryDuration: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    reasonCode: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class EventStatus:
    """Current status information relevant to a specific object.

    The Status object is used to indicate the current status of an
    Event. Devices can read the containing resource (e.g. TextMessage)
    to get the most up to date status of the event.  Devices can also
    subscribe to a specific resource instance to get updates when any of
    its attributes change, including the Status object.

    :ivar currentStatus: Field representing the current status type. 0 =
        Scheduled This status indicates that the event has been
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
    :ivar dateTime: The dateTime attribute will provide a timestamp of
        when the current status was defined. dateTime MUST be set to the
        time at which the status change occurred, not a time in the
        future or past.
    :ivar potentiallySuperseded: Set to true by a server of this event
        if there are events that overlap this event in time and also
        overlap in some, but not all, deviceCategory's (if applicable)
        AND DERControl controls (e.g., opModTargetW) (if applicable) in
        the same function set instance.
    :ivar potentiallySupersededTime: Indicates the time that the
        potentiallySuperseded flag was set.
    :ivar reason: The Reason attribute allows a Service provider to
        provide a textual explanation of the status.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    currentStatus: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    dateTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    potentiallySuperseded: bool | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    potentiallySupersededTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    reason: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 192,
        },
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

    multiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class FixedVar:
    """
    Specifies a signed setpoint for reactive power.

    :ivar refType: Indicates whether to interpret 'value' as %setMaxVar
        or %statVarAvail.
    :ivar value: Specify a signed setpoint for reactive power in % (see
        'refType' for context).
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    refType: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class FreqDroopType:
    """
    Type for Frequency-Droop (Frequency-Watt) operation.

    :ivar dBOF: Frequency droop dead band for over-frequency conditions.
        In thousandths of Hz.
    :ivar dBUF: Frequency droop dead band for under-frequency
        conditions. In thousandths of Hz.
    :ivar kOF: Frequency droop per-unit frequency change for over-
        frequency conditions corresponding to 1 per-unit power output
        change. In thousandths, unitless.
    :ivar kUF: Frequency droop per-unit frequency change for under-
        frequency conditions corresponding to 1 per-unit power output
        change. In thousandths, unitless.
    :ivar openLoopTms: Open loop response time, the duration from a step
        change in control signal input until the output changes by 90%
        of its final change before any overshoot, in hundredths of a
        second. Resolution is 1/100 sec. A value of 0 is used to mean no
        limit.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    dBOF: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    dBUF: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    kOF: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    kUF: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    openLoopTms: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class GPSLocationType:
    """
    Specifies a GPS location, expressed in WGS 84 coordinates.

    :ivar lat: Specifies the latitude from equator. -90 (south) to +90
        (north) in decimal degrees.
    :ivar lon: Specifies the longitude from Greenwich Meridian. -180
        (west) to +180 (east) in decimal degrees.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    lat: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 32,
        },
    )
    lon: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 32,
        },
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

    :ivar dateTime: The date and time at which the state applied.
    :ivar value: The value indicating the state.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    dateTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class Link:
    """
    Links provide a reference, via URI, to another resource.

    :ivar href: A URI reference.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    href: str | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class LocalControlModeStatusType:
    """DER LocalControlModeStatus/value:

    0 – local control 1 – remote control All other values reserved.

    :ivar dateTime: The date and time at which the state applied.
    :ivar value: The value indicating the state.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    dateTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class ManufacturerStatusType:
    """
    DER ManufacturerStatus/value: String data type.

    :ivar dateTime: The date and time at which the state applied.
    :ivar value: The value indicating the state.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    dateTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 6,
        },
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

    :ivar coolingOffset: The value change requested for the cooling
        offset, in degree C / 10. The value should be added to the
        normal set point for cooling, or if loadShiftForward is true,
        then the value should be subtracted from the normal set point.
    :ivar heatingOffset: The value change requested for the heating
        offset, in degree C / 10. The value should be subtracted for
        heating, or if loadShiftForward is true, then the value should
        be added to the normal set point.
    :ivar loadAdjustmentPercentageOffset: The value change requested for
        the load adjustment percentage. The value should be subtracted
        from the normal setting, or if loadShiftForward is true, then
        the value should be added to the normal setting.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    coolingOffset: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    heatingOffset: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    loadAdjustmentPercentageOffset: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class OperationalModeStatusType:
    """DER OperationalModeStatus value:

    0 - Not applicable / Unknown
    1 - Off
    2 - Operational mode
    3 - Test mode
    All other values reserved.

    :ivar dateTime: The date and time at which the state applied.
    :ivar value: The value indicating the state.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    dateTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class PowerConfiguration:
    """
    Contains configuration related to the device's power sources.

    :ivar batteryInstallTime: Time/Date at which battery was installed,
    :ivar lowChargeThreshold: In context of the PowerStatus resource,
        this is the value of EstimatedTimeRemaining below which
        BatteryStatus "low" is indicated and the PS_LOW_BATTERY is
        raised.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    batteryInstallTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    lowChargeThreshold: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
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

    displacement: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    multiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    displacement: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    excitation: bool | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    multiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    multiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    multiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    multiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_inclusive": 281474976710655,
        },
    )


@dataclass
class RequestStatus:
    """
    The RequestStatus object is used to indicate the current status of a Flow
    Reservation Request.

    :ivar dateTime: The dateTime attribute will provide a timestamp of
        when the request status was set. dateTime MUST be set to the
        time at which the status change occurred, not a time in the
        future or past.
    :ivar requestStatus: Field representing the request status type. 0 =
        Requested 1 = Cancelled All other values reserved.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    dateTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    requestStatus: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    href: str | None = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class ServiceChange:
    """
    Specifies a change to the service status.

    :ivar newStatus: The new service status, to take effect at the time
        specified by startTime
    :ivar startTime: The date/time when the change is to take effect.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    newStatus: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    startTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class SetPoint:
    """The SetPoint object is used to apply specific temperature set points to
    a temperature control device.

    The values of the heatingSetpoint and coolingSetpoint attributes SHALL be calculated as follows:
    Cooling/Heating Temperature Set Point / 100 = temperature in degrees Celsius where -273.15°C &amp;lt;= temperature &amp;lt;= 327.67°C, corresponding to a Cooling and/or Heating Temperature Set Point. The maximum resolution this format allows is 0.01°C.
    The field not present in a Response indicates that this field has not been used by the end device.
    If a temperature is sent that exceeds the temperature limit boundaries that are programmed into the device, the device SHALL respond by setting the temperature at the limit.

    :ivar coolingSetpoint: This attribute represents the cooling
        temperature set point in degrees Celsius / 100. (Hundredths of a
        degree C)
    :ivar heatingSetpoint: This attribute represents the heating
        temperature set point in degrees Celsius / 100. (Hundredths of a
        degree C)
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    coolingSetpoint: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    heatingSetpoint: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
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

    multiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "min_inclusive": -140737488355328,
            "max_inclusive": 140737488355328,
        },
    )


@dataclass
class StateOfChargeStatusType:
    """
    DER StateOfChargeStatus value: Percent data type.

    :ivar dateTime: The date and time at which the state applied.
    :ivar value: The value indicating the state.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    dateTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class StorageModeStatusType:
    """DER StorageModeStatus value:

    0 – storage charging 1 – storage discharging 2 – storage holding All
    other values reserved.

    :ivar dateTime: The date and time at which the state applied.
    :ivar value: The value indicating the state.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    dateTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    type: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    multiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    subject: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class TimeConfiguration:
    """
    Contains attributes related to the configuration of the time service.

    :ivar dstEndRule: Rule to calculate end of daylight savings time in
        the current year.  Result of dstEndRule must be greater than
        result of dstStartRule.
    :ivar dstOffset: Daylight savings time offset from local standard
        time.
    :ivar dstStartRule: Rule to calculate start of daylight savings time
        in the current year. Result of dstEndRule must be greater than
        result of dstStartRule.
    :ivar tzOffset: Local time zone offset from UTCTime. Does not
        include any daylight savings time offsets.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    dstEndRule: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 4,
            "format": "base16",
        },
    )
    dstOffset: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    dstStartRule: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 4,
            "format": "base16",
        },
    )
    tzOffset: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    multiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    unit: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    multiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class VoltageRMS:
    """
    Average electric potential difference between two points.

    :ivar multiplier: Specifies exponent of uom.
    :ivar value: Value in volts RMS (uom 29)
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    multiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    multiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class loWPAN:
    """
    Contains information specific to 6LoWPAN.

    :ivar octetsRx: Number of Bytes received
    :ivar octetsTx: Number of Bytes transmitted
    :ivar packetsRx: Number of packets received
    :ivar packetsTx: Number of packets transmitted
    :ivar rxFragError: Number of errors receiving fragments
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    octetsRx: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    octetsTx: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    packetsRx: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    packetsTx: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    rxFragError: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    :ivar energyUnit: Unit of service.
    :ivar monetaryUnit: Unit of currency.
    :ivar multiplier: Multiplier for the 'energyUnit' or 'monetaryUnit'.
    :ivar value: Value of the monetary aspect
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    energyUnit: RealEnergy | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    monetaryUnit: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    multiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    :ivar billLastPeriod: The amount of the bill for the previous
        billing period.
    :ivar billToDate: The bill amount related to the billing period as
        of the statusTimeStamp.
    :ivar interval: The time interval for this billing period.
    :ivar statusTimeStamp: The date / time of the last update of this
        resource.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    billLastPeriod: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "min_inclusive": -140737488355328,
            "max_inclusive": 140737488355328,
        },
    )
    billToDate: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "min_inclusive": -140737488355328,
            "max_inclusive": 140737488355328,
        },
    )
    interval: DateTimeInterval | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    statusTimeStamp: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
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

    :ivar consumptionBlock: Indicates the consumption block related to
        the reading. If not specified, is assumed to be "0 - N/A".
    :ivar EnvironmentalCost:
    :ivar price: The charge for this rate component, per unit of measure
        defined by the associated ReadingType, in currency specified in
        TariffProfile. The Pricing service provider determines the
        appropriate price attribute value based on its applicable
        regulatory rules. For example, price could be net or inclusive
        of applicable taxes, fees, or levies. The Billing function set
        provides the ability to represent billing information in a more
        detailed manner.
    :ivar startValue: The lowest level of consumption that defines the
        starting point of this consumption step or block. Thresholds
        start at zero for each billing period. If specified, the first
        ConsumptionTariffInterval.startValue for a TimeTariffInteral
        instance SHALL begin at "0." Subsequent
        ConsumptionTariffInterval.startValue elements SHALL be greater
        than the previous one.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    consumptionBlock: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    EnvironmentalCost: list[EnvironmentalCost] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    price: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    startValue: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_inclusive": 281474976710655,
        },
    )


@dataclass
class CurrentDERProgramLink(Link):
    """SHALL contain a Link to an instance of DERProgram.

    If present, this is the DERProgram containing the currently active
    DERControl.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class CustomerAccountLink(Link):
    """
    SHALL contain a Link to an instance of CustomerAccount.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DERAvailabilityLink(Link):
    """
    SHALL contain a Link to an instance of DERAvailability.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DERCapability(Resource):
    """
    Distributed energy resource type and nameplate ratings.

    :ivar modesSupported: Bitmap indicating the DER Controls implemented
        by the device. See DERControlType for values.
    :ivar rtgAbnormalCategory: Abnormal operating performance category
        as defined by IEEE 1547-2018. One of: 0 - not specified 1 -
        Category I 2 - Category II 3 - Category III All other values
        reserved.
    :ivar rtgMaxA: Maximum continuous AC current capability of the DER,
        in Amperes (RMS).
    :ivar rtgMaxAh: Usable energy storage capacity of the DER, in
        AmpHours.
    :ivar rtgMaxChargeRateVA: Maximum apparent power charge rating in
        Volt-Amperes. May differ from the maximum apparent power rating.
    :ivar rtgMaxChargeRateW: Maximum rate of energy transfer received by
        the storage DER, in Watts.
    :ivar rtgMaxDischargeRateVA: Maximum apparent power discharge rating
        in Volt-Amperes. May differ from the maximum apparent power
        rating.
    :ivar rtgMaxDischargeRateW: Maximum rate of energy transfer
        delivered by the storage DER, in Watts. Required for combined
        generation/storage DERs (e.g. DERType == 83).
    :ivar rtgMaxV: AC voltage maximum rating.
    :ivar rtgMaxVA: Maximum continuous apparent power output capability
        of the DER, in VA.
    :ivar rtgMaxVar: Maximum continuous reactive power delivered by the
        DER, in var.
    :ivar rtgMaxVarNeg: Maximum continuous reactive power received by
        the DER, in var.  If absent, defaults to negative rtgMaxVar.
    :ivar rtgMaxW: Maximum continuous active power output capability of
        the DER, in watts. Represents combined generation plus storage
        output if DERType == 83.
    :ivar rtgMaxWh: Maximum energy storage capacity of the DER, in
        WattHours.
    :ivar rtgMinPFOverExcited: Minimum Power Factor displacement
        capability of the DER when injecting reactive power (over-
        excited); SHALL be a positive value between 0.0 (typically
        &amp;gt; 0.7) and 1.0. If absent, defaults to unity.
    :ivar rtgMinPFUnderExcited: Minimum Power Factor displacement
        capability of the DER when absorbing reactive power (under-
        excited); SHALL be a positive value between 0.0 (typically
        &amp;gt; 0.7) and 0.9999.  If absent, defaults to
        rtgMinPFOverExcited.
    :ivar rtgMinV: AC voltage minimum rating.
    :ivar rtgNormalCategory: Normal operating performance category as
        defined by IEEE 1547-2018. One of: 0 - not specified 1 -
        Category A 2 - Category B All other values reserved.
    :ivar rtgOverExcitedPF: Specified over-excited power factor.
    :ivar rtgOverExcitedW: Active power rating in Watts at specified
        over-excited power factor (rtgOverExcitedPF). If present,
        rtgOverExcitedPF SHALL be present.
    :ivar rtgReactiveSusceptance: Reactive susceptance that remains
        connected to the Area EPS in the cease to energize and trip
        state.
    :ivar rtgUnderExcitedPF: Specified under-excited power factor.
    :ivar rtgUnderExcitedW: Active power rating in Watts at specified
        under-excited power factor (rtgUnderExcitedPF). If present,
        rtgUnderExcitedPF SHALL be present.
    :ivar rtgVNom: AC voltage nominal rating.
    :ivar type: Type of DER; see DERType object
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    modesSupported: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 4,
            "format": "base16",
        },
    )
    rtgAbnormalCategory: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgMaxA: CurrentRMS | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgMaxAh: AmpereHour | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgMaxChargeRateVA: ApparentPower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgMaxChargeRateW: ActivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgMaxDischargeRateVA: ApparentPower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgMaxDischargeRateW: ActivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgMaxV: VoltageRMS | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgMaxVA: ApparentPower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgMaxVar: ReactivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgMaxVarNeg: ReactivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgMaxW: ActivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    rtgMaxWh: WattHour | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgMinPFOverExcited: PowerFactor | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgMinPFUnderExcited: PowerFactor | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgMinV: VoltageRMS | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgNormalCategory: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgOverExcitedPF: PowerFactor | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgOverExcitedW: ActivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgReactiveSusceptance: ReactiveSusceptance | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgUnderExcitedPF: PowerFactor | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgUnderExcitedW: ActivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rtgVNom: VoltageRMS | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    type: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class DERCapabilityLink(Link):
    """
    SHALL contain a Link to an instance of DERCapability.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DERCurveLink(Link):
    """
    SHALL contain a Link to an instance of DERCurve.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DERLink(Link):
    """
    SHALL contain a Link to an instance of DER.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DERProgramLink(Link):
    """
    SHALL contain a Link to an instance of DERProgram.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DERSettingsLink(Link):
    """
    SHALL contain a Link to an instance of DERSettings.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DERStatusLink(Link):
    """
    SHALL contain a Link to an instance of DERStatus.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DRLCCapabilities:
    """
    Contains information about the static capabilities of the device, to allow
    service providers to know what types of functions are supported, what the
    normal operating ranges and limits are, and other similar information, in
    order to provide better suggestions of applicable programs to receive the
    maximum benefit.

    :ivar averageEnergy: The average hourly energy usage when in normal
        operating mode.
    :ivar maxDemand: The maximum demand rating of this end device.
    :ivar optionsImplemented: Bitmap indicating the DRLC options
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
        namespace = "urn:ieee:std:2030.5:ns"

    averageEnergy: RealEnergy | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    maxDemand: ActivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    optionsImplemented: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 4,
            "format": "base16",
        },
    )


@dataclass
class DefaultDERControlLink(Link):
    """SHALL contain a Link to an instance of DefaultDERControl.

    This is the default mode of the DER which MAY be overridden by
    DERControl events.
    """

    class Meta:
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

    :ivar activateTime: This element MUST be set to the date/time at
        which this file is activated. If the activation time is less
        than or equal to current time, the LD MUST immediately place the
        file into the activated state (in the case of a firmware file,
        the file is now the running image).  If the activation time is
        greater than the current time, the LD MUST wait until the
        specified activation time is reached, then MUST place the file
        into the activated state. Omission of this element means that
        the LD MUST NOT take any action to activate the file until a
        subsequent GET to this File resource provides an activateTime.
    :ivar fileURI: This element MUST be set to the URI location of the
        file binary artifact.  This is the BLOB (binary large object)
        that is actually loaded by the LD
    :ivar lFDI: This element MUST be set to the LFDI of the device for
        which this file in targeted.
    :ivar mfHwVer: This element MUST be set to the hardware version for
        which this file is targeted.
    :ivar mfID: This element MUST be set to the manufacturer's Private
        Enterprise Number (assigned by IANA).
    :ivar mfModel: This element MUST be set to the manufacturer model
        number for which this file is targeted. The syntax and semantics
        are left to the manufacturer.
    :ivar mfSerNum: This element MUST be set to the manufacturer serial
        number for which this file is targeted. The syntax and semantics
        are left to the manufacturer.
    :ivar mfVer: This element MUST be set to the software version
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

    activateTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    fileURI: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    lFDI: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 20,
            "format": "base16",
        },
    )
    mfHwVer: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 32,
        },
    )
    mfID: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    mfModel: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 32,
        },
    )
    mfSerNum: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 32,
        },
    )
    mfVer: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 16,
        },
    )
    size: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    type: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 2,
            "format": "base16",
        },
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

    :ivar mRID: The global identifier of the object.
    :ivar description: The description is a human readable text
        describing or naming the object.
    :ivar version: Contains the version number of the object. See the
        type definition for details.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    mRID: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 16,
            "format": "base16",
        },
    )
    description: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 32,
        },
    )
    version: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class List_type(Resource):
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

    all: int | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    results: int | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
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

    all: int | None = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class LogEvent(Resource):
    """
    A time stamped instance of a significant event detected by the device.

    :ivar createdDateTime: The date and time that the event occurred.
    :ivar details: Human readable text that MAY be used to transmit
        additional details about the event. A host MAY remove this field
        when received.
    :ivar extendedData: May be used to transmit additional details about
        the event.
    :ivar functionSet: If the profileID indicates this is IEEE 2030.5,
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
    :ivar logEventCode: An 8 bit unsigned integer. logEventCodes are
        scoped to a profile and a function set. If the profile is IEEE
        2030.5, the logEventCode is defined by IEEE 2030.5 within one of
        the function sets of IEEE 2030.5. If the profile is anything
        else, the logEventCode is defined by the specified profile.
    :ivar logEventID: This 16-bit value, combined with createdDateTime,
        profileID, and logEventPEN, should provide a reasonable level of
        uniqueness.
    :ivar logEventPEN: The Private Enterprise Number(PEN) of the entity
        that defined the profileID, functionSet, and logEventCode of the
        logEvent. IEEE 2030.5-assigned logEventCodes SHALL use the IEEE
        2030.5 PEN.  Combinations of profileID, functionSet, and
        logEventCode SHALL have unique meaning within a logEventPEN and
        are defined by the owner of the PEN.
    :ivar profileID: The profileID identifies which profile (HA, BA, SE,
        etc) defines the following event information. 0       Not
        profile specific. 1       Vendor Defined 2       IEEE 2030.5 3
        Home Automation 4       Building Automation All other values are
        reserved.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    createdDateTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    details: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 32,
        },
    )
    extendedData: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    functionSet: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    logEventCode: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    logEventID: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    logEventPEN: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    profileID: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    :ivar isChild: True if the neighbor is a child.
    :ivar linkQuality: The quality of the link, as defined by 802.15.4
    :ivar shortAddress: As defined by IEEE 802.15.4
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    isChild: bool | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    linkQuality: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    shortAddress: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class PEVInfo:
    """
    Contains attributes that can be exposed by PEVs and other devices that have
    charging requirements.

    :ivar chargingPowerNow: This is the actual power flow in or out of
        the charger or inverter. This is calculated by the vehicle based
        on actual measurements. This number is positive for charging.
    :ivar energyRequestNow: This is the amount of energy that must be
        transferred from the grid to EVSE and PEV to achieve the target
        state of charge allowing for charger efficiency and any vehicle
        and EVSE parasitic loads. This is calculated by the vehicle and
        changes throughout the connection as forward or reverse power
        flow change the battery state of charge.  This number is
        positive for charging.
    :ivar maxForwardPower: This is maximum power transfer capability
        that could be used for charging the PEV to perform the requested
        energy transfer.  It is the lower of the vehicle or EVSE
        physical power limitations. It is not based on economic
        considerations. The vehicle may draw less power than this value
        based on its charging cycle. The vehicle defines this parameter.
        This number is positive for charging power flow.
    :ivar minimumChargingDuration: This is computed by the PEV based on
        the charging profile to complete the energy transfer if the
        maximum power is authorized.  The value will never be smaller
        than the ratio of the energy request to the power request
        because the charging profile may not allow the maximum power to
        be used throughout the transfer.   This is a critical parameter
        for determining whether any slack time exists in the charging
        cycle between the current time and the TCIN.
    :ivar targetStateOfCharge: This is the target state of charge that
        is to be achieved during charging before the time of departure
        (TCIN).  The default value is 100%. The value cannot be set to a
        value less than the actual state of charge.
    :ivar timeChargeIsNeeded: Time Charge is Needed (TCIN) is the time
        that the PEV is expected to depart. The value is manually
        entered using controls and displays in the vehicle or on the
        EVSE or using a mobile device.  It is authenticated and saved by
        the PEV.  This value may be updated during a charging session.
    :ivar timeChargingStatusPEV: This is the time that the parameters
        are updated, except for changes to TCIN.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    chargingPowerNow: ActivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    energyRequestNow: RealEnergy | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    maxForwardPower: ActivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    minimumChargingDuration: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    targetStateOfCharge: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    timeChargeIsNeeded: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    timeChargingStatusPEV: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    :ivar creditTypeChange: CreditTypeChange is used to define a pending
        change of creditTypeInUse, which will activate at a specified
        time.
    :ivar creditTypeInUse: CreditTypeInUse identifies whether the
        present mode of operation is consuming regular credit or
        emergency credit.
    :ivar serviceChange: ServiceChange is used to define a pending
        change of serviceStatus, which will activate at a specified
        time.
    :ivar serviceStatus: ServiceStatus identifies whether the service is
        connected or disconnected, or armed for connection or
        disconnection.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    creditTypeChange: CreditTypeChange | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    creditTypeInUse: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    serviceChange: ServiceChange | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    serviceStatus: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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
class RPLSourceRoutes(Resource):
    """
    A RPL source routes object.

    :ivar DestAddress: See [RFC 6554].
    :ivar SourceRoute: See [RFC 6554].
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    DestAddress: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 16,
            "format": "base16",
        },
    )
    SourceRoute: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 16,
            "format": "base16",
        },
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

    :ivar consumptionBlock: Indicates the consumption block related to
        the reading. REQUIRED if ReadingType numberOfConsumptionBlocks
        is non-zero. If not specified, is assumed to be "0 - N/A".
    :ivar qualityFlags: List of codes indicating the quality of the
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
    :ivar timePeriod: The time interval associated with the reading. If
        not specified, then defaults to the intervalLength specified in
        the associated ReadingType.
    :ivar touTier: Indicates the time of use tier related to the
        reading. REQUIRED if ReadingType numberOfTouTiers is non-zero.
        If not specified, is assumed to be "0 - N/A".
    :ivar value: Value in units specified by ReadingType
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    consumptionBlock: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    qualityFlags: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 2,
            "format": "base16",
        },
    )
    timePeriod: DateTimeInterval | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    touTier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    value: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "min_inclusive": -140737488355328,
            "max_inclusive": 140737488355328,
        },
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

    :ivar accumulationBehaviour: The “accumulation behaviour” indicates
        how the value is represented to accumulate over time.
    :ivar calorificValue: The amount of heat generated when a given mass
        of fuel is completely burned. The CalorificValue is used to
        convert the measured volume or mass of gas into kWh. The
        CalorificValue attribute represents the current active value.
    :ivar commodity: Indicates the commodity applicable to this
        ReadingType.
    :ivar conversionFactor: Accounts for changes in the volume of gas
        based on temperature and pressure. The ConversionFactor
        attribute represents the current active value. The
        ConversionFactor is dimensionless. The default value for the
        ConversionFactor is 1, which means no conversion is applied. A
        price server can advertise a new/different value at any time.
    :ivar dataQualifier: The data type can be used to describe a salient
        attribute of the data. Possible values are average, absolute,
        and etc.
    :ivar flowDirection: Anything involving current might have a flow
        direction. Possible values include forward and reverse.
    :ivar intervalLength: Default interval length specified in seconds.
    :ivar kind: Compound class that contains kindCategory and kindIndex
    :ivar maxNumberOfIntervals: To be populated for mirrors of interval
        data to set the expected number of intervals per ReadingSet.
        Servers may discard intervals received that exceed this number.
    :ivar numberOfConsumptionBlocks: Number of consumption blocks. 0
        means not applicable, and is the default if not specified. The
        value needs to be at least 1 if any actual prices are provided.
    :ivar numberOfTouTiers: The number of TOU tiers that can be used by
        any resource configured by this ReadingType. Servers SHALL
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
    :ivar powerOfTenMultiplier: Indicates the power of ten multiplier
        applicable to the unit of measure of this ReadingType.
    :ivar subIntervalLength: Default sub-interval length specified in
        seconds for Readings of ReadingType. Some demand calculations
        are done over a number of smaller intervals. For example, in a
        rolling demand calculation, the demand value is defined as the
        rolling sum of smaller intervals over the intervalLength. The
        subintervalLength is the length of the smaller interval in this
        calculation. It SHALL be an integral division of the
        intervalLength. The number of sub-intervals can be calculated by
        dividing the intervalLength by the subintervalLength.
    :ivar supplyLimit: Reflects the supply limit set in the meter. This
        value can be compared to the Reading value to understand if
        limits are being approached or exceeded. Units follow the same
        definition as in this ReadingType.
    :ivar tieredConsumptionBlocks: Specifies whether or not the
        consumption blocks are differentiated by TOUTier or not. Default
        is false, if not specified. true = consumption accumulated over
        individual tiers false = consumption accumulated over all tiers
    :ivar uom: Indicates the measurement type for the units of measure
        for the readings of this type.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    accumulationBehaviour: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    calorificValue: UnitValueType | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    commodity: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    conversionFactor: UnitValueType | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    dataQualifier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    flowDirection: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    intervalLength: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    kind: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    maxNumberOfIntervals: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    numberOfConsumptionBlocks: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    numberOfTouTiers: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    phase: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    powerOfTenMultiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    subIntervalLength: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    supplyLimit: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_inclusive": 281474976710655,
        },
    )
    tieredConsumptionBlocks: bool | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    uom: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
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

    :ivar dateTimeRegistered: Contains the time at which this
        registration was created, by which clients MAY prioritize
        information providers with the most recent registrations, when
        no additional direction from the consumer is available.
    :ivar pIN: Contains the registration PIN number associated with the
        device, including the checksum digit.
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    dateTimeRegistered: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    pIN: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
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

    :ivar replyTo: A reference to the response resource address (URI).
        Required on a response to a GET if responseRequired is "true".
    :ivar responseRequired: Indicates whether or not a response is
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

    replyTo: str | None = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    responseRequired: bytes = field(
        default=b"\x00",
        metadata={
            "type": "Attribute",
            "max_length": 1,
            "format": "base16",
        },
    )


@dataclass
class Response(Resource):
    """
    The Response object is the generic response data repository which is
    extended for specific function sets.

    :ivar createdDateTime: The createdDateTime field contains the date
        and time when the acknowledgement/status occurred in the client.
        The client will provide the timestamp to ensure the proper time
        is captured in case the response is delayed in reaching the
        server (server receipt time would not be the same as the actual
        confirmation time). The time reported from the client should be
        relative to the time server indicated by the
        FunctionSetAssignment that also indicated the event resource; if
        no FunctionSetAssignment exists, the time of the server where
        the event resource was hosted.
    :ivar endDeviceLFDI: Contains the LFDI of the device providing the
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

    createdDateTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    endDeviceLFDI: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 20,
            "format": "base16",
        },
    )
    status: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    subject: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 16,
            "format": "base16",
        },
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
        },
    )


@dataclass
class SubscriptionBase(Resource):
    """Holds the information related to a client subscription to receive
    updates to a resource automatically.

    The actual resources may be passed in the Notification by specifying
    a specific xsi:type for the Resource and passing the full
    representation.

    :ivar subscribedResource: The resource for which the subscription
        applies. Query string parameters SHALL NOT be specified when
        subscribing to list resources.  Should a query string parameter
        be specified, servers SHALL ignore them.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    subscribedResource: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    description: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 32,
        },
    )
    interval: DateTimeInterval | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class SupportedLocale(Resource):
    """
    Specifies a locale that is supported.

    :ivar locale: The code for a locale that is supported
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    locale: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 42,
        },
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

    :ivar currentTime: The current time, in the format defined by
        TimeType.
    :ivar dstEndTime: Time at which daylight savings ends (dstOffset no
        longer applied).  Result of dstEndRule calculation.
    :ivar dstOffset: Daylight savings time offset from local standard
        time. A typical practice is advancing clocks one hour when
        daylight savings time is in effect, which would result in a
        positive dstOffset.
    :ivar dstStartTime: Time at which daylight savings begins (apply
        dstOffset).  Result of dstStartRule calculation.
    :ivar localTime: Local time: localTime = currentTime + tzOffset (+
        dstOffset when in effect).
    :ivar quality: Metric indicating the quality of the time source from
        which the service acquired time. Lower (smaller) quality
        enumeration values are assumed to be more accurate. 3 - time
        obtained from external authoritative source such as NTP 4 - time
        obtained from level 3 source 5 - time manually set or obtained
        from level 4 source 6 - time obtained from level 5 source 7 -
        time intentionally uncoordinated All other values are reserved
        for future use.
    :ivar tzOffset: Local time zone offset from currentTime. Does not
        include any daylight savings time offsets. For American time
        zones, a negative tzOffset SHALL be used (eg, EST = GMT-5 which
        is -18000).
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    currentTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    dstEndTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    dstOffset: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    dstStartTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    localTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    quality: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    tzOffset: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
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

    :ivar availableCredit: AvailableCredit shows the balance of the sum
        of credits minus the sum of charges. In a Central Wallet mode
        this value may be passed down to the Prepayment server via an
        out-of-band mechanism. In Local or ESI modes, this value may be
        calculated based upon summation of CreditRegister transactions
        minus consumption charges calculated using Metering (and
        possibly Pricing) function set data. This value may be negative;
        for instance, if disconnection is prevented due to a Supply
        Interruption Override.
    :ivar creditStatus: CreditStatus identifies whether the present
        value of availableCredit is considered OK, low, exhausted, or
        negative.
    :ivar emergencyCredit: EmergencyCredit is the amount of credit still
        available for the given service or commodity prepayment
        instance. If both availableCredit and emergyCredit are
        exhausted, then service will typically be disconnected.
    :ivar emergencyCreditStatus: EmergencyCreditStatus identifies
        whether the present value of emergencyCredit is considered OK,
        low, exhausted, or negative.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    availableCredit: AccountingUnit | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    creditStatus: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    emergencyCredit: AccountingUnit | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    emergencyCreditStatus: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
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
class ActiveDERControlListLink(ListLink):
    """
    SHALL contain a Link to a List of active DERControl instances.
    """

    class Meta:
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
class AssociatedDERProgramListLink(ListLink):
    """
    SHALL contain a Link to a List of DERPrograms having the DERControl(s) for
    this DER.
    """

    class Meta:
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

    Charge: list[Charge] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
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
class ConsumptionTariffIntervalList(List_type):
    """
    A List element to hold ConsumptionTariffInterval objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    ConsumptionTariffInterval: list[ConsumptionTariffInterval] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
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

    :ivar creditAmount: CreditAmount is the amount of credit being added
        by a particular CreditRegister transaction. Negative values
        indicate that credit is being subtracted.
    :ivar creditType: CreditType indicates whether the credit
        transaction applies to regular or emergency credit.
    :ivar effectiveTime: EffectiveTime identifies the time at which the
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

    creditAmount: AccountingUnit | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    creditType: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    effectiveTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    token: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 32,
        },
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
class DERAvailability(SubscribableResource):
    """
    Indicates current reserve generation status.

    :ivar availabilityDuration: Indicates number of seconds the DER will
        be able to deliver active power at the reservePercent level.
    :ivar maxChargeDuration: Indicates number of seconds the DER will be
        able to receive active power at the reserveChargePercent level.
    :ivar readingTime: The timestamp when the DER availability was last
        updated.
    :ivar reserveChargePercent: Percent of continuous received active
        power (%setMaxChargeRateW) that is estimated to be available in
        reserve.
    :ivar reservePercent: Percent of continuous delivered active power
        (%setMaxW) that is estimated to be available in reserve.
    :ivar statVarAvail: Estimated reserve reactive power, in var.
        Represents the lesser of received or delivered reactive power.
    :ivar statWAvail: Estimated reserve active power, in watts.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    availabilityDuration: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    maxChargeDuration: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    readingTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    reserveChargePercent: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    reservePercent: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    statVarAvail: ReactivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    statWAvail: ActivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class DERControlBase:
    """
    Distributed Energy Resource (DER) control values.

    :ivar opModConnect: Set DER as connected (true) or disconnected
        (false). Used in conjunction with ramp rate when re-connecting.
        Implies galvanic isolation.
    :ivar opModEnergize: Set DER as energized (true) or de-energized
        (false). Used in conjunction with ramp rate when re-energizing.
    :ivar opModFixedPFAbsorbW: The opModFixedPFAbsorbW function
        specifies a requested fixed Power Factor (PF) setting for when
        active power is being absorbed. The actual displacement SHALL be
        within the limits established by setMinPFOverExcited and
        setMinPFUnderExcited. If issued simultaneously with other
        reactive power controls (e.g. opModFixedVar) the control
        resulting in least var magnitude SHOULD take precedence.
    :ivar opModFixedPFInjectW: The opModFixedPFInjectW function
        specifies a requested fixed Power Factor (PF) setting for when
        active power is being injected. The actual displacement SHALL be
        within the limits established by setMinPFOverExcited and
        setMinPFUnderExcited. If issued simultaneously with other
        reactive power controls (e.g. opModFixedVar) the control
        resulting in least var magnitude SHOULD take precedence.
    :ivar opModFixedVar: The opModFixedVar function specifies the
        delivered or received reactive power setpoint.  The context for
        the setpoint value is determined by refType and SHALL be one of
        %setMaxW, %setMaxVar, or %statVarAvail.  If issued
        simultaneously with other reactive power controls (e.g.
        opModFixedPFInjectW) the control resulting in least var
        magnitude SHOULD take precedence.
    :ivar opModFixedW: The opModFixedW function specifies a requested
        charge or discharge mode setpoint, in %setMaxChargeRateW if
        negative value or %setMaxW or %setMaxDischargeRateW if positive
        value (in hundredths).
    :ivar opModFreqDroop: Specifies a frequency-watt operation. This
        operation limits active power generation or consumption when the
        line frequency deviates from nominal by a specified amount.
    :ivar opModFreqWatt: Specify DERCurveLink for curveType == 0.  The
        Frequency-Watt function limits active power generation or
        consumption when the line frequency deviates from nominal by a
        specified amount. The Frequency-Watt curve is specified as an
        array of Frequency-Watt pairs that are interpolated into a
        piecewise linear function with hysteresis.  The x value of each
        pair specifies a frequency in Hz. The y value specifies a
        corresponding active power output in %setMaxW.
    :ivar opModHFRTMayTrip: Specify DERCurveLink for curveType == 1. The
        High Frequency Ride-Through (HFRT) function is specified by one
        or two duration-frequency curves that define the operating
        region under high frequency conditions. Each HFRT curve is
        specified by an array of duration-frequency pairs that will be
        interpolated into a piecewise linear function that defines an
        operating region. The x value of each pair specifies a duration
        (time at a given frequency in seconds). The y value of each pair
        specifies a frequency, in Hz. This control specifies the "may
        trip" region.
    :ivar opModHFRTMustTrip: Specify DERCurveLink for curveType == 2.
        The High Frequency Ride-Through (HFRT) function is specified by
        a duration-frequency curve that defines the operating region
        under high frequency conditions.  Each HFRT curve is specified
        by an array of duration-frequency pairs that will be
        interpolated into a piecewise linear function that defines an
        operating region.  The x value of each pair specifies a duration
        (time at a given frequency in seconds). The y value of each pair
        specifies a frequency, in Hz. This control specifies the "must
        trip" region.
    :ivar opModHVRTMayTrip: Specify DERCurveLink for curveType == 3. The
        High Voltage Ride-Through (HVRT) function is specified by one,
        two, or three duration-volt curves that define the operating
        region under high voltage conditions. Each HVRT curve is
        specified by an array of duration-volt pairs that will be
        interpolated into a piecewise linear function that defines an
        operating region. The x value of each pair specifies a duration
        (time at a given voltage in seconds). The y value of each pair
        specifies an effective percentage voltage, defined as ((locally
        measured voltage - setVRefOfs / setVRef). This control specifies
        the "may trip" region.
    :ivar opModHVRTMomentaryCessation: Specify DERCurveLink for
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
    :ivar opModHVRTMustTrip: Specify DERCurveLink for curveType == 5.
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
    :ivar opModLFRTMayTrip: Specify DERCurveLink for curveType == 6. The
        Low Frequency Ride-Through (LFRT) function is specified by one
        or two duration-frequency curves that define the operating
        region under low frequency conditions. Each LFRT curve is
        specified by an array of duration-frequency pairs that will be
        interpolated into a piecewise linear function that defines an
        operating region. The x value of each pair specifies a duration
        (time at a given frequency in seconds). The y value of each pair
        specifies a frequency, in Hz. This control specifies the "may
        trip" region.
    :ivar opModLFRTMustTrip: Specify DERCurveLink for curveType == 7.
        The Low Frequency Ride-Through (LFRT) function is specified by a
        duration-frequency curve that defines the operating region under
        low frequency conditions.  Each LFRT curve is specified by an
        array of duration-frequency pairs that will be interpolated into
        a piecewise linear function that defines an operating region.
        The x value of each pair specifies a duration (time at a given
        frequency in seconds). The y value of each pair specifies a
        frequency, in Hz. This control specifies the "must trip" region.
    :ivar opModLVRTMayTrip: Specify DERCurveLink for curveType == 8. The
        Low Voltage Ride-Through (LVRT) function is specified by one,
        two, or three duration-volt curves that define the operating
        region under low voltage conditions. Each LVRT curve is
        specified by an array of duration-volt pairs that will be
        interpolated into a piecewise linear function that defines an
        operating region. The x value of each pair specifies a duration
        (time at a given voltage in seconds). The y value of each pair
        specifies an effective percent voltage, defined as ((locally
        measured voltage - setVRefOfs) / setVRef). This control
        specifies the "may trip" region.
    :ivar opModLVRTMomentaryCessation: Specify DERCurveLink for
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
    :ivar opModLVRTMustTrip: Specify DERCurveLink for curveType == 10.
        The Low Voltage Ride-Through (LVRT) function is specified by
        duration-volt curves that define the operating region under low
        voltage conditions.  Each LVRT curve is specified by an array of
        duration-volt pairs that will be interpolated into a piecewise
        linear function that defines an operating region.  The x value
        of each pair specifies a duration (time at a given voltage in
        seconds). The y value of each pair specifies an effective
        percent voltage, defined as ((locally measured voltage -
        setVRefOfs) / setVRef). This control specifies the "must trip"
        region.
    :ivar opModMaxLimW: The opModMaxLimW function sets the maximum
        active power generation level at the electrical coupling point
        as a percentage of set capacity (%setMaxW, in hundredths). This
        limitation may be met e.g. by reducing PV output or by using
        excess PV output to charge associated storage.
    :ivar opModTargetVar: Target reactive power, in var. This control is
        likely to be more useful for aggregators, as individual DERs may
        not be able to maintain a target setting.
    :ivar opModTargetW: Target output power, in Watts. This control is
        likely to be more useful for aggregators, as individual DERs may
        not be able to maintain a target setting.
    :ivar opModVoltVar: Specify DERCurveLink for curveType == 11.  The
        static volt-var function provides over- or under-excited var
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
    :ivar opModVoltWatt: Specify DERCurveLink for curveType == 12.  The
        Volt-Watt reduces active power output as a function of measured
        voltage. The Volt-Watt curve is specified as an array of Volt-
        Watt pairs that are interpolated into a piecewise linear
        function with hysteresis. The x value of each pair specifies an
        effective percent voltage, defined as ((locally measured voltage
        - setVRefOfs) / setVRef) and SHOULD support a domain of at least
        0 - 135. The y value specifies an active power output
        interpreted as a percentage (0 - 100). The meaning of the y
        value is determined by yRefType and must be one of %setMaxW or
        %statWAvail.
    :ivar opModWattPF: Specify DERCurveLink for curveType == 13.  The
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
    :ivar opModWattVar: Specify DERCurveLink for curveType == 14. The
        Watt-Var function varies vars as a function of delivered active
        power. The Watt-Var curve is specified as an array of Watt-Var
        pairs that are interpolated into a piecewise linear function
        with hysteresis. The x value of each pair specifies a watt
        setting in %setMaxW, (0-100). The y value specifies a target var
        output interpreted as a signed percentage (-100 to 100). The
        meaning of the y value is determined by yRefType and must be one
        of %setMaxW, %setMaxVar, or %statVarAvail.
    :ivar rampTms: Requested ramp time, in hundredths of a second, for
        the device to transition from the current DERControl  mode
        setting(s) to the new mode setting(s). If absent, use default
        ramp rate (setGradW).  Resolution is 1/100 sec.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    opModConnect: bool | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModEnergize: bool | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModFixedPFAbsorbW: PowerFactorWithExcitation | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModFixedPFInjectW: PowerFactorWithExcitation | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModFixedVar: FixedVar | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModFixedW: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModFreqDroop: FreqDroopType | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModFreqWatt: DERCurveLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModHFRTMayTrip: DERCurveLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModHFRTMustTrip: DERCurveLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModHVRTMayTrip: DERCurveLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModHVRTMomentaryCessation: DERCurveLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModHVRTMustTrip: DERCurveLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModLFRTMayTrip: DERCurveLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModLFRTMustTrip: DERCurveLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModLVRTMayTrip: DERCurveLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModLVRTMomentaryCessation: DERCurveLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModLVRTMustTrip: DERCurveLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModMaxLimW: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModTargetVar: ReactivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModTargetW: ActivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModVoltVar: DERCurveLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModVoltWatt: DERCurveLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModWattPF: DERCurveLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opModWattVar: DERCurveLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rampTms: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class DERControlListLink(ListLink):
    """
    SHALL contain a Link to a List of DERControl instances.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DERControlResponse(Response):
    """
    A response to a DERControl.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DERCurve(IdentifiedObject):
    """DER related curves such as Volt-Var mode curves.

    Relationship between an independent variable (X-axis) and a
    dependent variable (Y-axis).

    :ivar autonomousVRefEnable: If the curveType is opModVoltVar, then
        this field MAY be present. If the curveType is not opModVoltVar,
        then this field SHALL NOT be present. Enable/disable autonomous
        vRef adjustment. When enabled, the Volt-Var curve characteristic
        SHALL be adjusted autonomously as vRef changes and
        autonomousVRefTimeConstant SHALL be present. If a DER is able to
        support Volt-Var mode but is unable to support autonomous vRef
        adjustment, then the DER SHALL execute the curve without
        autonomous vRef adjustment. If not specified, then the value is
        false.
    :ivar autonomousVRefTimeConstant: If the curveType is opModVoltVar,
        then this field MAY be present. If the curveType is not
        opModVoltVar, then this field SHALL NOT be present. Adjustment
        range for vRef time constant, in hundredths of a second.
    :ivar creationTime: The time at which the object was created.
    :ivar CurveData:
    :ivar curveType: Specifies the associated curve-based control mode.
    :ivar openLoopTms: Open loop response time, the time to ramp up to
        90% of the new target in response to the change in voltage, in
        hundredths of a second. Resolution is 1/100 sec. A value of 0 is
        used to mean no limit. When not present, the device SHOULD
        follow its default behavior.
    :ivar rampDecTms: Decreasing ramp rate, interpreted as a percentage
        change in output capability limit per second (e.g. %setMaxW /
        sec).  Resolution is in hundredths of a percent/second. A value
        of 0 means there is no limit. If absent, ramp rate defaults to
        setGradW.
    :ivar rampIncTms: Increasing ramp rate, interpreted as a percentage
        change in output capability limit per second (e.g. %setMaxW /
        sec).  Resolution is in hundredths of a percent/second. A value
        of 0 means there is no limit. If absent, ramp rate defaults to
        rampDecTms.
    :ivar rampPT1Tms: The configuration parameter for a low-pass filter,
        PT1 is a time, in hundredths of a second, in which the filter
        will settle to 95% of a step change in the input value.
        Resolution is 1/100 sec.
    :ivar vRef: If the curveType is opModVoltVar, then this field MAY be
        present. If the curveType is not opModVoltVar, then this field
        SHALL NOT be present. The nominal AC voltage (RMS) adjustment to
        the voltage curve points for Volt-Var curves.
    :ivar xMultiplier: Exponent for X-axis value.
    :ivar yMultiplier: Exponent for Y-axis value.
    :ivar yRefType: The Y-axis units context.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    autonomousVRefEnable: bool | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    autonomousVRefTimeConstant: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    creationTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    CurveData: list[CurveData] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
            "max_occurs": 10,
        },
    )
    curveType: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    openLoopTms: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rampDecTms: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rampIncTms: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    rampPT1Tms: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    vRef: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    xMultiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    yMultiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    yRefType: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class DERCurveListLink(ListLink):
    """
    SHALL contain a Link to a List of DERCurve instances.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DERListLink(ListLink):
    """
    SHALL contain a Link to a List of DER instances.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DERProgramListLink(ListLink):
    """
    SHALL contain a Link to a List of DERProgram instances.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class DERSettings(SubscribableResource):
    """
    Distributed energy resource settings.

    :ivar modesEnabled: Bitmap indicating the DER Controls enabled on
        the device. See DERControlType for values. If a control is
        supported (see DERCapability::modesSupported), but not enabled,
        the control will not be executed if encountered.
    :ivar setESDelay: Enter service delay, in hundredths of a second.
    :ivar setESHighFreq: Enter service frequency high. Specified in
        hundredths of Hz.
    :ivar setESHighVolt: Enter service voltage high. Specified as an
        effective percent voltage, defined as (100% * (locally measured
        voltage - setVRefOfs) / setVRef), in hundredths of a percent.
    :ivar setESLowFreq: Enter service frequency low. Specified in
        hundredths of Hz.
    :ivar setESLowVolt: Enter service voltage low. Specified as an
        effective percent voltage, defined as (100% * (locally measured
        voltage - setVRefOfs) / setVRef), in hundredths of a percent.
    :ivar setESRampTms: Enter service ramp time, in hundredths of a
        second.
    :ivar setESRandomDelay: Enter service randomized delay, in
        hundredths of a second.
    :ivar setGradW: Set default rate of change (ramp rate) of active
        power output due to command or internal action, defined in
        %setWMax / second.  Resolution is in hundredths of a
        percent/second. A value of 0 means there is no limit.
        Interpreted as a percentage change in output capability limit
        per second when used as a default ramp rate.
    :ivar setMaxA: AC current maximum. Maximum AC current in RMS
        Amperes.
    :ivar setMaxAh: Maximum usable energy storage capacity of the DER,
        in AmpHours. Note: this may be different from physical
        capability.
    :ivar setMaxChargeRateVA: Apparent power charge maximum. Maximum
        apparent power the DER can absorb from the grid in Volt-Amperes.
        May differ from the apparent power maximum (setMaxVA).
    :ivar setMaxChargeRateW: Maximum rate of energy transfer received by
        the storage device, in Watts. Defaults to rtgMaxChargeRateW.
    :ivar setMaxDischargeRateVA: Apparent power discharge maximum.
        Maximum apparent power the DER can deliver to the grid in Volt-
        Amperes. May differ from the apparent power maximum (setMaxVA).
    :ivar setMaxDischargeRateW: Maximum rate of energy transfer
        delivered by the storage device, in Watts. Defaults to
        rtgMaxDischargeRateW.
    :ivar setMaxV: AC voltage maximum setting.
    :ivar setMaxVA: Set limit for maximum apparent power capability of
        the DER (in VA). Defaults to rtgMaxVA.
    :ivar setMaxVar: Set limit for maximum reactive power delivered by
        the DER (in var). SHALL be a positive value &amp;lt;= rtgMaxVar
        (default).
    :ivar setMaxVarNeg: Set limit for maximum reactive power received by
        the DER (in var). If present, SHALL be a negative value
        &amp;gt;= rtgMaxVarNeg (default). If absent, defaults to
        negative setMaxVar.
    :ivar setMaxW: Set limit for maximum active power capability of the
        DER (in W). Defaults to rtgMaxW.
    :ivar setMaxWh: Maximum energy storage capacity of the DER, in
        WattHours. Note: this may be different from physical capability.
    :ivar setMinPFOverExcited: Set minimum Power Factor displacement
        limit of the DER when injecting reactive power (over-excited);
        SHALL be a positive value between 0.0 (typically &amp;gt; 0.7)
        and 1.0.  SHALL be &amp;gt;= rtgMinPFOverExcited (default).
    :ivar setMinPFUnderExcited: Set minimum Power Factor displacement
        limit of the DER when absorbing reactive power (under-excited);
        SHALL be a positive value between 0.0 (typically &amp;gt; 0.7)
        and 0.9999.  If present, SHALL be &amp;gt;= rtgMinPFUnderExcited
        (default).  If absent, defaults to setMinPFOverExcited.
    :ivar setMinV: AC voltage minimum setting.
    :ivar setSoftGradW: Set soft-start rate of change (soft-start ramp
        rate) of active power output due to command or internal action,
        defined in %setWMax / second.  Resolution is in hundredths of a
        percent/second. A value of 0 means there is no limit.
        Interpreted as a percentage change in output capability limit
        per second when used as a ramp rate.
    :ivar setVNom: AC voltage nominal setting.
    :ivar setVRef: The nominal AC voltage (RMS) at the utility's point
        of common coupling.
    :ivar setVRefOfs: The nominal AC voltage (RMS) offset between the
        DER's electrical connection point and the utility's point of
        common coupling.
    :ivar updatedTime: Specifies the time at which the DER information
        was last updated.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    modesEnabled: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 4,
            "format": "base16",
        },
    )
    setESDelay: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setESHighFreq: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setESHighVolt: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setESLowFreq: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setESLowVolt: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setESRampTms: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setESRandomDelay: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setGradW: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    setMaxA: CurrentRMS | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setMaxAh: AmpereHour | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setMaxChargeRateVA: ApparentPower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setMaxChargeRateW: ActivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setMaxDischargeRateVA: ApparentPower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setMaxDischargeRateW: ActivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setMaxV: VoltageRMS | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setMaxVA: ApparentPower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setMaxVar: ReactivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setMaxVarNeg: ReactivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setMaxW: ActivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    setMaxWh: WattHour | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setMinPFOverExcited: PowerFactor | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setMinPFUnderExcited: PowerFactor | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setMinV: VoltageRMS | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setSoftGradW: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setVNom: VoltageRMS | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setVRef: VoltageRMS | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setVRefOfs: VoltageRMS | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    updatedTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class DERStatus(SubscribableResource):
    """
    DER status information.

    :ivar alarmStatus: Bitmap indicating the status of DER alarms (see
        DER LogEvents for more details). 0 - DER_FAULT_OVER_CURRENT 1 -
        DER_FAULT_OVER_VOLTAGE 2 - DER_FAULT_UNDER_VOLTAGE 3 -
        DER_FAULT_OVER_FREQUENCY 4 - DER_FAULT_UNDER_FREQUENCY 5 -
        DER_FAULT_VOLTAGE_IMBALANCE 6 - DER_FAULT_CURRENT_IMBALANCE 7 -
        DER_FAULT_EMERGENCY_LOCAL 8 - DER_FAULT_EMERGENCY_REMOTE 9 -
        DER_FAULT_LOW_POWER_INPUT 10 - DER_FAULT_PHASE_ROTATION 11-31 -
        Reserved
    :ivar genConnectStatus: Connect/status value for generator DER. See
        ConnectStatusType for values.
    :ivar inverterStatus: DER InverterStatus/value. See
        InverterStatusType for values.
    :ivar localControlModeStatus: The local control mode status. See
        LocalControlModeStatusType for values.
    :ivar manufacturerStatus: Manufacturer status code.
    :ivar operationalModeStatus: Operational mode currently in use. See
        OperationalModeStatusType for values.
    :ivar readingTime: The timestamp when the current status was last
        updated.
    :ivar stateOfChargeStatus: State of charge status. See
        StateOfChargeStatusType for values.
    :ivar storageModeStatus: Storage mode status. See
        StorageModeStatusType for values.
    :ivar storConnectStatus: Connect/status value for storage DER. See
        ConnectStatusType for values.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    alarmStatus: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 4,
            "format": "base16",
        },
    )
    genConnectStatus: ConnectStatusType | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    inverterStatus: InverterStatusType | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    localControlModeStatus: LocalControlModeStatusType | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    manufacturerStatus: ManufacturerStatusType | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    operationalModeStatus: OperationalModeStatusType | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    readingTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    stateOfChargeStatus: StateOfChargeStatusType | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    storageModeStatus: StorageModeStatusType | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    storConnectStatus: ConnectStatusType | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
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

    :ivar changedTime: The time at which the reported values were
        recorded.
    :ivar onCount: The number of times that the device has been turned
        on: Count of "device on" times, since the last time the counter
        was reset
    :ivar opState: Device operational state: 0 - Not applicable /
        Unknown 1 - Not operating 2 - Operating 3 - Starting up 4 -
        Shutting down 5 - At disconnect level 6 - kW ramping 7 - kVar
        ramping
    :ivar opTime: Total time device has operated: re-settable:
        Accumulated time in seconds since the last time the counter was
        reset.
    :ivar Temperature:
    :ivar TimeLink:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    changedTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    onCount: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opState: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    opTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    Temperature: list[Temperature] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    TimeLink: TimeLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class DrResponse(Response):
    """
    A response to a Demand Response Load Control (EndDeviceControl) message.

    :ivar ApplianceLoadReduction:
    :ivar AppliedTargetReduction:
    :ivar DutyCycle:
    :ivar Offset:
    :ivar overrideDuration: Indicates the amount of time, in seconds,
        that the client partially opts-out during the demand response
        event. When overriding within the allowed override duration, the
        client SHALL send a partial opt-out (Response status code 8) for
        partial opt-out upon completion, with the total time the event
        was overridden (this attribute) populated. The client SHALL send
        a no participation status response (status type 10) if the user
        partially opts-out for longer than
        EndDeviceControl.overrideDuration.
    :ivar SetPoint:
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    ApplianceLoadReduction: ApplianceLoadReduction | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    AppliedTargetReduction: AppliedTargetReduction | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    DutyCycle: DutyCycle | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    Offset: Offset | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    overrideDuration: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    SetPoint: SetPoint | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
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
class FileList(List_type):
    """
    A List element to hold File objects.

    :ivar File:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    File: list[File] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
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

    :ivar activateTime: Date/time at which this File, referred to by
        FileLink, will be activated. Omission of or presence and value
        of this element MUST exactly match omission or presence and
        value of the activateTime element from the File resource.
    :ivar FileLink:
    :ivar loadPercent: This element MUST be set to the percentage of the
        file, indicated by FileLink, that was loaded during the latest
        load attempt. This value MUST be reset to 0 each time a load
        attempt is started for the File indicated by FileLink. This
        value MUST be increased when an LD receives HTTP response
        containing file content. This value MUST be set to 100 when the
        full content of the file has been received by the LD
    :ivar nextRequestAttempt: This element MUST be set to the time at
        which the LD will issue its next GET request for file content
        from the File indicated by FileLink
    :ivar request503Count: This value MUST be reset to 0 when FileLink
        is first pointed at a new File. This value MUST be incremented
        each time an LD receives a 503 error from the FS.
    :ivar requestFailCount: This value MUST be reset to 0 when FileLink
        is first pointed at a new File. This value MUST be incremented
        each time a GET request for file content failed. 503 errors MUST
        be excluded from this counter.
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
    :ivar statusTime: This element MUST be set to the time at which file
        status transitioned to the value indicated in the status
        element.
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    activateTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    FileLink: FileLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    loadPercent: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    nextRequestAttempt: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    request503Count: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    requestFailCount: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    status: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    statusTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class FlowReservationRequest(IdentifiedObject):
    """Used to request flow transactions.

    Client EndDevices submit a request for charging or discharging from
    the server. The server creates an associated FlowReservationResponse
    containing the charging parameters and interval to provide a lower
    aggregated demand at the premises, or within a larger part of the
    distribution system.

    :ivar creationTime: The time at which the request was created.
    :ivar durationRequested: A value that is calculated by the storage
        device that defines the minimum duration, in seconds, that it
        will take to complete the actual flow transaction, including any
        ramp times and conditioning times, if applicable.
    :ivar energyRequested: Indicates the total amount of energy, in
        Watt-Hours, requested to be transferred between the storage
        device and the electric power system. Positive values indicate
        charging and negative values indicate discharging. This sign
        convention is different than for the DER function where
        discharging is positive.  Note that the energyRequestNow
        attribute in the PowerStatus Object must always represent a
        charging solution and it is not allowed to have a negative
        value.
    :ivar intervalRequested: The time window during which the flow
        reservation is needed. For example, if an electric vehicle is
        set with a 7:00 AM time charge is needed, and price drops to the
        lowest tier at 11:00 PM, then this window would likely be from
        11:00 PM until 7:00 AM.
    :ivar powerRequested: Indicates the sustained level of power, in
        Watts, that is requested. For charging this is calculated by the
        storage device and it represents the charging system capability
        (which for an electric vehicle must also account for any power
        limitations due to the EVSE control pilot). For discharging, a
        lower value than the inverter capability can be used as a
        target.
    :ivar RequestStatus:
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    creationTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    durationRequested: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    energyRequested: SignedRealEnergy | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    intervalRequested: DateTimeInterval | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    powerRequested: ActivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    RequestStatus: RequestStatus | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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
class IPAddrListLink(ListLink):
    """
    SHALL contain a Link to a List of IPAddr instances.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class IPInterfaceListLink(ListLink):
    """
    SHALL contain a Link to a List of IPInterface instances.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class LLInterfaceListLink(ListLink):
    """
    SHALL contain a Link to a List of LLInterface instances.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class LoadShedAvailability(Resource):
    """
    Indicates current consumption status and ability to shed load.

    :ivar availabilityDuration: Indicates for how many seconds the
        consuming device will be able to reduce consumption at the
        maximum response level.
    :ivar DemandResponseProgramLink:
    :ivar sheddablePercent: Maximum percent of current operating load
        that is estimated to be sheddable.
    :ivar sheddablePower: Maximum amount of current operating load that
        is estimated to be sheddable, in Watts.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    availabilityDuration: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    DemandResponseProgramLink: DemandResponseProgramLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    sheddablePercent: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    sheddablePower: ActivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
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
class NeighborList(List_type):
    """
    List of 15.4 neighbors.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    Neighbor: list[Neighbor] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
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

    :ivar newResourceURI: The new location of the resource, if moved.
        This attribute SHALL be a fully-qualified absolute URI, not a
        relative reference.
    :ivar Resource:
    :ivar status: 0 = Default Status 1 = Subscription canceled, no
        additional information 2 = Subscription canceled, resource moved
        3 = Subscription canceled, resource definition changed (e.g., a
        new version of IEEE 2030.5) 4 = Subscription canceled, resource
        deleted All other values reserved.
    :ivar subscriptionURI: The subscription from which this notification
        was triggered. This attribute SHALL be a fully-qualified
        absolute URI, not a relative reference.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    newResourceURI: str | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    Resource: Resource | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    status: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    subscriptionURI: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    :ivar batteryStatus: Battery system status 0 = unknown 1 = normal
        (more than LowChargeThreshold remaining) 2 = low (less than
        LowChargeThreshold remaining) 3 = depleted (0% charge remaining)
        4 = not applicable (mains powered only)
    :ivar changedTime: The time at which the reported values were
        recorded.
    :ivar currentPowerSource: This value will be fixed for devices
        powered by a single source.  This value may change for devices
        able to transition between multiple power sources (mains to
        battery backup, etc.).
    :ivar estimatedChargeRemaining: Estimate of remaining battery charge
        as a percent of full charge.
    :ivar estimatedTimeRemaining: Estimated time (in seconds) to total
        battery charge depletion (under current load)
    :ivar PEVInfo:
    :ivar sessionTimeOnBattery: If the device has a battery, this is the
        time since the device last switched to battery power, or the
        time since the device was restarted, whichever is less, in
        seconds.
    :ivar totalTimeOnBattery: If the device has a battery, this is the
        total time the device has been on battery power, in seconds. It
        may be reset when the battery is replaced.
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    batteryStatus: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    changedTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    currentPowerSource: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    estimatedChargeRemaining: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    estimatedTimeRemaining: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    PEVInfo: PEVInfo | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    sessionTimeOnBattery: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    totalTimeOnBattery: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
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

    :ivar consumeThreshold: Price responsive clients acting upon the
        associated RateComponent SHOULD consume the associated commodity
        while the price is less than this threshold.
    :ivar maxReductionThreshold: Price responsive clients acting upon
        the associated RateComponent SHOULD reduce consumption to the
        maximum extent possible while the price is greater than this
        threshold.
    :ivar RateComponentLink:
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    consumeThreshold: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    maxReductionThreshold: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    RateComponentLink: RateComponentLink | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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
class RPLInstanceListLink(ListLink):
    """
    SHALL contain a Link to a List of RPLInterface instances.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class RPLSourceRoutesList(List_type):
    """
    List or RPL source routes if the hosting device is the DODAGroot.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    RPLSourceRoutes: list[RPLSourceRoutes] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class RPLSourceRoutesListLink(ListLink):
    """
    SHALL contain a Link to a List of RPLSourceRoutes instances.
    """

    class Meta:
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

    :ivar localID: The local identifier for this reading within the
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

    localID: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 2,
            "format": "base16",
        },
    )
    subscribable: int = field(
        default=0,
        metadata={
            "type": "Attribute",
        },
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

    :ivar timePeriod: Specifies the time range during which the
        contained readings were taken.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    timePeriod: DateTimeInterval | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    :ivar mRID: The global identifier of the object.
    :ivar description: The description is a human readable text
        describing or naming the object.
    :ivar version: Contains the version number of the object. See the
        type definition for details.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    mRID: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 16,
            "format": "base16",
        },
    )
    description: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 32,
        },
    )
    version: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class RespondableSubscribableIdentifiedObject(RespondableResource):
    """
    An IdentifiedObject to which a Response can be requested.

    :ivar mRID: The global identifier of the object.
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

    mRID: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 16,
            "format": "base16",
        },
    )
    description: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 32,
        },
    )
    version: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    subscribable: int = field(
        default=0,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class ResponseList(List_type):
    """
    A List element to hold Response objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    Response: list[Response] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
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
    :ivar providerID: Contains the IANA PEN for the commodity provider.
    :ivar web: Website URI address for this service supplier.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    email: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 32,
        },
    )
    phone: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 20,
        },
    )
    providerID: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    web: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 42,
        },
    )


@dataclass
class SubscribableIdentifiedObject(SubscribableResource):
    """
    An IdentifiedObject to which a Subscription can be requested.

    :ivar mRID: The global identifier of the object.
    :ivar description: The description is a human readable text
        describing or naming the object.
    :ivar version: Contains the version number of the object. See the
        type definition for details.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    mRID: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 16,
            "format": "base16",
        },
    )
    description: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 32,
        },
    )
    version: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
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

    all: int | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    results: int | None = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class Subscription(SubscriptionBase):
    """
    Holds the information related to a client subscription to receive updates
    to a resource automatically.

    :ivar Condition:
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
    :ivar notificationURI: The resource to which to post the
        notifications about the requested subscribed resource. Because
        this URI will exist on a server other than the one being POSTed
        to, this attribute SHALL be a fully-qualified absolute URI, not
        a relative reference.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    Condition: Condition | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    encoding: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    level: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 16,
        },
    )
    limit: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    notificationURI: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class SubscriptionListLink(ListLink):
    """
    SHALL contain a Link to a List of Subscription instances.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class SupplyInterruptionOverrideList(List_type):
    """
    A List element to hold SupplyInterruptionOverride objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    SupplyInterruptionOverride: list[SupplyInterruptionOverride] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class SupplyInterruptionOverrideListLink(ListLink):
    """
    SHALL contain a Link to a List of SupplyInterruptionOverride instances.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"


@dataclass
class SupportedLocaleList(List_type):
    """
    A List element to hold SupportedLocale objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    SupportedLocale: list[SupportedLocale] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
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

    :ivar roleFlags: Specifies the roles that apply to the usage point.
    :ivar serviceCategoryKind: The kind of service provided by this
        usage point.
    :ivar status: Specifies the current status of the service at this
        usage point. 0 = off 1 = on
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    roleFlags: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 2,
            "format": "base16",
        },
    )
    serviceCategoryKind: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    status: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
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

    :ivar ConfigurationLink:
    :ivar DERListLink:
    :ivar deviceCategory: This field is for use in devices that can
        adjust energy usage (e.g., demand response, distributed energy
        resources).  For devices that do not respond to
        EndDeviceControls or DERControls (for instance, an ESI), this
        field should not have any bits set.
    :ivar DeviceInformationLink:
    :ivar DeviceStatusLink:
    :ivar FileStatusLink:
    :ivar IPInterfaceListLink:
    :ivar lFDI: Long form of device identifier. See the Security section
        for additional details.
    :ivar LoadShedAvailabilityListLink:
    :ivar LogEventListLink:
    :ivar PowerStatusLink:
    :ivar sFDI: Short form of device identifier, WITH the checksum
        digit. See the Security section for additional details.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    ConfigurationLink: ConfigurationLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    DERListLink: DERListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    deviceCategory: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 4,
            "format": "base16",
        },
    )
    DeviceInformationLink: DeviceInformationLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    DeviceStatusLink: DeviceStatusLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    FileStatusLink: FileStatusLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    IPInterfaceListLink: IPInterfaceListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    lFDI: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 20,
            "format": "base16",
        },
    )
    LoadShedAvailabilityListLink: LoadShedAvailabilityListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    LogEventListLink: LogEventListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    PowerStatusLink: PowerStatusLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    sFDI: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_inclusive": 281474976710655,
        },
    )


@dataclass
class BillingMeterReadingBase(MeterReadingBase):
    """
    Contains historical, target, and projection readings of various types,
    possibly associated with charges.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    BillingReadingSetListLink: BillingReadingSetListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ReadingTypeLink: ReadingTypeLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class BillingPeriodList(SubscribableList):
    """
    A List element to hold BillingPeriod objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    BillingPeriod: list[BillingPeriod] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class BillingReadingList(List_type):
    """
    A List element to hold BillingReading objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    BillingReading: list[BillingReading] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class BillingReadingSet(ReadingSetBase):
    """
    Time sequence of readings of the same reading type.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    BillingReadingListLink: BillingReadingListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class Configuration(SubscribableResource):
    """
    This resource contains various settings to control the operation of the
    device.

    :ivar currentLocale: [RFC 4646] identifier of the language-region
        currently in use.
    :ivar PowerConfiguration:
    :ivar PriceResponseCfgListLink:
    :ivar TimeConfiguration:
    :ivar userDeviceName: User assigned, convenience name used for
        network browsing displays, etc.  Example "My Thermostat"
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    currentLocale: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 42,
        },
    )
    PowerConfiguration: PowerConfiguration | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    PriceResponseCfgListLink: PriceResponseCfgListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    TimeConfiguration: TimeConfiguration | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    userDeviceName: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 32,
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class CreditRegisterList(List_type):
    """
    A List element to hold CreditRegister objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    CreditRegister: list[CreditRegister] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class CustomerAccount(IdentifiedObject):
    """Assignment of a group of products and services purchased by the Customer
    through a CustomerAgreement, used as a mechanism for customer billing and
    payment.

    It contains common information from the various types of
    CustomerAgreements to create billings (invoices) for a Customer and
    receive payment.

    :ivar currency: The ISO 4217 code indicating the currency applicable
        to the bill amounts in the summary. See list at
        http://www.unece.org/cefact/recommendations/rec09/rec09_ecetrd203.pdf
    :ivar customerAccount: The account number for the customer (if
        applicable).
    :ivar CustomerAgreementListLink:
    :ivar customerName: The name of the customer.
    :ivar pricePowerOfTenMultiplier: Indicates the power of ten
        multiplier for the prices in this function set.
    :ivar ServiceSupplierLink:
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    currency: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    customerAccount: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 42,
        },
    )
    CustomerAgreementListLink: CustomerAgreementListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    customerName: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 42,
        },
    )
    pricePowerOfTenMultiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    ServiceSupplierLink: ServiceSupplierLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class CustomerAgreement(IdentifiedObject):
    """Agreement between the customer and the service supplier to pay for
    service at a specific service location.

    It records certain billing information about the type of service
    provided at the service location and is used during charge creation
    to determine the type of service.

    :ivar ActiveBillingPeriodListLink:
    :ivar ActiveProjectionReadingListLink:
    :ivar ActiveTargetReadingListLink:
    :ivar BillingPeriodListLink:
    :ivar HistoricalReadingListLink:
    :ivar PrepaymentLink:
    :ivar ProjectionReadingListLink:
    :ivar serviceAccount: The account number of the service account (if
        applicable).
    :ivar serviceLocation: The address or textual description of the
        service location.
    :ivar TargetReadingListLink:
    :ivar TariffProfileLink:
    :ivar UsagePointLink:
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    ActiveBillingPeriodListLink: ActiveBillingPeriodListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ActiveProjectionReadingListLink: ActiveProjectionReadingListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ActiveTargetReadingListLink: ActiveTargetReadingListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    BillingPeriodListLink: BillingPeriodListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    HistoricalReadingListLink: HistoricalReadingListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    PrepaymentLink: PrepaymentLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ProjectionReadingListLink: ProjectionReadingListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    serviceAccount: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 42,
        },
    )
    serviceLocation: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 42,
        },
    )
    TargetReadingListLink: TargetReadingListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    TariffProfileLink: TariffProfileLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    UsagePointLink: UsagePointLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class DER(SubscribableResource):
    """
    Contains links to DER resources.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    AssociatedDERProgramListLink: AssociatedDERProgramListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    AssociatedUsagePointLink: AssociatedUsagePointLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    CurrentDERProgramLink: CurrentDERProgramLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    DERAvailabilityLink: DERAvailabilityLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    DERCapabilityLink: DERCapabilityLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    DERSettingsLink: DERSettingsLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    DERStatusLink: DERStatusLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class DERCurveList(List_type):
    """
    A List element to hold DERCurve objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    DERCurve: list[DERCurve] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class DERProgram(SubscribableIdentifiedObject):
    """
    Distributed Energy Resource program.

    :ivar ActiveDERControlListLink:
    :ivar DefaultDERControlLink:
    :ivar DERControlListLink:
    :ivar DERCurveListLink:
    :ivar primacy: Indicates the relative primacy of the provider of
        this Program.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    ActiveDERControlListLink: ActiveDERControlListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    DefaultDERControlLink: DefaultDERControlLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    DERControlListLink: DERControlListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    DERCurveListLink: DERCurveListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    primacy: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class DefaultDERControl(SubscribableIdentifiedObject):
    """
    Contains control mode information to be used if no active DERControl is
    found.

    :ivar DERControlBase:
    :ivar setESDelay: Enter service delay, in hundredths of a second.
        When present, this value SHALL update the value of the
        corresponding setting (DERSettings::setESDelay).
    :ivar setESHighFreq: Enter service frequency high. Specified in
        hundredths of Hz. When present, this value SHALL update the
        value of the corresponding setting (DERSettings::setESHighFreq).
    :ivar setESHighVolt: Enter service voltage high. Specified as an
        effective percent voltage, defined as (100% * (locally measured
        voltage - setVRefOfs) / setVRef), in hundredths of a percent.
        When present, this value SHALL update the value of the
        corresponding setting (DERSettings::setESHighVolt).
    :ivar setESLowFreq: Enter service frequency low. Specified in
        hundredths of Hz. When present, this value SHALL update the
        value of the corresponding setting (DERSettings::setESLowFreq).
    :ivar setESLowVolt: Enter service voltage low. Specified as an
        effective percent voltage, defined as (100% * (locally measured
        voltage - setVRefOfs) / setVRef), in hundredths of a percent.
        When present, this value SHALL update the value of the
        corresponding setting (DERSettings::setESLowVolt).
    :ivar setESRampTms: Enter service ramp time, in hundredths of a
        second. When present, this value SHALL update the value of the
        corresponding setting (DERSettings::setESRampTms).
    :ivar setESRandomDelay: Enter service randomized delay, in
        hundredths of a second. When present, this value SHALL update
        the value of the corresponding setting
        (DERSettings::setESRandomDelay).
    :ivar setGradW: Set default rate of change (ramp rate) of active
        power output due to command or internal action, defined in
        %setWMax / second.  Resolution is in hundredths of a
        percent/second. A value of 0 means there is no limit.
        Interpreted as a percentage change in output capability limit
        per second when used as a default ramp rate. When present, this
        value SHALL update the value of the corresponding setting
        (DERSettings::setGradW).
    :ivar setSoftGradW: Set soft-start rate of change (soft-start ramp
        rate) of active power output due to command or internal action,
        defined in %setWMax / second.  Resolution is in hundredths of a
        percent/second. A value of 0 means there is no limit.
        Interpreted as a percentage change in output capability limit
        per second when used as a ramp rate. When present, this value
        SHALL update the value of the corresponding setting
        (DERSettings::setSoftGradW).
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    DERControlBase: DERControlBase | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    setESDelay: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setESHighFreq: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setESHighVolt: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setESLowFreq: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setESLowVolt: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setESRampTms: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setESRandomDelay: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setGradW: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    setSoftGradW: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class DemandResponseProgram(IdentifiedObject):
    """
    Demand response program.

    :ivar ActiveEndDeviceControlListLink:
    :ivar availabilityUpdatePercentChangeThreshold: This attribute
        allows program providers to specify the requested granularity of
        updates to LoadShedAvailability sheddablePercent. If not
        present, or set to 0, then updates to LoadShedAvailability SHALL
        NOT be provided. If present and greater than zero, then clients
        SHALL provide their LoadShedAvailability if it has not
        previously been provided, and thereafter if the difference
        between the previously provided value and the current value of
        LoadShedAvailability sheddablePercent is greater than
        availabilityUpdatePercentChangeThreshold.
    :ivar availabilityUpdatePowerChangeThreshold: This attribute allows
        program providers to specify the requested granularity of
        updates to LoadShedAvailability sheddablePower. If not present,
        or set to 0, then updates to LoadShedAvailability SHALL NOT be
        provided. If present and greater than zero, then clients SHALL
        provide their LoadShedAvailability if it has not previously been
        provided, and thereafter if the difference between the
        previously provided value and the current value of
        LoadShedAvailability sheddablePower is greater than
        availabilityUpdatePowerChangeThreshold.
    :ivar EndDeviceControlListLink:
    :ivar primacy: Indicates the relative primacy of the provider of
        this program.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    ActiveEndDeviceControlListLink: ActiveEndDeviceControlListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    availabilityUpdatePercentChangeThreshold: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    availabilityUpdatePowerChangeThreshold: ActivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    EndDeviceControlListLink: EndDeviceControlListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    primacy: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class DeviceInformation(Resource):
    """
    Contains identification and other information about the device that changes
    very infrequently, typically only when updates are applied, if ever.

    :ivar DRLCCapabilities:
    :ivar functionsImplemented: Bitmap indicating the function sets used
        by the device as a client. 0 - Device Capability 1 - Self Device
        Resource 2 - End Device Resource 3 - Function Set Assignments 4
        - Subscription/Notification Mechanism 5 - Response 6 - Time 7 -
        Device Information 8 - Power Status 9 - Network Status 10 - Log
        Event 11 - Configuration Resource 12 - Software Download 13 -
        DRLC 14 - Metering 15 - Pricing 16 - Messaging 17 - Billing 18 -
        Prepayment 19 - Flow Reservation 20 - DER Control
    :ivar gpsLocation: GPS location of this device.
    :ivar lFDI: Long form device identifier. See the Security section
        for full details.
    :ivar mfDate: Date/time of manufacture
    :ivar mfHwVer: Manufacturer hardware version
    :ivar mfID: The manufacturer's IANA Enterprise Number.
    :ivar mfInfo: Manufacturer dependent information related to the
        manufacture of this device
    :ivar mfModel: Manufacturer's model number
    :ivar mfSerNum: Manufacturer assigned serial number
    :ivar primaryPower: Primary source of power.
    :ivar secondaryPower: Secondary source of power
    :ivar SupportedLocaleListLink:
    :ivar swActTime: Activation date/time of currently running software
    :ivar swVer: Currently running software version
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    DRLCCapabilities: DRLCCapabilities | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    functionsImplemented: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 8,
            "format": "base16",
        },
    )
    gpsLocation: GPSLocationType | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    lFDI: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 20,
            "format": "base16",
        },
    )
    mfDate: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    mfHwVer: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 32,
        },
    )
    mfID: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    mfInfo: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 32,
        },
    )
    mfModel: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 32,
        },
    )
    mfSerNum: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 32,
        },
    )
    primaryPower: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    secondaryPower: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    SupportedLocaleListLink: SupportedLocaleListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    swActTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    swVer: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 32,
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class Event(RespondableSubscribableIdentifiedObject):
    """An Event indicates information that applies to a particular period of
    time.

    Events SHALL be executed relative to the time of the server, as
    described in the Time function set section 11.1.

    :ivar creationTime: The time at which the Event was created.
    :ivar EventStatus:
    :ivar interval: The period during which the Event applies.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    creationTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    EventStatus: EventStatus | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    interval: DateTimeInterval | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class FlowReservationRequestList(List_type):
    """
    A List element to hold FlowReservationRequest objects.

    :ivar FlowReservationRequest:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    FlowReservationRequest: list[FlowReservationRequest] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class FunctionSetAssignmentsBase(Resource):
    """
    Defines a collection of function set instances that are to be used by one
    or more devices as indicated by the EndDevice object(s) of the server.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    CustomerAccountListLink: CustomerAccountListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    DemandResponseProgramListLink: DemandResponseProgramListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    DERProgramListLink: DERProgramListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    FileListLink: FileListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    MessagingProgramListLink: MessagingProgramListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    PrepaymentListLink: PrepaymentListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ResponseSetListLink: ResponseSetListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    TariffProfileListLink: TariffProfileListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    TimeLink: TimeLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    UsagePointListLink: UsagePointListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class IEEE_802_15_4:
    """
    Contains 802.15.4 link layer specific attributes.

    :ivar capabilityInfo: As defined by IEEE 802.15.4
    :ivar NeighborListLink:
    :ivar shortAddress: As defined by IEEE 802.15.4
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    capabilityInfo: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 1,
            "format": "base16",
        },
    )
    NeighborListLink: NeighborListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    shortAddress: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class IPAddr(Resource):
    """
    An Internet Protocol address object.

    :ivar address: An IP address value.
    :ivar RPLInstanceListLink:
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    address: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 16,
            "format": "base16",
        },
    )
    RPLInstanceListLink: RPLInstanceListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class IPInterface(Resource):
    """Specific IPInterface resource.

    This resource may be thought of as network status information for a
    specific network (IP) layer interface.

    :ivar ifDescr: Use rules from [RFC 2863].
    :ivar ifHighSpeed: Use rules from [RFC 2863].
    :ivar ifInBroadcastPkts: Use rules from [RFC 2863].
    :ivar ifIndex: Use rules from [RFC 2863].
    :ivar ifInDiscards: Use rules from [RFC 2863]. Can be thought of as
        Input Datagrams Discarded.
    :ivar ifInErrors: Use rules from [RFC 2863].
    :ivar ifInMulticastPkts: Use rules from [RFC 2863]. Can be thought
        of as Multicast Datagrams Received.
    :ivar ifInOctets: Use rules from [RFC 2863]. Can be thought of as
        Bytes Received.
    :ivar ifInUcastPkts: Use rules from [RFC 2863]. Can be thought of as
        Datagrams Received.
    :ivar ifInUnknownProtos: Use rules from [RFC 2863]. Can be thought
        of as Datagrams with Unknown Protocol Received.
    :ivar ifMtu: Use rules from [RFC 2863].
    :ivar ifName: Use rules from [RFC 2863].
    :ivar ifOperStatus: Use rules and assignments from [RFC 2863].
    :ivar ifOutBroadcastPkts: Use rules from [RFC 2863]. Can be thought
        of as Broadcast Datagrams Sent.
    :ivar ifOutDiscards: Use rules from [RFC 2863]. Can be thought of as
        Output Datagrams Discarded.
    :ivar ifOutErrors: Use rules from [RFC 2863].
    :ivar ifOutMulticastPkts: Use rules from [RFC 2863]. Can be thought
        of as Multicast Datagrams Sent.
    :ivar ifOutOctets: Use rules from [RFC 2863]. Can be thought of as
        Bytes Sent.
    :ivar ifOutUcastPkts: Use rules from [RFC 2863]. Can be thought of
        as Datagrams Sent.
    :ivar ifPromiscuousMode: Use rules from [RFC 2863].
    :ivar ifSpeed: Use rules from [RFC 2863].
    :ivar ifType: Use rules and assignments from [RFC 2863].
    :ivar IPAddrListLink:
    :ivar lastResetTime: Similar to ifLastChange in [RFC 2863].
    :ivar lastUpdatedTime: The date/time of the reported status.
    :ivar LLInterfaceListLink:
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    ifDescr: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 192,
        },
    )
    ifHighSpeed: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ifInBroadcastPkts: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ifIndex: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ifInDiscards: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ifInErrors: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ifInMulticastPkts: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ifInOctets: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ifInUcastPkts: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ifInUnknownProtos: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ifMtu: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ifName: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 16,
        },
    )
    ifOperStatus: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ifOutBroadcastPkts: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ifOutDiscards: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ifOutErrors: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ifOutMulticastPkts: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ifOutOctets: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ifOutUcastPkts: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ifPromiscuousMode: bool | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ifSpeed: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ifType: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    IPAddrListLink: IPAddrListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    lastResetTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    lastUpdatedTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    LLInterfaceListLink: LLInterfaceListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class LoadShedAvailabilityList(List_type):
    """
    A List element to hold LoadShedAvailability objects.

    :ivar LoadShedAvailability:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    LoadShedAvailability: list[LoadShedAvailability] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class LogEventList(SubscribableList):
    """
    A List element to hold LogEvent objects.

    :ivar LogEvent:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    LogEvent: list[LogEvent] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class MessagingProgram(SubscribableIdentifiedObject):
    """
    Provides a container for collections of text messages.

    :ivar ActiveTextMessageListLink:
    :ivar locale: Indicates the language and region of the messages in
        this collection.
    :ivar primacy: Indicates the relative primacy of the provider of
        this program.
    :ivar TextMessageListLink:
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    ActiveTextMessageListLink: ActiveTextMessageListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    locale: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 42,
        },
    )
    primacy: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    TextMessageListLink: TextMessageListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class MeterReading(MeterReadingBase):
    """
    Set of values obtained from the meter.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    RateComponentListLink: RateComponentListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ReadingLink: ReadingLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ReadingSetListLink: ReadingSetListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ReadingTypeLink: ReadingTypeLink | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class MirrorReadingSet(ReadingSetBase):
    """
    A set of Readings of the ReadingType indicated by the parent MeterReading.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    Reading: list[Reading] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class NotificationList(List_type):
    """
    A List element to hold Notification objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    Notification: list[Notification] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class PriceResponseCfgList(List_type):
    """
    A List element to hold PriceResponseCfg objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    PriceResponseCfg: list[PriceResponseCfg] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class RPLInstance(Resource):
    """Specific RPLInstance resource.

    This resource may be thought of as network status information for a
    specific RPL instance associated with IPInterface.

    :ivar DODAGid: See [RFC 6550].
    :ivar DODAGroot: See [RFC 6550].
    :ivar flags: See [RFC 6550].
    :ivar groundedFlag: See [RFC 6550].
    :ivar MOP: See [RFC 6550].
    :ivar PRF: See [RFC 6550].
    :ivar rank: See [RFC 6550].
    :ivar RPLInstanceID: See [RFC 6550].
    :ivar RPLSourceRoutesListLink:
    :ivar versionNumber: See [RFC 6550].
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    DODAGid: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    DODAGroot: bool | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    flags: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    groundedFlag: bool | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    MOP: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    PRF: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    rank: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    RPLInstanceID: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    RPLSourceRoutesListLink: RPLSourceRoutesListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    versionNumber: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class RateComponent(IdentifiedObject):
    """
    Specifies the applicable charges for a single component of the rate, which
    could be generation price or consumption price, for example.

    :ivar ActiveTimeTariffIntervalListLink:
    :ivar flowRateEndLimit: Specifies the maximum flow rate (e.g. kW for
        electricity) for which this RateComponent applies, for the usage
        point and given rate / tariff. In combination with
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
    :ivar flowRateStartLimit: Specifies the minimum flow rate (e.g., kW
        for electricity) for which this RateComponent applies, for the
        usage point and given rate / tariff. In combination with
        flowRateEndLimit, allows a service provider to define the demand
        or output characteristics for the particular tariff design.  If
        a server includes the flowRateStartLimit attribute, then it
        SHALL also include flowRateEndLimit attribute.
    :ivar ReadingTypeLink: Provides indication of the ReadingType with
        which this price is associated.
    :ivar roleFlags: Specifies the roles that this usage point has been
        assigned.
    :ivar TimeTariffIntervalListLink:
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    ActiveTimeTariffIntervalListLink: ActiveTimeTariffIntervalListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    flowRateEndLimit: UnitValueType | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    flowRateStartLimit: UnitValueType | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ReadingTypeLink: ReadingTypeLink | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    roleFlags: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 2,
            "format": "base16",
        },
    )
    TimeTariffIntervalListLink: TimeTariffIntervalListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class ReadingList(SubscribableList):
    """
    A List element to hold Reading objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    Reading: list[Reading] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class ReadingSet(ReadingSetBase):
    """
    A set of Readings of the ReadingType indicated by the parent MeterReading.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    ReadingListLink: ReadingListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class ResponseSet(IdentifiedObject):
    """
    A container for a ResponseList.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    ResponseListLink: ResponseListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class ServiceSupplierList(List_type):
    """
    A List element to hold ServiceSupplier objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    ServiceSupplier: list[ServiceSupplier] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class SubscriptionList(List_type):
    """
    A List element to hold Subscription objects.

    :ivar Subscription:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    Subscription: list[Subscription] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class TariffProfile(IdentifiedObject):
    """
    A schedule of charges; structure that allows the definition of tariff
    structures such as step (block) and time of use (tier) when used in
    conjunction with TimeTariffInterval and ConsumptionTariffInterval.

    :ivar currency: The currency code indicating the currency for this
        TariffProfile.
    :ivar pricePowerOfTenMultiplier: Indicates the power of ten
        multiplier for the price attribute.
    :ivar primacy: Indicates the relative primacy of the provider of
        this program.
    :ivar rateCode: The rate code for this tariff profile.  Provided by
        the Pricing service provider per its internal business needs and
        practices and provides a method to identify the specific rate
        code for the TariffProfile instance.  This would typically not
        be communicated to the user except to facilitate troubleshooting
        due to its service provider-specific technical nature.
    :ivar RateComponentListLink:
    :ivar serviceCategoryKind: The kind of service provided by this
        usage point.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    currency: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    pricePowerOfTenMultiplier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    primacy: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    rateCode: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 20,
        },
    )
    RateComponentListLink: RateComponentListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    serviceCategoryKind: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class UsagePoint(UsagePointBase):
    """
    Logical point on a network at which consumption or production is either
    physically measured (e.g. metered) or estimated (e.g. unmetered street
    lights).

    :ivar deviceLFDI: The LFDI of the source device. This attribute
        SHALL be present when mirroring.
    :ivar MeterReadingListLink:
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    deviceLFDI: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 20,
            "format": "base16",
        },
    )
    MeterReadingListLink: MeterReadingListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class BillingReadingSetList(SubscribableList):
    """
    A List element to hold BillingReadingSet objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    BillingReadingSet: list[BillingReadingSet] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class CustomerAccountList(SubscribableList):
    """
    A List element to hold CustomerAccount objects.

    :ivar CustomerAccount:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    CustomerAccount: list[CustomerAccount] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class CustomerAgreementList(SubscribableList):
    """
    A List element to hold CustomerAgreement objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    CustomerAgreement: list[CustomerAgreement] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class DERList(List_type):
    """
    A List element to hold DER objects.

    :ivar DER:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    DER: list[DER] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class DERProgramList(SubscribableList):
    """
    A List element to hold DERProgram objects.

    :ivar DERProgram:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    DERProgram: list[DERProgram] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class DemandResponseProgramList(SubscribableList):
    """
    A List element to hold DemandResponseProgram objects.

    :ivar DemandResponseProgram:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    DemandResponseProgram: list[DemandResponseProgram] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class DeviceCapability(FunctionSetAssignmentsBase):
    """
    Returned by the URI provided by DNS-SD, to allow clients to find the URIs
    to the resources in which they are interested.

    :ivar EndDeviceListLink:
    :ivar MirrorUsagePointListLink:
    :ivar SelfDeviceLink:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    EndDeviceListLink: EndDeviceListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    MirrorUsagePointListLink: MirrorUsagePointListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    SelfDeviceLink: SelfDeviceLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class EndDevice(AbstractDevice):
    """Asset container that performs one or more end device functions.

    Contains information about individual devices in the network.

    :ivar changedTime: The time at which this resource was last modified
        or created.
    :ivar enabled: This attribute indicates whether or not an EndDevice
        is enabled, or registered, on the server. If a server sets this
        attribute to false, the device is no longer registered. It
        should be noted that servers can delete EndDevice instances, but
        using this attribute for some time is more convenient for
        clients.
    :ivar FlowReservationRequestListLink:
    :ivar FlowReservationResponseListLink:
    :ivar FunctionSetAssignmentsListLink:
    :ivar postRate: POST rate, or how often EndDevice and subordinate
        resources should be POSTed, in seconds. A client MAY indicate a
        preferred postRate when POSTing EndDevice. A server MAY add or
        modify postRate to indicate its preferred posting rate.
    :ivar RegistrationLink:
    :ivar SubscriptionListLink:
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    changedTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    enabled: bool | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    FlowReservationRequestListLink: FlowReservationRequestListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    FlowReservationResponseListLink: FlowReservationResponseListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    FunctionSetAssignmentsListLink: FunctionSetAssignmentsListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    postRate: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    RegistrationLink: RegistrationLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    SubscriptionListLink: SubscriptionListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class FlowReservationResponse(Event):
    """
    The server may modify the charging or discharging parameters and interval
    to provide a lower aggregated demand at the premises, or within a larger
    part of the distribution system.

    :ivar energyAvailable: Indicates the amount of energy available.
    :ivar powerAvailable: Indicates the amount of power available.
    :ivar subject: The subject field provides a method to match the
        response with the originating event. It is populated with the
        mRID of the corresponding FlowReservationRequest object.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    energyAvailable: SignedRealEnergy | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    powerAvailable: ActivePower | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    subject: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 16,
            "format": "base16",
        },
    )


@dataclass
class FunctionSetAssignments(FunctionSetAssignmentsBase):
    """
    Provides an identifiable, subscribable collection of resources for a
    particular device to consume.

    :ivar mRID: The global identifier of the object.
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

    mRID: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 16,
            "format": "base16",
        },
    )
    description: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 32,
        },
    )
    version: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    subscribable: int = field(
        default=0,
        metadata={
            "type": "Attribute",
        },
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
class IPAddrList(List_type):
    """
    List of IPAddr instances.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    IPAddr: list[IPAddr] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class IPInterfaceList(List_type):
    """
    List of IPInterface instances.

    :ivar IPInterface:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    IPInterface: list[IPInterface] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class LLInterface(Resource):
    """
    A link-layer interface object.

    :ivar CRCerrors: Contains the number of CRC errors since reset.
    :ivar EUI64: Contains the EUI-64 of the link layer interface. 48 bit
        MAC addresses SHALL be changed into an EUI-64 using the method
        defined in [RFC 4291], Appendix A. (The method is to insert
        "0xFFFE" as described in the reference.)
    :ivar IEEE_802_15_4:
    :ivar linkLayerType: Specifies the type of link layer interface
        associated with the IPInterface. Values are below. 0 =
        Unspecified 1 = IEEE 802.3 (Ethernet) 2 = IEEE 802.11 (WLAN) 3 =
        IEEE 802.15 (PAN) 4 = IEEE 1901 (PLC) All other values reserved.
    :ivar LLAckNotRx: Number of times an ACK was not received for a
        frame transmitted (when ACK was requested).
    :ivar LLCSMAFail: Number of times CSMA failed.
    :ivar LLFramesDropRx: Number of dropped receive frames.
    :ivar LLFramesDropTx: Number of dropped transmit frames.
    :ivar LLFramesRx: Number of link layer frames received.
    :ivar LLFramesTx: Number of link layer frames transmitted.
    :ivar LLMediaAccessFail: Number of times access to media failed.
    :ivar LLOctetsRx: Number of Bytes received.
    :ivar LLOctetsTx: Number of Bytes transmitted.
    :ivar LLRetryCount: Number of MAC transmit retries.
    :ivar LLSecurityErrorRx: Number of receive security errors.
    :ivar loWPAN:
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    CRCerrors: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    EUI64: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 8,
            "format": "base16",
        },
    )
    IEEE_802_15_4: IEEE_802_15_4 | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    linkLayerType: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    LLAckNotRx: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    LLCSMAFail: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    LLFramesDropRx: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    LLFramesDropTx: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    LLFramesRx: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    LLFramesTx: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    LLMediaAccessFail: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    LLOctetsRx: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    LLOctetsTx: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    LLRetryCount: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    LLSecurityErrorRx: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    loWPAN: loWPAN | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class MessagingProgramList(SubscribableList):
    """
    A List element to hold MessagingProgram objects.

    :ivar MessagingProgram:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    MessagingProgram: list[MessagingProgram] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class MeterReadingList(SubscribableList):
    """
    A List element to hold MeterReading objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    MeterReading: list[MeterReading] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class MirrorMeterReading(MeterReadingBase):
    """
    Mimic of MeterReading used for managing mirrors.

    :ivar lastUpdateTime: The date and time of the last update.
    :ivar MirrorReadingSet:
    :ivar nextUpdateTime: The date and time of the next planned update.
    :ivar Reading:
    :ivar ReadingType:
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    lastUpdateTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    MirrorReadingSet: list[MirrorReadingSet] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    nextUpdateTime: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    Reading: Reading | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ReadingType: ReadingType | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class Prepayment(IdentifiedObject):
    """
    Prepayment (inherited from CIM SDPAccountingFunction)

    :ivar AccountBalanceLink:
    :ivar ActiveCreditRegisterListLink:
    :ivar ActiveSupplyInterruptionOverrideListLink:
    :ivar creditExpiryLevel: CreditExpiryLevel is the set point for
        availableCredit at which the service level may be changed. The
        typical value for this attribute is 0, regardless of whether the
        account balance is measured in a monetary or commodity basis.
        The units for this attribute SHALL match the units used for
        availableCredit.
    :ivar CreditRegisterListLink:
    :ivar lowCreditWarningLevel: LowCreditWarningLevel is the set point
        for availableCredit at which the creditStatus attribute in the
        AccountBalance resource SHALL indicate that available credit is
        low. The units for this attribute SHALL match the units used for
        availableCredit. Typically, this value is set by the service
        provider.
    :ivar lowEmergencyCreditWarningLevel: LowEmergencyCreditWarningLevel
        is the set point for emergencyCredit at which the creditStatus
        attribute in the AccountBalance resource SHALL indicate that
        emergencycredit is low. The units for this attribute SHALL match
        the units used for availableCredit. Typically, this value is set
        by the service provider.
    :ivar prepayMode: PrepayMode specifies whether the given Prepayment
        instance is operating in Credit, Central Wallet, ESI, or Local
        prepayment mode. The Credit mode indicates that prepayment is
        not presently in effect. The other modes are described in the
        Overview Section above.
    :ivar PrepayOperationStatusLink:
    :ivar SupplyInterruptionOverrideListLink:
    :ivar UsagePoint:
    :ivar UsagePointLink:
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    AccountBalanceLink: AccountBalanceLink | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    ActiveCreditRegisterListLink: ActiveCreditRegisterListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ActiveSupplyInterruptionOverrideListLink: ActiveSupplyInterruptionOverrideListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    creditExpiryLevel: AccountingUnit | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    CreditRegisterListLink: CreditRegisterListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    lowCreditWarningLevel: AccountingUnit | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    lowEmergencyCreditWarningLevel: AccountingUnit | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    prepayMode: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    PrepayOperationStatusLink: PrepayOperationStatusLink | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    SupplyInterruptionOverrideListLink: SupplyInterruptionOverrideListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    UsagePoint: list[UsagePoint] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    UsagePointLink: UsagePointLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
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
class RPLInstanceList(List_type):
    """
    List of RPLInstances associated with the IPinterface.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    RPLInstance: list[RPLInstance] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class RandomizableEvent(Event):
    """
    An Event that can indicate time ranges over which the start time and
    duration SHALL be randomized.

    :ivar randomizeDuration: Number of seconds boundary inside which a
        random value must be selected to be applied to the associated
        interval duration, to avoid sudden synchronized demand changes.
        If related to price level changes, sign may be ignored. Valid
        range is -3600 to 3600. If not specified, 0 is the default.
    :ivar randomizeStart: Number of seconds boundary inside which a
        random value must be selected to be applied to the associated
        interval start time, to avoid sudden synchronized demand
        changes. If related to price level changes, sign may be ignored.
        Valid range is -3600 to 3600. If not specified, 0 is the
        default.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    randomizeDuration: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    randomizeStart: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class RateComponentList(List_type):
    """
    A List element to hold RateComponent objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    RateComponent: list[RateComponent] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class ReadingSetList(SubscribableList):
    """
    A List element to hold ReadingSet objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    ReadingSet: list[ReadingSet] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class ResponseSetList(List_type):
    """
    A List element to hold ResponseSet objects.

    :ivar ResponseSet:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    ResponseSet: list[ResponseSet] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class SelfDevice(AbstractDevice):
    """
    The EndDevice providing the resources available within the
    DeviceCapabilities.

    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
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

    :ivar TariffProfile:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    TariffProfile: list[TariffProfile] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
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
    :ivar textMessage: The textMessage attribute contains the actual
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

    originator: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 20,
        },
    )
    priority: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    textMessage: str | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class UsagePointList(SubscribableList):
    """
    A List element to hold UsagePoint objects.

    :ivar UsagePoint:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    UsagePoint: list[UsagePoint] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class DERControl(RandomizableEvent):
    """
    Distributed Energy Resource (DER) time/event-based control.

    :ivar DERControlBase:
    :ivar deviceCategory: Specifies the bitmap indicating  the
        categories of devices that SHOULD respond. Devices SHOULD ignore
        events that do not indicate their device category. If not
        present, all devices SHOULD respond.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    DERControlBase: DERControlBase | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    deviceCategory: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "max_length": 4,
            "format": "base16",
        },
    )


@dataclass
class EndDeviceControl(RandomizableEvent):
    """
    Instructs an EndDevice to perform a specified action.

    :ivar ApplianceLoadReduction:
    :ivar deviceCategory: Specifies the bitmap indicating  the
        categories of devices that SHOULD respond. Devices SHOULD ignore
        events that do not indicate their device category.
    :ivar drProgramMandatory: A flag to indicate if the EndDeviceControl
        is considered a mandatory event as defined by the service
        provider issuing the EndDeviceControl. The drProgramMandatory
        flag alerts the client/user that they will be subject to penalty
        or ineligibility based on the service provider’s program rules
        for that deviceCategory.
    :ivar DutyCycle:
    :ivar loadShiftForward: Indicates that the event intends to increase
        consumption. A value of true indicates the intention to increase
        usage value, and a value of false indicates the intention to
        decrease usage.
    :ivar Offset:
    :ivar overrideDuration: The overrideDuration attribute provides a
        duration, in seconds, for which a client device is allowed to
        override this EndDeviceControl and still meet the contractual
        agreement with a service provider without opting out. If
        overrideDuration is not specified, then it SHALL default to 0.
    :ivar SetPoint:
    :ivar TargetReduction:
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    ApplianceLoadReduction: ApplianceLoadReduction | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    deviceCategory: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 4,
            "format": "base16",
        },
    )
    drProgramMandatory: bool | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    DutyCycle: DutyCycle | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    loadShiftForward: bool | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    Offset: Offset | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    overrideDuration: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    SetPoint: SetPoint | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    TargetReduction: TargetReduction | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class EndDeviceList(SubscribableList):
    """
    A List element to hold EndDevice objects.

    :ivar EndDevice:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    EndDevice: list[EndDevice] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class FlowReservationResponseList(SubscribableList):
    """
    A List element to hold FlowReservationResponse objects.

    :ivar FlowReservationResponse:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    FlowReservationResponse: list[FlowReservationResponse] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class FunctionSetAssignmentsList(SubscribableList):
    """
    A List element to hold FunctionSetAssignments objects.

    :ivar FunctionSetAssignments:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    FunctionSetAssignments: list[FunctionSetAssignments] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class HistoricalReadingList(List_type):
    """
    A List element to hold HistoricalReading objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    HistoricalReading: list[HistoricalReading] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class LLInterfaceList(List_type):
    """
    List of LLInterface instances.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    LLInterface: list[LLInterface] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class MirrorMeterReadingList(List_type):
    """
    A List of MirrorMeterReading instances.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    MirrorMeterReading: list[MirrorMeterReading] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class MirrorUsagePoint(UsagePointBase):
    """
    A parallel to UsagePoint to support mirroring.

    :ivar deviceLFDI: The LFDI of the device being mirrored.
    :ivar MirrorMeterReading:
    :ivar postRate: POST rate, or how often mirrored data should be
        POSTed, in seconds. A client MAY indicate a preferred postRate
        when POSTing MirrorUsagePoint. A server MAY add or modify
        postRate to indicate its preferred posting rate.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    deviceLFDI: bytes | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 20,
            "format": "base16",
        },
    )
    MirrorMeterReading: list[MirrorMeterReading] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    postRate: int | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class PrepaymentList(SubscribableList):
    """
    A List element to hold Prepayment objects.

    :ivar Prepayment:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    Prepayment: list[Prepayment] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class ProjectionReadingList(List_type):
    """
    A List element to hold ProjectionReading objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    ProjectionReading: list[ProjectionReading] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class TargetReadingList(List_type):
    """
    A List element to hold TargetReading objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    TargetReading: list[TargetReading] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class TextMessageList(SubscribableList):
    """
    A List element to hold TextMessage objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    TextMessage: list[TextMessage] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class TimeTariffInterval(RandomizableEvent):
    """
    Describes the time-differentiated portion of the RateComponent, if
    applicable, and provides the ability to specify multiple time intervals,
    each with its own consumption-based components and other attributes.

    :ivar ConsumptionTariffIntervalListLink:
    :ivar touTier: Indicates the time of use tier related to the
        reading. If not specified, is assumed to be "0 - N/A".
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    ConsumptionTariffIntervalListLink: ConsumptionTariffIntervalListLink | None = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    touTier: int | None = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class DERControlList(SubscribableList):
    """
    A List element to hold DERControl objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    DERControl: list[DERControl] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class EndDeviceControlList(SubscribableList):
    """
    A List element to hold EndDeviceControl objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    EndDeviceControl: list[EndDeviceControl] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )


@dataclass
class MirrorUsagePointList(List_type):
    """
    A List of MirrorUsagePoint instances.

    :ivar MirrorUsagePoint:
    :ivar pollRate: The default polling rate for this function set (this
        resource and all resources below), in seconds. If not specified,
        a default of 900 seconds (15 minutes) is used. It is RECOMMENDED
        a client poll the resources of this function set every pollRate
        seconds.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    MirrorUsagePoint: list[MirrorUsagePoint] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    pollRate: int = field(
        default=900,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class TimeTariffIntervalList(SubscribableList):
    """
    A List element to hold TimeTariffInterval objects.
    """

    class Meta:
        namespace = "urn:ieee:std:2030.5:ns"

    TimeTariffInterval: list[TimeTariffInterval] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
