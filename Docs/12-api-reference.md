# 12 — API Reference

[← Dynamic tools](11-dynamic-tools.md) · [Back to docs hub](README.md) · [Next: UI guide →](13-ui-guide.md)

All public HTTP traffic goes through **nginx** under `/api/...`.

## Auth (`/api/auth`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/register` | Create user |
| POST | `/login` | Issue tokens |
| POST | `/refresh` | Rotate tokens |
| POST | `/logout` | Revoke refresh |
| GET | `/me` | Current user |

## Orchestrator (`/api/orchestrator`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness |
| POST | `/chat` | Non-streaming chat |
| POST | `/chat/stream` | SSE streaming chat |
| GET | `/sessions` | List sessions |
| POST | `/sessions` | Create session |

## Knowledge (`/api/knowledge`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ingest/urls` | Scrape + index |
| POST | `/retrieve` | Vector search |
| POST | `/graph/query` | Cypher helper / entity neighbors |
| GET | `/sources` | List ingested sources |

## Memory (`/api/memory`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/{user_id}` | List facts |
| POST | `/{user_id}` | Upsert fact |
| DELETE | `/{user_id}/{key}` | Delete fact |

## Auth header

`Authorization: Bearer <access_token>` (or httpOnly cookie in browser).

## Related docs

- [Auth & data](20-auth-and-data.md)  
- [Microservices](21-microservices-nginx.md)  
