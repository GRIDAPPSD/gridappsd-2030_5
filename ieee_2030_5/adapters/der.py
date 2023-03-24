from __future__ import annotations

import logging
import uuid
from dataclasses import fields
from typing import Dict, List, Tuple

from blinker import Signal

import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.adapters import AdapterListProtocol, BaseAdapter, ready_signal
from ieee_2030_5.config import InvalidConfigFile
from ieee_2030_5.data.indexer import add_href, get_href_filtered
from ieee_2030_5.models.sep import DERProgram
from ieee_2030_5.types_ import StrPath

_log = logging.getLogger(__name__)

__all__: List[str] = [
    "DERControlAdapter",
    "DERProgramAdapter",
    "DERCurveAdapter",
    "DERAdapter"
]



class _DERCurveAdapter(BaseAdapter, AdapterListProtocol):
    
    def __init__(self) -> None:
        super().__init__()
        self._curves: List[m.DERCurve] = []
    

    def __initialize__(self, sender):
        """Initialize the DERCurve objects based upon the BaseAdapter.__device_configuration__"""

        if BaseAdapter.device_configs() is None:
            raise ValueError("Initialize BaseAdapter before initializing the Curves.")

        curves_cfg = BaseAdapter.server_config().curves

        for index, curve_cfg in enumerate(curves_cfg):

            der_curve = m.DERCurve(**curve_cfg.__dict__)
            der_curve.href = hrefs.curve_href(index)
            self._curves.append(der_curve)
            
        ready_signal.send(self)

    def fetch_all(self) -> List[m.DERCurve]:
        """Fetch all of the 2030.5 DERCurve objects as a list."""
        return self._curves

    def fetch_list(self, start=0, after=0, limit=0) -> m.DERCurveList:
        """Fetch a 2030.5 DERCurve object as a DERCurveList"""
        curve_list = m.DERCurveList(href=hrefs.curve_href())
        curve_list.DERCurve = self._curves
        curve_list.all = len(self._curves)
        curve_list.results = len(self._curves)
        return curve_list


DERCurveAdapter = _DERCurveAdapter()
ready_signal.connect(DERCurveAdapter.__initialize__, BaseAdapter)
#BaseAdapter.after_initialized.connect(DERCurveAdapter.__initialize__)


