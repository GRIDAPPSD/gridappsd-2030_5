import logging

from app_settings import get_tls_repo
from nicegui import ui
from pages import Pages, show_global_header
from session import get_certs, get_end_devices

_log = logging.getLogger(__name__)


@ui.page('/certs')
def show_certs():
    show_global_header(Pages.CERTS)
    device_list = get_end_devices()
    certs = get_certs()
    row_data = []
    for name, cert in certs.items():
        row = dict(name=f'{name}',
                   cert=f'<a href="/admin/download/cert/{name}">Cert File</a> &nbsp; <a href="/admin/download/key/{name}">Key File</a>',
                   lFDI=' ')
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
            {'headerName': 'Name', 'field': 'name'},
            {'headerName': 'lFDI', 'field': 'lFDI'}
        ],
        'rowData': row_data,
    }, html_columns=[0])
    