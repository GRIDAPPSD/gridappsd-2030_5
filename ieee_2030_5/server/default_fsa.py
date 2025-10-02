"""
Create and manage a default Function Set Assignment (FSA) with the default program.
This FSA is shared by all devices but each device gets individual controls.
"""

import logging

import ieee_2030_5.adapters as adpt
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.data.indexer import add_href
from ieee_2030_5.persistance.points import atomic_operation

_log = logging.getLogger(__name__)

# Global reference to the default FSA
_default_fsa_href: str | None = None


def create_default_fsa_with_program(
    config: ServerConfiguration,
) -> m.FunctionSetAssignments | None:
    """
    Create a shared default FSA containing the default DER program from config.
    This FSA can be referenced by all devices but each will get their own controls.

    Args:
        config: Server configuration containing default_program

    Returns:
        The created FunctionSetAssignments object or None if no default program
    """
    global _default_fsa_href

    if not config.default_program:
        _log.info("No default program configured, skipping default FSA creation")
        return None

    # Check if default FSA already exists
    if _default_fsa_href:
        from ieee_2030_5.data.indexer import get_href

        existing = get_href(_default_fsa_href)
        if existing:
            _log.debug(f"Default FSA already exists at {_default_fsa_href}")
            return existing

    with atomic_operation():
        # Create the default FSA at a well-known location
        _default_fsa_href = "/fsa/default"

        # Create the FSA object
        fsa = m.FunctionSetAssignments(
            href=_default_fsa_href,
            mRID=adpt.get_global_mrids().new_mrid(),
            description="default",  # Simplified description for client compatibility
            subscribable=1,  # Allow subscriptions
        )

        # Initialize the DER program list for this FSA
        derp_list_href = hrefs.SEP.join((_default_fsa_href, "derp"))
        adpt.ListAdapter.initialize_uri(derp_list_href, m.DERProgram)

        # Create a copy of the default DER program from config
        import copy

        default_program = copy.deepcopy(config.default_program)
        if not hasattr(default_program, "href") or not default_program.href:
            # Assign href if not already set
            default_program.href = hrefs.SEP.join((derp_list_href, "0"))

        if not hasattr(default_program, "mRID") or not default_program.mRID:
            default_program.mRID = adpt.get_global_mrids().new_mrid()

        # Initialize the DER control list for this program
        derc_list_href = hrefs.SEP.join((default_program.href, "derc"))
        adpt.ListAdapter.initialize_uri(derc_list_href, m.DERControl)

        # Set the control list link on the program (required by IEEE 2030.5)
        # The list starts empty - controls are added dynamically by GridAPPS-D
        default_program.DERControlListLink = m.DERControlListLink(
            href=derc_list_href,
            all=0,  # Empty list initially
        )

        # Set up DefaultDERControl if configured
        # This provides baseline settings when DERControlList is empty
        if config.default_der_control:
            dderc_href = hrefs.SEP.join((default_program.href, "dderc"))

            # Create a copy and set the href
            default_der_control = copy.deepcopy(config.default_der_control)
            default_der_control.href = dderc_href

            if not hasattr(default_der_control, "mRID") or not default_der_control.mRID:
                default_der_control.mRID = adpt.get_global_mrids().new_mrid()

            # Store the DefaultDERControl
            result = adpt.ListAdapter.set_single(dderc_href, default_der_control)
            if result.success:
                # Set the link on the program
                default_program.DefaultDERControlLink = m.DefaultDERControlLink(href=dderc_href)
                # Register in href indexer
                add_href(dderc_href, default_der_control)
                adpt.get_global_mrids().add_item_with_mrid(dderc_href, default_der_control)
                _log.info("Created DefaultDERControl at %s for FSA program", dderc_href)
            else:
                _log.error("Failed to create DefaultDERControl: %s", result.error)

        # Add the program to the FSA's program list
        result = adpt.ListAdapter.append(derp_list_href, default_program)
        if not result.success:
            raise Exception(f"Failed to add default program to FSA: {result.error}")

        # Set the DER program list link on the FSA
        fsa.DERProgramListLink = m.DERProgramListLink(
            href=derp_list_href,
            all=1,  # One program
        )

        # Store the FSA in the global FSA list
        global_fsa_list = "/fsa"
        adpt.ListAdapter.initialize_uri(global_fsa_list, m.FunctionSetAssignments)
        result = adpt.ListAdapter.append(global_fsa_list, fsa)
        if not result.success:
            raise Exception(f"Failed to add default FSA to global list: {result.error}")

        # Register in href indexer and mRID registry
        add_href(fsa.href, fsa)
        adpt.get_global_mrids().add_item_with_mrid(fsa.href, fsa)
        add_href(default_program.href, default_program)
        adpt.get_global_mrids().add_item_with_mrid(default_program.href, default_program)

        _log.info(f"Created default FSA at {fsa.href} with program at {default_program.href}")
        return fsa


