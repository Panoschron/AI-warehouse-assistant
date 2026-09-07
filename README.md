# AI Warehouse Assistant

A lightweight search assistant for warehouse data:
- Import data from CSV/Excel
- Build embeddings and a FAISS index
- Expose a FastAPI HTTP API for search
- Simple Chat-style Next.js frontend

## Demo slice (10′)

Catalog export (synthetic SoftOne-like CSV) → semantic match (including misspellings) → per-match grounded explain → shelf/location or empty state.

Sample catalog (committed): `backend/storage/samples/softone_warehouse_catalog.csv`

Typed columns for clarifying: `family`, `micron` ∈ {5,10,25}, `diameter` ∈ {1/2", 1", 1.5"} on a real filter grid, plus `sku_key` (bearing `6205-2RS`). ~30–40% of rows have no location; 1–2 filter rows omit diameter (ERP-ugly).

Rebuild the FAISS index from that CSV:

```bash
source .venv/bin/activate
python -m backend.scripts.build_demo_index
```

Equivalent:

```bash
python -m backend.scripts.build_index \
  --excel backend/storage/samples/softone_warehouse_catalog.csv \
  --out-dir backend/storage/embeddings
```

If `index.faiss` / `metadata.jsonl` are missing, the API builds this demo index on startup.

Explain is grounded only in matched catalog fields. With `OPENAI_API_KEY` set, the backend may phrase explains via OpenAI; without a key it uses a deterministic template so the demo works offline. Never commit API keys.

## How it works (runtime flow)

1) User types a query in the frontend (Next.js).
2) Frontend sends POST /query to the FastAPI backend.
3) Backend pipeline:
   - Processes the query (normalization).
   - Retrieves top-k relevant items from FAISS using prebuilt embeddings and metadata.
  - Builds structured `matches` (code, description, location/empty, grounded `explain`).
  - After junk/score gates, applies presentation: `single` | `list` | `clarifying` | `empty`.
  - Optionally adds `nl_response` (LLM if configured, otherwise a template).
4) Backend returns the locked contract (`presentation`, `matches`, `clarifying`, `empty`, optional `nl_response`). The Next.js chat renders per-match `explain` + shelf/empty; chip UI is a frontend follow-up (`constraints` are accepted on the request).

## Prerequisites

- Linux (commands below use bash)
- Python 3.10+
- Node.js 18+ with npm
- Built embeddings/index files:
  - backend/storage/embeddings/index.faiss
  - backend/storage/embeddings/metadata.jsonl

Python dependencies: requirements.txt

## Project structure (short)

```
backend/
  apis/                # FastAPI routes
  clients/             # LLM clients (optional)
  core/                # pipeline, retrieval, generation, formatters
  scripts/             # build-time scripts (indexing)
  server.py            # app entrypoint
frontend/
  app/                 # Next.js app router (page.tsx = chat page)
requirements.txt
```

Key files:
- API route: backend/apis/route_query.py
- Pipeline: backend/core/pipeline.py
- Query processing: backend/core/retrieval/query_processor.py
- Vector search: backend/core/retrieval/vector_search.py
- Result formatting: backend/core/retrieval/result_formatter.py
- Prompt builder (optional LLM): backend/core/generation/prompt_builder.py
- App settings: backend/app_settings.py

## Quickstart (end-to-end)

