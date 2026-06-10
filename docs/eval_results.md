# Eval results — `qwen2.5-coder:14b`

**2/4 passed.**

| Question | Expect | Pass | Latency (s) | Answer (truncated) |
|---|---|---|---|---|
| Using the local job postings, how many mention Python? Call query_jobs with limit=25 and answer with just the count. | `10` | ✅ | 8.0 | 10 |
| Using only the local job postings (the query_jobs tool), name one company hiring for a Rust role. | `ferroline` | ✅ | 10.3 | Ferroline |
| List remote postings that mention Parquet. Give company names. | `parquet` | ❌ | 10.8 | [] |
| What salary range is listed for the Senior Data Engineer at Parqion? | `160` | ❌ | 26.4 | The average salary range for a Senior Data Engineer is between $127,495 and $286 |