class _DERControlAdapter(BaseAdapter, AdapterListProtocol):

    def __init__(self) -> None:
        super().__init__()
        self._default_control: m.DefaultDERControl
        self._controls: List[m.DERControl] = []

    @staticmethod
    def fetch_default() -> m.DefaultDERControl:
        dderc = get_href(hrefs.get_dderc_href())

        if dderc is None:
            derbase = m.DERControlBase(opModConnect=True, opModEnergize=False)

            # Defaults from Jakaria on 1/26/2023
            dderc = m.DefaultDERControl(href=hrefs.get_dderc_href(),
                                        mRID=uuid.uuid4(),
                                        description="Default DER Control Mode",
                                        setESDelay=300,
                                        setESLowVolt=0.917,
                                        setESHighVolt=1.05,
                                        setESLowFreq=59.5,
                                        setESHighFreq=60.1,
                                        setESRampTms=300,
                                        setESRandomDelay=0,
                                        DERControlBase=derbase)
            add_href(dderc.href, dderc)

        return dderc

    @staticmethod
    def store_default(dderc: m.DefaultDERControl):
        add_href(hrefs.get_dderc_href(), dderc)

    def __initialize__(self, sender):
        """Initialize the DERControl and DERControlBase objects based upon the BaseAdapter.__server_configuration__"""
        config = DERControlAdapter.server_config().controls

        for index, ctl in enumerate(config):
            
            # Create a new DERControl and DERControlBase and initialize as much as possible
            base_control: m.DERControlBase = BaseAdapter.build_instance(m.DERControlBase, ctl.base)

            control: m.DERControl = BaseAdapter.build_instance(m.DERControl, ctl.__dict__)
            control.href = hrefs.get_derc_href(index=index)
            #control.mRID = f"MYCONTROL{index}"
            control.DERControlBase = base_control
            
            self._controls.append(control)
        
        ready_signal.send(self)
        
    def fetch_all(self) -> List[m.DERControl]:
        return self._controls
    
    def fetch_list(self, start: int = 0, after: int = 0, limit: int = 0) -> m.DERControlList:
        ctrl_list = m.DERControlList(href=hrefs.get_derc_href(),
                                     DERControl=self._controls,
                                     all=len(self._controls),
                                     results=len(self._controls))
        return ctrl_list

    @staticmethod
    def initialize_from_storage():
        dercs_href = hrefs.get_derc_href(hrefs.NO_INDEX)
        der_controls = get_href_filtered(dercs_href)
        DERControlAdapter.__count__ = len(der_controls)

    @staticmethod
    def create_from_parameters(**kwargs) -> m.DERControl:
        """Create and store a new DERControl object from the passed kwargs
        
        If invalid parameters are passed then a ValueError should be raised.        
        """
        control = m.DERControl()
        base_control = m.DERControlBase()
        control.DERControlBase = base_control
        field_list = fields(control)
        for k, v in kwargs.items():
            for f in field_list:
                if k == f.name:
                    setattr(control, k, v)
            for f in fields(base_control):
                if k == f.name:
                    setattr(base_control, k, v)

    @staticmethod
    def build_der_control(**kwargs) -> m.DERControl:
        """ Build a DERControl object from the passed parameters.

        Args:
            **params: The parameters passed in from the web application.
        """
        control = m.DERControl()
        base_control = m.DERControlBase()
        control.DERControlBase = base_control
        field_list = fields(control)
        for k, v in kwargs.items():
            for f in field_list:
                if k == f.name:
                    setattr(control, k, v)
            for f in fields(base_control):
                if k == f.name:
                    setattr(base_control, k, v)

        return control

    @staticmethod
    def store_single(der_control: m.DERControl | m.DefaultDERControl):
        if not der_control.mRID:
            der_control.mRID = uuid.uuid4()

        if not der_control.href:
            der_control.href = hrefs.get_derc_href(DERControlAdapter.__count__)
            add_href(der_control.href, der_control)
            DERControlAdapter.__count__ += 1

        add_href(der_control.href, der_control)

    @staticmethod
    def load_from_storage() -> Tuple[List[m.DERControl], m.DefaultDERControl]:
        der_controls, default_der_control = get_href_filtered(hrefs.get_derc_href(hrefs.NO_INDEX))
        return der_controls, default_der_control

    @staticmethod
    def get_all() -> List[m.DERControl]:
        """ Retrieve a list of dataclasses for DERControl for the """
        return list(filter(lambda a: isinstance(a, m.DERControl), get_href_filtered("")))

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
            raise ValueError(
                f"A default DERControl must be specified in {self.DERControlListFile}")

        # DERControls in the yaml file should be an array of DERControl instances.
        if 'DERControls' not in data or \
                not isinstance(data.get('DERControls'), list):
            raise ValueError(
                f"DERControls must be a list within the yaml file {self.DERControlListFile}")

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

            base_field_names = [fld.name for fld in fields(m.DERControlBase)]
            base_dict = {ctl: derc[ctl] for ctl in derc if ctl in base_field_names}
            control_fields = {ctl: derc[ctl] for ctl in derc if not ctl in base_dict.keys()}
            control_base = m.DERControlBase(**base_dict)
            item = m.DERControl(mRID=mrid,
                                description=description,
                                DERControlBase=control_base,
                                **control_fields)
            item.href = hrefs.get_derc_href(index)

            # TODO: Figure out if we need a global default or if that
            # is specific to the DERProgram construct.
            # Build a default der control
            # if name == default:
            #     try:
            #         default_derc = m.DefaultDERControl(mRID=mrid,
            #                                            description=description,
            #                                            DERControlBase=control_base,
            #                                            **control_fields)
            #         default_derc.href = hrefs.get_derc_default_href()
            #         add_href(default_derc.href, default_derc)
            #     except TypeError as ex:
            #         raise InvalidConfigFile(f"{yaml_file}\ndefault config parameter {ex.args[0]}")

            add_href(item.href, item)
            derc_list.append(item)

        # if not default_derc:
        #     raise InvalidConfigFile(f"{yaml_file} no DefaultDERControl specified.")
        if not len(derc_list) > 0:
            raise InvalidConfigFile(f"{yaml_file} must have at least one DERControl specified.")

        return derc_list, None    # default_derc

DERControlAdapter = _DERControlAdapter()
ready_signal.connect(DERControlAdapter.__initialize__, DERCurveAdapter)


