#  dalle-to-chat-proxy

一个将 *OpenAI* 的 *DALL-E* 接口转化为对话 *CHAT* 接口的 *Python* 微代理

---

### 功能

- 支持`OpenAI-API`: `v1/chat/completions`
- 支持`OpenAI-API`格式的流式输出
- 兼容`chatgpt-next-web`生成标题

### 使用

```python
import requests
import json

url = "http://127.0.0.1:5000/v1/chat/completions"
apikey = "YOUR OPENAI APIKEY"

payload = json.dumps({
  "model": "dall-e-3",
  "messages": [
    {
      "role": "user",
      "content": "画一只猫”"
    }
  ],
  "stream": False
})
headers = {
  'Content-Type': 'application/json',
  'Authorization': f'Bearer {apikey}'
}

response = requests.post(url, headers=headers, data=payload)
print(response.json())
```
