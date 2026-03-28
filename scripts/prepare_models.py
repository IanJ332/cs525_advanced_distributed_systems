"""
Offline Model Preparation Script for Triton Inference Server

Dependency Installation:
conda install pytorch torchvision -c pytorch
pip install transformers onnx
"""

import os
import torch
import torchvision.models as models
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Define base path for Triton models
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ansible', 'models'))

def create_triton_config(model_name, max_batch_size=8):
    """Generates a minimal Triton config.pbtxt with dynamic batching enabled."""
    config_dir = os.path.join(MODELS_DIR, model_name)
    os.makedirs(config_dir, exist_ok=True)
    
    config_path = os.path.join(config_dir, "config.pbtxt")
    
    # Triton config content
    config_content = f"""name: "{model_name}"
platform: "onnxruntime_onnx"
max_batch_size: {max_batch_size}
dynamic_batching {{ }}
"""
    
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"[config.pbtxt] Created config for {model_name} at {config_path}")

def export_resnet50():
    """Exports ResNet50 to ONNX format."""
    print("Exporting ResNet50...")
    model_name = "resnet50"
    version_dir = os.path.join(MODELS_DIR, model_name, "1")
    os.makedirs(version_dir, exist_ok=True)
    
    # Load ResNet50
    model = models.resnet50(pretrained=True)
    model.eval()
    
    # Dummy input with shape (1, 3, 224, 224)
    dummy_input = torch.randn(1, 3, 224, 224)
    onnx_path = os.path.join(version_dir, "model.onnx")
    
    # Export to ONNX with dynamic batch axis
    torch.onnx.export(
        model, 
        dummy_input, 
        onnx_path, 
        export_params=True, 
        opset_version=13, 
        do_constant_folding=True,
        input_names=['input'], 
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
    )
    print(f"[*] ResNet50 ONNX exported to {onnx_path}")
    
    create_triton_config(model_name)

def export_bert():
    """Exports DistilBERT to ONNX format."""
    print("Exporting DistilBERT (SST-2)...")
    model_name = "bert_sst2"
    version_dir = os.path.join(MODELS_DIR, model_name, "1")
    os.makedirs(version_dir, exist_ok=True)
    
    # Load DistilBERT from Hugging Face
    model_id = "distilbert-base-uncased-finetuned-sst-2-english"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSequenceClassification.from_pretrained(model_id)
    model.eval()
    
    # Dummy input
    dummy_text = "This is a great movie."
    inputs = tokenizer(dummy_text, return_tensors="pt", max_length=128, padding="max_length", truncation=True)
    
    onnx_path = os.path.join(version_dir, "model.onnx")
    
    # Export to ONNX with dynamic batch axis
    torch.onnx.export(
        model, 
        (inputs['input_ids'], inputs['attention_mask']), 
        onnx_path, 
        export_params=True, 
        opset_version=13, 
        do_constant_folding=True,
        input_names=['input_ids', 'attention_mask'], 
        output_names=['output'],
        dynamic_axes={
            'input_ids': {0: 'batch_size'}, 
            'attention_mask': {0: 'batch_size'},
            'output': {0: 'batch_size'}
        }
    )
    print(f"[*] DistilBERT ONNX exported to {onnx_path}")
    
    create_triton_config(model_name)

if __name__ == "__main__":
    print(f"Base Models Directory: {MODELS_DIR}")
    os.makedirs(MODELS_DIR, exist_ok=True)
    export_resnet50()
    print("-" * 40)
    export_bert()
    print("-" * 40)
    print("Model preparation complete.")
