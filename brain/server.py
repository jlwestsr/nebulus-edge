import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from mlx_lm import load, generate

app = FastAPI(title="Nebulus Edge Brain", version="0.1.0")

# Model Configuration
MODEL_PATH = "mlx-community/Qwen2.5-Coder-32B-Instruct-4bit"
model_instance = None
tokenizer_instance = None

import time

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "default-model"
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

@app.on_event("startup")
def load_model():
    global model_instance, tokenizer_instance
    print(f"Loading model: {MODEL_PATH}")
    model_instance, tokenizer_instance = load(MODEL_PATH)
    print("Model loaded successfully.")

@app.get("/")
def health_check():
    return {"status": "running", "model": MODEL_PATH}

@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_PATH,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "nebulus-edge",
            }
        ]
    }

@app.post("/v1/chat/completions")
def chat_completions(request: ChatCompletionRequest):
    global model_instance, tokenizer_instance
    if not model_instance or not tokenizer_instance:
         raise HTTPException(status_code=503, detail="Model not initialized")
    
    # Construct prompt from messages
    # Simple formatting: System -> User -> Assistant
    prompt = ""
    for msg in request.messages:
        role = msg.role
        content = msg.content
        if role == "system":
             prompt += f"<|im_start|>system\n{content}<|im_end|>\n"
        elif role == "user":
             prompt += f"<|im_start|>user\n{content}<|im_end|>\n"
        elif role == "assistant":
             prompt += f"<|im_start|>assistant\n{content}<|im_end|>\n"
    
    prompt += "<|im_start|>assistant\n"

    try:
        response_text = generate(
            model_instance, 
            tokenizer_instance, 
            prompt=prompt, 
            max_tokens=request.max_tokens, 
            verbose=True
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "id": "chatcmpl-" + str(int(time.time())),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 0, # Placeholder
            "completion_tokens": 0, # Placeholder
            "total_tokens": 0
        }
    }

def main():
    uvicorn.run(app, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    main()
