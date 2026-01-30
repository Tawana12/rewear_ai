import google.generativeai as genai
from PIL import Image
import json
import os
from dotenv import load_dotenv

# Load the variables from your .env file
load_dotenv()

# Securely grab the key
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

def analyze_clothing_image(image_path):
    """
    AI Vision analysis using the secure GEMINI_API_KEY from .env.
    """
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment or .env file.")
        return {
            "category": "Error",
            "color": "None",
            "celeb_twin": "API Key Missing",
            "styling_tip": "Check your .env file."
        }

    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        img = Image.open(image_path)
        
        prompt = """
        Analyze this clothing item and return ONLY a JSON object.
        
        CRITICAL INSTRUCTIONS for 'celeb_twin': 
        - You MUST provide the name of a SPECIFIC famous celebrity, fashion icon, or musician.
        - EXAMPLES: 'Burna Boy', 'Rihanna', 'A$AP Rocky', 'Zendaya', 'Harry Styles', 'Wizkid', 'Billie Eilish'.
        - DO NOT use generic terms like 'Style Icon'. Be bold and specific.

        Return format:
        {
            "category": "e.g. Vintage Denim Jacket",
            "color": "e.g. Acid Wash Blue",
            "celeb_twin": "Name of Celebrity",
            "styling_tip": "One professional fashion tip"
        }
        """
        
        response = model.generate_content([prompt, img])
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        result = json.loads(clean_json)
        
        # Final safety check on generic AI responses
        if "Icon" in result.get('celeb_twin', ''):
            result['celeb_twin'] = "Fashion Trailblazer"
            
        return result
        
    except Exception as e:
        print(f"AI Vision Error: {e}")
        return {
            "category": "Clothing", 
            "color": "Unknown", 
            "celeb_twin": "Vibe Detected", 
            "styling_tip": "Keep it simple and let the item speak for itself."
        }