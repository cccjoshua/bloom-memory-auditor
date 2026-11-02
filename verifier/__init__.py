"""The deterministic verifier: each tool's checks live in its own module, on contract instances."""

from contract import Task, Tool

from . import candidates, lookup, query, reference, report

TOOLS = {
    Tool.LIST_CANDIDATES: candidates,
    Tool.BLOOM_QUERY: query,
    Tool.EXACT_LOOKUP: lookup,
    Tool.AUDIT_MEMORY: reference,
}
# task -> its output's check, verify_task(arguments, output, reference, workspace)
TASKS = {Task.AUDIT_BLOOM_MEMORY: report.verify_task}


def verify_input(tool, value):
    return TOOLS[Tool(tool)].verify_input(value)


def verify_output(tool, input_value, output_value, workspace):
    return TOOLS[Tool(tool)].verify_output(input_value, output_value, workspace)


def verify_task(task, arguments, output, reference, workspace):
    return TASKS[Task(task)](arguments, output, reference, workspace)
