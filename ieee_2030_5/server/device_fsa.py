"""
Create device-specific Function Set Assignments (FSA).
Each device gets its own FSA with its own DERProgram and DERControlList.
"""

import copy
import logging

import ieee_2030_5.adapters as adpt
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.data.indexer import add_href
from ieee_2030_5.persistance.points import atomic_operation

_log = logging.getLogger(__name__)


def create_device_fsa_with_program(device_href: str, config: ServerConfiguration) -> m.FunctionSetAssignments | None:
    """
    Create a device-specific FSA with its own DERProgram and DERControlList.

    This allows GridAPPS-D to control each device individually by giving each
    device its own control list.

    Args:
        device_href: The device's href (e.g., "/edev_23030")
        config: Server configuration containing default_program template

    Returns:
        The created FunctionSetAssignments object or None if no default program
    """
    if not config.default_program:
        _log.info("No default program configured, skipping device FSA creation")
        return None

    with atomic_operation():
        # FSA list is at /edev_23030_fsa
        fsa_list_href = f"{device_href}_fsa"

        # Initialize the FSA list for this device
        adpt.ListAdapter.initialize_uri(fsa_list_href, m.FunctionSetAssignments)

        # Create device-specific FSA at /edev_23030_fsa_0
        fsa_href = hrefs.SEP.join((fsa_list_href, "0"))

        fsa = m.FunctionSetAssignments(
            href=fsa_href,
            mRID=adpt.get_global_mrids().new_mrid(),
            description="device_fsa",
            subscribable=1,
        )

        # Create DER program list for this device's FSA
        derp_list_href = hrefs.SEP.join((fsa_href, "derp"))
        adpt.ListAdapter.initialize_uri(derp_list_href, m.DERProgram)

        # Create a copy of the default DER program for this device
        device_program = copy.deepcopy(config.default_program)
        device_program.href = hrefs.SEP.join((derp_list_href, "0"))
        device_program.mRID = adpt.get_global_mrids().new_mrid()

        # Initialize the DER control list for this device's program
        derc_list_href = hrefs.SEP.join((device_program.href, "derc"))
        adpt.ListAdapter.initialize_uri(derc_list_href, m.DERControl)

        # Set the control list link (starts empty)
        device_program.DERControlListLink = m.DERControlListLink(
            href=derc_list_href,
            all=0,  # Empty initially
        )

        # Set up DefaultDERControl for this device if configured
        if config.default_der_control:
            dderc_href = hrefs.SEP.join((device_program.href, "dderc"))

            default_der_control = copy.deepcopy(config.default_der_control)
            default_der_control.href = dderc_href
            default_der_control.mRID = adpt.get_global_mrids().new_mrid()

            # Store the DefaultDERControl
            result = adpt.ListAdapter.set_single(dderc_href, default_der_control)
            if result.success:
                device_program.DefaultDERControlLink = m.DefaultDERControlLink(href=dderc_href)
                add_href(dderc_href, default_der_control)
                # Note: set_single() already registers the mRID automatically, no need to call add_item_with_mrid()
                _log.info("Created DefaultDERControl at %s for device %s", dderc_href, device_href)
            else:
                _log.error(
                    "Failed to create DefaultDERControl for device %s: %s",
                    device_href,
                    result.error,
                )

        # Add the program to the device's FSA program list
        result = adpt.ListAdapter.append(derp_list_href, device_program)
        if not result.success:
            raise Exception(f"Failed to add program to device FSA {fsa_href}: {result.error}")

        # Set the DER program list link on the FSA
        fsa.DERProgramListLink = m.DERProgramListLink(
            href=derp_list_href,
            all=1,  # One program
        )

        # Add the FSA to the device's FSA list
        result = adpt.ListAdapter.append(fsa_list_href, fsa)
        if not result.success:
            raise Exception(f"Failed to add FSA to device list {fsa_list_href}: {result.error}")

        # Register in href indexer and mRID registry
        add_href(fsa.href, fsa)
        adpt.get_global_mrids().add_item_with_mrid(fsa.href, fsa)
        add_href(device_program.href, device_program)
        adpt.get_global_mrids().add_item_with_mrid(device_program.href, device_program)

        _log.info(
            "Created device-specific FSA at %s with program at %s and control list at %s",
            fsa.href,
            device_program.href,
            derc_list_href,
        )

        return fsa
