import torch
from transformers import AutoProcessor, AutoModel
from PIL import Image
import numpy as np

def test_siglip():
    model_name = "google/siglip-base-patch16-224"
    print(f"Loading processor and model: {model_name}...")
    processor = AutoProcessor.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()

    # Test image encoding
    dummy_img = Image.new("RGB", (224, 224), color=(73, 109, 137))
    inputs = processor(images=dummy_img, return_tensors="pt")
    with torch.no_grad():
        img_out = model.get_image_features(**inputs)
        img_emb = img_out.pooler_output if hasattr(img_out, "pooler_output") else (img_out[0] if isinstance(img_out, tuple) else img_out)
        img_emb = img_emb / img_emb.norm(p=2, dim=-1, keepdim=True)
    
    # Test text encoding
    inputs_text = processor(text=["a modern living room"], padding="max_length", return_tensors="pt")
    with torch.no_grad():
        txt_out = model.get_text_features(**inputs_text)
        txt_emb = txt_out.pooler_output if hasattr(txt_out, "pooler_output") else (txt_out[0] if isinstance(txt_out, tuple) else txt_out)
        txt_emb = txt_emb / txt_emb.norm(p=2, dim=-1, keepdim=True)

    similarity = torch.cosine_similarity(img_emb, txt_emb).item()
    print(f"SigLIP initialized successfully! Embedding dim: {img_emb.shape[-1]}, Cosine sim: {similarity:.4f}")

if __name__ == "__main__":
    test_siglip()
