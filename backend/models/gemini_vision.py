import os
import io
import json
import re
from PIL import Image

try:
    import google.generativeai as genai
    GENAI_IMPORT_OK = True
except Exception:
    GENAI_IMPORT_OK = False


class GeminiVision:
    def __init__(self):
        self.model = None
        api_key = os.getenv("GEMINI_API_KEY")
        if not (GENAI_IMPORT_OK and api_key):
            return

        try:
            genai.configure(api_key=api_key)
            candidate_model_names = [
                "models/gemini-1.5-flash",
                "models/gemini-1.5-pro",
                "models/gemini-flash-latest",
                "models/gemini-2.5-flash",
                "models/gemini-2.0-flash",
                "models/gemini-pro-vision",
            ]
            for name in candidate_model_names:
                try:
                    model = genai.GenerativeModel(name)
                    _ = model.generate_content(["hello"], stream=True)
                    self.model = model
                    break
                except Exception:
                    continue
        except Exception:
            self.model = None

    def is_available(self):
        return self.model is not None

    def analyze(self, image):
        if not self.is_available():
            return None

        if not isinstance(image, Image.Image):
            return None

        try:
            img_bytes = io.BytesIO()
            image.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            img_part = {"mime_type": "image/png", "data": img_bytes.getvalue()}

            prompt = (
                "You are a radiology modality and quality assistant. "
                "Classify the image modality and body region, and list non-diagnostic, preliminary findings.\n\n"
                "Return STRICT JSON with keys: {\n"
                "  \"modality\": string one of ['chest-xray','non-chest-xray','ct','mri','document','other'],\n"
                "  \"body_region\": string (e.g., 'chest','dental','head','abdomen','unknown'),\n"
                "  \"is_chest_xray\": boolean,\n"
                "  \"is_dental\": boolean,\n"
                "  \"quality_issues\": [string],\n"
                "  \"preliminary_findings\": [string],\n"
                "  \"confidence\": number between 0 and 1\n"
                "}\n\n"
                "Rules:\n- Be conservative; DO NOT diagnose disease.\n- If panoramic dental pattern is seen, set is_dental=true and modality='non-chest-xray'.\n- If text/document, set modality='document'.\n- Keep findings short (phrases)."
            )

            resp = self.model.generate_content([prompt, img_part])
            text = (resp.text or "").strip()

            json_match = re.search(r"\{[\s\S]*\}", text)
            if not json_match:
                return None

            data = json.loads(json_match.group())
            return {
                "modality": data.get("modality", "other"),
                "body_region": data.get("body_region", "unknown"),
                "is_chest_xray": bool(data.get("is_chest_xray", False)),
                "is_dental": bool(data.get("is_dental", False)),
                "quality_issues": data.get("quality_issues", []) or [],
                "preliminary_findings": data.get("preliminary_findings", []) or [],
                "confidence": float(data.get("confidence", 0.8)),
            }
        except Exception:
            return None


# Singleton instance
gemini_vision = GeminiVision()


