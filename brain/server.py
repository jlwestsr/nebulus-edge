import time

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from mlx_lm import load, generate

app = FastAPI(title="Nebulus Edge Brain", version="0.1.0")

# Model Configuration
MODELS = {
    "default-model": "mlx-community/Qwen3-Coder-30B-A3B-Instruct-4bit",
    "qwen3-coder-30b": "mlx-community/Qwen3-Coder-30B-A3B-Instruct-4bit",
    "qwen2.5-coder-32b": "mlx-community/Qwen2.5-Coder-32B-Instruct-4bit",
    "llama3.1-8b": "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit",
}

# Global State
current_model_name = None
model_instance = None
tokenizer_instance = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "default-model"
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False


def load_model_by_name(model_key: str):
    global model_instance, tokenizer_instance, current_model_name

    if model_key not in MODELS:
        # Fallback to default if known model not found, or raise error?
        # Let's fallback to default for "default-model" alias, but raise for unknown
        if model_key == "default-model":
            target_path = MODELS["default-model"]
        else:
            # Try to find loose match or default
            print(f"Model {model_key} not found in config, using default.")
            target_path = MODELS["default-model"]
            model_key = "default-model"  # specific alias
    else:
        target_path = MODELS[model_key]

    if current_model_name == model_key and model_instance is not None:
        return  # Already loaded

    print(f"Loading model: {target_path} (Key: {model_key})")
    # TODO: Explicitly unload previous model if MLX doesn't handle it automatically
    # (Python GC should handle it if we drop references, but MLX has unified memory cache)
    # We will just overwrite the variables.
    model_instance, tokenizer_instance = load(target_path)
    current_model_name = model_key
    print(f"Model {model_key} loaded successfully.")


@app.on_event("startup")
def startup_event():
    load_model_by_name("default-model")


@app.get("/")
def health_check():
    return {
        "status": "running",
        "current_model": current_model_name,
        "available_models": list(MODELS.keys()),
    }


@app.get("/v1/models")
def list_models():
    data = []
    for key, path in MODELS.items():
        data.append(
            {
                "id": key,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "nebulus-edge",
                "permission": [],
                "root": key,
                "parent": None,
            }
        )
    return {"object": "list", "data": data}


@app.post("/v1/chat/completions")
def chat_completions(request: ChatCompletionRequest):
    global model_instance, tokenizer_instance

    # Check if we need to switch models
    requested_model = request.model.lower()
    if requested_model not in MODELS:
        requested_model = "default-model"

    if requested_model != current_model_name:
        try:
            load_model_by_name(requested_model)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load model {requested_model}: {str(e)}",
            )

    if not model_instance or not tokenizer_instance:
        raise HTTPException(status_code=503, detail="Model not initialized")

    # Construct prompt from messages using the tokenizer's chat template
    if hasattr(tokenizer_instance, "apply_chat_template"):
        prompt = tokenizer_instance.apply_chat_template(
            [msg.dict() for msg in request.messages],
            tokenize=False,
            add_generation_prompt=True,
        )
    else:
        # Fallback to simple ChatML if apply_chat_template is not available (unlikely)
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
            verbose=True,
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
                "message": {"role": "assistant", "content": response_text},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,  # Placeholder
            "completion_tokens": 0,  # Placeholder
            "total_tokens": 0,
        },
    }


def main():
    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
