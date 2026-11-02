# Bloom-Filter Memory Auditor

A `nanoagent.plugin/v0001` plugin. A web agent's "already-tried" memory is a Bloom filter of the
actions it tried. The agent audits it: for every candidate action it asks the filter and the exact log,
and reports the false positives, the false negatives and whether the filter is corrupted. A
deterministic verifier rebuilds the filter itself and checks the report.

Each memory is built from an integer seed alone (SHA-256 of the seed and a counter): 30 to 50 tried
actions out of 180, a filter of m = 128 bits with k = 3 hash functions (bit i of a key is
`sha256("<i>:<key>") mod 128`), and 26 to 34 candidates. On about half of the seeds one to three bits
are cleared, which shows up as false negatives. No network is used.

## Tools

| Tool | Does | Code |
|---|---|---|
| `list_candidates` | Lists the keys to audit and the filter's m and k | `src/plugin/tools.py` |
| `bloom_query` | Gives up to 40 keys' bit positions, which are set, and whether the filter holds each | `src/plugin/tools.py` |
| `exact_lookup` | Says whether the exact log holds each of up to 40 keys | `src/plugin/tools.py` |
| `audit_memory` | The whole log, filter and true audit: the task's reference, never shown to the agent | `src/plugin/tools.py` |

The memory itself is built in `src/plugin/memory.py`.

### Tasks

| Task | Does | Runner |
|---|---|---|
| `audit-bloom-memory` | Report every false positive and false negative, and whether the filter is corrupted | `agent`, with `list_candidates`, `bloom_query` and `exact_lookup`; reference `audit_memory` |

The verifier (`verifier/report.py`) recomputes every candidate's bits from the reference's filter and
log with its own SHA-256, and checks that the filter only lost bits a sound write sets. The report is
valid only when both sets and the corrupted flag match exactly. Its score is the share of candidates
classified correctly.

## Layout

```text
.
├── nanoagent.yaml   # manifest: id, runtime, permissions, tools, tasks
├── contract.py      # each tool's and task's typed input and output
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .env             # environment variable NAMEs this plugin needs (none)
├── src/plugin/      # the MCP server, the memory generator and the tools
├── tests/           # tests of the memory, the tools and the verifier
├── ui/              # outputs are drawn from their JSON Schema
├── product/         # the product page: product.yaml and icon.svg
└── verifier/        # deterministic verifier package
```

## Develop and run

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
```

Publishing checks every plugin rule: push the plugin to a public GitHub repository and submit its
URL on RUSH Lab.
