import os
from PIL import Image
import glob


def optimize_images():
    source_dir = "frontend/public/assets/games"
    files = glob.glob(os.path.join(source_dir, "*.png"))

    print(f"Found {len(files)} PNG images.")

    for file_path in files:
        try:
            with Image.open(file_path) as img:
                # Resize if width > 400
                if img.width > 400:
                    ratio = 400 / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((400, new_height), Image.Resampling.LANCZOS)

                # Save as WebP
                base_name = os.path.splitext(file_path)[0]
                new_path = f"{base_name}.webp"
                img.save(new_path, "WEBP", quality=80)

                print(
                    f"Converted: {os.path.basename(file_path)} -> {os.path.basename(new_path)}"
                )

            # Remove original png
            os.remove(file_path)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")


if __name__ == "__main__":
    optimize_images()
