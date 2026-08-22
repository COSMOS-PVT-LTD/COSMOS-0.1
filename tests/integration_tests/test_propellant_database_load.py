"""
COSMOS Rocket Propulsion Platform

Integration Tests:
    Propellant Database Loading
"""

from pathlib import Path

from physics.thermochemistry.propellants import (
    clear_registry,
    get_propellant,
    get_propellant_by_alias,
    list_fuels,
    list_inerts,
    list_oxidizers,
    list_pressurants,
    load_database,
    registry_size,
)


DATABASE_PATH = (
    Path.cwd()
    / "physics"
    / "thermochemistry"
    / "database"
    / "propellants_master_candidate_v1.json"
)


def setup_function() -> None:
    clear_registry()


def test_database_load() -> None:

    count = load_database(
        DATABASE_PATH
    )

    assert count == 6

    assert registry_size() == 6


def test_lox_lookup() -> None:

    load_database(
        DATABASE_PATH
    )

    lox = get_propellant(
        "Liquid Oxygen"
    )

    assert lox.short_name == "LOX"


def test_lch4_lookup() -> None:

    load_database(
        DATABASE_PATH
    )

    methane = get_propellant(
        "Liquid Methane"
    )

    assert methane.short_name == "LCH4"


def test_alias_lookup() -> None:

    load_database(
        DATABASE_PATH
    )

    propellant = (
        get_propellant_by_alias(
            "LOX"
        )
    )

    assert (
        propellant.name
        == "Liquid Oxygen"
    )


def test_fuels() -> None:

    load_database(
        DATABASE_PATH
    )

    fuels = list_fuels()

    assert len(fuels) == 3


def test_oxidizers() -> None:

    load_database(
        DATABASE_PATH
    )

    oxidizers = (
        list_oxidizers()
    )

    assert len(oxidizers) == 1


def test_pressurants() -> None:

    load_database(
        DATABASE_PATH
    )

    pressurants = (
        list_pressurants()
    )

    assert len(
        pressurants
    ) == 1


def test_inerts() -> None:

    load_database(
        DATABASE_PATH
    )

    inerts = list_inerts()

    assert len(inerts) == 1