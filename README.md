# AI Warehouse Assistant

A lightweight search assistant for warehouse data:
- Import data from CSV/Excel
- Build embeddings and a FAISS index
- Expose a FastAPI HTTP API for search
- Simple Chat-style Next.js frontend

## How it works (runtime flow)

1) User types a query in the frontend (Next.js).
2) Frontend sends POST /query to the FastAPI backend.
3) Backend pipeline:
   - Processes the query (normalization/expansion).
   - Retrieves top-k relevant items from FAISS using prebuilt embeddings and metadata.
   - Optionally formats or generates a natural-language answer (if you add LLM).
4) Backend returns a concise, structured answer; frontend renders it in a chat-style panel.

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
- Put your warehouse data in a CSV/Excel file with consistent columns (e.g., code, description, size, pressure, price, availability, shelf).
- Keep units consistent (e.g., inches as 1.00", pressure as 400 bar).
- Ensure text encoding is UTF-8 if possible.

3) Build the FAISS index from your file
```bash
source .venv/bin/activate
python -m backend.scripts.build_index \
  --excel /full/path/to/your_data.csv \
  --out-dir backend/storage/embeddings
```

Expected outputs:
- backend/storage/embeddings/index.faiss
- backend/storage/embeddings/metadata.jsonl

4) Configure settings (optional)
- Check backend/app_settings.py for:
  - DEFAULT_TOP_K (must be > 0)
  - STORAGE paths for index/metadata
  - Embedding model name
- Optional LLM: set OPENAI_API_KEY if you later enable LLM answers.

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
- Type a query (e.g., rakor, or a product code).
- The UI calls POST /query and shows the nl_response returned by the API.

## API

- GET /health
  - Returns {"status":"ok","service":"AI Warehouse Assistant"}

- POST /query
  - Request body:
    ```json
    { "query": "rakor", "top_k": 5 }
    ```
    - top_k is optional; when omitted, DEFAULT_TOP_K is used.
  - Response body:
    ```json
    { "nl_response": "..." }
    ```
  - Errors:
    - 400 Bad Request: when top_k <= 0
    - 503 Service Unavailable: when pipeline is not initialized
    - 500 Internal Server Error: unhandled exceptions (see server logs)

Linux example:
```bash
curl -s -H 'Content-Type: application/json' \
  -d '{"query":"Liebherr","top_k":5}' \
  http://127.0.0.1:8000/query | jq
```

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
  - The chat page reads nl_response from the /query response.

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

