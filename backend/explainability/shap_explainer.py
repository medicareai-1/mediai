"""
SHAP (SHapley Additive exPlanations) Explainability Module
Provides model-agnostic explanations for medical image predictions
"""

import numpy as np
import shap
from PIL import Image
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

class SHAPExplainer:
    """SHAP explainer for CNN models"""
    
    def __init__(self):
        self.explainer = None
    
    def explain(self, image, model, prediction_class, num_samples=100):
        """
        Generate SHAP explanation for a given image
        
        Args:
            image: PIL Image
            model: Trained CNN model
            prediction_class: Predicted class index
            num_samples: Number of samples for SHAP (default: 100)
            
        Returns:
            dict with SHAP values and visualization
        """
        try:
            # Preprocess image
            img_array = self._preprocess_image(image)
            
            # Create prediction function wrapper
            def predict_fn(x):
                # Convert from SHAP format to model input format
                predictions = []
                for img in x:
                    # Reshape if needed
                    if len(img.shape) == 3:
                        img = np.expand_dims(img, axis=0)
                    pred = model.predict(img, verbose=0)
                    predictions.append(pred[0])
                return np.array(predictions)
            
            # Create background dataset (mean image)
            background = np.zeros_like(img_array)
            
            # Initialize SHAP explainer with KernelExplainer (model-agnostic)
            self.explainer = shap.KernelExplainer(
                predict_fn, 
                background,
                link="identity"
            )
            
            # Calculate SHAP values
            shap_values = self.explainer.shap_values(
                img_array,
                nsamples=num_samples
            )
            
            # Generate visualization
            visualization = self._generate_visualization(
                image, 
                shap_values, 
                prediction_class
            )
            
            # Calculate feature importance
            importance_scores = self._calculate_importance(shap_values, prediction_class)
            
            return {
                "shap_values": shap_values,
                "visualization": visualization,
                "importance_scores": importance_scores,
                "method": "SHAP KernelExplainer",
                "num_samples": num_samples
            }
            
        except Exception as e:
            print(f"SHAP explanation error: {e}")
            return {
                "error": str(e),
                "visualization": None,
                "importance_scores": {}
            }
    
    def _preprocess_image(self, image):
        """Preprocess image for model input"""
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize to model input size
        image = image.resize((224, 224))
        
        # Convert to array and normalize
        img_array = np.array(image) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array
    
    def _generate_visualization(self, original_image, shap_values, prediction_class):
        """Generate SHAP visualization as base64 image"""
        try:
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            
            # Original image
            axes[0].imshow(original_image)
            axes[0].set_title('Original Image')
            axes[0].axis('off')
            
            # SHAP overlay
            if isinstance(shap_values, list):
                # Multi-class output
                shap_img = shap_values[prediction_class][0]
            else:
                # Single output
                shap_img = shap_values[0]
            
            # Normalize SHAP values for visualization
            shap_img = np.mean(np.abs(shap_img), axis=-1)
            
            im = axes[1].imshow(shap_img, cmap='hot', alpha=0.8)
            axes[1].imshow(original_image.resize((224, 224)), alpha=0.3)
            axes[1].set_title('SHAP Feature Importance')
            axes[1].axis('off')
            
            plt.colorbar(im, ax=axes[1], fraction=0.046, pad=0.04)
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            print(f"SHAP visualization error: {e}")
            return None
    
    def _calculate_importance(self, shap_values, prediction_class):
        """Calculate feature importance scores"""
        try:
            if isinstance(shap_values, list):
                values = shap_values[prediction_class][0]
            else:
                values = shap_values[0]
            
            # Calculate regional importance (divide image into quadrants)
            h, w = values.shape[:2]
            mid_h, mid_w = h // 2, w // 2
            
            quadrants = {
                "top_left": np.mean(np.abs(values[:mid_h, :mid_w])),
                "top_right": np.mean(np.abs(values[:mid_h, mid_w:])),
                "bottom_left": np.mean(np.abs(values[mid_h:, :mid_w])),
                "bottom_right": np.mean(np.abs(values[mid_h:, mid_w:])),
                "center": np.mean(np.abs(values[mid_h//2:mid_h+mid_h//2, mid_w//2:mid_w+mid_w//2]))
            }
            
            # Normalize to percentages
            total = sum(quadrants.values())
            if total > 0:
                quadrants = {k: float(v/total * 100) for k, v in quadrants.items()}
            
            return quadrants
            
        except Exception as e:
            print(f"Importance calculation error: {e}")
            return {}


# Global instance
shap_explainer = SHAPExplainer()

