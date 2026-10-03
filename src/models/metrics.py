"""
Evaluation Metrics and Visualization Module for ContractRisk AI
----------------------------------------------------------------
Calculates comprehensive classification metrics:
Accuracy, Macro/Weighted Precision, Recall, F1-score, per-class metrics,
and renders confusion matrices to file.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix
)

def compute_classification_metrics(y_true, y_pred, id2label=None):
    acc = accuracy_score(y_true, y_pred)
    
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average='macro', zero_division=0
    )
    weighted_p, weighted_r, weighted_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average='weighted', zero_division=0
    )

    labels = sorted(list(set(y_true).union(set(y_pred))))
    target_names = [id2label[i] if id2label and i in id2label else str(i) for i in labels]

    per_class_report = classification_report(
        y_true, y_pred,
        labels=labels,
        target_names=target_names,
        output_dict=True,
        zero_division=0
    )

    return {
        "accuracy": float(acc),
        "macro_precision": float(macro_p),
        "macro_recall": float(macro_r),
        "macro_f1": float(macro_f1),
        "weighted_precision": float(weighted_p),
        "weighted_recall": float(weighted_r),
        "weighted_f1": float(weighted_f1),
        "per_class": per_class_report
    }

def plot_confusion_matrix(y_true, y_pred, id2label, output_path="reports/bert_confusion_matrix.png"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    labels = sorted(list(id2label.keys()))
    target_names = [id2label[i] for i in labels]

    cm = confusion_matrix(y_true, y_pred, labels=labels)

    plt.figure(figsize=(18, 16))
    sns.heatmap(
        cm,
        annot=False,
        fmt='d',
        cmap='Blues',
        xticklabels=target_names,
        yticklabels=target_names
    )
    plt.title("ContractRisk AI — BERT Clause Classifier Confusion Matrix", fontsize=16, pad=20)
    plt.xlabel("Predicted Label", fontsize=12)
    plt.ylabel("True Label", fontsize=12)
    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(rotation=0, fontsize=8)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[OK] Confusion matrix plot saved to '{output_path}'")
