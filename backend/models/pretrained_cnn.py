"""
Pretrained X-ray classifier wrapper (prefers medical-domain weights).

Priority:
1) torchxrayvision DenseNet-121 (CheXNet-like) – no training needed
2) torchvision backbones (ImageNet) – not used for diagnosis, but can provide features

This module is OPTIONAL. If unavailable, callers should gracefully fall back.
"""

from typing import Dict, Optional

import numpy as np
from PIL import Image

try:
    import torch
    TORCH_OK = True
except Exception:
    TORCH_OK = False

# Try medical-domain pretrained first
_XRV_OK = False
try:
    import torchxrayvision as xrv  # type: ignore
    _XRV_OK = True
except Exception:
    _XRV_OK = False


class PretrainedXrayModel:
    def __init__(self):
        self.device = "cpu"
        self.backend = None
        self.model = None
        self.pathologies = []

        if not TORCH_OK:
            return

        # Prefer torchxrayvision DenseNet-121 pretrained on multiple datasets
        if _XRV_OK:
            try:
                self.model = xrv.models.DenseNet(weights="densenet121-res224-all")
                self.model.eval()
                self.backend = "xrv-densenet121"
                self.pathologies = list(self.model.pathologies)
                return
            except Exception:
                self.model = None
                self.backend = None

        # If other backbones are needed later, add here; for now, only xrv is used

    def is_available(self) -> bool:
        return self.model is not None and TORCH_OK

    def _preprocess_xrv(self, image: Image.Image) -> torch.Tensor:  # type: ignore[name-defined]
        # Convert to 1x1x224x224 float tensor, normalized to ~[-1, 1]
        img = image.convert("L").resize((224, 224))
        arr = np.array(img).astype("float32") / 255.0
        arr = (arr - 0.5) / 0.5
        arr = arr[None, None, :, :]
        return torch.from_numpy(arr)

    def infer(self, image: Image.Image) -> Optional[Dict[str, float]]:
        if not self.is_available():
            return None

        if self.backend == "xrv-densenet121":
            try:
                with torch.no_grad():
                    x = self._preprocess_xrv(image)
                    logits = self.model(x)  # type: ignore[operator]
                    probs = torch.sigmoid(logits)[0].cpu().numpy()
                # Map selected pathologies to our simplified classes
                pmap = {name: 0.0 for name in ["normal", "pneumonia", "tumor", "fracture"]}
                try:
                    idx = {n: self.pathologies.index(n) for n in self.pathologies}
                except Exception:
                    idx = {}

                # Pneumonia direct
                if "Pneumonia" in self.pathologies:
                    pmap["pneumonia"] = float(probs[self.pathologies.index("Pneumonia")])

                # Tumor proxy via Mass/Nodule
                p_mass = float(probs[self.pathologies.index("Mass")]) if "Mass" in self.pathologies else 0.0
                p_nodule = float(probs[self.pathologies.index("Nodule")]) if "Nodule" in self.pathologies else 0.0
                pmap["tumor"] = max(p_mass, p_nodule)

                # Fracture not present in NIH14; leave for heuristic to inform
                pmap["fracture"] = 0.0

                # Normal as complement (clipped)
                others = max(pmap["pneumonia"], pmap["tumor"], pmap["fracture"])
                pmap["normal"] = float(max(0.0, 1.0 - others))

                return pmap
            except Exception:
                return None

        return None


# Singleton
pretrained_xray = PretrainedXrayModel()


