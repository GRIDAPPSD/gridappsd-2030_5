from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import pvlib
import math

from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.client import IEEE2030_5_Client


def run_inverter(client: IEEE2030_5_Client):
    # PV module
    sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
    module = sandia_modules['Canadian_Solar_CS5P_220M___2009_']
    # Inverter model
    sapm_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')
    inverter = sapm_inverters['ABB__MICRO_0_25_I_OUTD_US_208__208V_']
    irradiance = [900, 1000, 925]
    temperature = [25, 28, 20]
    # Assumed constant power factor
    PF = 0.99
    # Assumed constant AC voltage
    v_ac = 120
    latitude = 32
    longitude = -111.0
    weather = pvlib.iotools.get_pvgis_tmy(latitude, longitude, map_variables=True)[0]
    total_solar_radiance = weather['ghi']
    # assumed that the total solar radiance is equal to ghi(global horizontal irradiance)
    outdoor_temp = weather["temp_air"]
    # both the total_solar_radiace and outdoor_temp has 1hr sampling rate.
    # you should be able modify the sampling rate by resampling it
    for x, y in zip(total_solar_radiance, outdoor_temp):
        dc = pvlib.pvsystem.sapm(x, y, module)
        # print(dc)
        p_ac = pvlib.inverter.sandia(dc['v_mp'], dc['p_mp'], inverter)
        s_ac = p_ac / PF
        q_ac = math.sqrt(p_ac**2 + s_ac**2)
        i_ac = (s_ac / v_ac) * 1000
        print(f"p_ac = {p_ac}, s_ac = {s_ac}, q_ac= {q_ac}, PF = {PF}, v_ac = {v_ac}, i_ac = {i_ac}")
        # single phase circuit calculation

if __name__ == '__main__':
    path = Path(__file__).parent.parent.parent.joinpath("openssl.cnf")
    print(str(path))
    tls_repo = TLSRepository(repo_dir="~/tls", openssl_cnffile=path,
                             serverhost="gridappsd_dev_2004", clear=False)
    # print(tls_repo.client_list)
    for p in tls_repo.client_list:
        print(p)
