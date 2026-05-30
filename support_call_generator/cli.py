from __future__ import annotations

import argparse
from pathlib import Path
import sys

from support_call_generator.exporter import export_reviewed
from support_call_generator.generator import generate_call
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

    batch = subparsers.add_parser("generate-batch")
    batch.add_argument("--count", type=int, default=50)
    batch.add_argument("--cases-dir", default="data/cases")
    batch.add_argument("--offline", action="store_true")

    export = subparsers.add_parser("export-reviewed")
    export.add_argument("--cases-dir", default="data/cases")
    export.add_argument("--export-dir", default="exports")
    export.add_argument("--status", choices=["accepted", "draft", "rejected", "all"], default="accepted")

    args = parser.parse_args()

    if args.command == "generate-one":
        case = generate_call(
            scenario_type=args.scenario,
            seed=args.seed,
            use_llm=False if args.offline else None,
        )
        save_case(case, cases_dir=Path(args.cases_dir))
        if args.accept:
            update_review(case["case_id"], "accepted", "", cases_dir=Path(args.cases_dir))
        print(case["case_id"])
        return

    if args.command == "generate-batch":
        saved = 0
        attempts = 0
        max_attempts = args.count * 4
        root_cause_counts = _root_cause_counts(Path(args.cases_dir))
        while saved < args.count and attempts < max_attempts:
            scenario = SCENARIO_TYPES[saved % len(SCENARIO_TYPES)]
            attempts += 1
            try:
                case = generate_call(
                    scenario_type=scenario,
                    use_llm=False if args.offline else None,
                    root_cause_counts=root_cause_counts,
                )
            except Exception as exc:
                if exc.__class__.__name__ == "AuthenticationError":
                    print("generation failed: authentication error", file=sys.stderr)
                    sys.exit(1)
                print(f"skipping malformed generation attempt: {exc.__class__.__name__}", file=sys.stderr)
                continue
            save_case(case, cases_dir=Path(args.cases_dir))
            root_cause_id = case["scenario_spec"]["root_cause_id"]
            root_cause_counts[root_cause_id] = root_cause_counts.get(root_cause_id, 0) + 1
            print(case["case_id"])
            saved += 1
        if saved < args.count:
            print(f"generation failed: only saved {saved} of {args.count} cases", file=sys.stderr)
            sys.exit(1)
        return

    if args.command == "export-reviewed":
        result = export_reviewed(
            cases_dir=Path(args.cases_dir),
            export_dir=Path(args.export_dir),
            status=args.status,
        )
        print(f"exported {result['exported']} cases")
        return


def _root_cause_counts(cases_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for summary in list_cases(cases_dir):
        case = load_case(summary["case_id"], cases_dir)
        root_id = case["scenario_spec"].get("root_cause_id")
        if root_id:
            counts[root_id] = counts.get(root_id, 0) + 1
    return counts
