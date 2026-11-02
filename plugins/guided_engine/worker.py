"""One trusted stdin request; process timeout/cancellation owned by supervisor."""

import json
import sys

from plugins.guided_engine.sources import package
from plugins.nasa_cea import bind_nasa_cea_engine
from systems.guided_engine.evaluate import evaluate
from systems.guided_engine.resolution import resolve


def main():
    raw = sys.stdin.buffer.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("Bounded guided request required")
    plan = json.loads(raw)
    expected = resolve(
        plan["brief"], plan["overrides"], package(), plan["method_sources"]
    )
    if plan != expected:
        raise ValueError("Worker resolution differs from accepted source/profile")
    e = plan["effective"]
    engine = bind_nasa_cea_engine(
        fuel_temperature_k=e["fuel_temperature"]["value"],
        oxidizer_temperature_k=e["oxidizer_temperature"]["value"],
        exit_pressure_pa=plan["ambient_pressure_pa"] or 101325,
        require_explicit_temperatures=True,
    )
    design, report = evaluate(plan, engine)
    sys.stdout.write(
        json.dumps(
            {
                "review_hash": plan["review_hash"],
                "design": design.to_canonical_dict(),
                "report": report,
            },
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