def link_device_to_default_fsa(end_device: m.EndDevice, ed_href) -> bool:
    """
    Link an EndDevice to the default FSA.

    Args:
        end_device: The EndDevice to link
        ed_href: The EndDeviceHref object containing device paths

    Returns:
        True if successfully linked, False otherwise
    """
    global _default_fsa_href

    if not _default_fsa_href:
        _log.debug("No default FSA available to link")
        return False

    # Get the default FSA from href indexer
    from ieee_2030_5.data.indexer import get_href

    default_fsa = get_href(_default_fsa_href)
    if not default_fsa:
        _log.warning(f"Default FSA at {_default_fsa_href} not found")
        return False

    with atomic_operation():
        # Initialize the device's FSA list if needed
        try:
            # Try to get the list first
            device_fsa_list = adpt.ListAdapter.get_list(ed_href.function_set_assignments)
        except:
            # If it doesn't exist, initialize it
            adpt.ListAdapter.initialize_uri(ed_href.function_set_assignments, m.FunctionSetAssignments)
            device_fsa_list = []

        # Also ensure it's initialized even if get_list returned empty
        if not device_fsa_list:
            # Make sure the URI is initialized
            adpt.ListAdapter.initialize_uri(ed_href.function_set_assignments, m.FunctionSetAssignments)
            device_fsa_list = []
        for fsa in device_fsa_list:
            if fsa.href == _default_fsa_href:
                _log.debug(f"Device {end_device.href} already linked to default FSA")
                return True

        # Create a reference to the default FSA for this device
        # Note: We're adding a reference, not copying the entire FSA
        fsa_ref = m.FunctionSetAssignments(
            href=_default_fsa_href,  # Point to the shared FSA
            mRID=default_fsa.mRID,
            description=default_fsa.description,
            DERProgramListLink=default_fsa.DERProgramListLink,
            subscribable=default_fsa.subscribable,
        )

        # Add the reference to the device's FSA list
        result = adpt.ListAdapter.append(ed_href.function_set_assignments, fsa_ref)
        if not result.success:
            _log.error(f"Failed to link device to default FSA: {result.error}")
            return False

        # Don't update the EndDevice FSA link here - it will be done by the caller
        # to avoid duplicate updates and ensure consistency

        list_size = adpt.ListAdapter.get_list_size(ed_href.function_set_assignments)
        _log.info(f"Linked device {end_device.href} to default FSA at {_default_fsa_href} (count={list_size})")
        return True


def create_device_specific_control(
    device_id: str, program: m.DERProgram, control_template: m.DERControl | None = None
) -> m.DERControl:
    """
    Create a device-specific DER control based on the program and template.

    Args:
        device_id: The device identifier (mRID or LFDI)
        program: The DER program this control belongs to
        control_template: Optional template control to base this on

    Returns:
        A new DERControl specific to this device
    """
    with atomic_operation():
        # Create control href specific to this device
        derc_list_href = hrefs.SEP.join((program.href, "derc"))
        control_index = adpt.ListAdapter.get_list_size(derc_list_href)
        control_href = hrefs.SEP.join((derc_list_href, str(control_index)))

        # Create the control
        if control_template:
            # Copy from template
            control = m.DERControl(
                href=control_href,
                mRID=adpt.get_global_mrids().new_mrid(),
                description=f"Control for device {device_id}",
                DERControlBase=control_template.DERControlBase if hasattr(control_template, "DERControlBase") else None,
                deviceCategory=control_template.deviceCategory if hasattr(control_template, "deviceCategory") else None,
            )
        else:
            # Create basic control
            control = m.DERControl(
                href=control_href,
                mRID=adpt.get_global_mrids().new_mrid(),
                description=f"Control for device {device_id}",
            )

        # Add device-specific targeting (this is where you'd add device mRID targeting)
        # For now, the client will filter based on their own mRID

        # Add to program's control list
        result = adpt.ListAdapter.append(derc_list_href, control)
        if not result.success:
            raise Exception(f"Failed to create control for device {device_id}: {result.error}")

        # Update program's control list count
        if hasattr(program, "DERControlListLink") and program.DERControlListLink:
            program.DERControlListLink.all = adpt.ListAdapter.get_list_size(derc_list_href)

        # Store in href indexer
        add_href(control.href, control)
        adpt.get_global_mrids().add_item_with_mrid(control.href, control)

        _log.debug(f"Created device-specific control at {control.href} for {device_id}")
        return control
