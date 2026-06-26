import sys
from pathlib import Path
import gradio as gr
import cv2
import numpy as np

# Add src to python path so we can import core
src_path = Path(__file__).parent.parent
sys.path.append(str(src_path))

from core.analyzer import CameraQAnalyzer

analyzer = CameraQAnalyzer()

def analyze_image(input_image):
    if input_image is None:
        return None, "请上传图片", 0, None, None, None
        
    try:
        # Convert PIL image/numpy array to BGR for OpenCV
        if len(input_image.shape) == 3 and input_image.shape[2] == 3:
            # Gradio passes RGB numpy arrays
            img_bgr = cv2.cvtColor(input_image, cv2.COLOR_RGB2BGR)
        else:
            img_bgr = input_image
            
        result = analyzer.process_frame(img_bgr)
        
        # Format the feedback
        feedback = f"### 构图建议\n**{result.feedback_message}**"
        
        # Format score
        score = result.score
        
        # Convert output image from BGR back to RGB for Gradio
        if result.image_with_overlays is not None:
            out_img = cv2.cvtColor(result.image_with_overlays, cv2.COLOR_BGR2RGB)
        else:
            out_img = input_image
        
        # Crop recommendations
        crops_images = [None, None, None]
        for i, crop_rec in enumerate(result.recommended_crops[:3]):
            box = crop_rec.bounding_box
            x1, y1 = int(box.x), int(box.y)
            x2, y2 = int(box.x + box.width), int(box.y + box.height)
            # Ensure coordinates are within bounds
            x1 = max(0, min(x1, input_image.shape[1] - 1))
            x2 = max(0, min(x2, input_image.shape[1]))
            y1 = max(0, min(y1, input_image.shape[0] - 1))
            y2 = max(0, min(y2, input_image.shape[0]))
            
            cropped_img = input_image[y1:y2, x1:x2]
            crops_images[i] = cropped_img
            
        crop1, crop2, crop3 = crops_images
        
        return out_img, feedback, score, crop1, crop2, crop3
        
    except Exception as e:
        return input_image, f"分析出错: {str(e)}", 0, None, None, None

# Gradio Interface
with gr.Blocks(title="CameraQ - 构图智能助手") as demo:
    gr.Markdown("# CameraQ 实时摄影构图智能助手 (MVP)")
    gr.Markdown("上传一张照片，系统将自动分析画面构图，并给出优化建议。")
    
    with gr.Row():
        with gr.Column(scale=1):
            input_img = gr.Image(label="上传照片", type="numpy")
            analyze_btn = gr.Button("分析构图", variant="primary")
            
        with gr.Column(scale=1):
            output_img = gr.Image(label="分析结果")
            feedback_text = gr.Markdown("等待分析...")
            score_bar = gr.Slider(minimum=0, maximum=100, label="构图评分", interactive=False)
            
    with gr.Row():
        gr.Markdown("### 推荐裁切")
    with gr.Row():
        crop_1_img = gr.Image(label="推荐裁切 1")
        crop_2_img = gr.Image(label="推荐裁切 2")
        crop_3_img = gr.Image(label="推荐裁切 3")
        
    analyze_btn.click(
        fn=analyze_image,
        inputs=input_img,
        outputs=[output_img, feedback_text, score_bar, crop_1_img, crop_2_img, crop_3_img]
    )

if __name__ == "__main__":
    demo.launch()
