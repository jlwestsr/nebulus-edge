import mlx.core as mx

def validate_mlx():
    print("Validating MLX Installation...")
    
    # Create an array
    a = mx.array([1, 2, 3, 4])
    print(f"Created array: {a}")
    
    # Check device
    device = mx.default_device()
    print(f"Default Device: {device}")
    
    if device == mx.gpu:
        print("SUCCESS: MLX is using the GPU (Metal).")
    else:
        print("WARNING: MLX is NOT using the GPU.")
        
    # Simple computation
    b = mx.array([1, 1, 1, 1])
    c = a + b
    print(f"Computation Result (a + b): {c}")

if __name__ == "__main__":
    validate_mlx()
