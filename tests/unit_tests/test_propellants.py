"""
COSMOS Rocket Propulsion Platform

Module: tests.unit_tests.test_propellants
Author: COSMOS Development Team
Version: 0.2.0

Purpose:
    Unit tests for physics.thermochemistry.propellants.
"""

from __future__ import annotations

# ============================================================================
# Third Party
# ============================================================================

try:
    import pytest  # type: ignore
except Exception:  # pragma: no cover - fallback for environments without pytest
    class _Raises:
        def __init__(self, exc):
            self._exc = exc

        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            if exc_type is None:
                raise AssertionError("Did not raise expected exception")
            return issubclass(exc_type, self._exc)

    class _PytestStub:
        def fixture(self, autouse=False):
            def _decorator(func):
                return func

            return _decorator

        def raises(self, exc):
            return _Raises(exc)

    pytest = _PytestStub()

import json

from pathlib import Path

# ============================================================================
# COSMOS Physics
# ============================================================================

from physics.thermochemistry.propellants import (
    DuplicatePropellantError,
    Phase,
    Propellant,
    PropellantError,
    PropellantNotFoundError,
    PropellantType,
    PropellantValidationError,
    clear_registry,
    exists,
    get_all_aliases,
    get_all_names,
    is_registry_empty,
    registry_size,
    database_exists,
    default_database_path,
    load_database,
    load_json_database,
    reload_database,
    load_sqlite_database,
     load_yaml_database,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(
    autouse=True,
)
def clean_registry():
    """
    Ensure registry isolation.
    """

    clear_registry()

    yield

    clear_registry()


# ============================================================================
# Enum Tests
# ============================================================================


def test_phase_enum_values() -> None:
    """
    Verify Phase enum.
    """

    assert (
        Phase.SOLID.value
        == "SOLID"
    )

    assert (
        Phase.LIQUID.value
        == "LIQUID"
    )

    assert (
        Phase.GAS.value
        == "GAS"
    )

    assert (
        Phase.SUPERCRITICAL.value
        == "SUPERCRITICAL"
    )


def test_propellant_type_enum_values() -> None:
    """
    Verify PropellantType enum.
    """

    assert (
        PropellantType.FUEL.value
        == "FUEL"
    )

    assert (
        PropellantType.OXIDIZER.value
        == "OXIDIZER"
    )

    assert (
        PropellantType.PRESSURANT.value
        == "PRESSURANT"
    )

    assert (
        PropellantType.INERT.value
        == "INERT"
    )


# ============================================================================
# Exception Hierarchy Tests
# ============================================================================


def test_exception_hierarchy() -> None:
    """
    Verify exception inheritance.
    """

    assert issubclass(
        PropellantValidationError,
        PropellantError,
    )

    assert issubclass(
        PropellantNotFoundError,
        PropellantError,
    )

    assert issubclass(
        DuplicatePropellantError,
        PropellantError,
    )


# ============================================================================
# Empty Registry Tests
# ============================================================================


def test_registry_initially_empty() -> None:
    """
    Verify empty registry.
    """

    assert (
        registry_size()
        == 0
    )

    assert (
        is_registry_empty()
        is True
    )


def test_get_all_names_empty() -> None:
    """
    Verify empty names list.
    """

    assert (
        get_all_names()
        == ()
    )


def test_get_all_aliases_empty() -> None:
    """
    Verify empty alias list.
    """

    assert (
        get_all_aliases()
        == ()
    )


def test_exists_false_for_empty_registry() -> None:
    """
    Verify exists().
    """

    assert (
        exists(
            "LOX"
        )
        is False
    )
# ============================================================================
# Test Propellant Factory
# ============================================================================


def create_test_propellant() -> Propellant:
    """
    Create valid test propellant.
    """

    return Propellant(
        name="TEST_FUEL",
        short_name="TF",
        formula="CH4",
        molecular_weight=16.043,
        phase=Phase.LIQUID,
        propellant_type=PropellantType.FUEL,
        cea_species_name="CH4",
        aliases=(
            "TEST",
            "TEST_METHANE",
        ),
        density=422.62,
        density_temperature=111.0,
        density_pressure=101325.0,
        storage_temperature=111.0,
        storage_pressure=101325.0,
        boiling_point=111.66,
        freezing_point=90.69,
        critical_temperature=190.56,
        critical_pressure=4.599e6,
        elements={
            "C": 1,
            "H": 4,
        },
        source="Unit Test",
        reference="Unit Test Reference",
        reference_date="2026-01-01",
        data_quality_level="TEST",
        version="1.0",
        last_verified="2026-01-01",
        notes="Test propellant",
    )


# ============================================================================
# Dataclass Construction Tests
# ============================================================================


def test_valid_propellant_creation() -> None:
    """
    Verify valid construction.
    """

    propellant = (
        create_test_propellant()
    )

    assert (
        propellant.name
        == "TEST_FUEL"
    )

    assert (
        propellant.phase
        is Phase.LIQUID
    )

    assert (
        propellant.propellant_type
        is PropellantType.FUEL
    )


def test_empty_name_fails() -> None:
    """
    Verify empty name rejection.
    """

    with pytest.raises(
        PropellantValidationError
    ):

        Propellant(
            **{
                **create_test_propellant()
                .to_dict(),
                "name": "",
            }
        )


def test_empty_formula_fails() -> None:
    """
    Verify empty formula rejection.
    """

    data = (
        create_test_propellant()
        .to_dict()
    )

    data["formula"] = ""

    with pytest.raises(
        PropellantValidationError
    ):
        Propellant.from_dict(
            data,
        )


def test_negative_density_fails() -> None:
    """
    Verify negative density rejection.
    """

    data = (
        create_test_propellant()
        .to_dict()
    )

    data["density"] = -1.0

    with pytest.raises(
        PropellantValidationError
    ):
        Propellant.from_dict(
            data,
        )


def test_zero_density_fails() -> None:
    """
    Verify zero density rejection.
    """

    data = (
        create_test_propellant()
        .to_dict()
    )

    data["density"] = 0.0

    with pytest.raises(
        PropellantValidationError
    ):
        Propellant.from_dict(
            data,
        )


def test_zero_molecular_weight_fails() -> None:
    """
    Verify molecular weight validation.
    """

    data = (
        create_test_propellant()
        .to_dict()
    )

    data["molecular_weight"] = 0.0

    with pytest.raises(
        PropellantValidationError
    ):
        Propellant.from_dict(
            data,
        )


def test_negative_molecular_weight_fails() -> None:
    """
    Verify molecular weight validation.
    """

    data = (
        create_test_propellant()
        .to_dict()
    )

    data["molecular_weight"] = -10.0

    with pytest.raises(
        PropellantValidationError
    ):
        Propellant.from_dict(
            data,
        )


# ============================================================================
# Alias Validation Tests
# ============================================================================


def test_duplicate_aliases_fail() -> None:
    """
    Verify duplicate alias detection.
    """

    data = (
        create_test_propellant()
        .to_dict()
    )

    data["aliases"] = (
        "LOX",
        "LOX",
    )

    with pytest.raises(
        PropellantValidationError
    ):
        Propellant.from_dict(
            data,
        )


def test_invalid_alias_fails() -> None:
    """
    Verify alias validation.
    """

    data = (
        create_test_propellant()
        .to_dict()
    )

    data["aliases"] = (
        "INVALID@ALIAS",
    )

    with pytest.raises(
        PropellantValidationError
    ):
        Propellant.from_dict(
            data,
        )


# ============================================================================
# Element Validation Tests
# ============================================================================


def test_empty_elements_fail() -> None:
    """
    Verify element validation.
    """

    data = (
        create_test_propellant()
        .to_dict()
    )

    data["elements"] = {}

    with pytest.raises(
        PropellantValidationError
    ):
        Propellant.from_dict(
            data,
        )


def test_negative_element_count_fails() -> None:
    """
    Verify element count validation.
    """

    data = (
        create_test_propellant()
        .to_dict()
    )

    data["elements"] = {
        "C": -1,
    }

    with pytest.raises(
        PropellantValidationError
    ):
        Propellant.from_dict(
            data,
        )


def test_zero_element_count_fails() -> None:
    """
    Verify element count validation.
    """

    data = (
        create_test_propellant()
        .to_dict()
    )

    data["elements"] = {
        "C": 0,
    }

    with pytest.raises(
        PropellantValidationError
    ):
        Propellant.from_dict(
            data,
        )


# ============================================================================
# Enum Validation Tests
# ============================================================================


def test_invalid_phase_fails() -> None:
    """
    Verify phase validation.
    """

    data = (
        create_test_propellant()
        .to_dict()
    )

    data["phase"] = "INVALID"

    with pytest.raises(
        Exception
    ):
        Propellant.from_dict(
            data,
        )


def test_invalid_propellant_type_fails() -> None:
    """
    Verify propellant type validation.
    """

    data = (
        create_test_propellant()
        .to_dict()
    )

    data["propellant_type"] = (
        "INVALID"
    )

    with pytest.raises(
        Exception
    ):
        Propellant.from_dict(
            data,
        )    
# ============================================================================
# Serialization Tests
# ============================================================================


def test_to_dict() -> None:
    """
    Verify dictionary serialization.
    """

    propellant = (
        create_test_propellant()
    )

    data = (
        propellant.to_dict()
    )

    assert isinstance(
        data,
        dict,
    )

    assert (
        data["name"]
        == "TEST_FUEL"
    )

    assert (
        data["phase"]
        == "LIQUID"
    )

    assert (
        data["propellant_type"]
        == "FUEL"
    )

    assert (
        data["density"]
        == 422.62
    )


def test_from_dict() -> None:
    """
    Verify dictionary deserialization.
    """

    original = (
        create_test_propellant()
    )

    data = (
        original.to_dict()
    )

    restored = (
        Propellant.from_dict(
            data,
        )
    )

    assert (
        restored.name
        == original.name
    )

    assert (
        restored.formula
        == original.formula
    )

    assert (
        restored.phase
        == original.phase
    )

    assert (
        restored.propellant_type
        == original.propellant_type
    )


def test_to_json() -> None:
    """
    Verify JSON serialization.
    """

    propellant = (
        create_test_propellant()
    )

    json_text = (
        propellant.to_json()
    )

    assert isinstance(
        json_text,
        str,
    )

    assert (
        "TEST_FUEL"
        in json_text
    )

    assert (
        "LIQUID"
        in json_text
    )

    assert (
        "FUEL"
        in json_text
    )


def test_from_json() -> None:
    """
    Verify JSON deserialization.
    """

    original = (
        create_test_propellant()
    )

    json_text = (
        original.to_json()
    )

    restored = (
        Propellant.from_json(
            json_text,
        )
    )

    assert (
        restored.name
        == original.name
    )

    assert (
        restored.short_name
        == original.short_name
    )

    assert (
        restored.formula
        == original.formula
    )


def test_round_trip_dict_serialization() -> None:
    """
    Verify dictionary round-trip.
    """

    original = (
        create_test_propellant()
    )

    restored = (
        Propellant.from_dict(
            original.to_dict()
        )
    )

    assert (
        restored
        == original
    )


def test_round_trip_json_serialization() -> None:
    """
    Verify JSON round-trip.
    """

    original = (
        create_test_propellant()
    )

    restored = (
        Propellant.from_json(
            original.to_json()
        )
    )

    assert (
        restored
        == original
    )


def test_json_output_contains_required_fields() -> None:
    """
    Verify JSON content.
    """

    propellant = (
        create_test_propellant()
    )

    json_text = (
        propellant.to_json()
    )

    required_fields = (
        "name",
        "formula",
        "density",
        "source",
        "reference",
        "phase",
        "propellant_type",
    )

    for field in required_fields:

        assert (
            field
            in json_text
        )


def test_invalid_json_fails() -> None:
    """
    Verify JSON validation.
    """

    with pytest.raises(
        PropellantValidationError
    ):
        Propellant.from_json(
            "{invalid json}"
        )


def test_invalid_json_root_fails() -> None:
    """
    Verify JSON root validation.
    """

    with pytest.raises(
        PropellantValidationError
    ):
        Propellant.from_json(
            '["not","object"]'
        )


def test_aliases_survive_serialization() -> None:
    """
    Verify alias preservation.
    """

    original = (
        create_test_propellant()
    )

    restored = (
        Propellant.from_json(
            original.to_json()
        )
    )

    assert (
        restored.aliases
        == original.aliases
    )


def test_elements_survive_serialization() -> None:
    """
    Verify element preservation.
    """

    original = (
        create_test_propellant()
    )

    restored = (
        Propellant.from_dict(
            original.to_dict()
        )
    )

    assert (
        restored.elements
        == original.elements
    )


def test_traceability_fields_survive_serialization() -> None:
    """
    Verify traceability preservation.
    """

    original = (
        create_test_propellant()
    )

    restored = (
        Propellant.from_json(
            original.to_json()
        )
    )

    assert (
        restored.source
        == original.source
    )

    assert (
        restored.reference
        == original.reference
    )

    assert (
        restored.reference_date
        == original.reference_date
    )

    assert (
        restored.last_verified
        == original.last_verified
    )

    assert (
        restored.version
        == original.version
    )
# ============================================================================
# Registry Tests
# ============================================================================

from physics.thermochemistry.propellants import (
    DuplicatePropellantError,
    PropellantNotFoundError,
    get_propellant,
    get_propellant_by_alias,
    list_fuels,
    list_inerts,
    list_oxidizers,
    list_pressurants,
    list_propellants,
    register_propellant,
    registry_statistics,
)


def test_register_propellant() -> None:
    """
    Verify propellant registration.
    """

    propellant = (
        create_test_propellant()
    )

    register_propellant(
        propellant,
    )

    assert (
        registry_size()
        == 1
    )


def test_exists_after_registration() -> None:
    """
    Verify exists() after registration.
    """

    propellant = (
        create_test_propellant()
    )

    register_propellant(
        propellant,
    )

    assert (
        exists(
            "TEST_FUEL"
        )
        is True
    )


def test_get_propellant() -> None:
    """
    Verify canonical lookup.
    """

    propellant = (
        create_test_propellant()
    )

    register_propellant(
        propellant,
    )

    retrieved = (
        get_propellant(
            "TEST_FUEL"
        )
    )

    assert (
        retrieved
        == propellant
    )


def test_get_propellant_case_insensitive() -> None:
    """
    Verify case-insensitive lookup.
    """

    propellant = (
        create_test_propellant()
    )

    register_propellant(
        propellant,
    )

    retrieved = (
        get_propellant(
            "test_fuel"
        )
    )

    assert (
        retrieved.name
        == "TEST_FUEL"
    )


def test_get_propellant_by_alias() -> None:
    """
    Verify alias lookup.
    """

    propellant = (
        create_test_propellant()
    )

    register_propellant(
        propellant,
    )

    retrieved = (
        get_propellant_by_alias(
            "TEST"
        )
    )

    assert (
        retrieved.name
        == "TEST_FUEL"
    )


def test_alias_lookup_case_insensitive() -> None:
    """
    Verify alias lookup.
    """

    propellant = (
        create_test_propellant()
    )

    register_propellant(
        propellant,
    )

    retrieved = (
        get_propellant_by_alias(
            "test"
        )
    )

    assert (
        retrieved.name
        == "TEST_FUEL"
    )


def test_get_missing_propellant_fails() -> None:
    """
    Verify missing lookup.
    """

    with pytest.raises(
        PropellantNotFoundError
    ):
        get_propellant(
            "DOES_NOT_EXIST"
        )


def test_get_missing_alias_fails() -> None:
    """
    Verify missing alias.
    """

    with pytest.raises(
        PropellantNotFoundError
    ):
        get_propellant_by_alias(
            "INVALID_ALIAS"
        )


def test_duplicate_propellant_rejected() -> None:
    """
    Verify duplicate protection.
    """

    propellant = (
        create_test_propellant()
    )

    register_propellant(
        propellant,
    )

    with pytest.raises(
        DuplicatePropellantError
    ):
        register_propellant(
            propellant,
        )


def test_alias_collision_rejected() -> None:
    """
    Verify alias collision detection.
    """

    register_propellant(
        create_test_propellant()
    )

    second = Propellant(
        name="SECOND",
        short_name="S2",
        formula="H2",
        molecular_weight=2.016,
        phase=Phase.GAS,
        propellant_type=PropellantType.INERT,
        cea_species_name="H2",
        aliases=("TEST",),
        density=1.0,
        density_temperature=300.0,
        density_pressure=101325.0,
        storage_temperature=300.0,
        storage_pressure=101325.0,
        boiling_point=20.0,
        freezing_point=14.0,
        critical_temperature=33.0,
        critical_pressure=1.3e6,
        elements={"H": 2},
        source="Unit Test",
        reference="Unit Test",
        reference_date="2026-01-01",
        data_quality_level="TEST",
        version="1.0",
        last_verified="2026-01-01",
        notes="",
    )

    with pytest.raises(
        DuplicatePropellantError
    ):
        register_propellant(
            second
        )


# ============================================================================
# Registry Category Tests
# ============================================================================


def test_list_fuels() -> None:
    """
    Verify fuel listing.
    """

    register_propellant(
        create_test_propellant()
    )

    fuels = list_fuels()

    assert (
        len(fuels)
        == 1
    )

    assert (
        fuels[0].propellant_type
        is PropellantType.FUEL
    )


def test_list_propellants() -> None:
    """
    Verify list all.
    """

    register_propellant(
        create_test_propellant()
    )

    all_items = (
        list_propellants()
    )

    assert (
        len(all_items)
        == 1
    )


def test_empty_category_lists() -> None:
    """
    Verify empty categories.
    """

    assert (
        list_oxidizers()
        == ()
    )

    assert (
        list_pressurants()
        == ()
    )

    assert (
        list_inerts()
        == ()
    )


# ============================================================================
# Registry Statistics Tests
# ============================================================================


def test_registry_statistics_empty() -> None:
    """
    Verify empty statistics.
    """

    stats = (
        registry_statistics()
    )

    assert (
        stats["total"]
        == 0
    )

    assert (
        stats["fuels"]
        == 0
    )


def test_registry_statistics_populated() -> None:
    """
    Verify populated statistics.
    """

    register_propellant(
        create_test_propellant()
    )

    stats = (
        registry_statistics()
    )

    assert (
        stats["total"]
        == 1
    )

    assert (
        stats["fuels"]
        == 1
    )

    assert (
        stats["aliases"]
        == 2
    )
# ============================================================================
# Database Loading Tests
# ============================================================================


def create_database_record() -> dict[str, object]:
    """
    Create valid database record.
    """

    return create_test_propellant().to_dict()


def test_default_database_path() -> None:
    """
    Verify default database path.
    """

    path = default_database_path()

    assert isinstance(
        path,
        Path,
    )

    assert (
        path.name
        == "propellants_master.json"
    )


def test_database_exists_false(
    tmp_path: Path,
) -> None:
    """
    Verify missing database.
    """

    database = (
        tmp_path
        / "missing.json"
    )

    assert (
        database_exists(
            database
        )
        is False
    )


def test_database_exists_true(
    tmp_path: Path,
) -> None:
    """
    Verify database detection.
    """

    database = (
        tmp_path
        / "database.json"
    )

    database.write_text(
        "[]",
        encoding="utf-8",
    )

    assert (
        database_exists(
            database
        )
        is True
    )


def test_load_json_database(
    tmp_path: Path,
) -> None:
    """
    Verify JSON database loading.
    """

    database = (
        tmp_path
        / "propellants.json"
    )

    records = [
        create_database_record(),
    ]

    database.write_text(
        json.dumps(records),
        encoding="utf-8",
    )

    loaded = (
        load_json_database(
            database
        )
    )

    assert (
        loaded
        == 1
    )

    assert (
        registry_size()
        == 1
    )


def test_load_database(
    tmp_path: Path,
) -> None:
    """
    Verify generic database loader.
    """

    database = (
        tmp_path
        / "database.json"
    )

    database.write_text(
        json.dumps(
            [
                create_database_record()
            ]
        ),
        encoding="utf-8",
    )

    loaded = load_database(
        database
    )

    assert (
        loaded
        == 1
    )


def test_reload_database(
    tmp_path: Path,
) -> None:
    """
    Verify database reload.
    """

    database = (
        tmp_path
        / "database.json"
    )

    database.write_text(
        json.dumps(
            [
                create_database_record()
            ]
        ),
        encoding="utf-8",
    )

    load_database(
        database
    )

    assert (
        registry_size()
        == 1
    )

    reloaded = (
        reload_database(
            database
        )
    )

    assert (
        reloaded
        == 1
    )

    assert (
        registry_size()
        == 1
    )


def test_invalid_json_database_fails(
    tmp_path: Path,
) -> None:
    """
    Verify invalid JSON handling.
    """

    database = (
        tmp_path
        / "invalid.json"
    )

    database.write_text(
        "{invalid}",
        encoding="utf-8",
    )

    with pytest.raises(
        PropellantValidationError
    ):
        load_json_database(
            database
        )


def test_invalid_database_root_fails(
    tmp_path: Path,
) -> None:
    """
    Verify root validation.
    """

    database = (
        tmp_path
        / "invalid.json"
    )

    database.write_text(
        json.dumps(
            {
                "bad": "root"
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        PropellantValidationError
    ):
        load_json_database(
            database
        )


def test_missing_required_field_fails(
    tmp_path: Path,
) -> None:
    """
    Verify schema validation.
    """

    record = (
        create_database_record()
    )

    del record["density"]

    database = (
        tmp_path
        / "invalid.json"
    )

    database.write_text(
        json.dumps(
            [record]
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        PropellantValidationError
    ):
        load_json_database(
            database
        )


def test_missing_database_fails(
    tmp_path: Path,
) -> None:
    """
    Verify missing file handling.
    """

    database = (
        tmp_path
        / "missing.json"
    )

    with pytest.raises(
        PropellantValidationError
    ):
        load_json_database(
            database
        )


# ============================================================================
# Backend Hook Tests
# ============================================================================


def test_yaml_backend_not_implemented(
    tmp_path: Path,
) -> None:
    """
    Verify YAML hook.
    """

    with pytest.raises(
        NotImplementedError
    ):
        load_yaml_database(
            tmp_path
            / "test.yaml"
        )


def test_sqlite_backend_not_implemented(
    tmp_path: Path,
) -> None:
    """
    Verify SQLite hook.
    """

    with pytest.raises(
        NotImplementedError
    ):
        load_sqlite_database(
            tmp_path
            / "test.db"
        )


# ============================================================================
# Reload Behavior Tests
# ============================================================================


def test_reload_clears_old_registry(
    tmp_path: Path,
) -> None:
    """
    Verify registry replacement.
    """

    database = (
        tmp_path
        / "database.json"
    )

    database.write_text(
        json.dumps(
            [
                create_database_record()
            ]
        ),
        encoding="utf-8",
    )

    load_database(
        database
    )

    assert (
        registry_size()
        == 1
    )

    reload_database(
        database
    )

    assert (
        registry_size()
        == 1
    )
    