class _DERProgramAdapter(BaseAdapter, AdapterListProtocol):
    
    def __init__(self) -> None:
        super().__init__()
        
        self._der_programs: List[DERProgram] = []
        
    
    def __initialize__(self, sender):
        """Initialize the DERProgram objects based upon the BaseAdapter.__server_configuration__"""
        cfg_programs = BaseAdapter.__server_configuration__.programs
        cfg_der_controls = BaseAdapter.__server_configuration__.controls
        _log.debug("Update m.DERPrograms' adding links to the different program pieces.")

        der_controls = DERControlAdapter.fetch_all()
        der_curves = DERCurveAdapter.fetch_all()
        # Initialize "global" m.DERPrograms href lists, including all the different links to
        # locations for active, default, curve and control lists.
        for index, program_cfg in enumerate(cfg_programs):
            # The configuration contains a mapping to control lists so when
            # building the DERProgram object we need to remove it from the paramters before
            # initialization.
            params = program_cfg.__dict__.copy()
            del params['default_control']
            del params['controls']
            del params['curves']
            
            program = m.DERProgram(**params)
            program.description = program_cfg.description
            program.primacy = program_cfg.primacy
            # program.version = program_cfg.version

            # TODO Fix this!
            # program.mRID =
            # mrid = program_cfg.get('mrid')
            # if mrid is None or len(mrid.trim()) == 0:
            #     program.mRID = f"program_mrid_{index}"
            # program_cfg['mrid'] = program.mRID

            program.href = hrefs.get_program_href(index)
            program.ActiveDERControlListLink = m.ActiveDERControlListLink(hrefs.der_href)

            try:
                der_ctl = next(
                    filter(lambda d: d.description == program_cfg.default_control, der_controls))
                der_cfg = next(
                    filter(lambda d: d.description == program_cfg.default_control,
                           cfg_der_controls))
            except StopIteration:
                raise InvalidConfigFile(
                    f"Section program: {program_cfg.description} default control {program_cfg.default_control} not found!"
                )
            else:
                default_ctl: m.DefaultDERControl = BaseAdapter.build_instance(
                    m.DefaultDERControl, der_cfg.__dict__)
                default_ctl.href = hrefs.get_derc_default_href(index)
                #default_ctl.mRID = der_ctl.mRID + " default"
                default_ctl.setESDelay = 20
                default_ctl.DERControlBase = der_ctl.DERControlBase

                program.DefaultDERControlLink = m.DefaultDERControlLink(href=default_ctl.href)
                self._der_programs.append(program)

            # der_control_list = m.DERControlList(href=hrefs.get_program_href(index, hrefs.DERC))

            # for ctl_description in program_cfg.controls:
            #     try:
            #         derc = next(filter(lambda d: d.description == ctl_description, der_controls))
            #     except StopIteration:
            #         raise InvalidConfigFile(
            #             f"Section program: {program_cfg.description} control {ctl_description} not found!"
            #         )
            #     else:
            #         der_control_list.DERControl.append(derc)

            # add_href(der_control_list.href, der_control_list)

            # der_curve_list = m.DERCurveList(href=hrefs.get_program_href(index, hrefs.CURVE))

            # for curve_description in program_cfg.curves:
            #     try:
            #         der_curve = next(
            #             filter(lambda d: d.description == curve_description, der_curves))
            #     except StopIteration:
            #         raise InvalidConfigFile(
            #             f"Section program: {program_cfg.description} curve {curve_description} not found!"
            #         )
            #     else:
            #         der_curve_list.DERCurve.append(der_curve)

            # der_curve_list.all = len(der_curve_list.DER)
            ready_signal.send(self)

    def fetch_all(self) -> List:
        return self._der_programs
    
    def fetch_list(self, start: int = 0, after: int = 0, limit: int = 0) -> m.DERProgramList:
        program_list = m.DERProgramList(href=hrefs.get_program_href(), DERProgram=self._der_programs,
                                        all=len(self._der_programs),
                                        results=len(self._der_programs))
        return program_list
    

    @staticmethod
    def build(**kwargs) -> m.DERProgram:
        """ Build a DERProgram from the passed kwargs

        kwarg variables:
            der_control_checked<int> - will be passed with the value of the href for the checked control.
            default_der_control - Is the default der control that should be used when no controls are active.
        """
        program = m.DERProgram()

        kwargs = populate_from_kwargs(program, **kwargs)

        href_default = kwargs.pop('default_der_control', None)
        hrefs_controls = [kwargs[k] for k in kwargs if k.startswith('der_control_checked')]

        program.DefaultDERControlLink = m.DefaultDERControlLink(href=href_default)
        # m.DERControlList
        program.DERControlListLink = hrefs.get_program_href()

        return program

DERProgramAdapter = _DERProgramAdapter()
ready_signal.connect(DERProgramAdapter.__initialize__, DERControlAdapter)


class _DERAdapter(BaseAdapter, AdapterListProtocol):
    def __init__(self) -> None:
        super().__init__()
        self._ders: List[m.DER] = []
        
    def __initialize__(self, sender):
        # TODO: Load ders
        cfg = BaseAdapter.server_config()
        
        
        
    def fetch_all(self) -> List:
        return self._ders
    
    def fetch_list(self, start: int = 0, after: int = 0, limit: int = 0) -> m.DERList:
        der_list = m.DERList(href=hrefs.get_der_list_href(), all=len(self._ders), results=len(self._ders), DER=self._ders)
        return der_list
    
DERAdapter = _DERAdapter()
ready_signal.connect(DERAdapter.__initialize__, BaseAdapter)



if __name__ == '__main__':
    from pathlib import Path

    import yaml

    from ieee_2030_5.__main__ import get_tls_repository
    from ieee_2030_5.config import ServerConfiguration
    
    cfg_pth = Path("/home/os2004/repos/gridappsd-2030_5/config.yml")
    cfg_dict = yaml.safe_load(cfg_pth.read_text())

    config = ServerConfiguration(**cfg_dict)

    tls_repo = get_tls_repository(config, False)

    BaseAdapter.initialize(config, tls_repo)    

    print(DERCurveAdapter.fetch_all())
    print(DERCurveAdapter.fetch_list())