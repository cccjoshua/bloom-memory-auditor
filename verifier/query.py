"""bloom_query: up to 40 keys' bits in the filter."""

from .checks import keys_problem, positions, result, seed_problem


def verify_input(value):
    problem = seed_problem(value.seed) or keys_problem(value.keys)
    return result(problem is None, problem or "input is valid")


def verify_output(input_value, output_value, workspace):
    if [answer.key for answer in output_value.answers] != input_value.keys:
        return result(False, "the answers are not for the keys given, in order")
    for answer in output_value.answers:
        if answer.positions != positions(answer.key):
            return result(False, f"{answer.key}'s positions are not its sha256 positions")
        if len(answer.bits_set) != len(answer.positions):
            return result(False, f"{answer.key} has one bit per position")
        if answer.member != all(answer.bits_set):
            return result(False, f"{answer.key} is a member exactly when all its bits are set")
    return result(True, f"{len(output_value.answers)} answers")
