import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.adapters import Adapter

DERCurveAdapter = Adapter[m.DERCurve](hrefs.curve_href(), generic_type=m.DERCurve)

DERControlAdapter = Adapter[m.DERControl]("/derc", generic_type=m.DERControl)
DERProgramAdapter = Adapter[m.DERProgram](hrefs.der_program_href(), generic_type=m.DERProgram)
FunctionSetAssignmentsAdapter = Adapter[m.FunctionSetAssignments](url_prefix=hrefs.fsa_href(), generic_type=m.FunctionSetAssignments)

EndDeviceAdapter = Adapter[m.EndDevice](hrefs.get_enddevice_href(), generic_type=m.EndDevice)
DeviceCapabilityAdapter = Adapter[m.DeviceCapability]("/dcap", generic_type=m.DeviceCapability)
# Generally the href will only be in the context of an end device.
RegistrationAdapter = Adapter[m.Registration](url_prefix="/reg", generic_type=m.Registration)
FunctionSetAssignmentsAdapter = Adapter[m.FunctionSetAssignments](url_prefix="/fsa", generic_type=m.FunctionSetAssignments)


# EndDeviceDeviceStatusAdapter = Adapter[m.DeviceStatus](hrefs.get_enddevice_device_status_href(), generic_type=m.DeviceStatus)
# EndDeviceDeviceInfoAdapter = Adapter[m.DeviceInformation](hrefs.get_enddevice_device_info_href(), generic_type=m.DeviceInformation)

# EndDevicePowerStatusAdapter = Adapter[m.PowerStatus](hrefs.get_enddevice_power_status_href(), generic_type=m.PowerStatus)

# EndDeviceConfigurationAdapter = Adapter[m.Configuration](hrefs.get_enddevice_configuration_href(), generic_type=m.Configuration)

