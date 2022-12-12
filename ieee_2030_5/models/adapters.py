from __future__ import annotations

import dataclasses
import uuid
from pathlib import Path
from typing import List, Tuple, Dict

import yaml

from ieee_2030_5 import hrefs
from ieee_2030_5.data.indexer import add_href, get_href_filtered
import ieee_2030_5.models as m
from ieee_2030_5.types_ import StrPath


class InvalidConfigFile(Exception):
    pass


class BaseAdapter:
    pass


class DERControlAdapter(BaseAdapter):
    _control_count = 0

    @staticmethod
    def initialize_from_storage():
        dercs_href = hrefs.get_derc_href(-1)
        der_controls = get_href_filtered(dercs_href)
        DERControlAdapter._control_count = len(der_controls)


    @staticmethod
    def build_der_control(**kwargs) -> m.DERControl:
        """ Build a DERControl object from the passed parameters.

        Args:
            **params: The parameters passed in from the web application.
        """
        control = m.DERControl()
        base_control = m.DERControlBase()
        control.DERControlBase = base_control
        field_list = dataclasses.fields(control)
        for k, v in kwargs.items():
            for f in field_list:
                if k == f.name:
                    setattr(control, k, v)
            for f in dataclasses.fields(base_control):
                if k == f.name:
                    setattr(base_control, k, v)

        return control

    @staticmethod
    def store_single(der_control: m.DERControl | m.DefaultDERControl):
        if not der_control.mRID:
            der_control.mRID = uuid.uuid4()

        if not der_control.href:
            der_control.href = hrefs.get_derc_href(DERControlAdapter._control_count)
            add_href(der_control.href, der_control)
            DERControlAdapter._control_count += 1

        add_href(der_control.href, der_control)

    @staticmethod
    def load_from_storage() -> Tuple[List[m.DERControl], m.DefaultDERControl]:
        dercs_href = hrefs.get_derc_href(-1)
        der_controls = get_href_filtered(hrefs.get_derc_href(-1))

    @staticmethod
    def get_all() -> Tuple[List[m.DERControl], m.DefaultDERControl]:
        """ Retrieve a list of dataclasses for DERControl for the """
        der_controls = get_href_filtered(hrefs.get_derc_href(-1))
        default_der = get_href_filtered(hrefs.get_derc_default_href())
        return der_controls, default_der


    @staticmethod
    def load_from_yaml_file(yaml_file: StrPath) -> Tuple[List[m.DERControl], m.DefaultDERControl]:
        """Load from a configuration yaml file

        The yaml file must have a list of DERControls dictionary items and a default str that matches
        with one of the DERControlName.  This method loops over the DERControls and
        creates a DERControlBase with the parameters in the config file.

        The validations that could throw errors are:

            - Required fields are DERControlName, mRID, description
            - Required no-duplicates in mRID and DERControlName

        Returns List[DERControls], DefaultDERControl
        """
        if isinstance(yaml_file, str):
            yaml_file = Path(yaml_file)
        yaml_file = yaml_file.expanduser()
        data = yaml.safe_load(yaml_file.read_text())
        default = data.get('default', None)
        if not default:
            raise ValueError(f"A default DERControl must be specified in {self.DERControlListFile}")

        # DERControls in the yaml file should be an array of DERControl instances.
        if 'DERControls' not in data or \
                not isinstance(data.get('DERControls'), list):
            raise ValueError(f"DERControls must be a list within the yaml file {self.DERControlListFile}")

        default_derc: m.DefaultDERControl = None
        derc_list: List[m.DERControl] = []
        derc_names: Dict[str, str] = {}
        mrids: Dict[str, str] = {}
        for index, derc in enumerate(data["DERControls"]):
            required = 'mRID', 'DERControlName', 'description'
            for req in required:
                if req not in derc:
                    raise ValueError(f"{req}[{index}] does not have a '{req}' in {yaml_file}.")
            name = derc.pop('DERControlName')
            mrid = derc.pop('mRID')
            description = derc.pop('description')
            if mrid in mrids:
                raise ValueError(f"Duplicate mrid {mrid} found in {yaml_file}")
            if name in derc_names:
                raise ValueError(f"Duplicate name {name} found in {yaml_file}")

            base_field_names = [fld.name for fld in dataclasses.fields(m.DERControlBase)]
            base_dict = {ctl: derc[ctl] for ctl in derc if ctl in base_field_names}
            control_fields = {ctl: derc[ctl] for ctl in derc if not ctl in base_dict.keys()}
            control_base = m.DERControlBase(**base_dict)
            item = m.DERControl(mRID=mrid, description=description, DERControlBase=control_base, **control_fields)
            item.href = hrefs.get_derc_href(index)

            # Build a default der control
            if name == default:
                try:
                    default_derc = m.DefaultDERControl(mRID=mrid, description=description, DERControlBase=control_base,
                                                       **control_fields)
                    default_derc.href = hrefs.get_derc_default_href()
                    add_href(default_derc.href, default_derc)
                except TypeError as ex:
                    raise InvalidConfigFile(f"{yaml_file}\ndefault config parameter {ex.args[0]}")

            add_href(item.href, item)
            derc_list.append(item)

        if not default_derc:
            raise InvalidConfigFile(f"{yaml_file} no DefaultDERControl specified.")
        if not len(derc_list) > 0:
            raise InvalidConfigFile(f"{yaml_file} must have at least one DERControl specified.")

        return derc_list, default_derc