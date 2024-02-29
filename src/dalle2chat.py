import json
import random
import string
import time

import requests
from flask import request, Response, stream_with_context

from src.Logger import Logger
from src.stream import generate_by_bytes

OPENAI_BASE_URL = "https://api.lqqq.ltd/v1"


def dalle2chat():
    data = request.json
    headers = request.headers
    messages = data.get("messages")
    model = data.get("model", "dall-e-3")
    stream = data.get("stream", False)
    authorization = headers.get("Authorization")
    size = data.get("size", "1024x1024")
    quality = data.get("quality", "standard")

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

    if "请直接返回“闲聊”" in prompt:
        payload = request.get_json()
        payload["model"] = "gpt-3.5-turbo"
        response = requests.post(f"{OPENAI_BASE_URL}/chat/completions",
                                 headers=headers,
                                 json=payload)
        Logger.info(payload)
        Logger.info(response.json())
        return Response(json.dumps(response.json()), status=response.status_code, content_type="application/json")

    try:
        response = requests.post(f"{OPENAI_BASE_URL}/images/generations",
                                 headers=headers,
                                 json=payload,
                                 stream=True)
        if response.status_code == 200:
            try:
                image_prompt = response.json()["data"][0]["revised_prompt"]
            except:
                image_prompt = prompt
            try:
                image_url = response.json()["data"][0]["url"]
            except:
                image_url = None
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
                    "prompt_tokens": int(size.split('x')[0]),
                    "completion_tokens": int(size.split('x')[0]),
                    "total_tokens": 2 * int(size.split('x')[0])
                }
            }
            Logger.info(payload)
            Logger.info(chat_response)
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
                return Response(json.dumps(chat_response), status=response.status_code,
                                content_type='application/json')
        else:
            Logger.info(payload)
            Logger.info(response.json())
            return Response(json.dumps(response.json()), status=response.status_code, content_type="application/json")

    except requests.exceptions.RequestException as e:
        Logger.error(str(e))
        return Response(json.dumps(str(e)), status=500, content_type="application/json")
