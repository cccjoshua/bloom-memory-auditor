"""The plugin's tools: each takes its contract input and the workspace, and reads the seed's memory."""

from __future__ import annotations

from pathlib import Path

from contract import (
    BloomAnswer,
    BloomOutput,
    CandidatesOutput,
    ExactAnswer,
    ExactOutput,
    KeyInput,
    ReferenceOutput,
    SeedInput,
)
from plugin.memory import FILTER_BITS, HASH_COUNT, MAX_KEYS, build_memory, check_key, positions


def list_candidates(given: SeedInput, workspace: Path) -> CandidatesOutput:
    memory = build_memory(given.seed)
    return CandidatesOutput(
        seed=given.seed, filter_bits=FILTER_BITS, hash_count=HASH_COUNT, candidates=list(memory.candidates)
    )


def _check_keys(keys: list[str]) -> None:
    if not 1 <= len(keys) <= MAX_KEYS or len(set(keys)) != len(keys):
        raise ValueError(f"give 1 to {MAX_KEYS} distinct keys")
    for key in keys:
        check_key(key)


def bloom_query(given: KeyInput, workspace: Path) -> BloomOutput:
    _check_keys(given.keys)
    memory = build_memory(given.seed)
    answers = []
    for key in given.keys:
        found = positions(key)
        bits_set = [bool(memory.bits >> bit & 1) for bit in found]
        answers.append(BloomAnswer(key=key, positions=found, bits_set=bits_set, member=all(bits_set)))
    return BloomOutput(answers=answers)


def exact_lookup(given: KeyInput, workspace: Path) -> ExactOutput:
    _check_keys(given.keys)
    tried = build_memory(given.seed).tried
    return ExactOutput(answers=[ExactAnswer(key=key, tried=key in tried) for key in given.keys])


def audit_memory(given: SeedInput, workspace: Path) -> ReferenceOutput:
    """The reference: the whole log and filter, run out of the agent's sight."""
    memory = build_memory(given.seed)
    negatives = memory.false_negatives()
    return ReferenceOutput(
        filter_bits=FILTER_BITS,
        hash_count=HASH_COUNT,
        tried=sorted(memory.tried),
        filter_hex=f"{memory.bits:032x}",
        candidates=list(memory.candidates),
        false_positives=memory.false_positives(),
        false_negatives=negatives,
        corrupted=bool(negatives),
    )
