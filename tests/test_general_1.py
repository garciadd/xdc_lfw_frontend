import pytest


@pytest.fixture
def supply_params():
    validate = 2
    return [validate]


def test_file1_method1(supply_params):
    assert supply_params[0] == 2
