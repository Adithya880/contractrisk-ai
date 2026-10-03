"""
BERT Clause Classifier Architecture Module
------------------------------------------
Wraps HuggingFace AutoModelForSequenceClassification (bert-base-uncased)
for multi-class legal clause categorization (41 classes).
"""

import torch
import torch.nn as nn
from transformers import AutoModelForSequenceClassification

class BertClauseClassifier(nn.Module):
    def __init__(self, model_name="bert-base-uncased", num_labels=41, dropout_prob=0.1):
        super(BertClauseClassifier, self).__init__()
        self.num_labels = num_labels
        self.bert = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=num_labels,
            hidden_dropout_prob=dropout_prob,
            attention_probs_dropout_prob=dropout_prob
        )

    def forward(self, input_ids, attention_mask, token_type_ids=None, labels=None):
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            labels=labels
        )
        return outputs
