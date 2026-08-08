# 15 — Configuration

[← Setup guide](14-setup-guide.md) · [Back to docs hub](README.md) · [Next: Evaluation →](16-evaluation.md)

## Required vs optional

| Key | Required? | Notes |
|-----|-----------|-------|
| `OPENROUTER_API_KEY` | **Yes** (for real answers) | https://openrouter.ai/keys |
| `OPENROUTER_BASE_URL` | No (has default) | `https://openrouter.ai/api/v1` |
| `JWT_SECRET` | **Yes** | Change from example value |
| `TAVILY_API_KEY` | Optional | Better web search; else DuckDuckGo |
| `POSTGRES_*` / `DATABASE_URL` | Auto via Compose | Don’t change unless custom DB |
| `MONGODB_URI` | Auto via Compose | |
| `NEO4J_URI` / `NEO4J_PASSWORD` | Auto via Compose | Match password in Compose |
| `VECTOR_BACKEND` | No | `faiss` (default) or `chroma` |
| Service `*_URL` | Auto via Compose | Leave defaults for Docker |
| `INTERNAL_SERVICE_KEY` | Yes for service-to-service | Same value on all services |

## Web search (no weather/stock API URLs)

```env
TAVILY_API_KEY=          # optional
TOOL_HTTP_TIMEOUT_SECONDS=20
```

## Full template

See [../.env.example](../.env.example).

## Related

- [Setup guide](14-setup-guide.md)  
- [Dynamic tools](11-dynamic-tools.md)  
