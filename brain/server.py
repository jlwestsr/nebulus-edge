import time
from pathlib import Path
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from mlx_lm import generate, load
from pydantic import BaseModel

from nebulus_core.intelligence.core.audit import AuditEvent, AuditEventType, AuditLogger
from shared.config.audit_config import AuditConfig
from shared.middleware.audit_middleware import AuditMiddleware

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
audit_logger = None
audit_config = None


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


def _warmup_model():
    """Run a minimal generation to warm up the model and eliminate cold start latency."""
    if not model_instance or not tokenizer_instance:
        print("Warning: Cannot warm up - model not loaded")
        return

    print("Warming up model...")
    warmup_messages = [{"role": "user", "content": "Hi"}]

    if hasattr(tokenizer_instance, "apply_chat_template"):
        warmup_prompt = tokenizer_instance.apply_chat_template(
            warmup_messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    else:
        warmup_prompt = "Hi"

    # Generate a single token to trigger all lazy initialization
    generate(
        model_instance,
        tokenizer_instance,
        prompt=warmup_prompt,
        max_tokens=1,
        verbose=False,
    )
    print("Model warmed up and ready.")


def _audit_log_completion(
    http_request: Request,
    model: str,
    message_count: int,
    prompt_length: int,
    response_length: int,
    max_tokens: int,
    temperature: float,
    duration_ms: float,
    success: bool,
    error: Optional[str] = None,
):
    """Log LLM completion to audit log."""
    if not audit_logger:
        return

    # Extract context from middleware
    user_id = getattr(http_request.state, "user_id", "unknown")
    session_id = getattr(http_request.state, "session_id", None)
    ip_address = getattr(http_request.state, "ip_address", None)
    request_hash = getattr(http_request.state, "request_hash", None)
    response_hash = getattr(http_request.state, "response_hash", None)

    # Build details
    details = {
        "model": model,
        "message_count": message_count,
        "prompt_length": prompt_length,
        "response_length": response_length,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "duration_ms": duration_ms,
    }
    if request_hash:
        details["request_hash"] = request_hash
    if response_hash:
        details["response_hash"] = response_hash

    # Create and log audit event
    from datetime import datetime

    event = AuditEvent(
        event_type=AuditEventType.QUERY_NATURAL,
        timestamp=datetime.now(),
        user_id=user_id,
        session_id=session_id,
        ip_address=ip_address,
        resource="chat_completion",
        action="generate",
        details=details,
        success=success,
        error_message=error,
    )
    audit_logger.log(event)


@app.on_event("startup")
def startup_event():
    global audit_logger, audit_config

    # Initialize audit logging
    audit_config = AuditConfig.from_env()
    audit_path = Path(__file__).parent / "audit"
    audit_path.mkdir(parents=True, exist_ok=True)
    audit_db_path = audit_path / "audit.db"
    audit_logger = AuditLogger(db_path=audit_db_path)

    print(f"Audit logging: {'enabled' if audit_config.enabled else 'disabled'}")
    print(f"Audit retention: {audit_config.retention_days} days")

    # Add audit middleware
    app.add_middleware(
        AuditMiddleware,
        enabled=audit_config.enabled,
        debug=audit_config.debug,
        default_user="appliance-admin",
    )

    load_model_by_name("default-model")
    _warmup_model()


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
def chat_completions(http_request: Request, request: ChatCompletionRequest):
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

    start_time = time.time()
    try:
        response_text = generate(
            model_instance,
            tokenizer_instance,
            prompt=prompt,
            max_tokens=request.max_tokens,
            verbose=True,
        )

        # Log successful completion
        if audit_logger and audit_config and audit_config.enabled:
            duration_ms = (time.time() - start_time) * 1000
            _audit_log_completion(
                http_request,
                model=request.model,
                message_count=len(request.messages),
                prompt_length=len(prompt),
                response_length=len(response_text),
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                duration_ms=duration_ms,
                success=True,
            )

    except Exception as e:
        import traceback

        traceback.print_exc()

        # Log failed completion
        if audit_logger and audit_config and audit_config.enabled:
            duration_ms = (time.time() - start_time) * 1000
            _audit_log_completion(
                http_request,
                model=request.model,
                message_count=len(request.messages),
                prompt_length=len(prompt),
                response_length=0,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                duration_ms=duration_ms,
                success=False,
                error=str(e),
            )

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
