from diffsynth import save_video, ModelManager, SVDVideoPipeline, HunyuanDiTImagePipeline
from diffsynth import ModelManager
import torch, os


def generate_image():
    # Load models
    os.environ["TOKENIZERS_PARALLELISM"] = "True"
    model_manager = ModelManager(torch_dtype=torch.float16, device="cuda")
    model_manager.load_models([
        "models/HunyuanDiT/t2i/clip_text_encoder/pytorch_model.bin",
        "models/HunyuanDiT/t2i/mt5/pytorch_model.bin",
        "models/HunyuanDiT/t2i/model/pytorch_model_ema.pt",
        "models/HunyuanDiT/t2i/sdxl-vae-fp16-fix/diffusion_pytorch_model.bin"
    ])
    pipe = HunyuanDiTImagePipeline.from_model_manager(model_manager)

    # Generate an image
    torch.manual_seed(0)
    image = pipe(
        prompt="bonfire, on the stone",
        negative_prompt="错误的眼睛，糟糕的人脸，毁容，糟糕的艺术，变形，多余的肢体，模糊的颜色，模糊，重复，病态，残缺，",
        num_inference_steps=50, height=1024, width=1024,
    )
    return image


def generate_video(image):
    # Load models
    model_manager = ModelManager(torch_dtype=torch.float16, device="cuda")
    model_manager.load_models([
        "models/stable_video_diffusion/svd_xt.safetensors",
        "models/stable_video_diffusion/model.fp16.safetensors"
    ])
    pipe = SVDVideoPipeline.from_model_manager(model_manager)

    # Generate a video
    torch.manual_seed(1)
    video = pipe(
        input_image=image.resize((512, 512)),
        num_frames=128, fps=30, height=512, width=512,
        motion_bucket_id=127,
        num_inference_steps=50,
        min_cfg_scale=2, max_cfg_scale=2, contrast_enhance_scale=1.2
    )
    return video


def upscale_video(image, video):
    # Load models
    model_manager = ModelManager(torch_dtype=torch.float16, device="cuda")
    model_manager.load_models([
        "models/stable_video_diffusion/svd_xt.safetensors",
        "models/stable_video_diffusion/model.fp16.safetensors"
    ])
    pipe = SVDVideoPipeline.from_model_manager(model_manager)

    # Generate a video
    torch.manual_seed(2)
    video = pipe(
        input_image=image.resize((1024, 1024)),
        input_video=[frame.resize((1024, 1024)) for frame in video], denoising_strength=0.5,
        num_frames=128, fps=30, height=1024, width=1024,
        motion_bucket_id=127,
        num_inference_steps=25,
        min_cfg_scale=2, max_cfg_scale=2, contrast_enhance_scale=1.2
    )
    return video


# We use Hunyuan DiT to generate the first frame.
# If you want to use your own image,
# please use `image = Image.open("your_image_file.png")` to replace the following code.
image = generate_image()
image.save("image.png")

# Now, generate a video with resolution of 512.
video = generate_video(image)
save_video(video, "video_512.mp4", fps=30)

# Upscale the video.
video = upscale_video(image, video)
save_video(video, "video_1024.mp4", fps=30)