1) Create and activate a Python virtual environment
```bash
cd /home/panagiotis/Desktop/AI-warehouse-assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Prepare your data
- Demo: use the committed sample at `backend/storage/samples/softone_warehouse_catalog.csv` (code, description, location, …).
- Or put your own warehouse CSV/Excel next to it with consistent columns (code, description, shelf/location).
- Keep units consistent. UTF-8 if possible. Do not delete the sample catalog.

3) Build the FAISS index
```bash
source .venv/bin/activate
python -m backend.scripts.build_demo_index
# or: python -m backend.scripts.build_index --excel /full/path/to/your_data.csv --out-dir backend/storage/embeddings
```

Expected outputs:
- backend/storage/embeddings/index.faiss
- backend/storage/embeddings/metadata.jsonl

4) Configure settings (optional)
- Check backend/app_settings.py for:
  - DEFAULT_TOP_K (must be > 0)
  - MIN_MATCH_SCORE (0.40 after lexical bonus), MIN_SEMANTIC_SCORE (0.75 for ungrounded hits), RELATIVE_SCORE_GAP (0.18), PRESENTATION_GAP (0.12)
  - STORAGE paths for index/metadata
  - Embedding model name
- Optional LLM: export OPENAI_API_KEY in the environment (never commit it). Without a key, template explains still work.

5) Run the API
```bash
source .venv/bin/activate
uvicorn backend.server:app --reload --host 127.0.0.1 --port 8000
```

Verify:
```bash
curl -s http://127.0.0.1:8000/health
# -> {"status":"ok","service":"AI Warehouse Assistant"}
```

6) Run the frontend
```bash
cd frontend
npm i
echo 'NEXT_PUBLIC_API_URL=http://127.0.0.1:8000' > .env.local
npm run dev
# open http://localhost:3000
```

7) Test the chat UI
- Type a query (e.g. `υδραυλικο φιλτρο`, `rakor`, or a product code).
- The UI calls POST /query and lists each match (code, description, explain, shelf or «χωρίς ράφι»). Empty catalog results show a dedicated empty state.

## API

- GET /health
  - Returns {"status":"ok","service":"AI Warehouse Assistant"}

- POST /query
  - Request body:
    ```json
    {
      "query": "υδραυλικο φιλτρο",
      "top_k": 5,
      "constraints": [{"field": "micron", "value": "10"}]
    }
    ```
    - `top_k` is optional; when omitted, DEFAULT_TOP_K is used.
    - `constraints` is optional (stateless chip answers: `{field, value}[]`).
  - Response body:
    ```json
    {
      "presentation": "single | list | clarifying | empty",
      "matches": [
        {
          "code": "string",
          "description": "string",
          "location": "string | null",
          "location_state": "present | empty",
          "explain": "string",
          "score": 0.0
        }
      ],
      "clarifying": {
        "field": "micron",
        "label": "Micron",
        "options": ["5", "10", "25"]
      },
      "empty": false,
      "nl_response": "string"
    }
    ```
    - `presentation` is mandatory
    - `clarifying` is `null` unless `presentation` is `clarifying`; options are real typed distinct values among the (family-restricted) top matches — never invented
    - No matches → `presentation: "empty"`, `matches: []`, `empty: true`, `clarifying: null`
    - Missing shelf → `location: null`, `location_state: "empty"` (never invented)
    - `explain` is required on every match and is grounded in catalog fields only
    - `nl_response` is optional (short summary bubble in the chat UI)
  - Presentation policy (after existing junk / score gates):
    - exact catalog code (`code` / `sku_key` / `size`, e.g. `6205-2RS`) **or** (leader_ok and gap ≥ 0.12) → `single`, `matches` = [#1] only
    - else if fewer than 2 typed `constraints` and usable column-diff (`micron` / `diameter` only) and gap < 0.12 → `clarifying`
    - else if matches → `list` (2–5)
    - else → `empty`
    - Up to 2 clarifying turns (stateless resubmit). After 2 typed chips — or when no usable diff remains — settle on `single` or `list`. Unknown `constraints.field` values are dropped (whitelist = `micron` / `diameter`)
    - Soft family filter: before column-diff, if a majority of top-M share `family`, restrict the diff to that family. Chips are only typed `micron` / `diameter` of that family — never bearing `size` / `sku_key`
  - Errors:
    - 400 Bad Request: empty query or top_k <= 0
    - 503 Service Unavailable: when pipeline is not initialized
    - 500 Internal Server Error: unhandled exceptions (see server logs)

Linux example:
```bash
curl -s -H 'Content-Type: application/json' \
  -d '{"query":"Liebherr","top_k":5}' \
  http://127.0.0.1:8000/query | jq
```

### Merge-gate smoke (copy-paste)

Rebuild the index after catalog edits, then start the API:

```bash
python -m backend.scripts.build_demo_index
uvicorn backend.server:app --reload --host 127.0.0.1 --port 8000
```

```bash
# 1) exact code → single, one match, explain + location
curl -s -H 'Content-Type: application/json' \
  -d '{"query":"6205-2RS"}' \
  http://127.0.0.1:8000/query | jq '{presentation,empty,clarifying,n:(.matches|length),match:(.matches[0]|{code,description,explain,location,location_state})}'

