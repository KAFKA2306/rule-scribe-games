from PIL import Image, ImageFilter
import argparse
import os
import glob

CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 670
# BG_COLOR = (245, 245, 240) # Off-white
BG_COLOR = (255, 255, 255) # White

def create_composite_header(image_paths, output_path):
    print(f"Creating composite header with {len(image_paths)} images...")
    
    # Base canvas
    canvas = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), BG_COLOR)
    
    loaded_images = []
    for p in image_paths:
        if os.path.exists(p):
            try:
                img = Image.open(p).convert('RGBA')
                loaded_images.append(img)
            except Exception as e:
                print(f"Error loading {p}: {e}")
        else:
            print(f"File not found: {p}")
            
    if not loaded_images:
        print("No images loaded.")
        return

    count = len(loaded_images)
    
    # Design Strategy:
    # Arrange images horizontally with equal spacing.
    # Max height = 500px, Max width per image = 1000px
    # Target total width = ~1100px leaving margins
    
    margin_x = 80
    available_width = CANVAS_WIDTH - (margin_x * 2)
    spacing = 40
    
    # Calculate optimal size
    # Total Width = (w * count) + (spacing * (count - 1)) = available_width
    # w * count = available_width - (spacing * (count - 1))
    # w = (available_width - (spacing * (count - 1))) / count
    
    target_item_width = (available_width - (spacing * (count - 1))) / count
    max_item_height = 550
    
    resized_images = []
    for img in loaded_images:
        # Resize preserving aspect ratio
        w, h = img.size
        aspect = w / h
        
        # Try adjusting by width first
        new_w = target_item_width
        new_h = new_w / aspect
        
        # If height is too tall, constrain by height
        if new_h > max_item_height:
            new_h = max_item_height
            new_w = new_h * aspect
            
        resized_images.append(img.resize((int(new_w), int(new_h)), Image.Resampling.LANCZOS))

    # Calculate total width of resized images to center them
    total_content_width = sum(img.size[0] for img in resized_images) + (spacing * (count - 1))
    start_x = (CANVAS_WIDTH - total_content_width) // 2
    
    current_x = start_x
    
    # Create a nice soft background using the first image blurred?
    # Optional: Gradient or blur background
    # Let's keep it clean white/off-white for Note.com simplicity, matches the site.
    
    for img in resized_images:
        # Center vertically
        y_pos = (CANVAS_HEIGHT - img.size[1]) // 2
        
        # Paste (using alphawhatever if needed, though they are likely rectangular covers)
        # Convert to RGBA for alpha composite if needed
        canvas.paste(img, (int(current_x), int(y_pos)), img)
        
        current_x += img.size[0] + spacing
        
    # Save
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    canvas.save(output_path, "PNG")
    print(f"Saved composite header to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("images", nargs="+")
    args = parser.parse_args()
    
    create_composite_header(args.images, args.output)
