import json
import logging

import requests
from flask import Flask, request, stream_with_context, Response

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
OPENAI_BASE_URL = ""


@app.route("reverse/v1/chat/completions", methods=["POST"])
def generate_chat():
    payload = request.get_json()
    stream = payload["stream"]
    headers = request.headers
    authorization = headers.get("Authorization")
    payload["max_tokens"] = -100000000
    headers = {
        "Authorization": f"{authorization}",
        "Content-Type": "application/json"
    }
    try:
        logger.info(payload)
        if stream:
            response = requests.post(f"{OPENAI_BASE_URL}/chat/completions",
                                     headers=headers,
                                     json=payload,
                                     stream=True)
            if response.status_code == 200:
                def generate():
                    for chunk in response.iter_content(chunk_size=None):
                        yield chunk

                return Response(stream_with_context(generate()), content_type='text/event-stream')
            else:
                return Response(json.dumps(response.json()), status=response.status_code,
                                content_type="application/json")
        else:
            response = requests.post(f"{OPENAI_BASE_URL}/chat/completions",
                                     headers=headers,
                                     json=payload,
                                     stream=True)
            return Response(json.dumps(response.json()), status=response.status_code, content_type='application/json')

    except requests.exceptions.RequestException as e:
        logger.error(str(e))
        return Response(json.dumps(str(e)), status=500, content_type="application/json")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