# 2) filter query → clarifying; chips ONLY micron/diameter of family=filter (must NOT be list)
curl -s -H 'Content-Type: application/json' \
  -d '{"query":"υδραυλικο φιλτρο"}' \
  http://127.0.0.1:8000/query | jq '{presentation,empty,clarifying,codes:[.matches[].code]}'

# 3a) first chip (micron) → still clarifying (remaining typed field, usually diameter)
curl -s -H 'Content-Type: application/json' \
  -d '{"query":"υδραυλικο φιλτρο","constraints":[{"field":"micron","value":"10"}]}' \
  http://127.0.0.1:8000/query | jq '{presentation,empty,clarifying,codes:[.matches[].code]}'

# 3b) both chips → single or list (2-turn cap)
curl -s -H 'Content-Type: application/json' \
  -d '{"query":"υδραυλικο φιλτρο","constraints":[{"field":"micron","value":"10"},{"field":"diameter","value":"1\""}]}' \
  http://127.0.0.1:8000/query | jq '{presentation,empty,clarifying,codes:[.matches[].code]}'

# 4) junk → empty
curl -s -H 'Content-Type: application/json' \
  -d '{"query":"zzzznotaproduct999"}' \
  http://127.0.0.1:8000/query | jq '{presentation,empty,matches,clarifying}'

# 5) no cross-family chip pollution (options ⊆ {5,10,25} or {1/2",1",1.5"} — never 6205-2RS)
curl -s -H 'Content-Type: application/json' \
  -d '{"query":"υδραυλικο φιλτρο"}' \
  http://127.0.0.1:8000/query | jq '{presentation,field:.clarifying.field,options:.clarifying.options}'
```

Offline unit proof (no FAISS): `python -m unittest backend.tests.test_presentation backend.tests.test_demo_slice`

## Detailed procedure and tips

- Data preparation
  - Normalize text (accents/case), unify units, and keep codes exact.
  - If you have Greek and Greeklish terms, consider adding synonyms in query processing.

- Index building
  - Re-run the build script each time your source data changes.
  - Output directory should match paths in backend/app_settings.py.
  - Large datasets: consider batching and a stronger embedding model (trade-off with build time/size).

- Running backend
  - Make sure the FAISS files exist at the configured paths.
  - If you change DEFAULT_TOP_K or paths, restart the server.

- Running frontend
  - Ensure NEXT_PUBLIC_API_URL points to your FastAPI host:port.
  - The chat page renders `matches` / `empty` / `explain` / location. `nl_response` is an optional summary.

- Error handling and logs
  - 400 responses include detail explaining the validation issue (e.g., top_k must be a positive integer).
  - 500 responses include a generic message; see terminal for stack traces.
  - Logging is configured in backend to print warnings/errors for easier troubleshooting.

## Updating data (daily/weekly workflow)

1) Export the latest CSV/Excel from your warehouse system.
2) Re-run the index build script to regenerate index.faiss and metadata.jsonl.
3) Restart the FastAPI server if paths or models changed (not always necessary if only files are replaced in-place).
4) Smoke test:
```bash
curl -s http://127.0.0.1:8000/health
curl -s -H 'Content-Type: application/json' \
  -d '{"query":"rakor","top_k":5}' \
  http://127.0.0.1:8000/query | jq
```

## Improving accuracy (optional roadmap)

- Query processing: add synonyms/aliases (Greek/Greeklish), normalize sizes ("1.00\"", "1 inch").
- Hybrid retrieval: combine FAISS with keyword/BM25 for exact codes/terms.
- Re-ranking: re-score FAISS candidates with simple rules (match by code/size/pressure) or a cross-encoder.
- Prompting (if using LLM): structured answer format, few-shot examples, and clear grounding to metadata.
- Evaluation: build a small test set and measure recall@k/MRR to tune top_k and filters.

## Troubleshooting

- 400 on /query
  - top_k must be > 0; or set a valid DEFAULT_TOP_K in backend/app_settings.py.
- 503 on /query
  - Pipeline not initialized; verify index paths and server startup logs.
- 500 on /query
  - Check the server terminal for stack traces.
- No results or empty answers
  - Rebuild the index from the latest data; verify metadata.jsonl contains expected fields.

## License / Thanks

- Built with FastAPI, FAISS, sentence-transformers, and Next.js.
- Warehouse data remains your own property and is not included in this repository.

