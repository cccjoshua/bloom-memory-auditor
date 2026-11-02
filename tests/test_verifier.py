from __future__ import annotations

from pathlib import Path

import pytest
from slimconfig import build_output, plain_output
from test_memory import audit_by_tools

import verifier
from contract import TASKS, TOOLS, KeyInput, ReferenceOutput, SeedInput, Task, Tool
from plugin import audit_memory, bloom_query, exact_lookup, list_candidates

TASK = "audit-bloom-memory"
SEEDS = range(60)


# The verifier gets contract instances, as NanoAgent's sandbox builds them from JSON.
def verify_task(seed: int, output: dict, reference: ReferenceOutput | None, workspace: Path) -> dict:
    given, made = TASKS[Task(TASK)]
    pinned = None if reference is None else build_output(plain_output(reference), ReferenceOutput)
    return verifier.verify_task(TASK, build_output({"seed": seed}, given), build_output(output, made), pinned,
                                str(workspace))


def verify_input(tool: str, value: dict) -> dict:
    return verifier.verify_input(tool, build_output(value, TOOLS[Tool(tool)][0]))


def verify_output(tool: str, given: dict, made: dict) -> dict:
    given_class, made_class = TOOLS[Tool(tool)]
    return verifier.verify_output(tool, build_output(given, given_class), build_output(made, made_class), "")


def reference(seed: int) -> ReferenceOutput:
    return audit_memory(SeedInput(seed=seed), None)


def corrupted_seed() -> int:
    return next(seed for seed in range(100) if reference(seed).corrupted)


def sound_seed_with_positives() -> int:
    return next(seed for seed in range(100) if not reference(seed).corrupted and reference(seed).false_positives)


# Correct


@pytest.mark.parametrize("seed", SEEDS)
def test_approves_the_true_audit(seed: int, tmp_path: Path) -> None:
    verdict = verify_task(seed, audit_by_tools(seed), reference(seed), tmp_path)
    assert verdict["valid"] is True and verdict["score"] == 1.0


def test_order_does_not_matter(tmp_path: Path) -> None:
    seed = corrupted_seed()
    found = audit_by_tools(seed)
    found = {key: value[::-1] if isinstance(value, list) else value for key, value in found.items()}
    assert verify_task(seed, found, reference(seed), tmp_path)["valid"] is True


# Incorrect


def test_refuses_a_missed_or_extra_false_positive(tmp_path: Path) -> None:
    seed = sound_seed_with_positives()
    found, total = audit_by_tools(seed), len(reference(seed).candidates)
    missed = found | {"false_positives": found["false_positives"][1:]}
    verdict = verify_task(seed, missed, reference(seed), tmp_path)
    assert verdict["valid"] is False and "missed false positives" in verdict["message"]
    assert verdict["score"] == pytest.approx(1 - 1 / total)
    true_positive = next(key for key in reference(seed).candidates if key in reference(seed).tried
                         and key not in found["false_negatives"])
    extra = found | {"false_positives": found["false_positives"] + [true_positive]}
    verdict = verify_task(seed, extra, reference(seed), tmp_path)
    assert verdict["valid"] is False and verdict["details"]["extra_false_positives"] == [true_positive]


def test_refuses_a_missed_corruption(tmp_path: Path) -> None:
    seed = corrupted_seed()
    found = audit_by_tools(seed)
    hidden = found | {"false_negatives": [], "corrupted": False}
    verdict = verify_task(seed, hidden, reference(seed), tmp_path)
    assert verdict["valid"] is False and "missed false negatives" in verdict["message"]
    flag = found | {"corrupted": False}
    verdict = verify_task(seed, flag, reference(seed), tmp_path)
    assert verdict["valid"] is False and "corrupted is False" in verdict["message"]


def test_refuses_a_corruption_claim_on_a_sound_filter(tmp_path: Path) -> None:
    seed = sound_seed_with_positives()
    found = audit_by_tools(seed) | {"corrupted": True}
    verdict = verify_task(seed, found, reference(seed), tmp_path)
    assert verdict["valid"] is False and "the filter is sound" in verdict["message"]


def test_refuses_another_seeds_audit(tmp_path: Path) -> None:
    other = next(seed for seed in range(1, 50) if audit_by_tools(seed) != audit_by_tools(0))
    assert verify_task(0, audit_by_tools(other), reference(0), tmp_path)["valid"] is False


# Missing


def test_refuses_an_empty_report_or_a_missing_reference(tmp_path: Path) -> None:
    seed = sound_seed_with_positives()
    empty = {"false_positives": [], "false_negatives": [], "corrupted": False}
    assert verify_task(seed, empty, reference(seed), tmp_path)["valid"] is False
    verdict = verify_task(seed, audit_by_tools(seed), None, tmp_path)
    assert verdict["valid"] is False and "no reference" in verdict["message"]


# Malformed


