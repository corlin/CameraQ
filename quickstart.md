# CameraQ - Quickstart

This quickstart guide demonstrates how to validate the core functionality of the CameraQ MVP (Stage 1 Offline Demo).

## Prerequisites
- Python 3.11+
- `uv` package manager (recommended) or `pip`
- A test image containing a person or object with poor composition (e.g., tilted horizon, cropped head).

## Setup
1. Clone the repository and navigate to the project directory.
2. Install dependencies:
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```
3. Download the YOLO11 weights (will be handled automatically by Ultralytics on first run).

## Run the Demo
1. Start the Gradio Web UI:
   ```bash
   python src/app.py
   ```
2. Open the provided local URL (e.g., `http://127.0.0.1:7860`) in your browser.
3. Upload your test image.
4. View the results:
   - **Processed Image**: Shows the detected subject box, rule-of-thirds grid, and horizon line.
   - **Feedback**: A single actionable tip (e.g., "画面向右倾斜，稍微顺时针调整。")
   - **Score**: A composition score out of 100.
   - **Recommended Crops**: 3 suggested cropped versions of your image.
