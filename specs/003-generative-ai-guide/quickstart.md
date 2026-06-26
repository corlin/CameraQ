# Quickstart: Generative AI Guide (Stage 4)

This guide provides instructions on how to validate the newly implemented Generative AI Guide in CameraQ.

## Prerequisites

1.  A valid Google Gemini API Key.
2.  Set the API key in your environment before running the application:
    ```bash
    export GEMINI_API_KEY="your-api-key-here"
    ```

## Validation Scenarios

### Scenario 1: Automated Background Coaching

**Goal**: Verify that the AI Coach automatically analyzes the scene without blocking the main OpenCV thread.

1.  Start the application:
    ```bash
    uv run python src/ui/camera_app.py
    ```
2.  Ensure your webcam is active and pointing at a subject (e.g., yourself, a cup, a plant).
3.  Wait for **~5 seconds**.
4.  **Expected Outcome**: A new text bubble should appear in the camera overlay containing a stylistic photography tip (e.g., "尝试换个角度...", "光线有点暗...").
5.  **Performance Check**: During the 5-second wait and the moment the text appears, wave your hand in front of the camera. The video feed MUST remain perfectly smooth (~30 FPS) without any stuttering.

### Scenario 2: Offline / Missing API Key Fallback

**Goal**: Verify that the application does not crash if the API key is missing or the network is disconnected.

1.  Unset the API key:
    ```bash
    unset GEMINI_API_KEY
    ```
2.  Start the application:
    ```bash
    uv run python src/ui/camera_app.py
    ```
3.  **Expected Outcome**: The camera app should start normally. The basic OpenCV tracking and lighting warnings (from Stage 3) will still work perfectly. No AI coaching text will appear, but the app will not crash.
