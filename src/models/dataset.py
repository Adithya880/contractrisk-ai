"""
PyTorch Dataset Module for ContractRisk AI BERT Clause Classifier
------------------------------------------------------------------
Loads segmented legal clause texts and encodes them using HuggingFace AutoTokenizer.
Maps string clause_type targets to integer class indices deterministically.
"""

import torch
from torch.utils.data import Dataset

class ClauseDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=256, label2id=None):
        self.texts = list(texts)
        self.labels = list(labels) if labels is not None else None
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.label2id = label2id

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding='max_length',
            return_tensors='pt'
        )

        item = {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0)
        }

        if 'token_type_ids' in encoding:
            item['token_type_ids'] = encoding['token_type_ids'].squeeze(0)

        if self.labels is not None:
            label = self.labels[idx]
            if self.label2id is not None and isinstance(label, str):
                label_id = self.label2id[label]
            else:
                label_id = int(label)
            item['labels'] = torch.tensor(label_id, dtype=torch.long)

        return item
