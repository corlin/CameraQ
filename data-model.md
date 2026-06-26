# CameraQ - Data Model

## Core Entities

### 1. `FrameAnalysisRequest`
Represents an incoming image frame to be analyzed.
- `image_id`: UUID
- `timestamp`: int (ms)
- `image_data`: Base64 string or file path
- `device_orientation`: enum (Portrait, LandscapeLeft, LandscapeRight)

### 2. `DetectedSubject`
Represents an identified subject in the frame.
- `subject_id`: UUID
- `class_name`: string (e.g., "person", "food", "building")
- `confidence`: float (0.0 - 1.0)
- `bounding_box`: `BoundingBox` (x, y, width, height)
- `keypoints`: List of `Keypoint` (optional, for human poses)
- `is_primary_subject`: boolean

### 3. `StructuralAnalysis`
Represents the structural elements detected in the frame.
- `horizon_angle`: float (degrees, 0 is perfectly level)
- `vertical_lines`: List of `Line`
- `vanishing_points`: List of `Point`
- `saliency_map`: Array/Reference to heatmap

### 4. `CompositionScore`
Represents the evaluated scores based on composition rules.
- `total_score`: int (0-100)
- `subject_score`: int
- `structure_score`: int
- `balance_score`: int
- `interference_score`: int
- `style_score`: int

### 5. `Feedback`
The final, single actionable recommendation given to the user.
- `priority_level`: int (1=Hard Error, 2=Subject, 3=Interference, 4=Optimization, 5=Style)
- `action_type`: enum (MoveLeft, MoveRight, MoveCloser, MoveBack, TiltUp, TiltDown, Rotate)
- `message`: string (e.g., "头顶空间太多，镜头向下。")
- `target_point`: `Point` (optional, for drawing a recommended target on UI)

### 6. `CropRecommendation`
Recommended crop configurations after the shot.
- `crop_style`: enum (RuleOfThirds, Centered, SocialVertical)
- `bounding_box`: `BoundingBox`
- `reasoning`: string
