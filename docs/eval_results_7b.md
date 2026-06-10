# Eval results — `qwen2.5-coder:7b`

**2/4 passed.**

| Question | Expect | Pass | Latency (s) | Answer (truncated) |
|---|---|---|---|---|
| Using the local job postings, how many mention Python? Call query_jobs with limit=25 and answer with just the count. | `10` | ✅ | 16.9 | 10 |
| Using only the local job postings (the query_jobs tool), name one company hiring for a Rust role. | `ferroline` | ✅ | 3.9 | Ferroline |
| List remote postings that mention Parquet. Give company names. | `parquet` | ❌ | 4.6 | [] |
| What salary range is listed for the Senior Data Engineer at Parqion? | `160` | ❌ | 8.0 | Salary range could not be determined |
