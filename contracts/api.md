# CameraQ - API Contracts

Since Stage 1 focuses on a Python + Gradio offline demo, the core contract is the interface of the `Analyzer` module, rather than a REST API.

## Python Inference Interface

### `Analyzer.process_frame(image_path: str) -> AnalysisResult`

**Input**: Path to the image file to be analyzed.
**Output**: `AnalysisResult` containing:
- `image_with_overlays`: Path or Numpy array of the processed image with drawn boxes/lines.
- `feedback_message`: The single actionable advice string (e.g., "人物脸太靠左，右边留白不足。")
- `score`: Integer out of 100 representing the composition quality.
- `recommended_crops`: List of cropped image arrays or bounding boxes.
- `debug_data`: Dictionary containing raw detected subjects, horizon angles, etc., for UI debugging purposes.
