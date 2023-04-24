
import ieee_2030_5.models as m
from ieee_2030_5.client.client import IEEE2030_5_Client


def test_admin_correct_derp_links(admin_client: IEEE2030_5_Client):
    assert admin_client
    
    def url(endpoint:str) -> str:
        return f"admin/{endpoint}"
    
    derp = admin_client.get(url("derp"))
    
    assert isinstance(derp, m.DERProgramList)
    assert len(derp.DERProgram) == 1
    
    derp_0 = derp.DERProgram[0]
    
    assert derp_0.description == "Program 1"
    assert derp_0.ActiveDERControlListLink.href
    assert derp_0.DefaultDERControlLink.href
    assert derp_0.DERControlListLink.href
    assert derp_0.DERCurveListLink.href
    
    derp_0_default_control = admin_client.get(url(f"derp/0/dderc"))
    
    assert isinstance(derp_0_default_control, m.DefaultDERControl)
    assert derp_0_default_control.DERControlBase.opModConnect == True
    assert derp_0_default_control.DERControlBase.opModMaxLimW == 9500
    
    derp_0_control_list = admin_client.get(url(f"derp/0/derc"))
    
    assert isinstance(derp_0_control_list, m.DERControlList)
    assert 2 == len(derp_0_control_list.DERControl)
    
    
    
    
        # app.add_url_rule("/admin", view_func=self._admin)
        # app.add_url_rule("/admin/enddevices/<int:index>", view_func=self._admin_enddevices)    
        # app.add_url_rule("/admin/enddevices", view_func=self._admin_enddevices)
        # app.add_url_rule("/admin/end-device-list", view_func=self._admin_enddevice_list)
        # app.add_url_rule("/admin/program-lists", view_func=self._admin_der_program_lists)
        # app.add_url_rule("/admin/lfdi", endpoint="admin/lfdi", view_func=self._lfdi_lists)
        # app.add_url_rule("/admin/edev/<int:edev_index>/ders/<int:der_index>/current_derp", view_func=self._admin_der_update_current_derp, methods=['PUT', 'GET'])
        # app.add_url_rule("/admin/ders/<int:edev_index>", view_func=self._admin_ders)
        
        # # COMPLETE
        # app.add_url_rule("/admin/edev/<int:edevid>/fsa/<int:fsaid>/derp", view_func=self._admin_edev_fsa_derp)
        # app.add_url_rule("/admin/edev/<int:edevid>/fsa/<int:fsaid>", view_func=self._admin_edev_fsa)
        # app.add_url_rule("/admin/edev/<int:edevid>/fsa", view_func=self._admin_edev_fsa)
        # # END COMPLETE
        
        # app.add_url_rule("/admin/derp/<int:derp_index>/derc/<int:control_index>",  methods=['GET', 'PUT'], view_func=self._admin_derp_derc)
        # app.add_url_rule("/admin/derp/<int:derp_index>/derc",  methods=['GET', 'POST'], view_func=self._admin_derp_derc)
        # app.add_url_rule("/admin/derp/<int:derp_index>/derca",  methods=['GET'], view_func=self._admin_derp_derca)
        # app.add_url_rule("/admin/derp/<int:derp_index>/dderc",  methods=['GET', 'PUT'], view_func=self._admin_derp_derc)
        # app.add_url_rule("/admin/derp",  methods=['GET', 'POST'], view_func=self._admin_derp)
    
    
    