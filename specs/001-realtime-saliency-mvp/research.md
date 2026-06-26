# Research & Decisions: Real-time Saliency MVP

## 1. 实时摄像头推流方案
**Decision**: 使用 OpenCV (`cv2.VideoCapture`) 进行本地摄像头视频流读取与展示。
**Rationale**: 鉴于项目当前仍为 Python 桌面 MVP 阶段，无需立即开发原生的 iOS/Android 代码。使用 OpenCV 能够最快速地获取摄像头帧，且与已有的 OpenCV 和 NumPy 处理管线无缝衔接。
**Alternatives considered**: WebRTC 浏览器推流 (Gradio 支持，但开发与调试复杂度较高且有网络层延迟)；原生端开发 (成本太高，不适合本阶段验证)。

## 2. 显著性 (Saliency) 模型选择
**Decision**: 使用超轻量级的 `U^2-Net` (u2netp) 或基于 `OpenCV` 自带的轻量显著性检测器 (如 `cv2.saliency.StaticSaliencyFineGrained_create()`) 作为初步探索。若 OpenCV 无法准确提取“心形云”，再引入 U^2-Net 的 ONNX 推理。
**Rationale**: 推流的实时性要求至少 15+ FPS，重度模型会拖垮整体帧率。OpenCV 自带的 Saliency 速度极快，适合 MVP 验证；U2Net 效果好但需要控制分辨率。我们决定先封装抽象层，以便后续灵活切换底层模型。
**Alternatives considered**: InSPyReNet (效果极好，但推理成本太高)；SAM (Segment Anything，无法达到实时要求)。

## 3. 多模型融合决策方案 (YOLO vs Saliency)
**Decision**: 当 Saliency 输出显著性热力图后，在热图上提取连通域或边界框，将其视作一个特殊的 `DetectedSubject(class_name='saliency')`，与 YOLO 的边界框进行 IOU 匹配或显著度加权打分对比。
**Rationale**: 统一数据结构，所有目标检测结果（无论来源）最终都汇聚在同一框架下处理，方便复用之前的 `portrait_rule.py`、`position_rule.py` 等逻辑。

## 4. UI 推流与 AI 推理的异步解耦
**Decision**: 开启 Python 多线程或多进程。主线程/主协程负责从摄像头抽帧并在 UI 上绘制（保证 30 FPS），后台线程按照固定频率（如 5 FPS）抓取最新一帧送入 AI 管线。AI 结果一旦产出，立即更新全局状态，主线程渲染时直接叠加最新的状态。
**Rationale**: 只有彻底分离 UI 和 Inference，才能满足 FR-004 的防卡顿要求。
