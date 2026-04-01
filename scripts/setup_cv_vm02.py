import os
import json
import torch
from torchvision import datasets, transforms
import math

PAYLOAD_DIR = os.path.expanduser("~/cs525_advanced_distributed_systems/data/payloads")
os.makedirs(PAYLOAD_DIR, exist_ok=True)

def prepare_resnet_payloads():
    print("\n[VM 02 - CV Node] Preparing CIFAR-10 Chunked Workloads...")
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    # Download CIFAR10
    dataset = datasets.CIFAR10(root='./data', train=False, download=True, transform=transform)
    
    total_images = 1000
    chunk_size = 200
    
    for chunk_id in range(math.ceil(total_images / chunk_size)):
        payloads = []
        start_idx = chunk_id * chunk_size
        end_idx = min(start_idx + chunk_size, total_images)
        for i in range(start_idx, end_idx):
            img_tensor, label = dataset[i]
            flat_data = img_tensor.flatten().tolist()
            
            payload = {
                "inputs": [{
                    "name": "data",
                    "shape": [1, 3, 224, 224],
                    "datatype": "FP32",
                    "data": flat_data
                }]
            }
            payloads.append(payload)
            
        out_path = os.path.join(PAYLOAD_DIR, f"resnet_chunk_{chunk_id+1}.json")
        with open(out_path, "w") as f:
            json.dump(payloads, f)
            
        print(f"✅ Created {out_path} (Images: {start_idx}-{end_idx-1}, Size: {os.path.getsize(out_path) / (1024 * 1024):.2f} MB)")

if __name__ == "__main__":
    prepare_resnet_payloads()
    print("\n🎉 CV Provisioning Phase completed.")
