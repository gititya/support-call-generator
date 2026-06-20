from __future__ import annotations

import argparse
from pathlib import Path
import sys

from support_call_generator.exporter import EXPORT_BUNDLE_DESCRIPTIONS, EXPORT_BUNDLES, export_reviewed
from support_call_generator.export_realtime import export_realtime_support
from support_call_generator.generator import generate_call
from support_call_generator.profiles import PROFILE_NAMES
from support_call_generator.report import print_batch_report
from support_call_generator.scenarios import SCENARIO_TYPES
from support_call_generator.storage import list_cases, load_case, save_case, update_review


def main() -> None:
    parser = argparse.ArgumentParser(prog="support-call-generator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    one = subparsers.add_parser("generate-one")
    one.add_argument("--scenario", choices=SCENARIO_TYPES, default="permissions_access")
    one.add_argument("--seed", type=int)
    one.add_argument("--cases-dir", default="data/cases")
    one.add_argument("--offline", action="store_true")
    one.add_argument("--accept", action="store_true")
    one.add_argument("--profile", choices=PROFILE_NAMES)

    batch = subparsers.add_parser("generate-batch")
    batch.add_argument("--count", type=int, default=50)
    batch.add_argument("--cases-dir", default="data/cases")
    batch.add_argument("--offline", action="store_true")
    batch.add_argument("--profile", choices=PROFILE_NAMES)

    export = subparsers.add_parser("export-reviewed")
    export.add_argument("--cases-dir", default="data/cases")
    export.add_argument("--export-dir", default="exports")
    export.add_argument("--status", choices=["accepted", "draft", "rejected", "all"], default="accepted")
    export.add_argument("--format", dest="export_format", choices=["default", "realtime_support"], default="default")
    export.add_argument("--bundle", choices=[*EXPORT_BUNDLES, "process_fixture"], default="eval_pack", help=_bundle_help())

    pack = subparsers.add_parser("generate-pack")
    pack.add_argument("--count", type=int, default=10)
    pack.add_argument("--cases-dir", default="data/generated_pack_cases")
    pack.add_argument("--export-dir", default="exports/generated_pack")
    pack.add_argument("--offline", action="store_true")
    pack.add_argument("--profile", choices=PROFILE_NAMES, default="hard")
    pack.add_argument("--bundle", choices=[*EXPORT_BUNDLES, "process_fixture"], default="review_pack", help=_bundle_help())

    args = parser.parse_args()

    if args.command == "generate-one":
        case = generate_call(
            scenario_type=args.scenario,
            seed=args.seed,
            use_llm=False if args.offline else None,
            profile=args.profile,
        )
        save_case(case, cases_dir=Path(args.cases_dir))
        if args.accept:
            update_review(case["case_id"], "accepted", "", cases_dir=Path(args.cases_dir))
        print(case["case_id"])
        return

    if args.command == "generate-batch":
        batch_cases = _generate_batch(args.count, Path(args.cases_dir), args.offline, args.profile)
        print_batch_report(batch_cases)
        return

    if args.command == "export-reviewed":
        if args.export_format == "realtime_support" or args.bundle == "process_fixture":
            result = export_realtime_support(
                cases_dir=Path(args.cases_dir),
                export_dir=Path(args.export_dir),
                status=args.status,
            )
        else:
            result = export_reviewed(
                cases_dir=Path(args.cases_dir),
                export_dir=Path(args.export_dir),
                status=args.status,
                bundle=args.bundle,
            )
        print(f"exported {result['exported']} cases")
        return

    if args.command == "generate-pack":
        batch_cases = _generate_batch(args.count, Path(args.cases_dir), args.offline, args.profile)
        print_batch_report(batch_cases)
        if args.bundle == "process_fixture":
            result = export_realtime_support(
                cases_dir=Path(args.cases_dir),
                export_dir=Path(args.export_dir),
                status="all",
                collection_name="process_fixture",
                envelope_name="process_fixture_envelope.json",
            )
        else:
            result = export_reviewed(
                cases_dir=Path(args.cases_dir),
                export_dir=Path(args.export_dir),
                status="all",
                bundle=args.bundle,
            )
        print(f"exported {result['exported']} cases to {args.export_dir}")
        return


def _root_cause_counts(cases_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for summary in list_cases(cases_dir):
        case = load_case(summary["case_id"], cases_dir)
        root_id = case["scenario_spec"].get("root_cause_id")
        if root_id:
            counts[root_id] = counts.get(root_id, 0) + 1
    return counts


def _bundle_help() -> str:
    descriptions = {
        **EXPORT_BUNDLE_DESCRIPTIONS,
        "process_fixture": "transcript plus context events, expected state, next checks, handoff fields, and outcome fields",
    }
    return "; ".join(f"{name}: {description}" for name, description in descriptions.items())


def _generate_batch(
    count: int,
    cases_dir: Path,
    offline: bool,
    profile: str | None,
) -> list[dict]:
    saved = 0
    attempts = 0
    max_attempts = count * 4
    root_cause_counts = _root_cause_counts(cases_dir)
    batch_cases: list = []
    while saved < count and attempts < max_attempts:
        scenario = SCENARIO_TYPES[saved % len(SCENARIO_TYPES)]
        attempts += 1
        try:
            case = generate_call(
                scenario_type=scenario,
                use_llm=False if offline else None,
                root_cause_counts=root_cause_counts,
                profile=profile,
            )
        except Exception as exc:
            if exc.__class__.__name__ == "AuthenticationError":
                print("generation failed: authentication error", file=sys.stderr)
                sys.exit(1)
            print(f"skipping malformed generation attempt: {exc.__class__.__name__}", file=sys.stderr)
            continue
        save_case(case, cases_dir=cases_dir)
        batch_cases.append(case)
        root_cause_id = case["scenario_spec"]["root_cause_id"]
        root_cause_counts[root_cause_id] = root_cause_counts.get(root_cause_id, 0) + 1
        print(case["case_id"])
        saved += 1
    if saved < count:
        print(f"generation failed: only saved {saved} of {count} cases", file=sys.stderr)
        sys.exit(1)
    print()
    return batch_cases
