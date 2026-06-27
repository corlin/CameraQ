# Research: deep-ai-assist

## 1. Camera Hardware Control (macOS OpenCV)

**Context**: We need to automatically adjust fundamental camera parameters (ISO, shutter speed, exposure) based on AI scene understanding (FR-001).

**Decision**: Attempt to use OpenCV `CAP_PROP_EXPOSURE` and `CAP_PROP_ISO_SPEED` where supported. If the hardware/OS driver rejects it (common on macOS AVFoundation backend), implement a Software-Simulated Exposure compensation as a fallback (adjusting brightness/contrast matrix).

**Rationale**: macOS has notoriously strict limitations on UVC camera control through OpenCV's default AVFoundation backend. Many webcams will silently ignore exposure setting commands. A graceful fallback ensures the feature still works functionally in the UI (simulating the effect for the user and the AI).

**Alternatives considered**:
- Writing a custom objective-C/Swift extension using `AVCaptureDevice` (Too complex, violates simplicity, breaks cross-platform compatibility).
- Using third-party CLI tools like `uvcc` (Not robust for a distributed app, requires user installation).

## 2. Proactive Voice Prompts

**Context**: We need to deliver proactive alerts via voice (FR-002).

**Decision**: Use the macOS native `say` command via `subprocess` for zero-dependency, low-latency text-to-speech.

**Rationale**: `pyttsx3` can sometimes cause threading issues in OpenCV video loops. macOS `say` is built-in, runs in a separate process seamlessly, and has extremely low latency which fits FR-003.

**Alternatives considered**:
- Cloud TTS (e.g., Google Cloud TTS, ElevenLabs) - Adds network latency and API cost. Violates the low-latency requirement for immediate alerts.
- `pyttsx3` - Python library, but can be blocking and buggy on some macOS versions when mixed with `cv2.imshow`.

## 3. Hybrid AI Architecture

**Context**: Balance low latency with deep scene understanding (FR-003).

**Decision**: 
1. **Local**: Use existing YOLO (for object/pose) and simple CV heuristic rules (brightness, contrast, motion blur) running at 25+ FPS.
2. **Cloud**: Every N seconds (e.g., 2 seconds), or when local heuristics detect a significant scene change, grab a frame and send it asynchronously to Gemini 1.5 Flash/Pro with a specific prompt ("Analyze this scene for photography. What is the context?").
3. **Merge**: The `Analyzer` will hold the latest "Cloud Scene Context" in state and merge it with the real-time local detections to make final decisions.

**Rationale**: Gemini Flash provides excellent multimodal reasoning with low latency (~1-2s), making it suitable for periodic contextual updates without blocking the main 25 FPS local render loop.

**Alternatives considered**:
- Running a large local LLM (e.g., LLaVA) - Too slow for real-time without heavy GPU hardware, wouldn't meet low latency on average machines.
