import ieee_2030_5.hrefs as hrefs

def test_usage_point_href():
    mup_root = hrefs.UsagePointHref()
    
    # If no argument passed to the constructor then nothing to compare with
    assert not mup_root.is_root()
    assert "/upt_0" == mup_root.usage_point(0)
    assert "/upt_0_mr" == mup_root.meterreading_list(0)
    assert "/upt_0_mr_0" == mup_root.meterreading(0, 0)
    assert "/upt_0_mr_0_rs" == mup_root.readingset_list(0, 0)
    assert "/upt_0_mr_0_rs_0" == mup_root.readingset(0, 0, 0)
    assert "/upt_0_mr_0_rs_0_r" == mup_root.readingsetreading_list(0, 0, 0)
    assert "/upt_0_mr_0_rs_0_r_0" == mup_root.readingsetreading(0, 0, 0, 0)
    
    
    assert "/upt_0_mr_0_r" == mup_root.reading_list(0, 0)
    assert "/upt_0_mr_0_r_0" == mup_root.reading(0, 0, 0)  

def test_usage_point_parsing():
    h = hrefs.ParsedUsagePointHref("/upt_0")
    
    assert h.usage_point_index == 0
    assert not h.has_reading_list()
    
    h = hrefs.ParsedUsagePointHref("/upt_1_mr_2_rs_3_r_4")
    
    assert h.has_meter_reading_list()
    assert h.has_reading_set_list()
    assert h.has_reading_set_reading_list()
    assert 1 == h.usage_point_index 
    assert 2 == h.meter_reading_index
    assert 3 == h.reading_set_index
    assert 4 == h.reading_set_reading_index
    

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
    
