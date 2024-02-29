import json
import time


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


def generate(response):
    for chunk in response.iter_content(chunk_size=None):
        yield chunk