```sh
curl http://localhost:8000/api/pull -d '{
  "model": "llama3.2:1b"
}'
```

```sh 
curl -X POST http://localhost:8000/v1/example-service \
-H "Content-Type: application/json" \
-d '{
    "model": "llama3.2:1b",
    "messages": [
        {
            "role": "user",
            "content": "Hello, how are you ?"
        }
    ]
}' \
-o response.json
```



```sh
 curl -X POST http://localhost:8000/v1/example-service \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Hello, this is a test message"
      }
    ],
    "model": "llama3.2:1b",
    "max_tokens": 100,
    "temperature": 0.7
  }' | jq '.' > output/$(date +%s)-response.json
  ```