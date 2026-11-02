"""The already-tried memory: an exact log of tried actions and a Bloom filter of it, built from a seed.

The filter has m = 128 bits and k = 3 hash functions; bit i of key is sha256('<i>:<key>') mod m. On
about half of the seeds a few bits are cleared, as a bad write would, so some tried candidates read as
untried: false negatives, which a sound Bloom filter never has.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

MAX_SEED = 1_000_000
FILTER_BITS = 128
HASH_COUNT = 3
MAX_KEYS = 40  # the most keys one query takes
KEYS = tuple(f"p{page:02d}:a{act}" for page in range(30) for act in range(6))
KEY_FORM = "p00:a0 to p29:a5"


def positions(key: str) -> list[int]:
    return [
        int.from_bytes(hashlib.sha256(f"{index}:{key}".encode()).digest()[:8], "big") % FILTER_BITS
        for index in range(HASH_COUNT)
    ]


@dataclass(frozen=True)
class Memory:
    tried: frozenset[str]
    bits: int  # bit i set = filter bit i set
    candidates: tuple[str, ...]

    def member(self, key: str) -> bool:
        return all(self.bits >> bit & 1 for bit in positions(key))

    def false_positives(self) -> list[str]:
        return sorted(key for key in self.candidates if self.member(key) and key not in self.tried)

    def false_negatives(self) -> list[str]:
        return sorted(key for key in self.candidates if not self.member(key) and key in self.tried)


class Draws:
    """A deterministic stream of choices from the seed: SHA-256 of the seed and a counter."""

    def __init__(self, seed: int) -> None:
        self.seed, self.count = seed, 0

    def below(self, bound: int) -> int:
        digest = hashlib.sha256(f"bloom-auditor:{self.seed}:{self.count}".encode()).digest()
        self.count += 1
        return int.from_bytes(digest[:8], "big") % bound

    def shuffled(self, items):
        items = list(items)
        for index in range(len(items) - 1, 0, -1):
            other = self.below(index + 1)
            items[index], items[other] = items[other], items[index]
        return items


def build_memory(seed: int) -> Memory:
    if not 0 <= seed <= MAX_SEED:
        raise ValueError(f"seed must be between 0 and {MAX_SEED}")
    draws = Draws(seed)
    keys = draws.shuffled(KEYS)
    tried_count = 30 + draws.below(21)  # 30 to 50
    tried, untried = keys[:tried_count], keys[tried_count:]
    bits = 0
    for key in tried:
        for bit in positions(key):
            bits |= 1 << bit
    candidates = tried[:10 + draws.below(5)] + untried[:16 + draws.below(5)]
    if draws.below(2) == 0:  # corrupt: clear one bit of 1 to 3 tried candidates
        for key in tried[: 1 + draws.below(3)]:
            bits &= ~(1 << positions(key)[draws.below(HASH_COUNT)])
    return Memory(frozenset(tried), bits, tuple(sorted(candidates)))


def check_key(key: str) -> None:
    if key not in KEYS:
        raise ValueError(f"{key!r} is not an action key, {KEY_FORM}")
