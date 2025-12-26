# Loto Demo API

## Run locally
```bash
python -m uvicorn main:app --reload
```

## Examples
- Balance: `curl "http://localhost:8000/balance?user_id=demo"`
- Play: `curl -X POST -H "Content-Type: application/json" -d '{"user_id":"demo","bet":10}' http://localhost:8000/play`
- History: `curl "http://localhost:8000/history?user_id=demo&limit=20"`

## Admin
- Header: `X-Admin-Token: 12345`
