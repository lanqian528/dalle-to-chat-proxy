import json
import random
import re
import string
import time

import requests
from flask import request, Response

from src.Logger import logger
from src.config import openai_base_url


def chat2dalle():
    data = request.json
    headers = request.headers
    prompt = data.get("prompt")
    model = data.get("model", "dall-e-3")
    size = data.get("size", "1024x1024")
    quality = data.get("quality", "standard")
    authorization = headers.get("Authorization")

    if not prompt:
        return Response(json.dumps({"error": "No prompt found in the request"}), status=400, content_type="application/json")

    headers = {
        "Authorization": f"{authorization}",
        "Content-Type": "application/json"
    }
    pre_prompt = f"Please use the information provided to call the delle function for drawing, without asking any detailed questions. After I give you the prompt, provide the image directly in the next message.\n\n"
    size_prompt = f"Size: {size}\n"
    quality_prompt = f"Quality: {quality}\n"
    prompt = f"Prompt: {prompt}\n"
    payload = {
        "messages": [
            {
                "content": pre_prompt + size_prompt + quality_prompt + prompt,
                "role": "user"
            }
        ],
        "model": "gpt-4-all",
        "stream": False
    }

    try:
        response = requests.post(f"{openai_base_url}/chat/completions",
                                 headers=headers,
                                 json=payload)

        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            prompt_match = re.search(r"```.*\n\s*(\{[\s\S]*?\})\s*\n```", content, re.DOTALL)
            if prompt_match:
                revised_prompt = json.loads(prompt_match.group(1))["prompt"]
            else:
                revised_prompt = prompt

            url_match = re.search(r'!\[image.*\]\((.*?)\)', content)
            if url_match:
                url = url_match.group(1)
            else:
                current_time = time.time()
                struct_time = time.localtime(current_time)
                time_str = time.strftime('%Y%m%d%H%M%S', struct_time)
                milliseconds = "{:06d}".format(int((current_time - int(current_time)) * 1000000))
                full_time_str = time_str + milliseconds
                random_str_length = 8
                random_str = ''.join(random.choices(string.ascii_letters, k=random_str_length))
                request_id = full_time_str + random_str
                error_response = {
                    "error": {
                        "message": f"Your request was rejected as a result of our safety system. Your prompt may contain text that is not allowed by our safety system. (request id: {request_id})",
                        "type": "invalid_request_error",
                        "param": "",
                        "code": "content_policy_violation"
                    }
                }
                logger.info(payload)
                logger.info(error_response)
                return Response(json.dumps(error_response), status=200, content_type="application/json")

            image_response = {
                "created": int(time.time()),
                "data": [
                    {
                        "revised_prompt": revised_prompt,
                        "url": url
                    }
                ]
            }
            logger.info(payload)
            logger.info(image_response)
            return Response(json.dumps(image_response), status=200, content_type="application/json")
        else:
            logger.info(payload)
            logger.info(response.json())
            return Response(json.dumps(response.json()), status=response.status_code, content_type="application/json")
    except requests.exceptions.RequestException as e:
        logger.error(str(e))
        return Response(json.dumps(str(e)), status=500, content_type="application/json")
