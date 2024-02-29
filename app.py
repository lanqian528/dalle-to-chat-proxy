from flask import Flask

from src.chat2dalle import chat2dalle
from src.dalle2chat import dalle2chat

app = Flask(__name__)


@app.route("/v1/chat/completions", methods=["POST"])
def handle_dalle2chat():
    return dalle2chat()


@app.route("/v1/images/generations", methods=["POST"])
def handle_chat2dalle():
    return chat2dalle()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
