"""
Quick verification that Gemini API is working correctly
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env
load_dotenv()

print("\n" + "="*60)
print("🔍 GEMINI API VERIFICATION")
print("="*60 + "\n")

# Check API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ GEMINI_API_KEY not found in environment!")
    print("   Make sure it's in your .env file")
    exit(1)

print(f"✅ API Key found: {api_key[:10]}...{api_key[-5:]}\n")

# Configure
try:
    genai.configure(api_key=api_key)
    print("✅ API configured successfully\n")
except Exception as e:
    print(f"❌ Failed to configure API: {e}")
    exit(1)

# List available models
print("📋 Available models:")
print("-" * 60)
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"  ✅ {m.name}")
    print()
except Exception as e:
    print(f"❌ Failed to list models: {e}\n")

# Test model initialization
print("🧪 Testing model initialization:")
print("-" * 60)

for model_name in ["models/gemini-1.5-flash", "models/gemini-1.5-pro"]:
    try:
        model = genai.GenerativeModel(model_name)
        print(f"  ✅ {model_name} - SUCCESS!")
    except Exception as e:
        print(f"  ❌ {model_name} - FAILED: {e}")

print("\n" + "="*60)
print("✅ VERIFICATION COMPLETE!")
print("="*60 + "\n")

