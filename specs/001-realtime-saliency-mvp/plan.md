# Implementation Plan: Stage 2 Real-time Saliency MVP

## Technical Context
本阶段核心在于将系统从“静态图片分析”改造为“实时视频流分析”，并引入 Saliency（显著性）检测解决特殊主体识别盲区。

## Constitution Check
- **Test-First Development**: 所有新功能在核心逻辑层（如融合算法）依然保持 TDD。涉及 UI/摄像头的侧重端到端验证。
- **Documentation**: 规范架构设计，更新 README 和架构图。
- **Modular Design**: 新增的 Saliency 引擎应实现与 YOLO 相同的检测器接口，解耦实现。

## Gates
- [x] Clear requirements
- [x] Architectural alignment
- [x] Technology selection verified (OpenCV VideoCapture + Saliency algorithms)

## Phase 0: Outline & Research
- 见 `research.md`。决策：采用多线程解耦 UI 与 AI；引入轻量级 Saliency 算法提取显著度连通域，与 YOLO 结果进行加权融合。

## Phase 1: Design & Contracts
- 见 `data-model.md`。
- 新增组件目录规划：`src/core/detectors/saliency.py`

## Phase 2: Implementation & Tasks
1. **基础设施**：实现 `CameraStream` 多线程视频抓取类。
2. **算法集成**：接入轻量级 Saliency 检测器。
3. **算法融合**：在 `CameraQAnalyzer` 中融合 YOLO 和 Saliency 的包围盒并裁定真正的 `Primary Subject`。
4. **实时反馈 UI**：将单句最高优先级 Feedback 叠加至视频流帧上，完成端到端闭环验证。
