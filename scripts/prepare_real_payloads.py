import os
import json
import torch
from torchvision import datasets, transforms
from datasets import load_dataset
from transformers import AutoTokenizer

PAYLOAD_DIR = os.path.expanduser("~/cs525_advanced_distributed_systems/data/payloads")
os.makedirs(PAYLOAD_DIR, exist_ok=True)

def prepare_resnet_payloads():
    print("\n[1/2] Preparing ResNet50 payloads (CIFAR-10)...")
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    # Download CIFAR10
    dataset = datasets.CIFAR10(root='./data', train=False, download=True, transform=transform)
    
    payloads = []
    for i in range(100):
        img_tensor, label = dataset[i]
        flat_data = img_tensor.flatten().tolist()
        
        # Format for Triton Python/ONNX Backend
        payload = {
            "inputs": [{
                "name": "data",  # Changed to "data" to match our Triton setup
                "shape": [1, 3, 224, 224],
                "datatype": "FP32",
                "data": flat_data
            }]
        }
        payloads.append(payload)
        
    out_path = os.path.join(PAYLOAD_DIR, "resnet_real.json")
    with open(out_path, "w") as f:
        json.dump(payloads, f)
    
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"✅ ResNet50 payloads saved: {out_path} (Size: {size_mb:.2f} MB)")

def prepare_mobilebert_payloads():
    print("\n[2/2] Preparing MobileBERT payloads (SST-2)...")
    dataset = load_dataset("glue", "sst2", split="validation")
    tokenizer = AutoTokenizer.from_pretrained("google/mobilebert-uncased")
    
    payloads = []
    for i in range(100):
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
        
    out_path = os.path.join(PAYLOAD_DIR, "bert_real.json")
    with open(out_path, "w") as f:
        json.dump(payloads, f)
        
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"✅ MobileBERT payloads saved: {out_path} (Size: {size_mb:.2f} MB)")

if __name__ == "__main__":
    prepare_resnet_payloads()
    prepare_mobilebert_payloads()
    print("\n🎉 All payload conversions completed successfully!")
