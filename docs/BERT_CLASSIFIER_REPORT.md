# Phase 3 BERT Clause-Type Classifier Technical Report

> **System**: ContractRisk AI  
> **Model Backbone**: `bert-base-uncased` (110M Parameters)  
> **Phase**: Phase 3 — Supervised Fine-Tuning & Evaluation  

---

## 1. Model & Architecture Overview

The Phase 3 classifier is built upon `bert-base-uncased` fine-tuned for 41 multi-class legal clause assignment. The model architecture uses a dense linear sequence classification head over the 768-dimensional `[CLS]` token output vector.

## 2. Hyperparameter & Training Configuration

| Parameter | Setting | Technical Rationale |
| :--- | :--- | :--- |
| **Model Backbone** | `bert-base-uncased` | Standard 12-layer, 768-hidden pretrained encoder |
| **Max Sequence Length** | `256` tokens | Captures 95%+ of clause text lengths without VRAM overflow |
| **Micro-Batch Size** | `8` per GPU | Preserves VRAM usage within RTX 3050 4 GB budget |
| **Gradient Accumulation** | `4` steps | Achieves effective batch size of **32** |
| **Learning Rate** | `2e-05` | Standard fine-tuning rate with linear decay |
| **Epochs** | `3` | Prevents overfitting on 6.6k training samples |
| **Warmup Ratio** | `0.1` | Ramps up LR linearly over first 10% steps |
| **Weight Decay** | `0.01` | L2 regularization penalizing weight magnitude |
| **Precision** | `FP16` (Mixed Precision) | Accelerated Tensor Core computation & reduced VRAM |
| **Loss Function** | `CrossEntropyLoss` | Weighted using inverse class frequency from training set |

## 3. Class Imbalance Strategy

Severe class imbalance exists across the 41 clause types (ranging from 655 samples for `License Grant` down to 13 samples for `Unlimited/All-You-Can-Eat-License`). To prevent model collapse onto majority classes, class weights were calculated from the **training set only** using inverse class frequency:
$$\text{Weight}_c = \frac{N_{\text{samples}}}{N_{\text{classes}} \times N_c}$$
These weights were loaded directly into `torch.nn.CrossEntropyLoss` during training.

## 4. Epoch Training History

