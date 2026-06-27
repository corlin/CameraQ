# Phase 0: Outline & Research

## Research Objectives
1. Determine the best way to render "Icon + Text" in PIL without external icon image files (to keep the MVP simple).
2. Determine how to implement "Tap to expand" or "Timeout" for long AI text.

## Findings & Decisions

### 1. Iconography in PIL
- **Decision**: Use Unicode Emoji characters for MVP icons.
- **Rationale**: PIL supports drawing Emoji characters if a supporting font (like Apple Color Emoji or standard fallback) is available. The current `overlay.py` already uses `📸`, `🤖`, and `🔊`. We will extend this to include specific scene indicators (e.g., ☀️ for bright, ⛰️ for outdoor, 👤 for portrait).
- **Alternatives considered**: Loading `.png`/`.svg` assets. This would require asset management and alpha compositing per frame which adds overhead and complexity to the current pure-code drawing approach.

### 2. Collapsible Text / Timeout
- **Decision**: Implement a time-based decay for AI coaching messages. The message shows fully (wrapped) for a few seconds, then collapses into a small indicator icon (e.g., `💬 AI Insight available (Tab to view)`).
- **Rationale**: OpenCV/cv2 desktop windows do not support native DOM-like click event listeners easily without complex coordinate mapping for mouse callbacks. Since the app relies on keyboard input (TAB for settings), we can rely on auto-hide (timeout) and perhaps a keyboard toggle to review past insights.
- **Alternatives considered**: True "Tap to expand" using mouse clicks. Rejected because OpenCV mouse callbacks on high-DPI screens have proven complex in this app (as seen in previous feature iterations), and we want to keep the UI interaction simple.

### 3. Professional Styling
- **Decision**: Use semi-transparent rounded rectangles (using `ImageDraw.rounded_rectangle`) with thin borders (e.g., 1px), small sans-serif fonts, and ample padding.
- **Rationale**: Replicates the "glass" or professional camera UI aesthetic better than sharp-cornered solid black boxes.

## Conclusion
Research complete. We will proceed to Phase 1 Design with Unicode Emojis for icons, time-based auto-collapsing for long text, and rounded PIL shapes for a more premium look.
