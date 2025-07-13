### How to run the server

```sh
uvicorn main:app --reload
```

### How to use the api

```sh
curl -X POST http://localhost:8000/api/agent \
    -H "Content-Type: application/json" \
    -d '{
        "message_request": "Find lyrics for YOASOBI Idol"
    }'
```
