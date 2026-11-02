"""list_candidates: the keys to audit and the filter's shape."""

from .checks import FILTER_BITS, HASH_COUNT, key_problem, result, seed_problem


def verify_input(value):
    problem = seed_problem(value.seed)
    return result(problem is None, problem or "input is valid")


def verify_output(input_value, output_value, workspace):
    if output_value.seed != input_value.seed:
        return result(False, "the candidates are for another seed")
    if (output_value.filter_bits, output_value.hash_count) != (FILTER_BITS, HASH_COUNT):
        return result(False, f"the filter has m = {FILTER_BITS} bits and k = {HASH_COUNT} hashes")
    keys = output_value.candidates
    if not keys or keys != sorted(set(keys)):
        return result(False, "candidates are distinct, sorted and not empty")
    for key in keys:
        problem = key_problem(key)
        if problem:
            return result(False, problem)
    return result(True, "candidates are well formed", candidates=len(keys))
