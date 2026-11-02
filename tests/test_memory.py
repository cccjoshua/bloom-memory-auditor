from __future__ import annotations

import pytest

from contract import KeyInput, SeedInput
from plugin import audit_memory, bloom_query, exact_lookup, list_candidates
from plugin.memory import build_memory


def audit_by_tools(seed: int) -> dict:
    """What an agent submits after querying both tools for every candidate."""
    positives, negatives = [], []
    keys = list_candidates(SeedInput(seed=seed), None).candidates
    filtered = bloom_query(KeyInput(seed=seed, keys=keys), None).answers
    logged = exact_lookup(KeyInput(seed=seed, keys=keys), None).answers
    for key, bloom, exact in zip(keys, filtered, logged, strict=True):
        member, tried = bloom.member, exact.tried
        if member and not tried:
            positives.append(key)
        if tried and not member:
            negatives.append(key)
    return {"false_positives": positives, "false_negatives": negatives, "corrupted": bool(negatives)}


def test_a_seed_always_builds_the_same_memory() -> None:
    assert build_memory(42) == build_memory(42)
    assert build_memory(42) != build_memory(43)


@pytest.mark.parametrize("seed", range(300))
def test_the_tools_and_the_reference_agree(seed: int) -> None:
    reference = audit_memory(SeedInput(seed=seed), None)
    found = audit_by_tools(seed)
    assert found["false_positives"] == reference.false_positives
    assert found["false_negatives"] == reference.false_negatives
    assert found["corrupted"] == reference.corrupted


@pytest.mark.parametrize("seed", range(300))
def test_every_candidate_list_fits_one_query(seed: int) -> None:
    assert len(list_candidates(SeedInput(seed=seed), None).candidates) <= 40


def test_seeds_cover_sound_and_corrupted_filters_and_empty_answers() -> None:
    audits = [audit_memory(SeedInput(seed=seed), None) for seed in range(300)]
    assert any(item.corrupted for item in audits) and any(not item.corrupted for item in audits)
    assert any(not item.false_positives for item in audits)


def test_the_tools_refuse_keys_that_are_not_actions() -> None:
    with pytest.raises(ValueError, match="not an action key"):
        bloom_query(KeyInput(seed=7, keys=["p30:a0"]), None)
    with pytest.raises(ValueError, match="distinct"):
        bloom_query(KeyInput(seed=7, keys=["p01:a0", "p01:a0"]), None)
    with pytest.raises(ValueError, match="distinct"):
        exact_lookup(KeyInput(seed=7, keys=[]), None)
    with pytest.raises(ValueError, match="not an action key"):
        exact_lookup(KeyInput(seed=7, keys=["home"]), None)
    with pytest.raises(ValueError, match="seed"):
        list_candidates(SeedInput(seed=-1), None)
