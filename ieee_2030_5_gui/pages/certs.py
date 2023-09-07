import logging

from nicegui import ui

from ..pages import Pages, show_global_header
from ..session import get_cert_list, get_enddevice_list

_log = logging.getLogger(__name__)


@ui.page('/certs')
def show_certs():
    show_global_header(Pages.CERTS)
    device_list = get_enddevice_list()
    certs = get_cert_list()
    row_data = []
    for name, cert in certs.items():
        row = dict(name=f'{name}',
                   cert=f'<a href="/admin/download/cert/{name}">Cert File</a> &nbsp; <a href="/admin/download/key/{name}">Key File</a>',
                   path=f"{cert.get('path', '')}",
                   lFDI='')
        if cert.get('lFDI'):
            for ed in device_list.EndDevice:
                if ed.lFDI == cert['lFDI'].encode('utf-8'):
                    row['lFDI'] = ed.lFDI
                    break
            
        row_data.append(row)
    # for ed in device_list.EndDevice:
    #     row = dict(name=f'{ed.lFDI}',
    #             cert=f'<a href="/admin/cert/{ed.lFDI}">cert</a>')
    #     row_data.append(row)
        

    ui.aggrid({
        'columnDefs': [
            {'headerName': '', 'field': 'cert'},
            {'headerName': 'Path', 'field': 'path'},
            {'headerName': 'Name', 'field': 'name'},
            {'headerName': 'lFDI', 'field': 'lFDI'}
        ],
        'rowData': row_data,
    }, html_columns=[0])
    