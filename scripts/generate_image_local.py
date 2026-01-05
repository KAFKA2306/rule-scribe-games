import argparse
import torch
from diffusers import DiffusionPipeline
from pathlib import Path
import os

MODEL_ID = "Tongyi-MAI/Z-Image-Turbo"


def generate_image(
    prompt: str, output_path: str, width: int = 1024, height: int = 1024
):
    print(f"Loading model: {MODEL_ID}")

    from diffusers import AutoencoderKL

    print("Loading VAE fix...")
    vae = AutoencoderKL.from_pretrained(
        "madebyollin/sdxl-vae-fp16-fix", torch_dtype=torch.float16
    )
    if not hasattr(vae.config, "shift_factor") or vae.config.shift_factor is None:
        vae.config.shift_factor = 0.0

    pipe = DiffusionPipeline.from_pretrained(
        MODEL_ID, vae=vae, torch_dtype=torch.float16, device_map="cuda"
    )
    # VAE fixを使えばcastは不要だが念の為無効化
    # pipe.vae.to(dtype=torch.float32)

    # Optimization - Removed incompatible with ZImagePipeline
    # pipe.unet.to(memory_format=torch.channels_last)

    full_prompt = (
        "(masterpiece), (best quality), (aesthetic), (absurdres), "
        f"{prompt}, "
        "(rating:safe)"
    )

    negative_prompt = "(worst quality, low quality:1.4), (grayscale)"

    print(f"Generating image...")

    image = pipe(
        prompt=full_prompt,
        negative_prompt=negative_prompt,
        width=width,
        height=height,
        guidance_scale=7.0,
        num_inference_steps=8,
    ).images[0]

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    image.save(output_path)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", type=str)
    parser.add_argument("output", type=str)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=670)

    args = parser.parse_args()
    generate_image(args.prompt, args.output, args.width, args.height)
