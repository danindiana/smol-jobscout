# Lessons learned — the tricky parts

Honest, measured notes from building and running smol-jobscout on worlock (RTX 5080 + RTX 3080,
Ollama). Numbers come from `scripts/eval.py`; see `docs/eval_results.md` for the raw table.

> This section is updated from **actual observed behavior** during the build, not assumptions.
> Sections marked _(pending live run)_ are filled in after `make smoke` / `make eval`.

## 1. The `num_ctx` trap (the #1 silent failure)

Ollama's default context window is **2048 tokens**. A `CodeAgent` prompt — system prompt + tool
schemas + code-action scaffolding — already approaches or exceeds that before the corpus briefs are
added. With `num_ctx=2048` the model silently truncates the system/tool context and either never
emits a tool call or emits malformed code. The fix is to set `num_ctx >= 8192` explicitly on the
`LiteLLMModel` (we default to 8192). `config.py` warns when it sees `< 4096`.

## 2. `ollama_chat/` not `ollama/`

LiteLLM exposes Ollama under two prefixes. `ollama_chat/<model>` uses the chat/messages API and
handles system/user/assistant roles correctly; `ollama/<model>` uses the older generate API and
mangles role separation, which degrades tool-calling. Always use `ollama_chat/`.

## 3. Tool docstrings + output shape drive behavior

Vague docstrings → the model skips the tool or passes garbage args. But the sharper lesson came from
the **tool's return shape**: the first live run of *"How many postings mention Python?"* returned
**2372** — the model had called `query_jobs` correctly, then ran `len(result)` on the **joined
string** and reported its character count. The deterministic layer was right; the model couldn't
recover a count from prose.

Fix: `query_jobs` now leads its output with an explicit `Found N matching posting(s) (count=N):`
header, and the docstring tells the model to read `count=` directly. After this change the count
question passes reliably on both `7b` and `14b`. Lesson: **make the tool emit the number you want the
model to report — don't make it derive it.** The `[id]` convention likewise lets the model chain into
`get_job`.

## 4. Small models vs. reliability — `7b` vs `14b`

Eval run 2026-06-10 against the bundled `sample_jobs.jsonl` (4 fixed Q/A, see `docs/eval_results.md`
and `docs/eval_results_7b.md`):

| Model | Eval pass rate | Latency range | Notes |
|---|---|---|---|
| `qwen2.5-coder:14b` | 2/4 | 8–26 s | default; warm |
| `qwen2.5-coder:7b`  | 2/4 | 4–17 s | "fast" profile; ~2× faster per step |

Both sizes **reliably** handle the simple cases: counting Python postings (→ `10`, correct ground
truth) and naming a Rust-hiring company from the local corpus (→ `Ferroline`). Both **fail the same
two harder prompts**, which is the honest finding:

- *"List remote postings that mention Parquet"* → the model emitted an empty list `[]`, mis-coding the
  filter chain rather than reusing the tool's results.
- *"What salary range … at Parqion?"* → the model **drifted to `WebSearchTool`** and returned a
  generic web "average salary" instead of reading the local posting (which plainly lists
  `$160k-$190k`). Disabling web tools, or instructing "use only the local job postings", steers it
  back — but the default agent will reach for the web when a question smells like a lookup.

Smaller models (≤3B) were not used as the default: in smolagents they frequently emit malformed code
blocks or skip tools entirely. The spec's recommended `7b-instruct` tag was absent on this host, so
`14b` is the default for reliability; `7b` is the documented fast profile.

## 4a. Vague prompts make agents loop to `max_steps`

The first integration prompt — *"How many postings mention Python? Use the tools."* — made `14b` loop
to `Reached max steps` (8–9 steps) without ever calling `final_answer`. The identical question phrased
explicitly (*"call query_jobs once with limit=25 and answer with just the number"*) finalized in **2
steps / ~8 s**. For a CodeAgent on a local model, prompt specificity is the difference between a clean
run and burning the whole step budget.

## 4b. `final_answer` preserves type — don't assume `str`

When the agent answered the count question, `agent.run(...)` returned the Python **int** `10`, not a
string (`final_answer(10)` keeps the type). An `isinstance(answer, str)` assertion in the smoke test
failed on a *correct* run. Callers must `str(answer)` defensively; the CLI's `print(answer)` already
handles this.

## 5. Import drift across smolagents versions

smolagents moves fast and import names shift between releases. Verified surface on this host:
- Installed `smolagents` version: **1.26.0** (Python 3.12.9 venv; the system `python3` is 3.10, which
  fails the `requires-python >= 3.11` pin — build the venv with `python3.12`).
- `LiteLLMModel`, `InferenceClientModel`, `TransformersModel`, `GradioUI`, `tool`, `CodeAgent`,
  `WebSearchTool`, `VisitWebpageTool`, `DuckDuckGoSearchTool` — **all present** in 1.26.0.
- `tools.py` / `agent.py` remain import-guarded (`WebSearchTool` → `DuckDuckGoSearchTool` fallback) so
  the code survives older/newer releases where a name is absent.

## 5a. Substring matching is a false-friend

The Rust query first returned both `Ferroline` *and* `Metricly` — because a naive `"rust" in text`
substring match hits "t**rust**worthy". `search_jobs` now uses word-boundary regex for alphanumeric
terms (falling back to substring for punctuated terms like `c++`). Cheap deterministic-layer bug, but
it would have quietly polluted every keyword answer.

## 6. Keep briefs short

Feeding full descriptions for many postings blows the context budget fast. `to_brief()` truncates the
description and surfaces only title/company/location/salary/top-tags; the agent pulls full text via
`get_job` only when it actually needs it.
