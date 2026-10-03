# Model Artifacts Directory

This directory stores trained machine learning checkpoints and artifacts for the ContractRisk AI system.

## Exclusion from Version Control

Trained weights and binary model checkpoints (such as `pytorch_model.bin`, `.safetensors`, `.pt`, `.onnx`) exceed GitHub repository size limits and are intentionally excluded from Git tracking via `.gitignore`.

## Local Model Training & Generation

To train and generate the BERT clause-type classifier checkpoint locally:

1. **Verify Prerequisites**:
   Ensure dependencies from `requirements.txt` are installed, and the dataset splits exist in `data/splits/` (specifically `train.csv`, `validation.csv`, and `test.csv`).

2. **Run Supervised Fine-Tuning**:
   Execute the fine-tuning script using PyTorch and Hugging Face Transformers:
   ```bash
   python -m src.models.train_bert --splits_dir data/splits --output_dir models/bert_clause_classifier
   ```

3. **Generated Artifacts**:
   The training pipeline will generate:
   - `models/bert_clause_classifier/best/pytorch_model.bin`: Best model weights based on validation Macro F1.
   - `models/bert_clause_classifier/best/tokenizer.json` and `tokenizer_config.json`: Hugging Face tokenizer configuration.
   - `models/bert_clause_classifier/label_mapping.json`: Mapping between the 41 legal clause categories and numeric label IDs.
   - `models/bert_clause_classifier/training_config.json`: Hyperparameters and training metadata.

For detailed architecture, hyperparameters, and training methodology, consult [`docs/BERT_CLASSIFIER_REPORT.md`](../docs/BERT_CLASSIFIER_REPORT.md).
