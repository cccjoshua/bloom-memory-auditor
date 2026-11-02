"""audit_memory, the reference: the log, the filter and their audit, each checked against the others."""

from .checks import FILTER_BITS, HASH_COUNT, audit, built_filter, key_problem, result, seed_problem


def verify_input(value):
    problem = seed_problem(value.seed)
    return result(problem is None, problem or "input is valid")


def verify_output(input_value, output_value, workspace):
    if (output_value.filter_bits, output_value.hash_count) != (FILTER_BITS, HASH_COUNT):
        return result(False, f"the filter has m = {FILTER_BITS} bits and k = {HASH_COUNT} hashes")
    for key in output_value.tried + output_value.candidates:
        problem = key_problem(key)
        if problem:
            return result(False, problem)
    if len(output_value.filter_hex) != FILTER_BITS // 4 or set(output_value.filter_hex) - set("0123456789abcdef"):
        return result(False, f"filter_hex is {FILTER_BITS // 4} lowercase hex digits")
    bits, sound = int(output_value.filter_hex, 16), built_filter(output_value.tried)
    if bits & ~sound:
        return result(False, "the filter has bits no tried key sets")
    positives, negatives = audit(output_value)
    if (output_value.false_positives, output_value.false_negatives) != (positives, negatives):
        return result(False, "the audit does not match the filter and the log")
    if output_value.corrupted != bool(negatives):
        return result(False, "corrupted is true exactly when there is a false negative")
    return result(True, "reference is consistent", cleared_bits=(sound & ~bits).bit_count())
