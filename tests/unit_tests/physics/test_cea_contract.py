"""External engine results are untrusted until the SI contract is checked."""

from dataclasses import replace

import pytest

from core.exceptions import DimensionError
from core.unit import SI
from physics.compressible_flow.external_nozzle import scale_external_nozzle
from physics.exceptions import OutOfRangeError, ThermochemistryError
from physics.quantities import kelvin, pascal, quantity
from physics.si import UNIT_MOLAR_MASS
from physics.thermochemistry.cea_interface import (
    CeaRequest,
    ThermochemicalResult,
    run_thermochemistry,
)
from physics.validity import ValidityStatus


def valid_result():
    return ThermochemicalResult(kelvin(3000), 1.2, quantity(.022, UNIT_MOLAR_MASS),
                                quantity(1800, SI.get("m/s")), {"H2O": 1.}, ValidityStatus.VALID, "regression-engine")


@pytest.mark.parametrize("changes", [{"gamma": float("nan")}, {"gamma": 1}, {"mole_fractions": {}},
                                     {"mole_fractions": {"H2O": .9}}, {"mole_fractions": {"H2O": float("nan")}},
                                     {"engine_name": ""}, {"validity": ValidityStatus.INSUFFICIENT_DATA},
                                     {"rocket_stations": {"exit": {"mach": float("inf")}}}])
def test_external_invalid_solution_is_rejected(changes):
    class Engine:
        def evaluate(self, request):
            return replace(valid_result(), **changes)
    with pytest.raises(ThermochemistryError):
        run_thermochemistry(CeaRequest("LCH4", "LOX", 3, pascal(1e6)), Engine())


def test_wrong_dimensions_never_convert_as_correct_thermo_units():
    class Engine:
        def evaluate(self, request):
            return replace(valid_result(), chamber_temperature=pascal(3000))
    with pytest.raises(DimensionError):
        run_thermochemistry(CeaRequest("LCH4", "LOX", 3, pascal(1e6)), Engine())


@pytest.mark.parametrize("ratio", [float("nan"), -1, 0])
def test_invalid_request_never_reaches_native_engine(ratio):
    class Engine:
        def evaluate(self, request):
            raise AssertionError("Native engine must not receive invalid input")
    with pytest.raises(ThermochemistryError):
        run_thermochemistry(CeaRequest("LCH4", "LOX", ratio, pascal(1e6)), Engine())


@pytest.mark.parametrize("ambient", [1e6, 1e5])
def test_unsupported_attached_nozzle_conditions_are_rejected(ambient):
    with pytest.raises(OutOfRangeError):
        scale_external_nozzle(pascal(5e5), pascal(ambient), quantity(.001, SI.get("m2")),
                              10, quantity(1800, SI.get("m/s")), quantity(1000, SI.get("m/s")), pascal(6000))
