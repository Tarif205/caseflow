"""Day 0 hello-world check 3: offer qwen3:4b a made-up tool and show what it sends back.

The model never runs the tool. It can only *ask* for it; running it would be our job.
"""

import json
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:4b"

# The tool exists only as a description. There is no real function behind it.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Look up the status of a customer order by its id",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string", "description": "The order id"}},
                "required": ["order_id"],
            },
        },
    }
]

# One question that needs the tool, one that does not.
QUESTIONS = [
    "What is the status of order 1042?",
    "What is the capital of France?",
]


def ask(question: str) -> dict:
    body = {
        "model": MODEL,
        "stream": False,
        "think": False,
        "messages": [{"role": "user", "content": question}],
        "tools": TOOLS,
    }
    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read())


for question in QUESTIONS:
    for attempt in (1, 2):
        message = ask(question)["message"]
        print("=" * 70)
        print(f"Question: {question}   (attempt {attempt})")
        print(f"Text reply: {message.get('content', '').strip()[:300]!r}")
        calls = message.get("tool_calls")
        if calls:
            for call in calls:
                fn = call["function"]
                print(f"TOOL REQUEST: {fn['name']}({json.dumps(fn['arguments'])})")
        else:
            print("TOOL REQUEST: none")
