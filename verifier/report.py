"""audit-bloom-memory: the agent's audit, compared with the audit of the rebuilt filter.

Valid only when both sets and the corrupted flag match exactly, with no key twice and no key that is
not a candidate. The score is the share of candidates the report classifies correctly.
"""

from .checks import audit, key_problem, result


def verify_task(arguments, output, reference, workspace):
    """``output``: a contract AuditOutput; ``reference``: the audit_memory ReferenceOutput of the same seed."""
    if reference is None:
        return result(False, "no reference memory: the audit cannot be checked")
    candidates = set(reference.candidates)
    for name, keys in (("false_positives", output.false_positives), ("false_negatives", output.false_negatives)):
        for key in keys:
            problem = key_problem(key)
            if problem:
                return result(False, f"{name}: {problem}")
        if len(set(keys)) != len(keys):
            return result(False, f"{name} lists a key twice")
        outside = sorted(set(keys) - candidates)
        if outside:
            return result(False, f"{name} holds keys that are not candidates: {', '.join(outside)}")
    both = sorted(set(output.false_positives) & set(output.false_negatives))
    if both:
        return result(False, f"a key cannot be both a false positive and a false negative: {', '.join(both)}")

    positives, negatives = audit(reference)
    wrong = {
        "missed_false_positives": sorted(set(positives) - set(output.false_positives)),
        "extra_false_positives": sorted(set(output.false_positives) - set(positives)),
        "missed_false_negatives": sorted(set(negatives) - set(output.false_negatives)),
        "extra_false_negatives": sorted(set(output.false_negatives) - set(negatives)),
    }
    misclassified = len(set().union(*wrong.values()))
    score = 1 - misclassified / len(candidates)
    corrupted = bool(negatives)
    if misclassified:
        found = ", ".join(f"{len(keys)} {name.replace('_', ' ')}" for name, keys in wrong.items() if keys)
        return result(False, found, score=score, **{name: keys for name, keys in wrong.items() if keys})
    if output.corrupted != corrupted:
        return result(False, f"corrupted is {output.corrupted}, the filter is {'corrupted' if corrupted else 'sound'}",
                      score=score)
    return result(
        True,
        f"{len(positives)} false positive(s), {len(negatives)} false negative(s), "
        + ("corrupted" if corrupted else "sound"),
        false_positives=len(positives),
        false_negatives=len(negatives),
    )
