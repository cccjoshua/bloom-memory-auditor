"""exact_lookup: whether the exact log holds each of up to 40 keys."""

from .checks import keys_problem, result, seed_problem


def verify_input(value):
    problem = seed_problem(value.seed) or keys_problem(value.keys)
    return result(problem is None, problem or "input is valid")


def verify_output(input_value, output_value, workspace):
    if [answer.key for answer in output_value.answers] != input_value.keys:
        return result(False, "the answers are not for the keys given, in order")
    return result(True, f"{len(output_value.answers)} answers")
