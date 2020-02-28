import pytest
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import XDC_nb

from datetime import datetime


@pytest.fixture
def supply_params():
    start_date = datetime.date(
        datetime.strptime('10-12-2018 00:00:00', "%m-%d-%Y %H:%M:%S"))
    end_date = datetime.date(
        datetime.strptime('11-10-2018 00:00:00', "%m-%d-%Y %H:%M:%S"))
    onedata_token = ("MDAxNWxvY2F00aW9uIG9uZXpvbmUKMDAzMGlkZW500aWZpZX"
                     "IgOTAwNGNlNzBiYWQyMTYzYzY1YWY4NTNhZjQyMGJlYWEK"
                     "MDAxYWNpZCB00aW1lIDwgMTU4MzkxODYyOQowMDJmc2lnb"
                     "mF00dXJlICmASYmuGx6CSPHwkf3s9pXW2szUqJPBPoFEXI"
                     "KOZ2L00Cg")
    return [start_date, end_date, onedata_token]


def test_model_meta_discovery(supply_params):
    result = XDC_nb.find_dataset_type(
        supply_params[0], supply_params[1], '', supply_params[2])
    assert len(result) > 0
