# CameraQ

CameraQ is an intelligent photography assistant designed to analyze image composition and provide real-time feedback using advanced AI models.

## Features

- 📸 **Real-time Composition Scoring**: Evaluates framing in real-time via a 5-axis model (Subject, Structure, Balance, Interference, Style) and presents visual feedback.
- 🤖 **Generative AI Coaching**: Integrates Gemini 2.5 Flash for contextual, stylistic, and emotional photography tips directly from the viewfinder.
- 👁️ **Advanced Computer Vision**: Leverages YOLO11 for object and human pose detection, alongside visual saliency mapping to identify the natural focal points of an image.
- 📐 **Dynamic Aesthetic Rules**: Automatically detects rule-of-thirds alignment, horizon leveling, color harmony, over/under exposure, and background interference.
- ⚙️ **Pro Settings Dashboard**: Interactive sliding side panel with granular control over AI sampling rates, analysis throttling to optimize FPS, and module toggles.

## Roadmap

- [x] **Stage 1 (Offline MVP)**: Process local images with basic Saliency & YOLO detection, and output static compositional score/feedback.
- [x] **Stage 2 (Real-time Viewfinder)**: Live video feed integration, threaded processing, and basic UI overlays.
- [x] **Stage 3 (Advanced Aesthetics & Tracking)**: Lighting/color analysis (overexposed/underexposed warnings) and dynamic subject tracking for shutter timing predictions.
- [x] **Stage 4 (Generative AI Guide)**: Gemini multimodal integration for contextual, stylistic photography coaching.
- [x] **Stage 5 (UI/UX Polish)**: Translucent, elegant visual overlays with dynamic AI prompt lifecycles.
- [x] **Stage 6 (Pro Optimization)**: Multi-dimensional scoring (5-axis radar), performance throttling (FPS > 25), sliding settings sidebar, and graceful API degradation.

## Running the App

### Real-time Viewfinder (Stage 4)
To launch the real-time camera assistant with AI Coaching enabled:
```bash
export GEMINI_API_KEY="your_api_key_here"  # Optional, but required for AI Coaching
uv run python src/ui/camera_app.py
```
Press 'q' to quit the application, press 'TAB' to toggle the settings sidebar, or press 'c' to manually request AI coaching on the current frame.

### Offline Image Upload (Stage 1)
To launch the Gradio web UI for static image analysis:
```bash
uv run python src/ui/gradio_app.py
```

## Testing
Run the test suite using pytest:
```bash
uv run pytest tests/
```
