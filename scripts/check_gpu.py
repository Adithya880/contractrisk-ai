"""
GPU & CUDA Verification Script for ContractRisk AI
-------------------------------------------------
Checks Python version, PyTorch version, CUDA availability,
PyTorch CUDA version, GPU device name, GPU count, and available VRAM.
"""

import sys

def check_gpu():
    print("=" * 60)
    print(" CONTRACTRISK AI — GPU & CUDA VERIFICATION")
    print("=" * 60)

    try:
        import torch
    except ImportError as e:
        print(f"[ERROR] PyTorch is not installed in the current environment.")
        print(f"Details: {e}")
        sys.exit(1)

    print(f"Python Version:       {sys.version.split()[0]}")
    print(f"PyTorch Version:      {torch.__version__}")
    
    cuda_available = torch.cuda.is_available()
    print(f"CUDA Available:       {cuda_available}")

    if not cuda_available:
        print("\n[ERROR] CUDA is NOT available to PyTorch!")
        sys.exit(1)

    cuda_version = torch.version.cuda
    device_count = torch.cuda.device_count()
    device_name = torch.cuda.get_device_name(0)

    print(f"PyTorch CUDA Version: {cuda_version}")
    print(f"GPU Device Count:     {device_count}")
    print(f"GPU 0 Name:           {device_name}")

    try:
        total_memory_bytes = torch.cuda.get_device_properties(0).total_memory
        total_memory_gb = total_memory_bytes / (1024 ** 3)
        print(f"GPU 0 VRAM:           {total_memory_gb:.2f} GB ({total_memory_bytes} bytes)")
    except Exception as e:
        print(f"GPU VRAM Query Error: {e}")

    print("\n[SUCCESS] GPU & CUDA environment verification completed cleanly.")
    print("=" * 60)

if __name__ == "__main__":
    check_gpu()
