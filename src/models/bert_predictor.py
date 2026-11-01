"""
BERT Clause Predictor Module for ContractRisk AI
------------------------------------------------
Provides production-ready inference wrapper for the fine-tuned BERT clause classifier.
Loads weights from models/bert_clause_classifier/best/, tokenizer, and label mappings.
Supports single-clause and high-throughput batch inference with GPU/CPU auto-detection.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any, Union
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, logging as hf_logging

from src.models.bert_classifier import BertClauseClassifier

logger = logging.getLogger(__name__)

# Default artifact paths relative to project root
DEFAULT_MODEL_DIR = Path("models/bert_clause_classifier")
DEFAULT_WEIGHTS_PATH = DEFAULT_MODEL_DIR / "best" / "pytorch_model.bin"
DEFAULT_TOKENIZER_DIR = DEFAULT_MODEL_DIR / "best"
DEFAULT_LABEL_MAPPING_PATH = DEFAULT_MODEL_DIR / "label_mapping.json"

# Prevent huggingface from making blocking DNS requests when local weights are present
if DEFAULT_WEIGHTS_PATH.exists():
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


class BERTClausePredictor:
    """
    Inference engine for fine-tuned 41-class BERT legal clause classification.
    """

    def __init__(
        self,
        model_dir: Union[str, Path] = DEFAULT_MODEL_DIR,
        device: Optional[str] = None,
        max_length: int = 256,
    ):
        """
        Initialize the predictor by loading tokenizer, label mapping, and model weights.

        Args:
            model_dir: Base directory containing model artifacts and label_mapping.json.
            device: 'cuda' or 'cpu'. If None, auto-selects cuda if available.
            max_length: Maximum token sequence length for truncation/padding (default 256).
        """
        self.model_dir = Path(model_dir)
        self.weights_path = self.model_dir / "best" / "pytorch_model.bin"
        self.tokenizer_dir = self.model_dir / "best"
        self.label_mapping_path = self.model_dir / "label_mapping.json"
        self.max_length = max_length

        # 1. Device selection
        if device is not None:
            self.device = torch.device(device)
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        logger.info(f"Initializing BERTClausePredictor on device: {self.device}")

        # 2. Load Label Mappings
        self.id2label, self.label2id = self._load_label_mapping()
        self.num_labels = len(self.id2label)

        # 3. Load Tokenizer
        self.tokenizer = self._load_tokenizer()

        # 4. Load PyTorch Model & Weights
        self.model = self._load_model()
        self.model.to(self.device)
        self.model.eval()

        logger.info(
            f"BERTClausePredictor initialized successfully with {self.num_labels} classes."
        )

    def _load_label_mapping(self) -> Tuple[Dict[int, str], Dict[str, int]]:
        """Loads and parses label_mapping.json."""
        if not self.label_mapping_path.exists():
            raise FileNotFoundError(
                f"BERT label mapping file not found at: {self.label_mapping_path.resolve()}"
            )

        with open(self.label_mapping_path, "r", encoding="utf-8") as f:
            mapping_data = json.load(f)

        raw_id2label = mapping_data.get("id2label", {})
        raw_label2id = mapping_data.get("label2id", {})

        id2label = {int(k): str(v) for k, v in raw_id2label.items()}
        label2id = {str(k): int(v) for k, v in raw_label2id.items()}

        return id2label, label2id

    def _load_tokenizer(self) -> AutoTokenizer:
        """Loads HuggingFace tokenizer from checkpoint directory."""
        # Suppress HF informational logs during loading
        hf_logging.set_verbosity_error()

        if self.tokenizer_dir.exists() and (
            (self.tokenizer_dir / "tokenizer.json").exists()
            or (self.tokenizer_dir / "vocab.txt").exists()
        ):
            return AutoTokenizer.from_pretrained(str(self.tokenizer_dir), local_files_only=True)
        else:
            raise FileNotFoundError(
                f"Tokenizer artifacts not found in checkpoint directory: {self.tokenizer_dir.resolve()}"
            )

    def _load_model(self) -> BertClauseClassifier:
        """Instantiates BertClauseClassifier and loads state dict weights."""
        if not self.weights_path.exists():
            raise FileNotFoundError(
                f"BERT model weights not found at: {self.weights_path.resolve()}"
            )

        model = BertClauseClassifier(
            model_name="bert-base-uncased",
            num_labels=self.num_labels,
            dropout_prob=0.1,
        )

        # Load weights onto target device (safely with fallback)
        try:
            state_dict = torch.load(self.weights_path, map_location=self.device, weights_only=True)
        except Exception:
            state_dict = torch.load(self.weights_path, map_location=self.device, weights_only=False)
        model.load_state_dict(state_dict)
        return model

    def _tokenize_head_tail(self, text: str) -> Dict[str, torch.Tensor]:
        """
        Tokenizes text using Head+Tail truncation when token length exceeds max_length - 2.
        Preserves the first 128 tokens (heading/intro) and last 126 tokens (operative conditions/exceptions).
        """
        raw_ids = self.tokenizer.encode(text, add_special_tokens=False)
        max_content_len = self.max_length - 2

        if len(raw_ids) > max_content_len:
            head_len = 128
            tail_len = max_content_len - head_len
            selected_ids = raw_ids[:head_len] + raw_ids[-tail_len:]
        else:
            selected_ids = raw_ids

        cls_id = self.tokenizer.cls_token_id if self.tokenizer.cls_token_id is not None else 101
        sep_id = self.tokenizer.sep_token_id if self.tokenizer.sep_token_id is not None else 102
        input_ids = [cls_id] + selected_ids + [sep_id]
        attention_mask = [1] * len(input_ids)

        return {
            "input_ids": torch.tensor([input_ids], dtype=torch.long, device=self.device),
            "attention_mask": torch.tensor([attention_mask], dtype=torch.long, device=self.device),
        }

    def _tokenize_head_tail_batch(self, texts: List[str]) -> Dict[str, torch.Tensor]:
        """
        Tokenizes batch using Head+Tail truncation and pads to max sequence length in batch.
        """
        max_content_len = self.max_length - 2
        cls_id = self.tokenizer.cls_token_id if self.tokenizer.cls_token_id is not None else 101
        sep_id = self.tokenizer.sep_token_id if self.tokenizer.sep_token_id is not None else 102
        pad_id = self.tokenizer.pad_token_id if self.tokenizer.pad_token_id is not None else 0

        batch_ids = []
        for t in texts:
            raw_ids = self.tokenizer.encode(t, add_special_tokens=False)
            if len(raw_ids) > max_content_len:
                head_len = 128
                tail_len = max_content_len - head_len
                selected_ids = raw_ids[:head_len] + raw_ids[-tail_len:]
            else:
                selected_ids = raw_ids
            batch_ids.append([cls_id] + selected_ids + [sep_id])

        max_batch_len = max(len(b) for b in batch_ids) if batch_ids else 1
        padded_ids = []
        padded_masks = []
        for b in batch_ids:
            pad_len = max_batch_len - len(b)
            padded_ids.append(b + [pad_id] * pad_len)
            padded_masks.append([1] * len(b) + [0] * pad_len)

        return {
            "input_ids": torch.tensor(padded_ids, dtype=torch.long, device=self.device),
            "attention_mask": torch.tensor(padded_masks, dtype=torch.long, device=self.device),
        }

    def predict_clause(self, clause_text: str) -> Tuple[str, float]:
        """
        Predict clause category and softmax confidence for a single clause string.

        Args:
            clause_text: Text content of the clause.

        Returns:
            Tuple of (predicted_category_name: str, confidence_score: float)
        """
        if not clause_text or not clause_text.strip():
            return "Other", 0.0

        cleaned_text = clause_text.strip()
        inputs = self._tokenize_head_tail(cleaned_text)

        with torch.no_grad():
            outputs = self.model(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                token_type_ids=None,
            )
            logits = outputs.logits
            probs = F.softmax(logits, dim=-1)
            conf, pred_idx = torch.max(probs, dim=-1)

        predicted_class_id = pred_idx.item()
        confidence = float(conf.item())
        predicted_label = self.id2label.get(predicted_class_id, "Other")

        return predicted_label, round(confidence, 4)

    def predict_clauses_batch(
        self, clause_texts: List[str], batch_size: int = 32
    ) -> List[Tuple[str, float]]:
        """
        Predict clause categories and confidences for a batch of clauses.

        Args:
            clause_texts: List of clause text strings.
            batch_size: Processing batch size (default 32).

        Returns:
            List of Tuples: [(predicted_category, confidence), ...]
        """
        if not clause_texts:
            return []

        results: List[Tuple[str, float]] = []

        for i in range(0, len(clause_texts), batch_size):
            batch_chunk = clause_texts[i : i + batch_size]
            sanitized_chunk = [
                t.strip() if (t and t.strip()) else "empty clause"
                for t in batch_chunk
            ]

            inputs = self._tokenize_head_tail_batch(sanitized_chunk)

            with torch.no_grad():
                outputs = self.model(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    token_type_ids=None,
                )
                logits = outputs.logits
                probs = F.softmax(logits, dim=-1)
                confs, pred_indices = torch.max(probs, dim=-1)

            for original_text, conf, idx in zip(
                batch_chunk, confs.cpu().tolist(), pred_indices.cpu().tolist()
            ):
                if not original_text or not original_text.strip():
                    results.append(("Other", 0.0))
                else:
                    label = self.id2label.get(idx, "Other")
                    results.append((label, round(float(conf), 4)))

        return results


# Module-level singleton instance
_singleton_predictor: Optional[BERTClausePredictor] = None


def get_bert_predictor() -> BERTClausePredictor:
    """
    Thread-safe / cached singleton accessor for BERTClausePredictor.
    Loads the weights once into memory on initial request.
    """
    global _singleton_predictor
    if _singleton_predictor is None:
        _singleton_predictor = BERTClausePredictor()
    return _singleton_predictor
