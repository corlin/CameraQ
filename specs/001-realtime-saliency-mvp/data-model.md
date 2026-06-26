# Data Model: Real-time Saliency MVP

## Core Entities

### CameraStream
负责管理视频流抓取与帧分发。
- `frame_width`: 帧宽
- `frame_height`: 帧高
- `fps`: 当前推流帧率
- `current_frame`: 最新的图像矩阵 (numpy array)
- `is_running`: 是否正在推流的状态

### SaliencyMap
显著性引擎输出的结果。
- `heatmap`: 显著度灰度图矩阵 (0-255)
- `bounding_boxes`: 显著性区域的包围盒列表
- `max_salient_score`: 核心高亮区的分数

### FusedSubject (继承自 DetectedSubject)
经过 YOLO 和 Saliency 综合评估后的最终目标。
- `subject_id`: 目标 ID
- `class_name`: "person" / "car" / "saliency_blob" (显著性色块)
- `confidence`: 置信度 / 显著度
- `bounding_box`: 边界框
- `source`: 数据来源 (Enum: YOLO, SALIENCY, FUSED)
- `is_primary_subject`: 布尔值，标识其为当前画面的主导目标
