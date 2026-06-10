# smol-jobscout

A **local-first [smolagents](https://github.com/huggingface/smolagents) `CodeAgent`** that answers
natural-language questions over a corpus of crawled job postings — *"which remote roles mention
Parquet?"*, *"summarize the top 3 Python infra roles"*, *"what salary ranges are listed?"* — with an
optional web-search-and-summarize path.

**Runs on a single consumer GPU via Ollama — no cluster, no paid API.** The agent orchestrates over a
deterministic, pure-Python data layer; the LLM only plans and summarizes.

## 60-second quickstart

```bash
git clone <this-repo> && cd smol-jobscout
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip && pip install -e ".[dev,ui]"

# Ollama must be serving on :11434 with the model pulled:
#   ollama pull qwen2.5-coder:14b      (default, see note below)
jobscout "How many postings mention Python?"
```

No `.env` is required — it works out of the box against the bundled `data/sample_jobs.jsonl`.

### Example

```
$ jobscout "List remote postings that mention Parquet. Give the company names."
The remote postings mentioning Parquet are: Parqion (Senior Data Engineer),
Lakeside Analytics (Data Platform Engineer), and Scaleflow (Big Data Engineer).
```

## Model note

The spec's default `qwen2.5-coder:7b-instruct` was not present on the build host, so this repo
defaults to **`qwen2.5-coder:14b`** (more reliable agentic behavior). A smaller
**`qwen2.5-coder:7b`** "fast" profile is available via `--model qwen2.5-coder:7b` — faster, but less
reliable at multi-step tool use. See [`docs/LESSONS_LEARNED.md`](docs/LESSONS_LEARNED.md) for the
honest size/reliability tradeoff with real numbers.

## Usage

```bash
jobscout "Which remote postings mention Parquet or S3? Summarize the top 3."
jobscout --model qwen2.5-coder:7b "List Python data-infra roles with salaries."
make ui                     # Gradio chat at http://localhost:7860
make test                   # Tier-1 unit tests (no model)
make smoke                  # Tier-2 integration (needs Ollama)
make eval                   # writes docs/eval_results.md
```

Point it at your own data by editing `config.yaml` (`data.path` / `data.format`), or convert a
crawler dump with `python scripts/ingest_crawler.py --input dump.json --output data/jobs.jsonl`.

## Security note

`CodeAgent` **executes Python that the LLM writes, in-process, on the host.** With a local model and a
tight `additional_authorized_imports` allowlist the risk is bounded — but **never expose this agent to
untrusted input over a network without sandboxing.** For any shared/remote deployment, switch
`executor_type` to a sandboxed runner (Docker/E2B) and keep the import allowlist minimal. Do not put a
code-executing agent on an open port.

## How it works

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the component diagram and notes. In short:
CLI/UI → `CodeAgent` → {Ollama model via LiteLLM, tools → local job corpus / web}.

## License

MIT — see [LICENSE](LICENSE).
