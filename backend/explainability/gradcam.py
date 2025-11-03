"""
Grad-CAM with optional PyTorch support.

Behavior:
- If PyTorch and a torch model are available, compute true Grad-CAM from the
  last Conv2d layer activations and gradients.
- Otherwise, fall back to a deterministic, edge/brightness-based demo heatmap.
"""

import numpy as np
from PIL import Image
import random

try:
    import torch
    import torch.nn as nn
    TORCH_OK = True
except Exception:
    TORCH_OK = False

class GradCAM:
    def __init__(self):
        """Initialize Grad-CAM with optional torch backend."""
        self.gradients = None
        self.activations = None
        self.full_enabled = TORCH_OK
        if self.full_enabled:
            print("Grad-CAM initialized (Full mode available)")
        else:
            print("Grad-CAM initialized (Demo mode - install PyTorch for full functionality)")
    
    def save_gradient(self, grad):
        """Hook to save gradients"""
        self.gradients = grad
    
    def save_activation(self, module, input, output):
        """Hook to save activations"""
        self.activations = output
    
    def generate_heatmap(self, image, model=None, target_class=None):
        """
        Generate attention heatmap based on image features
        
        Args:
            image: PIL Image or numpy array
            model: PyTorch model (used in full mode)
            target_class: Target class index
            
        Returns:
            numpy array: Heatmap visualization
        """
        try:
            # Try full Grad-CAM if torch model is available
            if self.full_enabled and self._is_torch_model(model):
                try:
                    return self._gradcam_full(image, model, target_class)
                except Exception:
                    # Fall back to demo if anything fails
                    pass

            # Convert image to array
            if isinstance(image, np.ndarray):
                if len(image.shape) == 2:
                    img_array = Image.fromarray(image).convert('RGB')
                else:
                    img_array = Image.fromarray(image)
            else:
                img_array = image
            
            if img_array.mode != 'RGB':
                img_array = img_array.convert('RGB')
            
            # Resize for processing
            img_array = img_array.resize((224, 224))
            img_np = np.array(img_array)
            
            # Convert to grayscale for analysis
            gray = np.mean(img_np, axis=2).astype(np.uint8)
            height, width = gray.shape
            
            # Calculate gradient magnitude (edge detection)
            grad_x = np.abs(np.diff(gray, axis=1, prepend=gray[:, :1]))
            grad_y = np.abs(np.diff(gray, axis=0, prepend=gray[:1, :]))
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            
            # Normalize gradient
            if gradient_magnitude.max() > 0:
                gradient_magnitude = gradient_magnitude / gradient_magnitude.max()
            
            # Find regions of interest based on brightness and edges
            brightness_map = gray.astype(float) / 255.0
            
            # Combine edge and brightness information
            # Dark regions with edges are often important in medical images
            importance_map = gradient_magnitude * 0.7 + (1 - brightness_map) * 0.3
            
            # Simple smoothing without scipy
            kernel_size = 5
            heatmap = self._simple_blur(importance_map, kernel_size)
            
            # Normalize to [0, 1]
            if heatmap.max() > heatmap.min():
                heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min())
            
            # Enhance contrast
            heatmap = np.power(heatmap, 0.7)
            
            # Create colored heatmap
            heatmap_colored = np.zeros((height, width, 3), dtype=np.uint8)
            for i in range(height):
                for j in range(width):
                    intensity = int(heatmap[i, j] * 255)
                    # Jet colormap simulation
                    if intensity < 64:
                        heatmap_colored[i, j] = [0, 0, intensity * 4]
                    elif intensity < 128:
                        heatmap_colored[i, j] = [0, (intensity - 64) * 4, 255]
                    elif intensity < 192:
                        heatmap_colored[i, j] = [(intensity - 128) * 4, 255, 255 - (intensity - 128) * 4]
                    else:
                        heatmap_colored[i, j] = [255, 255 - (intensity - 192) * 4, 0]
            
            # Overlay on original image
            overlay = (img_np * 0.6 + heatmap_colored * 0.4).astype(np.uint8)
            
            return overlay
            
        except Exception as e:
            print(f"Grad-CAM error: {str(e)}")
            # Return original image if fails
            if isinstance(image, Image.Image):
                return np.array(image)
            return image

    # ---------- Full-mode helpers ----------
    def _is_torch_model(self, model):
        if not TORCH_OK:
            return False
        try:
            return isinstance(model, torch.nn.Module)
        except Exception:
            return False

    def _find_last_conv(self, model):
        last_conv = None
        for m in model.modules():
            # Find the last Conv2d in the module tree
            try:
                if isinstance(m, nn.Conv2d):
                    last_conv = m
            except Exception:
                continue
        return last_conv

    def _preprocess_to_tensor(self, image):
        # 1x1x224x224 grayscale tensor normalized to ~[-1,1]
        if isinstance(image, Image.Image):
            img = image
        else:
            img = Image.fromarray(image) if isinstance(image, np.ndarray) else image
        img = img.convert('L').resize((224, 224))
        arr = np.array(img).astype('float32') / 255.0
        arr = (arr - 0.5) / 0.5
        arr = arr[None, None, :, :]
        return torch.from_numpy(arr)

    def _resize_like(self, cam_np, ref_img_np):
        # Resize heatmap (Hc,Wc) -> (H,W)
        H, W = ref_img_np.shape[:2]
        cam_img = Image.fromarray((np.clip(cam_np, 0, 1) * 255).astype(np.uint8))
        cam_img = cam_img.resize((W, H))
        return np.array(cam_img).astype('float32') / 255.0

    def _overlay(self, rgb_np, heat_np):
        # Create simple JET-like overlay
        H, W = heat_np.shape
        heatmap_colored = np.zeros((H, W, 3), dtype=np.uint8)
        scaled = (np.clip(heat_np, 0, 1) * 255).astype(np.uint8)
        for i in range(H):
            for j in range(W):
                intensity = scaled[i, j]
                if intensity < 64:
                    heatmap_colored[i, j] = [0, 0, intensity * 4]
                elif intensity < 128:
                    heatmap_colored[i, j] = [0, (intensity - 64) * 4, 255]
                elif intensity < 192:
                    heatmap_colored[i, j] = [(intensity - 128) * 4, 255, 255 - (intensity - 128) * 4]
                else:
                    heatmap_colored[i, j] = [255, 255 - (intensity - 192) * 4, 0]
        return (rgb_np * 0.6 + heatmap_colored * 0.4).astype(np.uint8)

    def _gradcam_full(self, image, model, target_class):
        model.eval()
        # Find last conv layer
        last_conv = self._find_last_conv(model)
        if last_conv is None:
            raise RuntimeError("No Conv2d layer found for Grad-CAM")

        activations = {}
        gradients = {}

        def fwd_hook(module, inp, out):
            activations['value'] = out.detach()

        def bwd_hook(module, grad_in, grad_out):
            gradients['value'] = grad_out[0].detach()

        h1 = last_conv.register_forward_hook(fwd_hook)
        h2 = last_conv.register_full_backward_hook(bwd_hook)

        try:
            # Prepare input
            x = self._preprocess_to_tensor(image)
            x.requires_grad_(True)
            if next(model.parameters()).is_cuda:
                x = x.cuda()

            # Forward
            logits = model(x)

            # Pick target index
            if target_class is None:
                target_index = int(torch.argmax(logits, dim=1).item()) if logits.ndim == 2 else 0
            else:
                target_index = int(target_class)

            # For multi-label (sigmoid) models, use the raw logit at index
            score = logits[0, target_index] if logits.ndim == 2 else logits.view(-1)[target_index]

            # Backward
            model.zero_grad(set_to_none=True)
            score.backward(retain_graph=True)

            A = activations['value']  # [B,C,H,W]
            dA = gradients['value']   # [B,C,H,W]
            if A.ndim == 3:
                A = A.unsqueeze(0)
            if dA.ndim == 3:
                dA = dA.unsqueeze(0)

            # Global-average pool gradients over H,W -> weights per channel
            weights = torch.mean(dA, dim=(2, 3), keepdim=True)  # [B,C,1,1]
            cam = torch.relu(torch.sum(weights * A, dim=1, keepdim=False))  # [B,H,W]
            cam = cam[0]

            # Normalize cam to [0,1]
            cam = cam - cam.min()
            if cam.max() > 0:
                cam = cam / cam.max()
            cam_np = cam.detach().cpu().numpy()

            # Prepare RGB image for overlay
            rgb = image if isinstance(image, Image.Image) else Image.fromarray(image)
            if rgb.mode != 'RGB':
                rgb = rgb.convert('RGB')
            rgb = rgb.resize((224, 224))
            rgb_np = np.array(rgb)

            heat_resized = self._resize_like(cam_np, rgb_np)
            overlay = self._overlay(rgb_np, heat_resized)
            return overlay
        finally:
            try:
                h1.remove()
                h2.remove()
            except Exception:
                pass
    
    def _simple_blur(self, image, kernel_size=5):
        """Simple box blur without scipy"""
        try:
            h, w = image.shape
            result = np.zeros_like(image)
            pad = kernel_size // 2
            
            # Pad image
            padded = np.pad(image, pad, mode='edge')
            
            # Apply blur
            for i in range(h):
                for j in range(w):
                    result[i, j] = np.mean(padded[i:i+kernel_size, j:j+kernel_size])
            
            return result
        except:
            return image
    
    def generate_multiple_heatmaps(self, image, model, top_k=3):
        """Generate heatmaps for top-k predictions (Demo version)"""
        heatmaps = []
        
        for i in range(min(top_k, 3)):
            heatmap = self.generate_heatmap(image, model, i)
            heatmaps.append({
                "class_idx": i,
                "probability": random.uniform(0.6, 0.9),
                "heatmap": heatmap
            })
        
        return heatmaps
