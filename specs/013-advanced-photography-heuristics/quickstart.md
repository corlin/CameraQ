# Quickstart: Validation Guide for Advanced Photography Heuristics

**Feature**: [spec.md](file:///Users/corlin/2026/CameraQ/specs/013-advanced-photography-heuristics/spec.md)

## Validation Scenarios

### 1. Test Lighting Direction Detection
**Setup**: Open the CameraQ app in a room with a single strong light source (like a window).
**Action**: Have a subject stand facing the camera with the window directly behind them (backlit).
**Expected**: The AI should warn about severe backlight.
**Action**: Have the subject turn 90 degrees so the window is on their left or right (side lighting).
**Expected**: The AI should praise the side lighting or remove the lighting warning.

### 2. Test Histogram Exposure Warnings
**Action**: Point the camera directly at a bright light bulb or the sun.
**Expected**: The AI should warn "高光溢出，建议降低曝光 (EV-)".
**Action**: Cover the camera lens almost completely with your hand, leaving only a tiny crack of light.
**Expected**: The AI should warn "暗部细节丢失，建议增加曝光 (EV+)".

### 3. Test Color Contrast Separation
**Setup**: Wear a shirt of a specific color (e.g., a green shirt).
**Action**: Stand in front of a background of the same color (e.g., green bushes or a green wall).
**Expected**: The AI should warn "主体与背景颜色接近，建议更换对比色背景".

### 4. Test Depth of Field (DoF) Warnings
**Action**: Stand far away from a subject (subject box < 15% of frame) where the background has many objects (high Canny edge density).
**Expected**: The AI should suggest "靠近主体以虚化背景，或开启人像模式".
