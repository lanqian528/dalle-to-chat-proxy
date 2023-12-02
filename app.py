import json
import logging
import random
import string
import time

import requests
from flask import Flask, request, stream_with_context, Response

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
OPENAI_BASE_URL = "https://api.lqqq.ltd/v1"


def find_safe_end(data_bytes, start_index, max_chunk_size):
    end_index = start_index + max_chunk_size
    if end_index >= len(data_bytes):
        return len(data_bytes)
    while end_index > start_index and (data_bytes[end_index] & 0xC0) == 0x80:
        end_index -= 1
    return end_index


def generate_by_bytes(data, chat_id, bytes_per_chunk=10):
    start_index = 0
    data_bytes = data.encode('utf-8')
    while start_index < len(data_bytes):
        end_index = find_safe_end(data_bytes, start_index, bytes_per_chunk)
        chunk_bytes = data_bytes[start_index:end_index]
        decoded_chunk = chunk_bytes.decode('utf-8')
        chunk_data = {
            "id": chat_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "model",
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "content": decoded_chunk
                    },
                    "finish_reason": None
                }
            ]
        }
        yield f"data: {json.dumps(chunk_data)}\n\n"
        start_index = end_index
    yield f"data: [DONE]\n\n"


@app.route("/v1/chat/completions", methods=["POST"])
def generate_image_chat():
    data = request.json
    headers = request.headers
    messages = data.get("messages")
    model = data.get("model")
    stream = data.get("stream")
    authorization = headers.get("Authorization")
    size = data.get("size")
    quality = data.get("quality")

    if not size:
        size = "1024x1024"
    if not quality:
        quality = "standard"
    try:
        prompt = next((msg["content"] for msg in reversed(messages) if msg["role"] == "user"), None)
    except:
        prompt = None

    headers = {
        "Authorization": f"{authorization}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "n": 1
    }

    if prompt == "使用四到五个字直接返回这句话的简要主题，不要解释、不要标点、不要语气词、不要多余文本，如果没有主题，请直接返回“闲聊”":
        payload = request.get_json()
        payload["model"] = "gpt-3.5-turbo"
        logger.info(payload)
        response = requests.post(f"{OPENAI_BASE_URL}/chat/completions",
                                 headers=headers,
                                 json=payload)
        return Response(json.dumps(response.json()), status=response.status_code, content_type="application/json")

    try:
        logger.info(payload)
        response = requests.post(f"{OPENAI_BASE_URL}/images/generations",
                                 headers=headers,
                                 json=payload,
                                 stream=True)

        if response.status_code == 200:
            try:
                image_prompt = response.json()["data"][0]["revised_prompt"]
            except:
                image_prompt = prompt
            image_url = response.json()["data"][0]["url"]
            chat_id = f"chatcmpl-{''.join(random.choice(string.ascii_letters + string.digits) for _ in range(29))}"
            dalle_prompt = json.dumps({
                "size": size,
                "prompt": image_prompt
            })
            chat_response = {
                "id": chat_id,
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": f"```json dalle-prompt\n"
                                       f"{dalle_prompt}\n"
                                       f"```\n"
                                       f"![image]({image_url})\n"
                                       f"[download]({image_url})"
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 1024,
                    "completion_tokens": 1024,
                    "total_tokens": 2048
                }
            }
            if stream:
                headers = {
                    'Cache-Control': 'no-cache',
                    'Content-Type': 'text/event-stream',
                    'Connection': 'keep-alive',
                }
                return Response(
                    stream_with_context(generate_by_bytes(chat_response["choices"][0]["message"]["content"], chat_id)),
                    headers=headers)
            else:
                return Response(json.dumps(response.json()), status=response.status_code, content_type='application/json')
        else:
            return Response(json.dumps(response.json()), status=response.status_code, content_type="application/json")

    except requests.exceptions.RequestException as e:
        logger.error(str(e))
        return Response(json.dumps(str(e)), status=500, content_type="application/json")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
