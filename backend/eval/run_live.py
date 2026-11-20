"""Evaluate the actual model through a running Product Finder API."""

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
from time import perf_counter

import httpx

from backend.app.conversation import search
from backend.app.models import ProductFilters


def percentile(samples, fraction):
    return round(sorted(samples)[math.ceil(len(samples) * fraction) - 1], 1) if samples else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--case")
    args = parser.parse_args()
    if args.runs < 1:
        parser.error("--runs must be positive")
    cases = json.loads(Path(__file__).with_name("conversations.json").read_text())
    if args.case:
        if args.case not in cases:
            parser.error("unknown case")
        cases = {args.case: cases[args.case]}

    totals = defaultdict(int)
    timing = defaultdict(list)
    failures = []
    with httpx.Client(base_url=args.base_url, timeout=60) as client:
        # Keep the first observed request distinct without claiming it was a cold start.
        for run in range(args.runs):
            for name, turns in cases.items():
                state = None
                case_passed = True
                for index, turn in enumerate(turns):
                    totals["attempted_turns"] += 1
                    started = perf_counter()
                    try:
                        response = client.post("/api/v1/chat", json={
                            "message": turn["message"], "active_filters": state,
                            "demo_catalogue": True,
                        })
                        response.raise_for_status()
                        result = response.json()
                        state = result["applied_filters"]
                        filters = {k: v for k, v in state.items() if v is not None}
                        ids = [p["id"] for p in result["products"]]
                        expected_ids = {p.id for p in search(ProductFilters(**turn["filters"]), True).products}
                        totals["returned_products"] += len(ids)
                        totals["products_matching_expected_filters"] += sum(p in expected_ids for p in ids)
                        expected_filters = turn["filters"]
                        alternatives = [expected_filters, turn.get("equivalent")]
                        # In the sample jacket catalogue, "jacket" already limits
                        # results to clothing. The walkthrough never asks for category.
                        if name in {"walkthrough", "accept_budget_offer", "budget_down",
                                    "budget_up", "clear_colour", "clear_budget",
                                    "ambiguity", "size_then_clear"} and (
                            expected_filters.get("category") == "clothing"
                            and expected_filters.get("search_text") == "jacket"
                        ):
                            alternatives.append({
                                key: value for key, value in expected_filters.items()
                                if key != "category"
                            })
                        checks = {
                            "filters": filters in alternatives,
                            "products": sorted(ids) == sorted(turn["ids"]),
                            "clarification": result["clarification"] == turn.get("clarification", False),
                            "offer": result["relaxation_offer"] == turn.get("offer"),
                        }
                        for key, passed in checks.items():
                            totals[f"{key}_passed"] += int(passed)
                        missed = [key for key, passed in checks.items() if not passed]
                        if missed:
                            failure = {"run": run + 1, "case": name, "turn": index + 1, "failed": missed}
                            if "filters" in missed:
                                failure.update(expected_filters=expected_filters, actual_filters=filters)
                            failures.append(failure)
                            case_passed = False
                    except (httpx.HTTPError, KeyError, ValueError) as exc:
                        failures.append({"run": run + 1, "case": name, "turn": index + 1,
                                         "error": str(exc),
                                         "request_id": exc.response.headers.get("X-Request-ID")
                                         if isinstance(exc, httpx.HTTPStatusError) else None})
                        case_passed = False
                        break
                    finally:
                        group = "first_turn" if index == 0 else "follow_up"
                        timing[group].append((perf_counter() - started) * 1000)
                totals["conversations_passed"] += int(case_passed)
    totals["conversations_attempted"] = args.runs * len(cases)
    print(json.dumps({
        "totals": dict(totals),
        "latency_ms": {key: {"p50": percentile(values, .5), "p95": percentile(values, .95)}
                       for key, values in timing.items()},
        "failures": failures,
    }, indent=2))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
