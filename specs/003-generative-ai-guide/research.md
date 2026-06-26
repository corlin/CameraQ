# Research: Generative AI Guide (Stage 4)

## 1. Asynchronous Architecture for OpenCV

**Decision**: We will use a dedicated `threading.Thread` with a `queue.Queue` to handle the Gemini API calls.

**Rationale**:
- OpenCV's `VideoCapture` loop must run at ~30 FPS on the main thread (or the dedicated camera thread).
- Any network call to an LLM will take 1-4 seconds, which would block the frame capture and processing.
- A `queue.Queue(maxsize=1)` allows the main thread to "drop" a frame into the queue without blocking. If the background thread is busy processing a previous frame, the new frame can be ignored or override the queue, ensuring we only process the latest frame when the LLM is ready.
- `threading` is simpler and perfectly adequate for I/O bound tasks (like waiting for a network request) compared to `multiprocessing`.

**Alternatives considered**:
- `asyncio`: Requires rewriting the entire camera loop to be asynchronous, which is complex and doesn't play well with OpenCV's blocking `read()` by default.
- `multiprocessing`: Too heavy for simply making network calls, and passing large image numpy arrays between processes adds overhead.

## 2. Throttling and Cooldowns

**Decision**: Implement a 5-second cooldown between automated requests. 

**Rationale**:
- Calling the Gemini API every frame is impossible and financially costly.
- A 5-second cooldown ensures that the coaching text remains on screen long enough for the user to read it before it refreshes.

**Alternatives considered**:
- Stability-based trigger: Only trigger when optical flow / centroid velocity is zero. This could be added later, but a simple time-based throttle is a robust baseline.

## 3. Rendering Multi-line Chinese Text

**Decision**: Continue using the `Pillow` (PIL) `ImageDraw` implementation introduced in Stage 2/3.

**Rationale**:
- OpenCV `cv2.putText` does not natively support Chinese fonts well.
- We already have a fast BGR -> RGB -> PIL -> RGB -> BGR conversion pipeline in `OverlayRenderer`.
- We will add a "text wrapping" utility or handle newlines from Gemini's response gracefully so it fits in a nice "bubble".