def test_refuses_keys_twice_outside_the_candidates_or_in_both_sets(tmp_path: Path) -> None:
    seed = corrupted_seed()
    found = audit_by_tools(seed)
    twice = found | {"false_negatives": found["false_negatives"] * 2}
    assert "twice" in verify_task(seed, twice, reference(seed), tmp_path)["message"]
    outside = next(key for key in reference(seed).tried if key not in reference(seed).candidates)
    stranger = found | {"false_positives": found["false_positives"] + [outside]}
    assert "not candidates" in verify_task(seed, stranger, reference(seed), tmp_path)["message"]
    both = found | {"false_positives": found["false_positives"] + found["false_negatives"][:1]}
    assert "both" in verify_task(seed, both, reference(seed), tmp_path)["message"]
    shaped = found | {"false_positives": ["p3-a2"]}
    assert "not an action key" in verify_task(seed, shaped, reference(seed), tmp_path)["message"]


@pytest.mark.parametrize(
    "output",
    [
        {"false_positives": [], "false_negatives": []},
        {"false_positives": "p01:a0", "false_negatives": [], "corrupted": False},
        {"false_positives": [], "false_negatives": [], "corrupted": "maybe"},
    ],
)
def test_the_contract_refuses_a_malformed_report(output: dict) -> None:
    with pytest.raises(Exception):  # noqa: B017 - slimconfig's error type is its own
        build_output(output, TASKS[Task(TASK)][1])


def test_refuses_malformed_tool_input() -> None:
    assert verify_input("bloom_query", {"seed": 7, "keys": ["p03:a2", "p04:a1"]})["valid"] is True
    assert verify_input("bloom_query", {"seed": 7, "keys": ["p30:a2"]})["valid"] is False
    assert verify_input("bloom_query", {"seed": 7, "keys": []})["valid"] is False
    assert verify_input("bloom_query", {"seed": 7, "keys": ["p03:a2", "p03:a2"]})["valid"] is False
    many = [f"p{page:02d}:a{act}" for page in range(7) for act in range(6)]
    assert verify_input("bloom_query", {"seed": 7, "keys": many})["valid"] is False
    assert verify_input("exact_lookup", {"seed": 7, "keys": ["p03:a6"]})["valid"] is False
    assert verify_input("list_candidates", {"seed": -5})["valid"] is False


# Boundary


def test_a_sound_filter_with_no_false_positive_takes_an_empty_report(tmp_path: Path) -> None:
    seed = next(seed for seed in range(1000) if not reference(seed).false_positives and not reference(seed).corrupted)
    empty = {"false_positives": [], "false_negatives": [], "corrupted": False}
    assert verify_task(seed, empty, reference(seed), tmp_path)["valid"] is True


def test_boundary_seeds(tmp_path: Path) -> None:
    for seed in (0, 1_000_000):
        assert verify_task(seed, audit_by_tools(seed), reference(seed), tmp_path)["valid"] is True


# Each tool's own checks


def test_tool_outputs_pass_their_checks_and_tampered_ones_do_not() -> None:
    listed = plain_output(list_candidates(SeedInput(seed=7), None))
    assert verify_output("list_candidates", {"seed": 7}, listed)["valid"] is True
    assert verify_output("list_candidates", {"seed": 7}, listed | {"filter_bits": 64})["valid"] is False

    asked = {"seed": 7, "keys": listed["candidates"]}
    queried = plain_output(bloom_query(KeyInput(**asked), None))
    assert verify_output("bloom_query", asked, queried)["valid"] is True
    first = queried["answers"][0]
    lied = {"answers": [first | {"member": not first["member"]}] + queried["answers"][1:]}
    assert verify_output("bloom_query", asked, lied)["valid"] is False
    moved = {"answers": [first | {"positions": [0, 1, 2]}] + queried["answers"][1:]}
    assert verify_output("bloom_query", asked, moved)["valid"] is False
    assert verify_output("bloom_query", asked, {"answers": queried["answers"][::-1]})["valid"] is False

    looked = plain_output(exact_lookup(KeyInput(**asked), None))
    assert verify_output("exact_lookup", asked, looked)["valid"] is True
    assert verify_output("exact_lookup", asked, {"answers": looked["answers"][1:]})["valid"] is False

    found = plain_output(reference(7))
    assert verify_output("audit_memory", {"seed": 7}, found)["valid"] is True
    extra_bits = found | {"filter_hex": "f" * 32}
    assert verify_output("audit_memory", {"seed": 7}, extra_bits)["valid"] is False
    wrong = found | {"false_positives": found["false_positives"][1:]}
    assert verify_output("audit_memory", {"seed": 7}, wrong)["valid"] is False


def test_the_verdict_is_the_same_every_time(tmp_path: Path) -> None:
    seed = corrupted_seed()
    found = audit_by_tools(seed) | {"false_negatives": []}
    verdicts = [verify_task(seed, found, reference(seed), tmp_path) for _ in range(3)]
    assert verdicts[0] == verdicts[1] == verdicts[2]
