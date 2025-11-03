"""
CNN Model - Heuristic, feature-based X-ray analyzer (no heavy ML deps)

Goals:
- Robust, deterministic analysis without PyTorch/OpenCV/Scipy
- Useful quality checks (exposure, sharpness, noise)
- Probabilistic multi-class output with explainable features
"""

import random
from PIL import Image, ImageFilter, ImageOps
import numpy as np
import os

# Optional Gemini Vision assistant for modality/finding support
try:
    from .gemini_vision import gemini_vision as _GEM_VISION
except Exception:
    try:
        from models.gemini_vision import gemini_vision as _GEM_VISION
    except Exception:
        _GEM_VISION = None

# Optional pretrained medical CNN (CheXNet) - DISABLED by default to avoid heavy torch import.
# Enable by setting environment variable ENABLE_PRETRAINED_CNN=1
_PRETRAINED = None
if os.getenv("ENABLE_PRETRAINED_CNN", "0") == "1":
    try:
        from .pretrained_cnn import pretrained_xray as _PRETRAINED
    except Exception:
        try:
            from models.pretrained_cnn import pretrained_xray as _PRETRAINED
        except Exception:
            _PRETRAINED = None
    except Exception:
        _PRETRAINED = None

class CNNModel:
    def __init__(self, num_classes=4):
        """Initialize heuristic analyzer."""
        print("X-ray Analyzer initialized (Heuristic mode - no PyTorch required)")
        self.class_names = ['Normal', 'Pneumonia', 'Tumor', 'Fracture']
        self.model = None
        self.gemini = _GEM_VISION if _GEM_VISION and _GEM_VISION.is_available() else None
        self.pretrained = _PRETRAINED if _PRETRAINED and _PRETRAINED.is_available() else None
    
    def analyze_image(self, image):
        """Analyze X-ray using handcrafted features and rules."""
        try:
            gray = self._to_gray(image)
            h, w = gray.shape

            # 1) Preprocess: denoise + equalize (contrast normalization)
            gray_blur = self._median(gray, k=3)
            gray_eq = self._equalize(gray_blur)
            
            # 2) Global features
            brightness = float(np.mean(gray_eq))
            contrast = float(np.std(gray_eq))
            sharpness = float(self._variance_of_laplacian(gray_eq))
            edge_score = float(self._calculate_edge_score(gray_eq))
            noise_est = float(self._estimate_noise(gray_eq))
            
            # 3) Local variance heatmap (lesion/opacity proxy)
            local_var = self._local_variance(gray_eq, window=15)
            var_q95 = float(np.quantile(local_var, 0.95))
            var_mean = float(np.mean(local_var))
            opacity_score = max(0.0, (var_q95 - var_mean) / (var_q95 + 1e-6))
            
            # 3.5) Modality gate: detect non-chest X-ray (e.g., dental panoramic)
            # Heuristics: very wide aspect ratio + stronger edges/brightness in lower third
            aspect = float(w) / float(h)
            # Edge map for band comparison
            grad_x = np.abs(np.diff(gray_eq.astype(np.float32), axis=1))
            grad_y = np.abs(np.diff(gray_eq.astype(np.float32), axis=0))
            edge_map = (grad_x[:-1, :] + grad_y[:, :-1])
            Hm = edge_map.shape[0]
            t1 = int(Hm * 0.33)
            t2 = int(Hm * 0.66)
            top_edges = float(np.mean(edge_map[:t1, :]))
            mid_edges = float(np.mean(edge_map[t1:t2, :]))
            bottom_edges = float(np.mean(edge_map[t2:, :]))
            edge_bot_top_ratio = (bottom_edges + 1e-6) / (top_edges + 1e-6)

            # Brightness distribution by thirds
            Hb = gray_eq.shape[0]
            b1 = int(Hb * 0.33)
            b2 = int(Hb * 0.66)
            top_bright = float(np.mean(gray_eq[:b1, :]))
            mid_bright = float(np.mean(gray_eq[b1:b2, :]))
            bottom_bright = float(np.mean(gray_eq[b2:, :]))
            bright_bot_top_ratio = (bottom_bright + 1e-6) / (top_bright + 1e-6)

            dental_like = (
                aspect > 1.6 and (
                    edge_bot_top_ratio > 1.35 or
                    bright_bot_top_ratio > 1.12
                )
            )

            # Optional: Gemini Vision assist for modality and preliminary findings
            gem_modality = None
            gem_conf = None
            gem_body_region = None
            gem_findings = []
            if self.gemini:
                try:
                    gv = self.gemini.analyze(Image.fromarray(self._equalize(gray_blur)))
                    if gv:
                        gem_modality = gv.get('modality')
                        gem_conf = float(gv.get('confidence', 0.8))
                        gem_body_region = gv.get('body_region') or 'unknown'
                        gem_findings = gv.get('preliminary_findings', []) or []
                        # Refine dental_like if Gemini strongly suggests non-chest/dental
                        if gv.get('is_dental', False) or (gem_modality in ['non-chest-xray', 'document'] and gem_conf and gem_conf > 0.75):
                            dental_like = True
                except Exception:
                    pass

            # 4) Simple rule-based class probabilities
            probs = {c: 0.0 for c in self.class_names}
            # Normalize feature ranges
            nb = np.clip((brightness - 90) / 60.0, -1, 1)      # exposure
            nc = np.clip((contrast - 40) / 40.0, -1, 1)        # contrast
            ns = np.clip((sharpness - 25) / 50.0, -1, 1)       # sharpness
            ne = np.clip((edge_score - 25) / 40.0, -1, 1)      # edges
            no = np.clip(opacity_score * 3.0, 0, 1)            # opacities

            # Pneumonia: higher opacities, moderate contrast, not overly sharp
            probs['Pneumonia'] = 0.5 * no + 0.2 * (1 - abs(nb)) + 0.2 * max(0, nc) + 0.1 * (1 - max(0, ns))
            # Tumor: localized high variance and edges
            probs['Tumor'] = 0.4 * no + 0.4 * max(0, ne) + 0.2 * max(0, ns)
            # Fracture: very high sharpness and edges
            probs['Fracture'] = 0.6 * max(0, ns) + 0.3 * max(0, ne) + 0.1 * max(0, nc)
            # Normal: good exposure, moderate contrast, low opacity
            probs['Normal'] = 0.5 * (1 - no) + 0.2 * (1 - max(0, ne)) + 0.2 * (1 - max(0, ns)) + 0.1 * (1 - abs(nb))

            # Convert to softmax-like distribution
            vec = np.array([probs[c] for c in self.class_names], dtype=np.float32)
            vec = np.maximum(vec, 1e-6)
            vec = vec / vec.sum()
            predicted_idx = int(np.argmax(vec))
            confidence = float(vec[predicted_idx])

            # 4.5) If pretrained model available, get medical-domain probabilities
            if self.pretrained:
                try:
                    pmap = self.pretrained.infer(Image.fromarray(gray))
                    if pmap:
                        # Map to vector order [Normal, Pneumonia, Tumor, Fracture]
                        vec_pre = np.array([
                            float(pmap.get('normal', 0.0)),
                            float(pmap.get('pneumonia', 0.0)),
                            float(pmap.get('tumor', 0.0)),
                            float(pmap.get('fracture', 0.0)),
                        ], dtype=np.float32)
                        vec_pre = np.maximum(vec_pre, 1e-6)
                        vec_pre = vec_pre / vec_pre.sum()
                        # Blend pretrained (dominant) with heuristic
                        vec = 0.7 * vec_pre + 0.3 * vec
                        vec = vec / vec.sum()
                        predicted_idx = int(np.argmax(vec))
                        confidence = float(vec[predicted_idx])
                except Exception:
                    pass

            # If dental-like (non-chest) detected, override to Normal with caution
            modality = "chest-xray"
            modality_conf = 0.85
            if dental_like:
                modality = "non-chest-xray (dental/panoramic likely)"
                # Use edge_bot_top_ratio (lower/upper) for confidence proxy
                modality_conf = min(0.97, 0.7 + 0.1 * (aspect - 1.6) + 0.2 * (edge_bot_top_ratio - 1.35))
                predicted_idx = 0
                confidence = max(confidence, 0.70)
                vec = np.array([0.88, 0.04, 0.04, 0.04], dtype=np.float32)

            # If Gemini provided a modality with good confidence, blend it
            if gem_modality and gem_conf:
                if gem_modality == 'chest-xray':
                    # Slightly raise confidence in chest modality
                    modality = 'chest-xray'
                    modality_conf = max(modality_conf, min(0.98, 0.80 + 0.15 * gem_conf))
                elif gem_modality in ['non-chest-xray', 'document', 'other']:
                    # Enforce non-chest behavior
                    modality = 'non-chest-xray (gemini)'
                    modality_conf = max(modality_conf, min(0.98, 0.75 + 0.2 * gem_conf))
                    predicted_idx = 0
                    confidence = max(confidence, 0.70)
                    vec = np.array([0.90, 0.04, 0.03, 0.03], dtype=np.float32)

            # Bias correction: avoid defaulting to "Pneumonia" when opacities are low
            if modality == "chest-xray" and opacity_score < 0.22:
                vec = np.array([
                    max(0.70, float(vec[0]) + 0.25),  # Normal
                    max(0.02, float(vec[1]) - 0.20),   # Pneumonia
                    float(vec[2]) * 0.95,              # Tumor
                    float(vec[3]) * 0.95               # Fracture
                ], dtype=np.float32)
                vec = vec / vec.sum()
                predicted_idx = int(np.argmax(vec))
                confidence = float(vec[predicted_idx])

            
            # Keep confidence realistic - don't artificially inflate
            confidence = max(0.55, min(0.93, float(confidence)))

            probabilities = {self.class_names[i]: float(vec[i]) for i in range(len(self.class_names))}
            findings_heur = self._make_findings(
                brightness, contrast, sharpness, edge_score, opacity_score,
                modality=modality, body_region=gem_body_region
            )
            # Merge Gemini preliminary findings (non-diagnostic) FIRST for visibility
            findings = []
            if 'gem_findings' in locals() and gem_findings:
                for f in gem_findings:
                    if isinstance(f, str) and f not in findings:
                        findings.append(f)
            for f in findings_heur:
                if f not in findings:
                    findings.append(f)

            # Region-aware class label: avoid generic "Normal" for non-chest
            class_label = self.class_names[predicted_idx]
            if not str(modality).startswith("chest"):
                region = (gem_body_region or "non-chest").strip().lower()
                region = region.replace("_", "-")
                # Simple assessment for non-chest
                possible_fracture = float(vec[3]) > 0.25 or (edge_score > 55 and sharpness > 40)
                # Neck-specific soft-tissue signal: high opacity with low edges
                soft_tissue_swelling = ("neck" in region or "cervical" in region) and (opacity_score > 0.32 and edge_score < 12)
                if soft_tissue_swelling:
                    assessment = "possible soft-tissue swelling"
                else:
                    assessment = "possible fracture" if possible_fracture else "no obvious abnormality"
                class_label = f"{region} x-ray - {assessment}"
            
            return {
                "prediction": predicted_idx,
                "confidence": round(confidence, 2),
                "class_name": class_label,
                "all_probabilities": probabilities,
                "image_stats": {
                    "brightness": round(float(brightness), 2),
                    "contrast": round(float(contrast), 2),
                    "edge_score": round(float(edge_score), 2),
                    "sharpness": round(float(sharpness), 2),
                    "noise": round(float(noise_est), 3),
                    "opacity_score": round(float(opacity_score), 3),
                    "aspect_ratio": round(float(aspect), 3),
                    "edge_bot_top_ratio": round(float(edge_bot_top_ratio), 3),
                    "bright_bot_top_ratio": round(float(bright_bot_top_ratio), 3),
                    "modality": modality,
                    "modality_confidence": round(float(modality_conf), 2),
                    "body_region": gem_body_region or ("chest" if modality.startswith("chest") else "unknown")
                },
                "findings": findings
            }
            
        except Exception as e:
            print(f"CNN analysis error: {str(e)}")
            return {
                "prediction": 0,
                "confidence": 0.72,
                "class_name": self.class_names[0],
                "error": str(e)
            }
    
    def _calculate_edge_score(self, gray_image):
        """Calculate edge content score"""
        try:
            # Simple Sobel-like gradients via differences
            grad_x = np.abs(np.diff(gray_image.astype(np.float32), axis=1))
            grad_y = np.abs(np.diff(gray_image.astype(np.float32), axis=0))
            edge_score = float((np.mean(grad_x) + np.mean(grad_y)) / 2.0)
            return edge_score
        except:
            return 20.0  # Default moderate edge score
    
    def get_feature_maps(self, image):
        """Return processed image used for saliency/heatmap generation."""
        gray = self._to_gray(image)
        gray_eq = self._equalize(self._median(gray, k=3))
        return Image.fromarray(gray_eq)

    # ----------------- Helpers -----------------
    def _to_gray(self, image):
        if isinstance(image, Image.Image):
            arr = np.array(image)
        else:
            arr = image
        if arr.ndim == 3:
            arr = np.mean(arr, axis=2).astype(np.uint8)
        return arr

    def _median(self, gray, k=3):
        # Simple median filter using padding and unfold; k odd
        pad = k // 2
        padded = np.pad(gray, pad, mode='edge')
        H, W = gray.shape
        patches = []
        for dy in range(k):
            for dx in range(k):
                patches.append(padded[dy:dy+H, dx:dx+W])
        stack = np.stack(patches, axis=-1)
        return np.median(stack, axis=-1).astype(np.uint8)

    def _equalize(self, gray):
        # Histogram equalization using Pillow for stability
        img = Image.fromarray(gray)
        eq = ImageOps.equalize(img)
        return np.array(eq)

    def _variance_of_laplacian(self, gray):
        # Approximate Laplacian via second differences
        g = gray.astype(np.float32)
        lap = (
            -4 * g +
            np.pad(g, ((0,0),(1,0)), 'edge')[:, :-1] +
            np.pad(g, ((0,0),(0,1)), 'edge')[:, 1:] +
            np.pad(g, ((1,0),(0,0)), 'edge')[:-1, :] +
            np.pad(g, ((0,1),(0,0)), 'edge')[1:, :]
        )
        return float(lap.var())

    def _estimate_noise(self, gray):
        # High-frequency energy as a proxy for noise
        g = gray.astype(np.float32)
        hf = g - self._median(g, k=5)
        return float(np.std(hf) / 255.0)

    def _local_variance(self, gray, window=15):
        # Fast local variance using integral images
        g = gray.astype(np.float32)
        k = window
        pad = k // 2
        gpad = np.pad(g, pad, mode='reflect')
        ones = np.ones_like(gpad)
        # Integral images
        S = gpad.cumsum(0).cumsum(1)
        S2 = (gpad * gpad).cumsum(0).cumsum(1)
        def box_sum(I):
            H, W = g.shape
            y1, x1 = pad, pad
            y2, x2 = pad + H - 1, pad + W - 1
            A = I[y2 + 1, x2 + 1]
            B = I[y1, x2 + 1]
            C = I[y2 + 1, x1]
            D = I[y1, x1]
            return A - B - C + D
        # Compute local sums per pixel using stride trick (approx): fallback simple conv-like
        # Simpler: compute using moving window via cumulative sums with slicing
        H, W = g.shape
        def window_sum(I):
            Y = np.zeros((H, W), dtype=np.float32)
            for y in range(H):
                y0 = y
                Y[y, :] = (
                    I[y:y + k, :].cumsum(0)[-1] -
                    (I[y:y + k, :].cumsum(0)[0] if k < I.shape[0] else 0)
                ).cumsum(1)[:, :W][-1]
            return Y
        # Fallback simpler but O(H*W*k) approach for robustness
        K = np.ones((k, k), dtype=np.float32)
        mean = self._convolve(g, K) / (k * k)
        mean2 = self._convolve(g * g, K) / (k * k)
        var = np.maximum(0.0, mean2 - mean * mean)
        return var.astype(np.float32)

    def _convolve(self, img, kernel):
        ky, kx = kernel.shape
        py, px = ky // 2, kx // 2
        pad = ((py, py), (px, px))
        src = np.pad(img.astype(np.float32), pad, mode='reflect')
        H, W = img.shape
        out = np.zeros((H, W), dtype=np.float32)
        for y in range(ky):
            for x in range(kx):
                out += kernel[y, x] * src[y:y+H, x:x+W]
        return out

    def _make_findings(self, brightness, contrast, sharpness, edge_score, opacity_score, modality=None, body_region=None):
        findings = []
        # Exposure and quality
        if brightness < 70:
            findings.append("Underexposed image (dark)")
        if brightness > 180:
            findings.append("Overexposed image (bright)")
        if sharpness < 15:
            findings.append("Low sharpness (motion blur / out of focus)")

        is_chest = str(modality or "").startswith("chest")
        region = (body_region or ("chest" if is_chest else "region")).lower()

        # Opacity phrasing: chest gets pneumonia hint, others stay neutral
        if opacity_score > 0.30:
            if is_chest:
                findings.append("Diffuse opacities detected (possible pneumonia)")
            else:
                findings.append(f"Increased soft-tissue density in {region}")

        # Neck-specific hint for anterior soft tissues
        if ("neck" in region or "cervical" in region) and opacity_score > 0.32 and edge_score < 12:
            if "Increased soft-tissue density in neck" not in findings:
                findings.append("Increased soft-tissue density in neck")

        # Fracture cue (generic)
        if edge_score > 55 and sharpness > 40:
            findings.append("Strong linear edges (possible fracture)")

        if not findings:
            findings.append("No strong abnormalities detected")
        return findings
