import pytest

import ieee_2030_5.hrefs as hrefs

args = [
    ['edev_0_rg', 0, hrefs.EDevSubType.Registration, hrefs.NO_INDEX],
    ['edev_2_rg', 2, hrefs.EDevSubType.Registration, hrefs.NO_INDEX],
    ['edev_3_dstat', 3, hrefs.EDevSubType.DeviceStatus, hrefs.NO_INDEX],
    ['edev_3_fsa', 3, hrefs.EDevSubType.FunctionSetAssignments, hrefs.NO_INDEX],
    ['edev_3_fsa_1', 3, hrefs.EDevSubType.FunctionSetAssignments, 1],
    
    
]

@pytest.mark.parametrize("path,edev_index,edev_subtype,edev_subtype_index", args)
def test_edev_href(path, edev_index, edev_subtype, edev_subtype_index):
    edevhref = hrefs.EdevHref.parse(path)
    
    assert edevhref.edev_index == edev_index
    assert edevhref.edev_subtype == edev_subtype
    assert edevhref.edev_subtype_index == edev_subtype_index
    
def test_value_error_not_start_with_edev():
    with pytest.raises(ValueError):
        hrefs.EdevHref.parse("foo_2_rg")
        