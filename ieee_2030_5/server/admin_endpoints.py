import json
import logging
from pathlib import Path
from typing import Optional

import flask
from blinker import Signal
from flask import Flask, Response, g, render_template, request

import ieee_2030_5.adapters as adpt
from ieee_2030_5.data.indexer import add_href, get_href
import ieee_2030_5.hrefs as hrefs
import ieee_2030_5.models as m
from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.config import ServerConfiguration
from ieee_2030_5.server.server_constructs import create_device_capability
from ieee_2030_5.utils import (dataclass_to_xml, get_lfdi_from_cert, get_sfdi_from_lfdi,
                               xml_to_dataclass)

_log = logging.getLogger(__name__)


class AdminEndpoints:

    def __init__(self, app: Flask, tls_repo: TLSRepository, config: ServerConfiguration):
        self.tls_repo = tls_repo
        self.server_config = config

        app.add_url_rule("/admin", view_func=self._admin)
        #app.add_url_rule("/admin/enddevices/<int:index>", view_func=self._admin_enddevices)
        #app.add_url_rule("/admin/enddevices", view_func=self._admin_enddevices)
        #app.add_url_rule("/admin/end-device-list", view_func=self._admin_enddevice_list)
        #app.add_url_rule("/admin/program-lists", view_func=self._admin_der_program_lists)
        #app.add_url_rule("/admin/lfdi", endpoint="admin/lfdi", view_func=self._lfdi_lists)
        #app.add_url_rule("/admin/edev/<int:edev_index>/ders/<int:der_index>/current_derp", view_func=self._admin_der_update_current_derp, methods=['PUT', 'GET'])

        #        app.add_url_rule("/admin/ders/<int:edev_index>", view_func=self._admin_ders)

        # COMPLETE
        app.add_url_rule("/admin/edev/<int:edevid>/fsa/<int:fsaid>/derp",
                         view_func=self._admin_edev_fsa_derp)
        app.add_url_rule("/admin/edev/<int:edevid>/fsa/<int:fsaid>",
                         view_func=self._admin_edev_fsa)
        app.add_url_rule("/admin/edev/<int:edevid>/fsa", view_func=self._admin_edev_fsa)
        app.add_url_rule("/admin/edev/<int:edevid>/der", view_func=self._admin_edev_ders)
        app.add_url_rule("/admin/edev/<int:edevid>/der/<int:derid>/current_derp",
                         view_func=self._admin_edev_ders)
        app.add_url_rule("/admin/edev/<int:edevid>/der/<int:derid>",
                         view_func=self._admin_edev_ders)
        app.add_url_rule("/admin/edev", view_func=self._admin_edev)
        # END COMPLETE

        app.add_url_rule("/admin/certs", endpoint="admin/certs", view_func=self._admin_certs)
        app.add_url_rule("/admin/enddevices",
                         methods=['GET', 'PUT', 'POST', 'DELETE'],
                         view_func=self._admin_enddevices)
        app.add_url_rule("/admin/curves",
                         methods=['GET', 'PUT', 'POST', 'DELETE'],
                         view_func=self._admin_curves)
        app.add_url_rule("/admin/controls",
                         methods=['GET', 'PUT', 'POST', 'DELETE'],
                         view_func=self._admin_controls)
        app.add_url_rule("/admin/programs",
                         methods=['GET', 'PUT', 'POST', 'DELETE'],
                         view_func=self._admin_programs)
        app.add_url_rule("/admin/fsa",
                         methods=['GET', 'PUT', 'POST', 'DELETE'],
                         view_func=self._admin_fsa)
        app.add_url_rule("/admin/der",
                         methods=['GET', 'PUT', 'POST', 'DELETE'],
                         view_func=self._admin_ders)

        app.add_url_rule("/admin/derp/<int:derp_index>/derc/<int:control_index>",
                         methods=['GET', 'PUT'],
                         view_func=self._admin_derp_derc)
        app.add_url_rule("/admin/derp/<int:derp_index>/derc",
                         methods=['GET', 'POST'],
                         view_func=self._admin_derp_derc)
        app.add_url_rule("/admin/derp/<int:derp_index>/derca",
                         methods=['GET'],
                         view_func=self._admin_derp_derca)
        app.add_url_rule("/admin/derp/<int:derp_index>/dderc",
                         methods=['GET', 'PUT'],
                         view_func=self._admin_derp_derc)
        app.add_url_rule("/admin/derp", methods=['GET', 'POST'], view_func=self._admin_derp)
        #app.add_url_rule("/admin/derp/<int:index>",  methods=['GET', 'POST'], view_func=self._derp)
        #app.add_url_rule("/admin/derp/<int:index>/derc", methods=['GET', 'POST'], view_func=self._derp_derc)

    # def _admin_edev_fsa(self, edevid: int, fsaid: int = -1, derc: int = -1) -> Response:
    #     #edev = EndDeviceAdapter.fetch_at(edevid)

    #     if fsaid > -1 and derc > -1:

    #fsa = FSAAdapter.fetch_by_end_device(edevid)

    def _admin_certs(self) -> Response:
        headers = {'CONTENT-TYPE': "application/json"}
        tls_repo: TLSRepository = g.TLS_REPOSITORY

        return Response(json.dumps(tls_repo.client_list), headers=headers)

    def _admin_ders(self) -> Response:
        """Returns DER or DERList depending on the request method.
        
        If request method is GET, return an DERList object.
        
        If request method is POST, save the DER object and return it with new href for the end device.
        
        If request method is PUT, update the DER object and return it.
        
        If request method is DELETE, remove the DER object and return None.
        """
        if request.method in ('POST', 'PUT'):
            data = request.data.decode('utf-8')
            item = xml_to_dataclass(data)
            if not isinstance(item, m.DER):
                _log.error("DER was not passed via data.")
                return Response(status=400)

            if request.method == 'POST':
                if item.href:
                    _log.error(f"POST method with existing object {item.href}")
                    return Response(400)

                item = adpt.DERAdapter.add(item)
                response_status = 201

            elif request.method == 'PUT':
                if not item.href:
                    _log.error(f"PUT method without an existing object.")
                    return Response(400)

                index = int(item.href.rsplit(hrefs.SEP)[-1])
                adpt.DERAdapter.put(index, item)
                response_status = 200

            return Response(dataclass_to_xml(item), status=response_status)

    def _admin_programs(self) -> Response:
        """Returns EndDevice or EndDeviceList depending on the request method.
        
        If request method is GET, return an EndDeviceList object.
        
        If request method is POST, save the EndDevice object and return it with new href for the end device.
        
        If request method is PUT, update the EndDevice object and return it.
        
        If request method is DELETE, remove the EndDevice object and return None.
        """
        if request.method in ('POST', 'PUT'):

            def normalize_certificate_name(pre_name: str) -> str:
                if pre_name.startswith('/'):
                    pre_name = pre_name[1:]
                return pre_name.replace('/', '-')

            data = request.data.decode('utf-8')
            item = xml_to_dataclass(data)
            if not isinstance(item, m.DERProgram):
                _log.error("DERProgram was not passed via data.")
                return Response(status=400)

            if request.method == 'POST':
                if item.href:
                    _log.error(f"POST method with existing object {item.href}")
                    return Response(400)

                item = adpt.DERProgramAdapter.add(item)
                response_status = 201

            elif request.method == 'PUT':
                if not item.href:
                    _log.error(f"PUT method without an existing object.")
                    return Response(400)

                index = int(item.href.rsplit(hrefs.SEP)[-1])
                adpt.DERProgramAdapter.put(index, item)
                response_status = 200

            return Response(dataclass_to_xml(item), status=response_status)

        # Get all end devices
        start = int(request.args.get('s', 0))
        after = int(request.args.get('a', 0))
        limit = int(request.args.get('l', 1))

        allofem = adpt.DERProgramAdapter.fetch_all(m.DERProgramList(),
                                                   start=start,
                                                   after=after,
                                                   limit=limit)
        return Response(dataclass_to_xml(allofem), status=200)

    def _admin_fsa(self) -> Response:
        """Returns EndDevice or EndDeviceList depending on the request method.
        
        If request method is GET, return an EndDeviceList object.
        
        If request method is POST, save the EndDevice object and return it with new href for the end device.
        
        If request method is PUT, update the EndDevice object and return it.
        
        If request method is DELETE, remove the EndDevice object and return None.
        """
        if request.method in ('POST', 'PUT'):

            def normalize_certificate_name(pre_name: str) -> str:
                if pre_name.startswith('/'):
                    pre_name = pre_name[1:]
                return pre_name.replace('/', '-')

            data = request.data.decode('utf-8')
            item = xml_to_dataclass(data)
            if not isinstance(item, m.FunctionSetAssignments):
                _log.error("FuncitonSetAssignments was not passed via data.")
                return Response(status=400)

            if request.method == 'POST':
                if item.href:
                    _log.error(f"POST method with existing object {item.href}")
                    return Response(400)

                item = adpt.FunctionSetAssignmentsAdapter.add(item)
                response_status = 201

            elif request.method == 'PUT':
                if not item.href:
                    _log.error(f"PUT method without an existing object.")
                    return Response(400)

                index = int(item.href.rsplit(hrefs.SEP)[-1])
                adpt.FunctionSetAssignmentsAdapter.put(index, item)
                response_status = 200

            return Response(dataclass_to_xml(item), status=response_status)

        # Get all end devices
        start = int(request.args.get('s', 0))
        after = int(request.args.get('a', 0))
        limit = int(request.args.get('l', 1))

        allofem = adpt.FunctionSetAssignmentsAdapter.fetch_all(m.FunctionSetAssignmentsList(),
                                                               start=start,
                                                               after=after,
                                                               limit=limit)
        return Response(dataclass_to_xml(allofem), status=200)

    def _admin_enddevices(self) -> Response:
        """Returns EndDevice or EndDeviceList depending on the request method.
        
        If request method is GET, return an EndDeviceList object.
        
        If request method is POST, save the EndDevice object and return it with new href for the end device.
        
        If request method is PUT, update the EndDevice object and return it.
        
        If request method is DELETE, remove the EndDevice object and return None.
        """
        if request.method in ('POST', 'PUT'):

            def normalize_certificate_name(pre_name: str) -> str:
                if pre_name.startswith('/'):
                    pre_name = pre_name[1:]
                return pre_name.replace('/', '-')

            data = request.data.decode('utf-8')
            item = xml_to_dataclass(data)
            if not isinstance(item, m.EndDevice):
                _log.error("EndDevice was not passed via data.")
                return Response(status=400)

            if request.method == 'POST':
                if item.href:
                    _log.error(f"POST method with existing object {item.href}")
                    return Response(400)

                item = adpt.EndDeviceAdapter.add(item)
                cert_filename = normalize_certificate_name(item.href)
                tls_repo: TLSRepository = g.TLS_REPOSITORY
                cert, key = tls_repo.get_file_pair(cert_filename)
                Path(cert).unlink(missing_ok=True)
                Path(key).unlink(missing_ok=True)
                tls_repo.create_cert(cert_filename)

                item.lFDI = get_lfdi_from_cert(cert)
                item.sFDI = get_sfdi_from_lfdi(item.lFDI)
                index = int(item.href.rsplit(hrefs.SEP)[-1])
                adpt.EndDeviceAdapter.put(index, item)
                create_device_capability(index)
                response_status = 201

            elif request.method == 'PUT':
                if not item.href:
                    _log.error(f"PUT method without an existing object.")
                    return Response(400)

                index = int(item.href.rsplit(hrefs.SEP)[-1])
                adpt.EndDeviceAdapter.put(index, item)
                response_status = 200

            return Response(dataclass_to_xml(item), status=response_status)

        # Get all end devices
        start = int(request.args.get('s', 0))
        after = int(request.args.get('a', 0))
        limit = int(request.args.get('l', 1))

        allofem = adpt.EndDeviceAdapter.fetch_all(m.EndDeviceList(),
                                                  start=start,
                                                  after=after,
                                                  limit=limit)
        return Response(dataclass_to_xml(allofem), status=200)

    def _admin_controls(self) -> Response:
        """Returns DERControl or DERControlList depending on the request method.
        
        If request method is GET, return a DERControlList object.
        
        If request method is POST, save the DERControl object and return it with new href for the control.
        
        If request method is PUT, update the DERControl object and return it.
        
        If request method is DELETE, remove the DERControl object and return None.
        
        """

        if request.method in ('POST', 'PUT'):
            data = request.data.decode('utf-8')
            control = xml_to_dataclass(data)
            if not isinstance(control, m.DERControl):
                _log.error("DERControl was not passed via data.")
                return Response(status=400)

            if request.method == 'POST':
                if control.href:
                    _log.error(f"POST method with existing object {control.href}")
                    return Response(400)

                control = adpt.DERControlAdapter.add(control)
                response_status = 201

            elif request.method == 'PUT':
                if not control.href:
                    _log.error(f"PUT method without an existing object.")
                    return Response(400)

                index = int(control.href.rsplit(hrefs.SEP)[-1])
                adpt.DERControlAdapter.put(index, control)
                response_status = 200

            return Response(dataclass_to_xml(control), status=response_status)

        start = int(request.args.get('s', 0))
        after = int(request.args.get('a', 0))
        limit = int(request.args.get('l', 1))

        return Response(dataclass_to_xml(
            adpt.DERControlAdapter.fetch_all(m.DERControlList(),
                                             start=start,
                                             after=after,
                                             limit=limit)),
                        status=200)

    def _admin_curves(self) -> Response:
        """Returns DERCurve or DERCurve List depending upon request method.
        
        If request method is GET, return a DERCurveList object.
        
        If request method is POST or PUT, return a DERCurve object.
        
        If request method is DELETE return None.        
        """
        if request.method in ('POST', 'PUT'):
            data = request.data.decode('utf-8')
            curve = xml_to_dataclass(data)
            if not isinstance(curve, m.DERCurve):
                _log.error("DERCurve was not passed via data.")
                return Response(status=400)

            if request.method == 'POST':
                if curve.href:
                    _log.error(f"POST method with existing object {curve.href}")
                    return Response(400)

                curve = adpt.DERControlAdapter.add(curve)
                response_status = 201

            elif request.method == 'PUT':
                if not curve.href:
                    _log.error(f"PUT method without an existing object.")
                    return Response(400)

                index = int(curve.href.rsplit(hrefs.SEP)[-1])
                adpt.DERControlAdapter.put(index, curve)
                response_status = 200

            return Response(dataclass_to_xml(curve), status=response_status)

        start = int(request.args.get('s', 0))
        after = int(request.args.get('a', 0))
        limit = int(request.args.get('l', 1))

        return Response(dataclass_to_xml(
            adpt.DERCurveAdapter.fetch_all(m.DERCurveList(), start=start, after=after,
                                           limit=limit)),
                        status=200)

    def _admin_edev(self) -> Response:
        return Response(dataclass_to_xml(adpt.EndDeviceAdapter.fetch_all(m.EndDeviceList())))

    def _admin_edev_ders(self, edevid: int, derid: int = None) -> Response:
        ed = EndDeviceAdapter.fetch(edevid)
        deradpter: Adapter[m.DER] = EndDeviceAdapter.fetch_child(ed, hrefs.DER)
        if derid:
            retval: m.DER = deradpter.fetch(derid)
            if request.path.endswith('current_derp'):
                derp_href = hrefs.DERProgramHrefOld.parse(retval.CurrentDERProgramLink)
                retval = DERProgramAdapter.fetch(derp_href.index)
        else:
            retval = deradpter.fetch_all(m.DERList())

        return Response(dataclass_to_xml(retval))

    def _admin_edev_fsa(self, edevid: int, fsaid: int = -1) -> Response:
        if not edevid > -1:
            raise ValueError("Invalid end device id passed")

        ed = EndDeviceAdapter.fetch(edevid)

        if fsaid > -1:
            obj = FSAAdapter.fetch(fsaid)
        else:
            obj = FSAAdapter.fetch_all(m.FunctionSetAssignmentsList())

        # if edevid > -1 and fsaid > -1:
        #     obj = EndDeviceAdapter.fetch_all(m.FunctionSetAssignmentsList())
        #     #obj = EndDeviceAdapter.fetch_fsa(edev_index=edevid, fsa_index=fsaid)
        # elif edevid > -1:
        #     ed = EndDeviceAdapter.fetch(edevid)
        #     obj = EndDeviceAdapter.fetch_child(ed, hrefs.FSA)
        #     #obj = EndDeviceAdapter.fetch_fsa_list(edev_index=edevid)
        # else:
        #     return Response("Invalid edevid specified", status=400)

        return Response(dataclass_to_xml(obj))

    def _admin_edev_fsa_derp(self, edevid: int, fsaid: int) -> Response:
        derps = EndDeviceAdapter.fetch_derp_list(edev_index=edevid, fsa_index=fsaid)
        return Response(dataclass_to_xml(derps))

    def _admin_der_program_lists(self) -> Response:
        return Response(dataclass_to_xml(DERProgramAdapter.fetch_list()))

    # def _admin_ders(self, edev_index: int) -> Response:
    #     return Response(dataclass_to_xml(DERAdapter.fetch_list(edev_index=edev_index)))

    # def _der_settings(self, edev_index: int, der_index: int):
    #     return Response(dataclass_to_xml(DERAdapter.fetch_settings_at(edev_index=edev_index, der_index=der_index)))

    def _admin_der_update_current_derp(self, edev_index: int, der_index: int):
        if request.method == 'PUT':
            data: m.DERProgram = xml_to_dataclass(request.data.decode('utf-8'))
            if not isinstance(data, m.DERProgram):
                return Response(status=400)

            if data.mRID:
                program = DERProgramAdapter.fetch_by_mrid(data.mRID)
                response_status = 200
                if not program:
                    program = DERProgramAdapter.create(data).data
                    response_status = 201
            else:
                program = DERProgramAdapter.create(data).data
                response_status = 201
            print(EndDeviceAdapter.fetch_child_names())
            der = DERAdapter.fetch_at(edev_index, der_index)
            der.CurrentDERProgramLink = m.CurrentDERProgramLink(program.href)
            return Response(dataclass_to_xml(program), status=response_status)
        else:
            der = DERAdapter.fetch_at(edev_index, der_index)
            if der.CurrentDERProgramLink:
                parsed = hrefs.der_program_parse(der.CurrentDERProgramLink.href)
                program = DERProgramAdapter.fetch_at(parsed.index)
            else:
                program = m.DERProgram()

            return Response(dataclass_to_xml(program))

    def _admin_derp(self, index: int = -1) -> Response:

        # Get all end devices
        start = int(request.args.get('s', 0))
        after = int(request.args.get('a', 0))
        limit = int(request.args.get('l', 1))

        if request.method == 'GET':
            if index < 0:
                retval = adpt.ListAdapter.get_resource_list(hrefs.DEFAULT_DERP_ROOT,
                                                            start=start,
                                                            after=after,
                                                            limit=limit)
                #return Response(dataclass_to_xml(DERProgramAdapter.fetch_all(m.DERProgramList())))
            elif request.method == 'GET':
                retval = adpt.ListAdapter.get(hrefs.DEFAULT_DERP_ROOT, index)

            return Response(dataclass_to_xml(retval))

        if request.method == 'POST':
            raise NotImplemented("POST not implemented")
            # xml = request.data.decode('utf-8')
            # data = xml_to_dataclass(request.data.decode('utf-8'))

            # if not isinstance(data, m.DERProgram):
            #     raise BadRequest("Invalid DERProgram")
            # response = DERProgramAdapter.create(data)

            return Response(headers={'Location': response.href}, status=response.statusint)

        return Response(f"I am {index}, {request.method}")

    def _admin_derp_derca(self, derp_index: int) -> Response:
        ctrl_list = DERProgramAdapter.fetch_der_active_control_list(derp_index)
        return Response(dataclass_to_xml(ctrl_list))

    def _admin_derp_derc(self, derp_index: int) -> Response:
        derp = adpt.ListAdapter.get(hrefs.DEFAULT_DERP_ROOT, derp_index)
        # derp = adpt.DERProgramAdapter.fetch(derp_index)

        if request.method in ("PUT", "POST"):

            data = request.get_data(as_text=True)
            # Retrieve data from xml
            data = xml_to_dataclass(data)

            # If we are retrieving the default instance.
            if isinstance(data, m.DefaultDERControl):
                data.href = derp.DefaultDERControlLink.href

                status_code = 201
                if get_href(derp.DefaultDERControlLink.href):
                    status_code = 204
                add_href(data.href, data)

            elif isinstance(data, m.DERControl):
                status_code = 201

                der_cntl_list: m.DERControlList = adpt.ListAdapter.get_resource_list(
                    derp.DERControlListLink.href)
                assert isinstance(der_cntl_list, m.DERControlList)

                found_at = None
                for indx, cntl in enumerate(der_cntl_list.DERControl):
                    if cntl.mRID == data.mRID:
                        found_at = indx

                if not found_at:
                    data.href = derp.DERControlListLink.href + hrefs.SEP + str(
                        len(der_cntl_list.DERControl))
                    adpt.ListAdapter.append(derp.DERControlListLink.href, data)
                    #der_cntl_list.DERControl.append(data)
                else:
                    status_code = 204
                    data.href = der_cntl_list.DERControl[found_at].href
                    der_cntl_list.DERControl[found_at] = data

                der_cntl_list.all = len(der_cntl_list.DERControl)
                #add_href(derp.DERControlListLink.href, der_cntl_list)
                adpt.TimeAdapter.add_event(data)

            return Response(headers={'Location': data.href}, status=status_code)

    def _admin(self) -> Response:
        arg_path = request.args.get('path')
        device = request.args.get('device')

        if arg_path == '/enddevices':
            return Response(dataclass_to_xml(EndDeviceAdapter.fetch_list()))

        if arg_path.startswith('/edev'):
            edev_path = hrefs.edev_parse(arg_path)
            if edev_path.der_index == hrefs.NO_INDEX:
                return Response(
                    dataclass_to_xml(DERAdapter.fetch_list(edev_index=edev_path.edev_index)))
            elif edev_path.der_sub is None:
                return Response(
                    dataclass_to_xml(
                        DERAdapter.fetch_at(edev_index=edev_path.edev_index,
                                            der_index=edev_path.der_index)))
            elif edev_path.der_sub == hrefs.DERSubType.CurrentProgram.value:
                return Response(
                    dataclass_to_xml(
                        DERAdapter.fetch_current_program_at(edev_index=edev_path.edev_index,
                                                            der_index=edev_path.der_index)))

        elif arg_path.startswith("/fsa"):

            fsa_path = hrefs.fsa_parse(arg_path)

            if fsa_path.fsa_index == hrefs.NO_INDEX:
                return Response(dataclass_to_xml(FSAAdapter.fetch_list()))
            elif fsa_path.fsa_index != hrefs.NO_INDEX and fsa_path.fsa_sub is None:
                return Response(dataclass_to_xml(FSAAdapter.fetch_at(fsa_path.fsa_index)))
            else:
                return Response(dataclass_to_xml(FSAAdapter.fetch_program_list(
                    fsa_path.fsa_index)))

    def _lfdi_lists(self) -> Response:
        items = []

        for k, v in self.end_devices.__all_end_devices__.items():
            items.append({"key": k, "lfdi": int(v.end_device.lFDI)})

        return Response(json.dumps(items))

    # def _admin_edev_fsa(self, edevid: int, fsaid: int = -1) -> Response:
    #     #edev = self.end_devices.get(edevid)
    #     return Response(json.dumps(json.dumps(self.end_devices.get_fsa_list(edevid=edevid))))

    def _program_lists(self) -> str:
        return render_template("admin/program-lists.html",
                               program_lists=self.server_config.program_lists)

    def _admin_enddevice_list(self) -> str:
        return render_template("admin/end-device-list.html",
                               end_device_list=self.end_devices.get_end_devices())
