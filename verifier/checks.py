"""Checks shared by the tool verifiers. Pure functions of their arguments.

The verifier rebuilds the Bloom filter itself: bit i of a key is sha256('<i>:<key>') mod m.
"""

import hashlib
import re

KEY = re.compile(r"^p(?:[01]\d|2\d):a[0-5]$")
MAX_SEED = 1_000_000
FILTER_BITS = 128
HASH_COUNT = 3
MAX_KEYS = 40


def result(valid, message, *, score=None, **details):
    return {
        "valid": valid,
        "score": float(valid) if score is None else score,
        "message": message,
        "details": details,
    }


def seed_problem(seed):
    if not 0 <= seed <= MAX_SEED:
        return f"seed must be between 0 and {MAX_SEED}"
    return None


def key_problem(key):
    if not KEY.fullmatch(key):
        return f"{key!r} is not an action key, p00:a0 to p29:a5"
    return None


def keys_problem(keys):
    if not 1 <= len(keys) <= MAX_KEYS:
        return f"give 1 to {MAX_KEYS} keys"
    if len(set(keys)) != len(keys):
        return "a key is given twice"
    for key in keys:
        problem = key_problem(key)
        if problem:
            return problem
    return None


def positions(key, bits=FILTER_BITS, count=HASH_COUNT):
    return [int.from_bytes(hashlib.sha256(f"{index}:{key}".encode()).digest()[:8], "big") % bits for index in range(count)]


def built_filter(keys):
    """The filter a sound write of ``keys`` gives, as an integer of bits."""
    bits = 0
    for key in keys:
        for bit in positions(key):
            bits |= 1 << bit
    return bits


def member(bits, key):
    return all(bits >> bit & 1 for bit in positions(key))


def audit(reference):
    """The false positives and false negatives of a contract ReferenceOutput, from its filter bits and log."""
    bits = int(reference.filter_hex, 16)
    tried = set(reference.tried)
    positives = sorted(key for key in reference.candidates if member(bits, key) and key not in tried)
    negatives = sorted(key for key in reference.candidates if not member(bits, key) and key in tried)
    return positives, negatives
