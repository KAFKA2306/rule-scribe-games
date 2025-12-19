import os
import glob
import shutil
from pathlib import Path
from PIL import Image

SOURCE_DIR = "/home/kafka/.gemini/antigravity/brain/76c2613c-a3c3-48ca-bf57-dcbf95fb5012"
TARGET_DIR = "/home/kafka/projects/rule-scribe-games/frontend/public/assets/games"

MAPPING = {
    "yokohama_duel": "yokohama-duel.webp",
    "fort_boardgame": "fort.webp",
    "hey_thats_my_fish": "hey-thats-my-fish.webp",
    "hackclad": "hackclad.webp",
    "istanbul_boardgame": "istanbul.webp",
    "high_society": "high-society.webp",
    "oriflamme": "oriflamme.webp",
    "bohnanza": "bohnanza.webp"
}

def process_images():
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR, exist_ok=True)
        print(f"Created directory: {TARGET_DIR}")

    files = glob.glob(os.path.join(SOURCE_DIR, "*.png"))
    
    for file_path in files:
        filename = os.path.basename(file_path)
        
        # Find matching key
        target_name = None
        for key, value in MAPPING.items():
            if key in filename:
                target_name = value
                break
        
        if target_name:
            target_path = os.path.join(TARGET_DIR, target_name)
            print(f"Processing {filename} -> {target_name}")
            
            try:
                with Image.open(file_path) as img:
                    img.save(target_path, "WEBP", quality=90)
                print(f"Success: {target_path}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")
        else:
            print(f"Skipping {filename} (no match)")

if __name__ == "__main__":
    process_images()
