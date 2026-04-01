import os
import json
from datasets import load_dataset
from transformers import AutoTokenizer

PAYLOAD_DIR = os.path.expanduser("~/cs525_advanced_distributed_systems/data/payloads")
os.makedirs(PAYLOAD_DIR, exist_ok=True)

def prepare_mobilebert_payloads():
    print("\n[VM 03 - NLP Node] Preparing SST-2 Complete Validation Split Workload...")
    dataset = load_dataset("glue", "sst2", split="validation")
    tokenizer = AutoTokenizer.from_pretrained("google/mobilebert-uncased")
    
    payloads = []
    print(f"Tokenizing {len(dataset)} items...")
    
    for i in range(len(dataset)):
        sentence = dataset[i]['sentence']
        tokens = tokenizer(sentence, padding='max_length', truncation=True, max_length=128)
        
        payload = {
            "inputs": [
                {
                    "name": "input_ids",
                    "shape": [1, 128],
                    "datatype": "INT64",
                    "data": tokens['input_ids']
                },
                {
                    "name": "attention_mask",
                    "shape": [1, 128],
                    "datatype": "INT64",
                    "data": tokens['attention_mask']
                }
            ]
        }
        payloads.append(payload)
        
    out_path = os.path.join(PAYLOAD_DIR, "bert_full_corpus.json")
    with open(out_path, "w") as f:
        json.dump(payloads, f)
        
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"✅ NLP Complete Corpus saved: {out_path} (Size: {size_mb:.2f} MB)")

if __name__ == "__main__":
    prepare_mobilebert_payloads()
    print("\n🎉 NLP Provisioning Phase completed.")
