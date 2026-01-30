import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("HF_TOKEN")

# Initialize the client
client = InferenceClient(api_key=token)

def test_hf_official():
    img_path = "download (2).jpg" 

    if not os.path.exists(img_path):
        print(f"❌ Error: Image '{img_path}' not found!")
        return

    print(f"🚀 Sending image to Hugging Face via Official Client...")

    try:
        # We'll use a very stable model: Salesforce BLIP
        # It's great for basic category/color identification
        model_id = "Salesforce/blip-image-captioning-large"
        
        # Open and send image
        with open(img_path, "rb") as f:
            image_data = f.read()
            
        # 1. Get basic description
        description = client.image_to_text(image_data, model=model_id)
        
        print("\n--- TEST RESULT ---")
        print(f"AI Description: {description}")
        print("-------------------\n")
        print("🎉 SUCCESS! The connection is working.")

    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    if not token:
        print("❌ ERROR: No HF_TOKEN found in .env!")
    else:
        test_hf_official()