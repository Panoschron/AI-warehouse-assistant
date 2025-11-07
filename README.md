#AI Warehouse assistant 

This project aims to provide solution to industries who has big or small warehouses and they need to find easier 
their products.

##Targets
PDF/CSV/EXCEL import of variable sources where client store his warehouse data
Vectorizing words and phrases with different technologies like Word2Vec using the sigmoid algebra method.
Chat interface where client can search his warehouse and find the expected result with the highest possible accuracy

## API server

A lightweight FastAPI server is available to query the FAISS index via HTTP.

### Install requirements

```
pip install -r requirements.txt
```

Make sure you've already built the index so that `backend/storage/embeddings/index.faiss` and `metadata.jsonl` exist.

### Run the server

```
uvicorn backend.server:app --reload --host 127.0.0.1 --port 8000
```

### Query the API (PowerShell)


# Health check (GET)
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/health"

# Query (POST) using PowerShell objects (safer quoting)
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/query" `
  -ContentType "application/json" `
  -Body (@{ query = "Liebherr"; top_k = 5 } | ConvertTo-Json)

# Alternatively, using curl.exe (Windows curl wrapper)
curl.exe -s -H "Content-Type: application/json" `
  -d "{\"query\":\"Liebherr\",\"top_k\":5}" `
  http://127.0.0.1:8000/query


### Query the API (Linux)


# Health check (GET)
curl -s http://127.0.0.1:8000/health

# Query (POST)
curl -s -H 'Content-Type: application/json' \
  -d '{"query":"Liebherr","top_k":5}' \
  http://127.0.0.1:8000/query | jq

