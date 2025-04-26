# backend/main.py
"""
- Serves API endpoint `/process_dream`.
- Uses Hugging Face for sentiment/keywords (in executor).
- Uses OpenAI ONLY for interpretation (via async client).
- Silences tokenizer parallelism warning.
- Async optimizations applied.
"""
import os
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn
import numpy as np

# --- AI Library Imports ---
from transformers import pipeline
from openai import AsyncOpenAI # Import the async client

# --- Environment Variable Setup ---
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# --- Initialization and Model/Client Loading ---
print("Initializing application and loading models/clients...")
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key: print("CRITICAL: OpenAI API key not found.")

# --- OpenAI Async Client ---
async_openai_client = AsyncOpenAI(api_key=openai_api_key)

# --- Hugging Face Model Loading ---
try:
    sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    dream_themes = ["flying", "falling", "being chased", "teeth falling out", "water", "school", "public nudity", "transportation", "death", "magic", "talking animals"]
    keyword_extractor = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    print("Hugging Face models loaded successfully.")
except Exception as e:
    print(f"CRITICAL: Error loading Hugging Face models: {e}")
    sentiment_analyzer = None
    keyword_extractor = None

# --- SYNCHRONOUS AI Helper Function (for Executor) ---
def analyze_hf_sync(text: str):
    """Synchronous function to perform HF analysis."""
    # (Implementation unchanged)
    if not sentiment_analyzer or not keyword_extractor: return {'sentiment_label': 'N/A', 'sentiment_score': 0.0, 'keywords': ['Analysis unavailable']}
    if not text: return {'sentiment_label': 'N/A', 'sentiment_score': 0.0, 'keywords': ['No text']}
    try:
        sentiment = sentiment_analyzer(text)[0]
        keywords_raw = keyword_extractor(text, dream_themes, multi_label=True)
        threshold = 0.6
        keywords = [ lbl for lbl, score in zip(keywords_raw['labels'], keywords_raw['scores']) if score > threshold ] or ["None detected"]
        return { 'sentiment_label': sentiment['label'], 'sentiment_score': round(sentiment['score'], 3), 'keywords': keywords }
    except Exception as e: print(f"Error during HF analysis: {e}"); return {'sentiment_label': 'Error', 'sentiment_score': 0.0, 'keywords': ['Analysis error']}

# --- ASYNCHRONOUS AI Helper Function (Interpretation ONLY) ---
async def coro_get_interpretation(text: str, sentiment: str, keywords: list):
    """Async Coroutine: Generates interpretation via AsyncOpenAI client."""
    # (Implementation unchanged, except removed the sibling image prompt coro)
    if not async_openai_client.api_key or not text: return "OpenAI key missing or no text."
    keyword_str = ", ".join(keywords) if keywords and keywords[0] not in ["None detected", "Analysis unavailable", "Analysis error"] else "general dream themes"
    interp_prompt = f"""Disclaimer: For entertainment only. Dream: "{text}" Sentiment: {sentiment}. Themes: {keyword_str}. Provide a brief (2-3 sentence) symbolic interpretation:"""
    try:
        response = await async_openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[ {"role": "system", "content": "You interpret dream symbols creatively for fun."}, {"role": "user", "content": interp_prompt} ],
            max_tokens=100, temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e: print(f"OpenAI Interpretation Coroutine Error: {e}"); return f"API error during interpretation: {type(e).__name__}"

# --- Pydantic Models (Removed image_prompt) ---
class DreamRequest(BaseModel):
    dream_text: str

class DreamResponse(BaseModel):
    sentiment_label: str = "N/A"
    sentiment_score: float = 0.0
    keywords: list[str] = []
    interpretation: str = "Processing..."
    # image_prompt field REMOVED
    error: str | None = None

# --- FastAPI App Setup ---
app = FastAPI(title="AI Dream Interpreter API (Interpretation Only)", version="1.2.0")
origins = ["http://localhost:3000", "http://localhost:5173"]
app.add_middleware( CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"], )

# --- Optimized API Endpoint (Simplified for Interpretation Only) ---
@app.post("/process_dream", response_model=DreamResponse)
async def process_dream_endpoint(request: DreamRequest):
    """Endpoint processes dream text for analysis and interpretation."""
    dream_text = request.dream_text
    MAX_LENGTH = 1200
    if not dream_text or not dream_text.strip(): raise HTTPException(status_code=400, detail="Dream text required.")
    if len(dream_text) > MAX_LENGTH: raise HTTPException(status_code=413, detail=f"Text too long (max {MAX_LENGTH} chars).")

    response_data = DreamResponse()
    overall_error = None
    loop = asyncio.get_running_loop()

    # 1. Run HF analysis in executor
    try:
        hf_results = await loop.run_in_executor(None, analyze_hf_sync, dream_text)
    except Exception as e:
        print(f"Error running HF analysis in executor: {e}")
        hf_results = {'sentiment_label': 'Error', 'sentiment_score': 0.0, 'keywords': ['Analysis failed']}

    response_data.sentiment_label = hf_results.get('sentiment_label', 'Error')
    response_data.sentiment_score = hf_results.get('sentiment_score', 0.0)
    response_data.keywords = hf_results.get('keywords', ['Analysis failed'])
    if "error" in response_data.sentiment_label.lower() or "fail" in response_data.keywords[0].lower():
        overall_error = "HF analysis failed. "

    # Prepare context for OpenAI
    sentiment_for_openai = response_data.sentiment_label if "error" not in response_data.sentiment_label.lower() else "Neutral"
    keywords_for_openai = response_data.keywords if "error" not in response_data.keywords[0].lower() and "fail" not in response_data.keywords[0].lower() else []

    # 2. Run ONLY OpenAI interpretation call
    try:
        # Directly await the single coroutine
        interpretation_result = await coro_get_interpretation(dream_text, sentiment_for_openai, keywords_for_openai)

        if isinstance(interpretation_result, Exception): # Should not happen if coro handles exceptions, but belt-and-suspenders
             raise interpretation_result
        elif "API error" in interpretation_result or "OpenAI key missing" in interpretation_result:
             response_data.interpretation = interpretation_result # Show error from coro
             if overall_error: overall_error += " OpenAI Interpretation Error."
             else: overall_error = "OpenAI Interpretation Error."
        else:
             response_data.interpretation = interpretation_result

    except Exception as e:
        print(f"Error during OpenAI interpretation call: {e}")
        response_data.interpretation = "System error during OpenAI interpretation."
        if overall_error: overall_error += " OpenAI processing error."
        else: overall_error = "OpenAI processing error."

    response_data.error = overall_error
    return response_data

# --- Root Endpoint ---
@app.get("/")
async def root():
    return {"message": "AI Dream Interpreter API (Interpretation Only) is running."}

# --- Run Command ---
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)