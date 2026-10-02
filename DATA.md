# Dataset notes: runs.jsonl

201 lines, one JSON object per line, UTF-8. Runs span 20 July to 31 August 2026.
Timestamps are ISO 8601 with a `Z` suffix.

## Run fields

| field | type | notes |
| --- | --- | --- |
| `id` | string | `run_0001` style |
| `agent` | string | one of five agent names |
| `model` | string | model that served the run |
| `status` | string | `succeeded`, `failed`, `cancelled`, `running` |
| `started_at` | string | ISO 8601 |
| `ended_at` | string or null | null while `running` |
| `duration_ms` | number or null | null while `running` |
| `input_tokens` | number | summed across steps |
| `output_tokens` | number | summed across steps |
| `cost_usd` | number or null | null on a few records |
| `prompt` | string | may contain newlines, emoji, non-ASCII, leading whitespace |
| `error` | object or null | `type`, `message`, `step_index` |
| `tenant_id` | string | 12 tenants |
| `steps` | array | ordered, see below |

## Step fields

| field | type | notes |
| --- | --- | --- |
| `index` | number | 0-based, matches array position |
| `name` | string | may repeat within a run |
| `tool` | string | `llm`, `sql`, `http`, `vector_search`, `none` |
| `status` | string | same vocabulary as run status |
| `started_at` | string | ISO 8601 |
| `duration_ms` | number or null | null while `running` |
| `input` | string | |
| `output` | string or null | null when the step failed or is still running |
| `tokens` | object | `input` and `output`, both 0 for non-LLM steps |

## Known irregularities

These are in the file on purpose. Do not clean them out of the source data; handle them
in your code and record what you did.

- Three runs have `cost_usd: null`.
- One run has a negative `duration_ms` because `ended_at` precedes `started_at`.
- One run has an empty `steps` array.
- One `id` appears twice, on two records that disagree about `status`.
- Nine runs are still `running`, so they have no end time and no duration.
- One prompt is in French; one is padded with leading and trailing whitespace.
