"""Each tool's and task's typed input and output (see nanoagent.plugin.v0001.contract): declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    LIST_CANDIDATES = "list_candidates"
    BLOOM_QUERY = "bloom_query"
    EXACT_LOOKUP = "exact_lookup"
    AUDIT_MEMORY = "audit_memory"


class Task(Enum):
    AUDIT_BLOOM_MEMORY = "audit-bloom-memory"


SEED = "The memory's seed, 0 to 1000000: the same seed always builds the same memory"
KEY = "An action key, page:action, e.g. p03:a2"


@dataclass
class SeedInput(Output):
    seed: Annotated[int, SEED]


@dataclass
class CandidatesOutput(Output):
    seed: Annotated[int, SEED]
    filter_bits: Annotated[int, "The Bloom filter's size m, in bits"]
    hash_count: Annotated[int, "How many hash functions k the filter uses"]
    candidates: Annotated[list[str], "The action keys to audit, sorted"]


@dataclass
class KeyInput(Output):
    seed: Annotated[int, SEED]
    keys: Annotated[list[str], "The action keys to ask about, 1 to 40 distinct keys, e.g. [p03:a2, p11:a0]"]


@dataclass
class BloomAnswer(Output):
    key: Annotated[str, KEY]
    positions: Annotated[list[int], "The key's bit positions, one per hash function: sha256('<i>:<key>') mod m"]
    bits_set: Annotated[list[bool], "Whether each of those bits is set in the filter"]
    member: Annotated[bool, "Whether the filter says the key was tried: every one of its bits is set"]


@dataclass
class BloomOutput(Output):
    answers: Annotated[list[BloomAnswer], "The filter's answer for each key, in the order given"]


@dataclass
class ExactAnswer(Output):
    key: Annotated[str, KEY]
    tried: Annotated[bool, "Whether the exact log of the episode holds the key"]


@dataclass
class ExactOutput(Output):
    answers: Annotated[list[ExactAnswer], "The exact log's answer for each key, in the order given"]


@dataclass
class ReferenceOutput(Output):
    filter_bits: Annotated[int, "The filter's size m"]
    hash_count: Annotated[int, "The filter's k"]
    tried: Annotated[list[str], "Every key in the exact log, sorted"]
    filter_hex: Annotated[str, "The filter's bits as hex, bit i is bit i of the integer"]
    candidates: Annotated[list[str], "The keys to audit, sorted"]
    false_positives: Annotated[list[str], "Candidates the filter holds that the log does not, sorted"]
    false_negatives: Annotated[list[str], "Candidates the log holds that the filter does not, sorted"]
    corrupted: Annotated[bool, "Whether any candidate is a false negative"]


@dataclass
class AuditOutput(Output):
    false_positives: Annotated[list[str], "Every candidate the filter says was tried but the exact log never tried"]
    false_negatives: Annotated[list[str], "Every candidate the exact log tried but the filter says was not"]
    corrupted: Annotated[bool, "True when there is any false negative: a sound Bloom filter never has one"]


TOOLS = {
    Tool.LIST_CANDIDATES: (SeedInput, CandidatesOutput),
    Tool.BLOOM_QUERY: (KeyInput, BloomOutput),
    Tool.EXACT_LOOKUP: (KeyInput, ExactOutput),
    Tool.AUDIT_MEMORY: (SeedInput, ReferenceOutput),
}
TASKS = {
    Task.AUDIT_BLOOM_MEMORY: (SeedInput, AuditOutput),
}
