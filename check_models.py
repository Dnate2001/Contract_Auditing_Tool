#!/usr/bin/env python3
"""
Check which Gemini models are available for your API key
"""

import google.generativeai as genai
import os

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ No API Key found in environment!")
    exit(1)

genai.configure(api_key=api_key)

print(f"🔍 Checking available models for key: {api_key[:10]}...")
try:
    # List all models that support 'generateContent'
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"   ✅ Available: {m.name}")
            available_models.append(m.name)
            
    if not available_models:
        print("❌ No models found! Your API key might be invalid or region-locked.")
    else:
        print("\n💡 ACTION: Update your ai_analyzer.py line:")
        print(f"   self.model = genai.GenerativeModel('{available_models[0].replace('models/', '')}')")

except Exception as e:
    print(f"❌ Error: {e}")
