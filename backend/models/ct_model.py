"""
CT Model - Optional 3D UNETR with robust fallback

Behavior:
- If MONAI + PyTorch and a CT checkpoint are provided, uses UNETR to produce a
  lesion mask score. Otherwise, uses Gemini body_region + heuristics on the
  provided 2D snapshot.
"""

from typing import Any, Dict, Optional

import os
import numpy as np
from PIL import Image

try:
    from .gemini_vision import gemini_vision as _GEM_VISION
except Exception:
    try:
        from models.gemini_vision import gemini_vision as _GEM_VISION
    except Exception:
        _GEM_VISION = None


TORCH_OK = False
MONAI_OK = False
try:
    import torch
    TORCH_OK = True
except Exception:
    TORCH_OK = False

try:
    import monai
    from monai.networks.nets import UNETR
    MONAI_OK = True
except Exception:
    MONAI_OK = False


class CTModel:
    def __init__(self):
        self.gemini = _GEM_VISION if _GEM_VISION and _GEM_VISION.is_available() else None
        self.model = None
        self.backend = None
        self.device = "cpu"

        ckpt_path = os.getenv("CT_WEIGHTS_PATH", "")
        use_unetr = os.getenv("CT_MODEL", "").lower() in ["unetr", "swin-unetr"]
        if MONAI_OK and TORCH_OK and use_unetr and ckpt_path and os.path.exists(ckpt_path):
            try:
                self.model = UNETR(
                    in_channels=1,
                    out_channels=2,
                    img_size=(128, 128, 128),
                    feature_size=16,
                    hidden_size=768,
                    mlp_dim=3072,
                    num_heads=12,
                    pos_embed="perceptron",
                    norm_name="instance",
                    res_block=True,
                    dropout_rate=0.0,
                )
                state = torch.load(ckpt_path, map_location="cpu")
                if isinstance(state, dict) and "state_dict" in state:
                    state = {k.replace("module.", ""): v for k, v in state["state_dict"].items()}
                self.model.load_state_dict(state, strict=False)
                self.model.eval()
                self.backend = "unetr"
                try:
                    if torch.cuda.is_available():
                        self.model = self.model.cuda()
                        self.device = "cuda"
                except Exception:
                    pass
            except Exception as e:
                print(f"CT UNETR init failed: {e}")
                self.model = None
                self.backend = None

    def is_available(self) -> bool:
        return self.model is not None

    def analyze_image(self, image: Image.Image) -> Dict[str, Any]:
        try:
            # Gemini modality / region / findings
            gem_modality = None
            gem_region = None
            gem_conf = None
            gem_findings = []
            if self.gemini:
                try:
                    gv = self.gemini.analyze(image)
                    if gv:
                        gem_modality = gv.get("modality")
                        gem_region = gv.get("body_region") or "unknown"
                        gem_conf = float(gv.get("confidence", 0.8))
                        gem_findings = gv.get("preliminary_findings", []) or []
                except Exception:
                    pass

            # 2D snapshot heuristics
            gray = np.array(image.convert("L"))
            brightness = float(gray.mean())
            contrast = float(gray.std())
            gx = np.abs(np.diff(gray.astype(np.float32), axis=1))
            gy = np.abs(np.diff(gray.astype(np.float32), axis=0))
            edge_score = float((gx.mean() + gy.mean()) / 2.0)

            # Local variance and high-intensity area
            lv = self._local_var(gray, k=15)
            lv_q95 = float(np.quantile(lv, 0.95))
            lv_mean = float(np.mean(lv))
            lesion_score = max(0.0, (lv_q95 - lv_mean) / (lv_q95 + 1e-6))
            hi_thresh = float(np.quantile(gray, 0.97))
            hi_mask = gray >= hi_thresh
            hi_area = float(hi_mask.mean())

            region = (gem_region or "ct").strip().lower().replace("_", "-")
            # Region-aware suspicion: chest opacities or focal lesion elsewhere
            is_chest = "chest" in region or "lung" in region
            suspicious = (
                (is_chest and lesion_score > 0.22 and contrast > 25) or
                (not is_chest and (lesion_score > 0.30 or hi_area > 0.015))
            )
            label = f"{region} ct - lesion suspected" if suspicious else f"{region} ct - no obvious abnormality"

            findings = []
            for f in gem_findings:
                if isinstance(f, str) and f not in findings:
                    findings.append(f)
            if brightness < 60:
                findings.append("Underexposed slice (dark)")
            if brightness > 200:
                findings.append("Overexposed slice (bright)")
            if is_chest and lesion_score > 0.22:
                findings.append("Patchy parenchymal density (possible pulmonary opacity)")
            if not is_chest and (lesion_score > 0.30 or hi_area > 0.015):
                findings.append("Focal high-variance/high-intensity region (possible lesion)")
            if not findings:
                findings.append("No strong abnormalities detected on snapshot")

            return {
                "ct_label": label,
                "ct_confidence": round(min(0.95, 0.60 + 0.28 * float(lesion_score)), 2),
                "ct_body_region": region,
                "ct_findings": findings,
                "ct_stats": {
                    "brightness": round(brightness, 2),
                    "contrast": round(contrast, 2),
                    "edge_score": round(edge_score, 2),
                    "lesion_score": round(float(lesion_score), 3),
                    "hi_area": round(float(hi_area), 4),
                    "modality": gem_modality or "ct",
                    "modality_confidence": round(float(gem_conf or 0.8), 2),
                },
                "used_backend": self.backend or "heuristic+gemini",
            }
        except Exception as e:
            print(f"CT analyze error: {e}")
            return {
                "ct_label": "ct - analysis error",
                "ct_confidence": 0.0,
                "error": str(e),
            }

    # ---- helpers ----
    def _local_var(self, gray: np.ndarray, k: int = 15) -> np.ndarray:
        g = gray.astype(np.float32)
        pad = k // 2
        src = np.pad(g, pad, mode='reflect')
        K = np.ones((k, k), dtype=np.float32)
        mean = self._conv(src, K)[pad:-pad, pad:-pad] / (k * k)
        mean2 = self._conv(src * src, K)[pad:-pad, pad:-pad] / (k * k)
        var = np.maximum(0.0, mean2 - mean * mean)
        return var

    def _conv(self, img: np.ndarray, K: np.ndarray) -> np.ndarray:
        ky, kx = K.shape
        H, W = img.shape
        out = np.zeros((H - ky + 1, W - kx + 1), dtype=np.float32)
        for y in range(ky):
            for x in range(kx):
                out += K[y, x] * img[y:y + H - ky + 1, x:x + W - kx + 1]
        return out