| Epoch | Train Loss | Val Loss | Val Accuracy | Val Macro F1 | Val Weighted F1 | Duration (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 3.3734 | 2.7039 | 0.5639 | **0.3291** | 0.5082 | 197.9 |
| 2 | 2.3464 | 1.9956 | 0.6909 | **0.4671** | 0.6587 | 222.9 |
| 3 | 1.8925 | 1.8248 | 0.7361 | **0.5520** | 0.7162 | 200.2 |

*Total Fine-Tuning Duration*: **10.39 minutes**

## 5. Model Selection & Final Test Evaluation

Model selection was performed using **Validation Macro F1**. The best checkpoint was evaluated **exactly once** on the held-out test dataset (1,418 clauses).

### Comparative Metrics Breakdown

| Evaluation Split | Accuracy | Macro Precision | Macro Recall | **Macro F1** | Weighted F1 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Validation Set (Epoch 3)** | 0.7361 | 0.6290 | 0.5588 | **0.5520** | 0.7162 |
| **Final Test Set** | **0.7186** | **0.5545** | **0.5338** | **0.5115** | **0.6977** |

## 6. Per-Class Test Performance (41 Categories)

| Clause Type | Support (Count) | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- | :--- |
| `Affiliate License-Licensee` | 6.0 | 0.2857 | 0.3333 | 0.3077 |
| `Affiliate License-Licensor` | 3.0 | 0.0000 | 0.0000 | 0.0000 |
| `Agreement Date` | 3.0 | 0.5000 | 0.6667 | 0.5714 |
| `Anti-Assignment` | 91.0 | 0.8421 | 0.8791 | 0.8602 |
| `Audit Rights` | 95.0 | 0.8214 | 0.9684 | 0.8889 |
| `Cap On Liability` | 82.0 | 0.8125 | 0.6341 | 0.7123 |
| `Change Of Control` | 36.0 | 0.5429 | 0.5278 | 0.5352 |
| `Competitive Restriction Exception` | 14.0 | 0.5000 | 0.1429 | 0.2222 |
| `Covenant Not To Sue` | 25.0 | 0.8077 | 0.8400 | 0.8235 |
| `Document Name` | 24.0 | 0.8889 | 1.0000 | 0.9412 |
| `Effective Date` | 21.0 | 0.5882 | 0.4762 | 0.5263 |
| `Exclusivity` | 60.0 | 0.5128 | 0.3333 | 0.4040 |
| `Expiration Date` | 62.0 | 0.7778 | 0.7903 | 0.7840 |
| `Governing Law` | 68.0 | 0.9565 | 0.9706 | 0.9635 |
| `Insurance` | 82.0 | 0.9506 | 0.9390 | 0.9448 |
| `Ip Ownership Assignment` | 47.0 | 0.6800 | 0.7234 | 0.7010 |
| `Irrevocable Or Perpetual License` | 4.0 | 0.0000 | 0.0000 | 0.0000 |
| `Joint Ip Ownership` | 15.0 | 0.6667 | 0.1333 | 0.2222 |
| `License Grant` | 99.0 | 0.5896 | 0.7980 | 0.6781 |
| `Liquidated Damages` | 15.0 | 0.4231 | 0.7333 | 0.5366 |
| `Minimum Commitment` | 60.0 | 0.5952 | 0.4167 | 0.4902 |
| `Most Favored Nation` | 5.0 | 0.0000 | 0.0000 | 0.0000 |
| `No-Solicit Of Customers` | 7.0 | 0.0000 | 0.0000 | 0.0000 |
| `No-Solicit Of Employees` | 11.0 | 0.3929 | 1.0000 | 0.5641 |
| `Non-Compete` | 39.0 | 0.5758 | 0.4872 | 0.5278 |
| `Non-Disparagement` | 9.0 | 1.0000 | 0.3333 | 0.5000 |
| `Non-Transferable License` | 14.0 | 1.0000 | 0.0714 | 0.1333 |
| `Notice Period To Terminate Renewal` | 3.0 | 0.0000 | 0.0000 | 0.0000 |
| `Parties` | 88.0 | 0.9556 | 0.9773 | 0.9663 |
| `Post-Termination Services` | 62.0 | 0.7368 | 0.4516 | 0.5600 |
| `Price Restrictions` | 3.0 | 0.0000 | 0.0000 | 0.0000 |
| `Renewal Term` | 25.0 | 0.7667 | 0.9200 | 0.8364 |
| `Revenue/Profit Sharing` | 62.0 | 0.6829 | 0.9032 | 0.7778 |
| `Rofr/Rofo/Rofn` | 53.0 | 0.6346 | 0.6226 | 0.6286 |
| `Source Code Escrow` | 9.0 | 0.0000 | 0.0000 | 0.0000 |
| `Termination For Convenience` | 34.0 | 0.6226 | 0.9706 | 0.7586 |
| `Third Party Beneficiary` | 5.0 | 1.0000 | 0.6000 | 0.7500 |
| `Uncapped Liability` | 25.0 | 0.4255 | 0.8000 | 0.5556 |
| `Unlimited/All-You-Can-Eat-License` | 2.0 | 0.0000 | 0.0000 | 0.0000 |
| `Volume Restriction` | 25.0 | 0.6000 | 0.6000 | 0.6000 |
| `Warranty Duration` | 25.0 | 0.6000 | 0.8400 | 0.7000 |

## 7. GPU Memory & Execution Safety

- **GPU Hardware**: NVIDIA GeForce RTX 3050 Laptop GPU (4 GB GDDR6 VRAM)
- **Peak VRAM Occupancy**: ~2.6 GB / 4.0 GB (No CUDA OOM errors encountered)
- **FP16 Mixed Precision**: Enabled via PyTorch `autocast` and `GradScaler`

## 8. Limitations & Legal Disclaimer

1. **Row-Level Boilerplate Overlap**: As identified in Phase 2, standard legal boilerplate clauses overlap across splits (8 exact matches), which may introduce minor optimistic evaluation bias.
2. **Absence of Document Context**: The classifier processes individual isolated clauses without full document context.
3. **Non-Production Disclaimer**: This classifier is designed for technical evaluation and decision support. It does NOT provide legal advice or legally binding guarantees.
