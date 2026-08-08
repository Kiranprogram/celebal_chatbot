# 20 — Auth & Data Model

[← Configuration](15-configuration.md) · [Back to docs hub](README.md) · [Next: Microservices →](21-microservices-nginx.md)

## Auth flow

1. Register with email + password → bcrypt hash stored in Postgres  
2. Login → short-lived **access JWT** + longer **refresh token**  
3. Frontend prefers **httpOnly cookies**  
4. Protected APIs validate Bearer/cookie JWT  
5. `/auth/refresh` rotates tokens  
6. Logout invalidates refresh token server-side  

## PostgreSQL tables

| Table | Key fields | Purpose |
|-------|------------|---------|
| `users` | id, email, password_hash, name, created_at | Accounts |
| `refresh_tokens` | id, user_id, token_hash, expires_at, revoked | Session refresh |
| `sessions` | id, user_id, title, created_at, updated_at | Chat threads (sidebar) |
| `messages` | id, session_id, role, content, sources_json, created_at | Turns + citations |
| `user_memory` | id, user_id, key, value, updated_at, source_session_id | Structured facts |
| `eval_logs` | id, session_id, message_id, relevance, correctness, faithfulness | Scores |

## MongoDB

- Raw transcripts / bulky message payloads during iteration  
- Embedding-backed memory snippets  
- Cross-referenced by `user_id` and `session_id`

## Security basics

- bcrypt hashing  
- Short-lived access tokens  
- Rate limiting (nginx / app middleware)  
- Validate URLs before scrape/tool calls  
- Secrets only from environment  

## Related docs

- [UI guide](13-ui-guide.md)  
- [API reference](12-api-reference.md)  
- [DevOps](22-devops.md)  
