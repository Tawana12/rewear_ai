import os
import json
import urllib.parse
import google.generativeai as genai
from flask import Blueprint, render_template, request, flash, redirect, url_for
from rewear_ai.wardrobe.models import ClothingItem
from rewear_ai.app import db

upcycle = Blueprint('upcycle', __name__, template_folder='templates')

@upcycle.route('/item/<int:item_id>')
def upcycle_item(item_id):
    # Fetch the specific item from the database
    item = ClothingItem.query.get_or_404(item_id)
    
    # Configure Gemini 1.5 Flash
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # The Prompt: Structured for a clean JSON response
    prompt = f"""
    Create a creative upcycling project for a {item.color} {item.category}.
    The item is old or damaged. Provide a project name, difficulty level (Easy, Medium, or Hard), 
    and a list of 4 clear, actionable steps.
    
    Return ONLY a JSON object:
    {{
        "project_name": "...",
        "difficulty": "...",
        "steps": ["Step 1", "Step 2", "Step 3", "Step 4"]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        # Clean potential markdown formatting from AI response
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        recipe = json.loads(clean_json)
    except Exception as e:
        print(f"Upcycle AI Error: {e}")
        # Robust fallback if AI or JSON parsing fails
        recipe = {
            "project_name": "Custom Style Transformation",
            "difficulty": "Medium",
            "steps": [
                "Evaluate the current condition of the fabric.",
                "Mark out a new pattern based on your needs.",
                "Carefully cut and sew edges to prevent fraying.",
                "Add personal embellishments for a unique finish."
            ]
        }

    # Generate the Dynamic YouTube Search Link
    yt_query = f"DIY upcycle {item.category} into {recipe['project_name']} tutorial"
    encoded_query = urllib.parse.quote(yt_query)
    youtube_url = f"https://www.youtube.com/results?search_query={encoded_query}"

    return render_template(
        'upcycle/idea.html', 
        item=item, 
        recipe=recipe, 
        youtube_url=youtube_url
    )