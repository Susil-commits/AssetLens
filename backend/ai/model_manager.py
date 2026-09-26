import threading
from pathlib import Path
from typing import List, Union
from PIL import Image
import torch
import numpy as np
from transformers import AutoProcessor, AutoModel
from sentence_transformers import SentenceTransformer
from backend.config import settings

class ModelManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ModelManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.device = settings.get_resolved_device()
        self.siglip_model_name = settings.SIGLIP_MODEL_NAME
        self.text_model_name = "sentence-transformers/all-MiniLM-L6-v2"

        self._siglip_processor = None
        self._siglip_model = None
        self._text_model = None
        self._load_lock = threading.Lock()
        self._initialized = True

    def _ensure_siglip(self):
        with self._load_lock:
            if self._siglip_model is None:
                self._siglip_processor = AutoProcessor.from_pretrained(self.siglip_model_name)
                self._siglip_model = AutoModel.from_pretrained(self.siglip_model_name)
                self._siglip_model.to(self.device)
                self._siglip_model.eval()

    def _ensure_text_model(self):
        with self._load_lock:
            if self._text_model is None:
                self._text_model = SentenceTransformer(self.text_model_name, device=self.device)

    def encode_image(self, image_input: Union[Image.Image, Path, str]) -> List[float]:
        """Encodes an image into a 768-dim L2-normalized vector using SigLIP."""
        self._ensure_siglip()
        if isinstance(image_input, (str, Path)):
            with Image.open(image_input) as img:
                pil_img = img.convert("RGB")
        else:
            pil_img = image_input.convert("RGB")

        inputs = self._siglip_processor(images=pil_img, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            output = self._siglip_model.get_image_features(**inputs)
            emb = output.pooler_output if hasattr(output, "pooler_output") else (output[0] if isinstance(output, tuple) else output)
            emb = emb / emb.norm(p=2, dim=-1, keepdim=True)
            return emb.cpu().squeeze().tolist()

    def encode_text_for_visual_search(self, text: str) -> List[float]:
        """Encodes a query text into the SigLIP 768-dim multimodal space for visual matching."""
        self._ensure_siglip()
        inputs = self._siglip_processor(text=[text], padding="max_length", return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            output = self._siglip_model.get_text_features(**inputs)
            emb = output.pooler_output if hasattr(output, "pooler_output") else (output[0] if isinstance(output, tuple) else output)
            emb = emb / emb.norm(p=2, dim=-1, keepdim=True)
            return emb.cpu().squeeze().tolist()

    def encode_text_dense(self, text: str) -> List[float]:
        """Encodes document/transcript text into a 384-dim normalized vector using SentenceTransformer."""
        self._ensure_text_model()
        emb = self._text_model.encode(text, normalize_embeddings=True)
        return emb.tolist()

# Global model manager singleton
model_manager = ModelManager()
