# LM Studio Local LLM Setup Guide for ContractRisk AI

This document provides setup and verification details for running the local generative Large Language Model (**Qwen3 4B Instruct 2507**) via **LM Studio**.

---

## Hardware & Privacy Specifications

- **Development Hardware**: ASUS TUF Gaming F15 (NVIDIA GeForce RTX 3050 Laptop GPU, 4 GB VRAM, 16 GB RAM)
- **Local API Endpoint**: `http://127.0.0.1:1234/v1`
- **Target Model**: `Qwen3 4B Instruct 2507`
- **Format**: GGUF
- **Quantization**: `Q4_K_M` (Recommended 4-bit quantization for 4 GB VRAM budget)
- **Model ID**: `qwen3-4b-instruct-2507`
- **Privacy Guarantee**: All processing runs on local GPU/RAM. No contract data or API keys are sent over external networks.

---

## LM Studio Configuration

### 1. Model Loading
1. Open **LM Studio**.
2. Search and download `Qwen3 4B Instruct 2507 GGUF` (`Q4_K_M`).
3. Load the model via the top dropdown menu.
4. Set **GPU Offload** to **Max / Full** to utilize NVIDIA RTX 3050 CUDA acceleration.

### 2. Starting & Stopping the Server
- **To Start**:
  1. Click the **Developer / Local Server** tab (`<->` icon).
  2. Ensure Server Port is set to `1234`.
  3. Click **Start Server**.
  4. Verify endpoint is listening on `http://127.0.0.1:1234/v1`.
- **To Stop**:
  1. Open the Developer tab and click **Stop Server**.

---

## Running Verification

Verify the local server status and execution from the project virtual environment:

```powershell
.\.venv\Scripts\python.exe scripts/test_lm_studio.py
```

### Expected Output

```
=================================================================
 CONTRACTRISK AI — LOCAL LM STUDIO VERIFICATION
=================================================================
Target Base URL: http://127.0.0.1:1234/v1
Target Model:    qwen3-4b-instruct-2507

1. Querying available models at: http://127.0.0.1:1234/v1/models
   HTTP Status: 200
   Available Models: ['qwen3-4b-instruct-2507']

2. Sending test prompt to chat endpoint: http://127.0.0.1:1234/v1/chat/completions
   HTTP Status: 200

Returned Model Response:
--------------------------------------------------
Local LLM server is active and responding correctly.
--------------------------------------------------

[SUCCESS] LM Studio local API is fully operational!
=================================================================
```
