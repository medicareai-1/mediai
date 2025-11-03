"""
LIME (Local Interpretable Model-agnostic Explanations) Module
Provides interpretable explanations for medical image predictions
"""

import numpy as np
from lime import lime_image
from PIL import Image
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from skimage.segmentation import mark_boundaries

class LIMEExplainer:
    """LIME explainer for CNN models"""
    
    def __init__(self):
        self.explainer = lime_image.LimeImageExplainer()
    
    def explain(self, image, model, prediction_class, num_samples=200, num_features=10):
        """
        Generate LIME explanation for a given image
        
        Args:
            image: PIL Image
            model: Trained CNN model
            prediction_class: Predicted class index
            num_samples: Number of samples for LIME (default: 200)
            num_features: Number of top features to show (default: 10)
            
        Returns:
            dict with LIME explanation and visualization
        """
        try:
            # Preprocess image
            img_array = self._preprocess_image(image)
            
            # Create prediction function wrapper
            def predict_fn(images):
                predictions = []
                for img in images:
                    # Add batch dimension if needed
                    if len(img.shape) == 3:
                        img = np.expand_dims(img, axis=0)
                    pred = model.predict(img, verbose=0)
                    predictions.append(pred[0])
                return np.array(predictions)
            
            # Generate LIME explanation
            explanation = self.explainer.explain_instance(
                img_array[0],
                predict_fn,
                top_labels=5,
                hide_color=0,
                num_samples=num_samples
            )
            
            # Generate visualizations
            visualization_positive = self._generate_visualization(
                img_array[0], 
                explanation, 
                prediction_class,
                positive_only=True,
                num_features=num_features
            )
            
            visualization_both = self._generate_visualization(
                img_array[0], 
                explanation, 
                prediction_class,
                positive_only=False,
                num_features=num_features
            )
            
            # Get feature weights
            feature_weights = self._get_feature_weights(
                explanation, 
                prediction_class
            )
            
            return {
                "explanation": explanation,
                "visualization_positive": visualization_positive,
                "visualization_both": visualization_both,
                "feature_weights": feature_weights,
                "method": "LIME",
                "num_samples": num_samples,
                "num_features": num_features
            }
            
        except Exception as e:
            print(f"LIME explanation error: {e}")
            return {
                "error": str(e),
                "visualization_positive": None,
                "visualization_both": None,
                "feature_weights": {}
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
    
    def _generate_visualization(self, img_array, explanation, prediction_class, 
                                positive_only=True, num_features=10):
        """Generate LIME visualization as base64 image"""
        try:
            # Get image and mask
            temp, mask = explanation.get_image_and_mask(
                prediction_class,
                positive_only=positive_only,
                num_features=num_features,
                hide_rest=False
            )
            
            # Create figure
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            
            # Original image
            axes[0].imshow(img_array)
            axes[0].set_title('Original Image')
            axes[0].axis('off')
            
            # LIME explanation with boundaries
            axes[1].imshow(mark_boundaries(temp, mask))
            title = 'LIME: Positive Features' if positive_only else 'LIME: All Features'
            axes[1].set_title(title)
            axes[1].axis('off')
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            print(f"LIME visualization error: {e}")
            return None
    
    def _get_feature_weights(self, explanation, prediction_class):
        """Extract feature weights from LIME explanation"""
        try:
            # Get local explanation for the predicted class
            local_exp = explanation.local_exp[prediction_class]
            
            # Sort by absolute weight
            sorted_exp = sorted(local_exp, key=lambda x: abs(x[1]), reverse=True)
            
            # Return top features with their weights
            feature_weights = {
                f"feature_{i}": {
                    "segment_id": int(feat[0]),
                    "weight": float(feat[1]),
                    "importance": "positive" if feat[1] > 0 else "negative"
                }
                for i, feat in enumerate(sorted_exp[:10])
            }
            
            return feature_weights
            
        except Exception as e:
            print(f"Feature weight extraction error: {e}")
            return {}


# Global instance
lime_explainer = LIMEExplainer()

