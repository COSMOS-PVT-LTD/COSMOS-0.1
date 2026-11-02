"""Execute small native/software campaigns inside a NEW desktop package.

Never regenerate the full engine, reuse old receipts as new evidence, modify
user projects, or perform R08 acceptance. The large display case reads an
explicit existing engine STL and writes only isolated temporary display data.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


def execute(argv, root, environment, log):
    with log.open("xb") as stream:
        result = subprocess.run(
            [str(a) for a in argv],
            cwd=root,
            env=environment,
            stdout=stream,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if result.returncode:
        raise RuntimeError("Desktop qualification failed; inspect " + str(log))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", required=True, type=Path)
    parser.add_argument("--engine-inputs", required=True, type=Path)
    parser.add_argument("--engine-record", required=True, type=Path)
    parser.add_argument("--engine-stl", required=True, type=Path)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume a task-built, still-unqualified campaign; retain failed reports",
    )
    args = parser.parse_args()
    args.engine_inputs = args.engine_inputs.resolve(strict=True)
    args.engine_record = args.engine_record.resolve(strict=True)
    args.engine_stl = args.engine_stl.resolve(strict=True)
    root = args.app / "Contents/Resources/app"
    proof = root / "desktop-qualification"
    if args.resume and (
        list(root.glob("desktop-verified*.json"))
        or (proof / "occt").exists()
        or (proof / "pico").exists()
        or not (args.app / "Contents/Resources/desktop-stage.json").is_file()
    ):
        raise ValueError(
            "Resume is limited to this builder's not-yet-admitted desktop stage; historical receipts are never replaced"
        )
    proof.mkdir(exist_ok=args.resume)
    python = root / ".venv-cad-inspection/bin/python"
    runtime = root / ".runtime-picogk/2026-10-24-v1"
    prepared = proof / "prepared.json"
    prepared.write_text(
        json.dumps(
            {
                "occt": {
                    "argv": [str(python)],
                    "environment": {
                        "PYTHONPATH": str(root),
                        "OMP_NUM_THREADS": "1",
                        "OPENBLAS_NUM_THREADS": "1",
                    },
                }
            }
        )
    )
    env = {
        key: os.environ[key] for key in ("PATH", "LANG", "TMPDIR") if key in os.environ
    }
    env.update(
        R07_COMPONENT_CONFIG=str(prepared),
        PICO_COMPONENT_RUNTIME_ROOT=str(runtime),
        PICO_PREVIEW_PYTHON=str(python),
        PICO_LARGE_INPUTS=str(args.engine_inputs),
        PICO_LARGE_RECORD=str(args.engine_record),
        PICO_LARGE_STL=str(args.engine_stl),
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        PYTHONDONTWRITEBYTECODE="1",
    )
    groups = {
        "native-components": [
            "tests/integration_tests/geometry/test_component_native.py"
        ],
        "component-http": [
            "tests/integration_tests/gui/test_component_projects_http.py"
        ],
        "driving-constraints": [
            "tests/unit_tests/systems_layer/test_driving_constraints.py"
        ],
        "pico-unit": [
            "tests/unit_tests/systems_layer/test_pico_components.py",
            "tests/unit_tests/api/test_pico_component_runtime.py",
        ],
        "pico-native": [
            "tests/integration_tests/geometry/test_pico_components_native.py"
        ],
        "pico-http": ["tests/integration_tests/gui/test_pico_components_http.py"],
        "pico-preview": [
            "tests/integration_tests/geometry/test_pico_preview_native.py",
            "tests/integration_tests/geometry/test_pico_large_preview_native.py",
        ],
    }
    for name, tests in groups.items():
        if args.resume and (proof / (name + ".xml")).is_file():
            suites = list(ET.parse(proof / (name + ".xml")).getroot().iter("testsuite"))
            if (
                suites
                and sum(int(s.get("tests", 0)) for s in suites) > 0
                and not any(
                    int(s.get(key, 0))
                    for s in suites
                    for key in ("failures", "errors", "skipped")
                )
            ):
                print("Retaining completed executed stage " + name, flush=True)
                continue
        if args.resume:
            # Preserve the failed attempt instead of truncating its evidence.
            version = 1
            while (proof / (name + ".failed-" + str(version) + ".log")).exists():
                version += 1
            for suffix in (".log", ".xml"):
                prior = proof / (name + suffix)
                if prior.exists():
                    prior.rename(proof / (name + ".failed-" + str(version) + suffix))
        print("Executing bundled " + name, flush=True)
        execute(
            [
                python,
                "-m",
                "pytest",
                "-q",
                "--tb=short",
                "-p",
                "no:cacheprovider",
                *tests,
                "--junitxml=" + str(proof / (name + ".xml")),
            ],
            root,
            env,
            proof / (name + ".log"),
        )
    execute(
        [
            python,
            "-m",
            "scripts.qualify_occt_component_runtime",
            "--python",
            python,
            "--output",
            proof / "occt",
            "--native-components",
            proof / "native-components.xml",
            "--component-http",
            proof / "component-http.xml",
            "--driving-constraints",
            proof / "driving-constraints.xml",
        ],
        root,
        env,
        proof / "occt-admission.log",
    )
    pico = [
        python,
        "-m",
        "scripts.qualify_picogk_components",
        "--runtime-root",
        runtime,
        "--preview-python",
        python,
        "--output",
        proof / "pico",
    ]
    for key in ("unit", "native", "http", "preview"):
        pico.extend(["--" + key, proof / ("pico-" + key + ".xml")])
    execute(pico, root, env, proof / "pico-admission.log")
    print(
        "New bundle-local OCCT and PicoGK profiles qualified; no physical or R08 acceptance",
        flush=True,
    )


if __name__ == "__main__":
    main()
