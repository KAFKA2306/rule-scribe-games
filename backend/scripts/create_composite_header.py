import argparse
import os

from PIL import Image

CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 670
BG_COLOR = (255, 255, 255)


def create_composite_header(image_paths, output_path):
    print(f"Creating composite header with {len(image_paths)} images...")
    canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), BG_COLOR)
    loaded_images = []
    for p in image_paths:
        if os.path.exists(p):
            try:
                img = Image.open(p).convert("RGBA")
                loaded_images.append(img)
            except Exception as e:
                print(f"Error loading {p}: {e}")
        else:
            print(f"File not found: {p}")
    if not loaded_images:
        print("No images loaded.")
        return
    count = len(loaded_images)
    margin_x = 80
    available_width = CANVAS_WIDTH - (margin_x * 2)
    spacing = 40
    target_item_width = (available_width - (spacing * (count - 1))) / count
    max_item_height = 550
    resized_images = []
    for img in loaded_images:
        w, h = img.size
        aspect = w / h
        new_w = target_item_width
        new_h = new_w / aspect
        if new_h > max_item_height:
            new_h = max_item_height
            new_w = new_h * aspect
        resized_images.append(img.resize((int(new_w), int(new_h)), Image.Resampling.LANCZOS))
    total_content_width = sum(img.size[0] for img in resized_images) + (spacing * (count - 1))
    start_x = (CANVAS_WIDTH - total_content_width) // 2
    current_x = start_x
    for img in resized_images:
        y_pos = (CANVAS_HEIGHT - img.size[1]) // 2
        canvas.paste(img, (int(current_x), int(y_pos)), img)
        current_x += img.size[0] + spacing
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    canvas.save(output_path, "PNG")
    print(f"Saved composite header to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("images", nargs="+")
    args = parser.parse_args()
    create_composite_header(args.images, args.output)
