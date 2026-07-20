# CameraQ

CameraQ is an intelligent photography assistant designed to analyze image composition and provide real-time feedback using advanced AI models.

## Features

- 📸 **Real-time Composition Scoring**: Evaluates framing in real-time via a 5-axis model (Subject, Structure, Balance, Interference, Style) and presents visual feedback.
- 🤖 **Generative AI Coaching**: Integrates Gemini 2.5 Flash for contextual, stylistic, and emotional photography tips directly from the viewfinder.
- 👁️ **Advanced Computer Vision**: Leverages YOLO11 for object and human pose detection, alongside visual saliency mapping to identify the natural focal points of an image.
- 📐 **Dynamic Aesthetic Rules**: Automatically detects rule-of-thirds alignment, horizon leveling, color harmony, over/under exposure, and background interference.
- 🎯 **Progressive Alignment & Clutter Detection**: Real-time IoU-based alignment "snap" for perfect composition and background clutter tracking via edge density analysis.
- ⚙️ **Pro Settings Dashboard**: Interactive sliding side panel with granular control over AI sampling rates, analysis throttling to optimize FPS, and module toggles.

## Offline composition recognition

CameraQ can analyze composition locally with OpenCV/NumPy rules. The real-time path does not upload
frames and does not require Gemini or another network service. It evaluates 15 non-exclusive modes:

- rule of thirds, dynamic symmetry, balanced, triangle;
- diagonal, horizontal, oblique, vertical, and cross;
- curve, radial, checkerboard, centripetal, tunnel, and frame-within-frame.

The displayed number is a deterministic **match score** (evidence score), not a statistical probability.
Up to three stable modes are shown at once. When local evidence is weak, CameraQ lowers confidence,
shows that evidence is insufficient, and suppresses directional advice instead of forcing a label.

Coaching levels control information density:

- `MINIMAL`: the strongest stable composition name;
- `COACH`: Top 3 modes and at most one reachable camera action;
- `PRO`: match score, confidence, and localized point/line/contour evidence.

The settings sidebar contains separate controls for composition recognition and composition diagnostics,
plus a clear-diagnostics action. Diagnostics always keep at most 300 structured results in memory. Disk
logging is off by default; when explicitly enabled it writes NDJSON under
`~/.cameraq/diagnostics/composition/`, never stores raw frames, rotates each file at 20 MB, retains files
for at most seven days, and can be cleared from the sidebar. Disabling composition recognition removes
only its overlay and leaves the viewfinder and capture operations available.

### Validation status

The current per-mode thresholds are frozen from the isolated calibration split (`reviewed-calibration-v2`).
On the untouched acceptance split, macro precision is 80.50% and macro recall is 70.36%; however, Top 3
coverage is 77/138 (55.80%), below the 85% target. The offline engine, diagnostics, and regression suite
are verified, while final acceptance remains open for Top 3 quality, minimum-device real-camera performance,
manual native-window scenarios, and independent human review of real acceptance images. See
[`specs/014-composition-pattern-recognition/validation.md`](specs/014-composition-pattern-recognition/validation.md)
for the detailed evidence and limitations.

## Roadmap

- [x] **Stage 1 (Offline MVP)**: Process local images with basic Saliency & YOLO detection, and output static compositional score/feedback.
- [x] **Stage 2 (Real-time Viewfinder)**: Live video feed integration, threaded processing, and basic UI overlays.
- [x] **Stage 3 (Advanced Aesthetics & Tracking)**: Lighting/color analysis (overexposed/underexposed warnings) and dynamic subject tracking for shutter timing predictions.
- [x] **Stage 4 (Generative AI Guide)**: Gemini multimodal integration for contextual, stylistic photography coaching.
- [x] **Stage 5 (UI/UX Polish)**: Translucent, elegant visual overlays with dynamic AI prompt lifecycles.
- [x] **Stage 6 (Pro Optimization)**: Multi-dimensional scoring (5-axis radar), performance throttling (FPS > 25), sliding settings sidebar, and graceful API degradation.
- [x] **Stage 7 (Progressive Alignment & UX Levels)**: Implemented 4-tier coaching levels, Canny edge background clutter detection, and real-time IoU-based haptic alignment snapping.
- [x] **Stage 13 (Advanced Photography Heuristics)**: Implemented fast (<15ms) lighting direction, EV warnings via histograms, color contrast checks, leading lines, and dynamic DoF blurring advice using classical CV techniques.
- [~] **Stage 14 (Offline Composition Recognition)**: Local 15-mode recognition, guidance, diagnostics, and automated gating are implemented; final Top 3 quality and real-device/manual acceptance remain open.

## Running the App

### Real-time Viewfinder (Stage 4)
To launch the real-time camera assistant with AI Coaching enabled:
```bash
export GEMINI_API_KEY="your_api_key_here"  # Optional, but required for AI Coaching
uv run python src/ui/camera_app.py
```
Press 'q' to quit the application, press 'TAB' to toggle the settings sidebar, or press 'c' to manually request AI coaching on the current frame.

The viewfinder is usable without `GEMINI_API_KEY`; the local OpenCV/NumPy composition
recognizer and overlay remain active, while network coaching is disabled. To make the
offline behavior explicit, run `env -u GEMINI_API_KEY uv run python src/ui/camera_app.py`.
On cold start, CameraQ opens a status page before loading the YOLO/torch analyzer, then
discards the first three camera warm-up frames. If macOS denies camera access, the same
page shows the error instead of leaving a black window; enable the terminal or IDE under
System Settings → Privacy & Security → Camera and restart the command.

The overlay keeps the composition summary in the upper-left, the scene badge in the
upper-right, and stacks exposure/AI prompts below the summary. Text uses the installed
system font and the layout reserves space between prompt boxes so simultaneous alerts do
not cover the composition labels.

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
