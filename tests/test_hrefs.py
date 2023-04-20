import ieee_2030_5.hrefs as hrefs


def test_edev_href():
        
    href = hrefs.EdevHref.parse("/edev")
    
    assert href.edev_der_subtype is hrefs.DERSubType.None_Available
    assert href.edev_subtype is hrefs.EDevSubType.None_Available
    assert hrefs.NO_INDEX == href.edev_index
    assert hrefs.NO_INDEX == href.edev_subtype_index

    href = hrefs.EdevHref.parse(f"/edev_0")
    
    assert href.edev_der_subtype is hrefs.DERSubType.None_Available
    assert href.edev_subtype is hrefs.EDevSubType.None_Available
    assert 0 == href.edev_index
    assert hrefs.NO_INDEX == href.edev_subtype_index
    
    href = hrefs.EdevHref.parse(f"/edev_0_der")
    
    assert href.edev_der_subtype is hrefs.DERSubType.None_Available
    assert href.edev_subtype is hrefs.EDevSubType.DER
    assert 0 == href.edev_index
    assert hrefs.NO_INDEX == href.edev_subtype_index
    
    href = hrefs.EdevHref.parse(f"/edev_0_der_0")
    
    assert href.edev_der_subtype is hrefs.DERSubType.None_Available
    assert href.edev_subtype is hrefs.EDevSubType.DER
    assert 0 == href.edev_index
    assert 0 == href.edev_subtype_index
    
    href = hrefs.EdevHref.parse(f"/edev_0_der_0_dera")
    
    assert href.edev_der_subtype is hrefs.DERSubType.Availability
    assert href.edev_subtype is hrefs.EDevSubType.DER
    assert 0 == href.edev_index
    assert 0 == href.edev_subtype_index
    
    href = hrefs.EdevHref.parse(f"/edev_0_der_0_dera")
    
    assert href.edev_der_subtype is hrefs.DERSubType.Availability
    assert href.edev_subtype is hrefs.EDevSubType.DER
    assert 0 == href.edev_index
    assert 0 == href.edev_subtype_index
    
    href = hrefs.EdevHref.parse(f"/edev_0_der_0_derg")
    
    assert href.edev_der_subtype is hrefs.DERSubType.Settings
    assert href.edev_subtype is hrefs.EDevSubType.DER
    assert 0 == href.edev_index
    assert 0 == href.edev_subtype_index
    
    href = hrefs.EdevHref.parse(f"/edev_0_der_0_dstat")
    
    assert href.edev_der_subtype is hrefs.DERSubType.Status
    assert href.edev_subtype is hrefs.EDevSubType.DER
    assert 0 == href.edev_index
    assert 0 == href.edev_subtype_index
    
