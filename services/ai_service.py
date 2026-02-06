import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Initialize Client
# Note: User's example passes api_key directly. We fetch it from env.
# Support both GEMINI_API_KEY (used previously) and GOOGLE_API_KEY (standard for new SDK)
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

# Using the requested model or falling back to a standard one if 2.5 isn't public yet
MODEL_NAME = "gemini-2.5-flash" 

def analyze_financial_data(text_data):
    """
    Sends financial data text to Gemini and expects a specific JSON response.
    """
    prompt = f"""
    You are a professional financial analyst AI. Analyze the following financial data extracted from documents.
    
    Data:
    {text_data[:15000]}  # Increased context limit for newer models

    Provide a JSON response with the following structure:
    {{
        "creditScore": <integer between 300-900>,
        "confidence": <integer between 0-100>,
        "riskLevel": "<low|medium|high>",
        "totalRevenue": <float or 0 if not found>,
        "totalExpenses": <float or 0 if not found>,
        "netProfit": <float or 0 if not found>,
        "currentAssets": <float or 0>,
        "currentLiabilities": <float or 0>,
        "monthlyData": [
            {{ "month": "<Jan|Feb|...>", "revenue": <float>, "expenses": <float> }}
        ],
        "category": "<Retail|Tech|Services|Manufacturing|Other>",
        "industry": "<Software|E-commerce|Healthcare|Finance|Other>",
        "recommendations": [
            {{ "text": "<actionable advice>", "done": <boolean> }}
        ]
    }}
    
    Do not include any markdown formatting (like ```json), just the raw JSON string.
    """

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        
        # Clean response if it contains markdown
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        
        return json.loads(clean_text)
    except json.JSONDecodeError:
        # If model returned non-JSON text, return a structured error or raw text wrapping
        return {
            "creditScore": 0,
            "confidence": 0,
            "riskLevel": "unknown",
            "totalRevenue": 0,
            "totalExpenses": 0,
            "netProfit": 0,
            "currentAssets": 0,
            "currentLiabilities": 0,
            "monthlyData": [],
            "category": "Unknown",
            "industry": "Unknown",
            "recommendations": [{"text": "AI returned invalid JSON format", "done": False}],
            "raw_response": clean_text
        }
