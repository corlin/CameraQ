# Implementation Plan: 实时构图模式识别与引导

**Branch**: `[014-composition-pattern-recognition]` | **Date**: 2026-07-03 | **Spec**: [spec.md](./spec.md)

**Input**: `specs/014-composition-pattern-recognition/spec.md` 中的 15 类离线多标签构图识别、证据解释、稳定输出和目标构图引导需求。

## Summary

在 CameraQ 现有主体检测、显著性、线条分析和实时取景线程上增加独立的 `composition` 域模块。模块把输入帧缩放到最长边 320px，只执行一次灰度、边缘、线段、轮廓、角点、视觉质量和消失点等共享特征提取；15 个构图评分器消费同一份不可变特征快照，输出证据匹配度而非伪概率。时序层以 150ms 为目标更新周期，使用迟滞与连续命中规则抑制闪烁；推荐层只从有可靠结构证据、且可以通过小幅平移、旋转或距离调整达到的候选中选择一个目标。首期完全离线、纯 CPU、无新增运行时依赖，也不训练小模型。

## Technical Context

**Language/Version**: Python 3.12（当前环境 3.12.9）

**Primary Dependencies**: OpenCV 4.11、NumPy 1.26、Pydantic、现有 Ultralytics YOLO11n/YOLO11n-pose 与 CameraQ 显著性模块；不新增首期运行时依赖

**Storage**: 无数据库；设置继续使用本地 `config.json`。每次可见结果进入最多 300 条的内存环形缓冲区；仅当 `composition_diagnostics_enabled=true` 时写入 `~/.cameraq/diagnostics/composition/` 下的 NDJSON，单文件最大 20MB、保留 7 天、从不包含原始图像，并提供清除操作

**Testing**: pytest；合成几何图、固定图像夹具、分析器集成测试、覆盖层测试和独立性能基准

**Target Platform**: CameraQ 当前 macOS 桌面实时取景；设计保持 NumPy/OpenCV 可移植性，不依赖 Apple 专有加速

**Project Type**: 单体 Python 桌面视觉应用，分析线程与显示线程分离

**Performance Goals**: 构图模块在 720p 输入上完成缩放和分析的平均耗时不超过 25ms；结果至少 5Hz 更新；启用后实时取景平均不低于 25 FPS

**Constraints**: 纯 CPU、完全离线、最长边 320px 的分析图、15 类非互斥、输出为证据匹配度、专业模式可解释、普通模式最多展示 Top 3

**Scale/Scope**: 15 个构图评分器、8 类共享证据、1 个目标推荐、1 套时序状态机；单相机、单帧主主体或显著焦点

## Constitution Check

*GATE: Phase 0 前检查，Phase 1 设计后复查。*

- [x] **I 本地实时核心**：构图识别、推荐与诊断缓冲完全离线；Gemini 不在依赖链中。
- [x] **II 证据优先**：每个显示模式有可定位证据；规则分数只称匹配度；低证据允许弃权。
- [x] **III 性能预算**：共享 320px 特征、独立 150ms 时间门、分析线程缓存和端到端 5 分钟基准均有专项验收。
- [x] **IV 测试先行**：每一评分器先建立正例、临界、困难反例和退化输入失败测试。
- [x] **V 模块边界**：特征、评分、推荐、时序、诊断与渲染各有单一所有者，公开字段向后兼容。
- [x] **隐私与数据**：诊断默认只驻留有界内存；持久化需用户启用，NDJSON 无原始帧、限额、限期、可清除。

**Gate 结果**: PASS。无需要豁免的复杂度。

## Project Structure

### Documentation (this feature)

```text
specs/014-composition-pattern-recognition/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   └── requirements.md
├── contracts/
│   └── composition-analysis.schema.json
└── tasks.md                              # 由 /speckit-tasks 生成
```

### Source Code (repository root)

```text
src/core/
├── analyzer.py                           # 接入构图引擎与缓存结果
├── entities.py                           # 增加公开构图结果实体
├── settings.py                           # 增加启用开关与更新周期
└── composition/
    ├── __init__.py
    ├── features.py                       # 共享特征快照与内部几何类型
    ├── extractor.py                      # 单次特征提取
    ├── geometry.py                       # 归一化距离、交点、方向等纯函数
    ├── thresholds.py                     # 集中管理首期阈值与权重
    ├── engine.py                         # 评分器编排、Top 3 与质量门控
    ├── recommender.py                    # 目标模式、调整成本与动作
    ├── temporal.py                       # 迟滞、连续命中与场景重置
    ├── diagnostics.py                    # 有界会话缓冲、可选 NDJSON 与清理
    └── scorers/
        ├── __init__.py
        ├── position.py                   # 三分、动态对称、平衡、三角形
        ├── linear.py                     # 对角、横线、斜线、十字、垂直
        └── topology.py                   # 曲线、放射、棋盘、向心、隧道、框式

src/ui/
└── overlay.py                            # Top 3、证据线和目标动作

tests/
├── fixtures/composition/                 # 小型、可再分发的验收图像与清单
├── unit/core/composition/
│   ├── test_entities.py
│   ├── test_contract.py
│   ├── test_extractor.py
│   ├── test_geometry.py
│   ├── test_engine.py
│   ├── test_position_scorers.py
│   ├── test_linear_scorers.py
│   ├── test_topology_scorers.py
│   ├── test_recommender.py
│   └── test_temporal.py
├── unit/core/test_analyzer.py
├── unit/ui/test_overlay.py
└── integration/
    ├── test_composition_pipeline.py
    ├── test_composition_recommendation.py
    ├── test_composition_stability.py
    └── test_performance.py
```

**Structure Decision**: 保持现有单项目结构，在 `src/core/composition/` 内建立清晰边界。公开结果模型留在现有 `src/core/entities.py`，避免 `AnalysisResult` 出现跨域循环导入；仅供评分器使用的数组与几何快照留在 `composition/features.py`。

## Phase 0: Research

研究结论见 [research.md](./research.md)。关键决定：

1. 共享特征提取采用现有 OpenCV 算子，不引入新模型。
2. 线性构图使用概率霍夫线段和长度加权方向直方图；轮廓层级支持框式与隧道式。
3. 主体框与显著性热图合成视觉质量图，服务三分法、平衡式、动态对称和向心式。
4. 所有评分由必备证据门控和归一化子分数组成，输出 0–100 匹配度，不声称统计概率。
5. 首期小模型路线只保留接口兼容性，不下载、不训练、不加载权重。

## Phase 1: Design & Contracts

### 1. 数据模型

详见 [data-model.md](./data-model.md)。`AnalysisResult` 增加可选 `composition_analysis`，旧调用者无需提供即可继续工作。所有点和线以 0–1 归一化坐标传递给覆盖层，避免分析分辨率与显示分辨率耦合。

### 2. 共享特征流水线

`CompositionFeatureExtractor.extract()` 接收原始帧、融合主体和显著性图，返回不可变 `CompositionFeatures`：

1. 等比缩放至最长边 320px，保留原图到分析图的映射。
2. 生成灰度图、轻度平滑图、边缘图和梯度方向/强度图。
3. 提取并过滤长线段，计算长度加权的方向直方图、平行线族、交点候选和稳健汇聚中心。
4. 提取轮廓及层级，保留长曲线、近矩形轮廓、嵌套深度和尺寸递减关系。
5. 合成主体框、主体置信度与显著性热图为视觉质量图，计算焦点、质量质心、四象限质量和镜像平衡。
6. 计算场景质量，包括有效边缘量、模糊、曝光退化和可用证据覆盖率。

特征只在 150ms 时间门到期时重算；其他帧复用最近的完整结果。首次输入必须立即分析。150ms 是调度目标而不是对外更新承诺；10 秒窗口内必须实测达到至少 5 次/秒。

### 3. 评分器分组

每个评分器实现统一的纯函数契约：输入 `CompositionFeatures`，输出一个 `CompositionModeResult`，不得修改共享特征。

| 分组 | 模式 | 核心证据 |
|------|------|----------|
| 位置与质量 | 三分法 | 主焦点到三分交点/线的归一化距离、三分结构线覆盖 |
| 位置与质量 | 动态对称 | 主焦点和强线段对主对角线、反向对角线及呼应斜线的贴合 |
| 位置与质量 | 平衡式 | 左右/上下质量差、质量质心偏移、大小与数量的互补 |
| 位置与质量 | 三角形 | 三个稳定焦点的非共线性、面积、边缘连接与主体支持 |
| 线性 | 对角线 | 跨画面长线与两条画面对角方向的贴合及跨度 |
| 线性 | 横线 | 近水平线段的长度占比、层次一致性和全局覆盖 |
| 线性 | 斜线 | 非水平/垂直的主方向强度，排除仅局部纹理和弱短线 |
| 线性 | 十字形 | 强水平/垂直线族的交点及其与焦点的关系 |
| 线性 | 垂直线 | 近垂直线段的长度占比、柱列一致性和全局覆盖 |
| 拓扑 | 曲线 | 长轮廓的弧长、曲率连续性和 C/S/弧形路径覆盖 |
| 拓扑 | 放射式 | 至少三条方向分散的强线共享稳健中心 |
| 拓扑 | 棋盘式 | 两组近正交平行线、近周期间距及二维交点覆盖 |
| 拓扑 | 向心式 | 汇聚中心附近存在焦点，周边质量和方向证据共同收束 |
| 拓扑 | 隧道式 | 轮廓嵌套、尺寸递减、透视汇聚和内部消失区域 |
| 拓扑 | 框式 | 两侧以上边界包围内部焦点，且不要求重复纵深层次 |

### 4. 匹配度与可信等级

- 每个模式由 2–5 个归一化子分数组成；缺少定义所要求的必备证据时，匹配度上限受限。
- `match_score` 为 0–100 的确定性证据分；初始阈值集中在 `thresholds.py`，不得散落在评分器中。
- `confidence` 由证据数量、证据覆盖、场景质量和子分一致性决定，与 `match_score` 分离。
- 默认候选进入门槛 65、退出门槛 55；阈值在固定验收集上校准后再冻结。
- Top 3 先按可见状态过滤，再按匹配度、可信等级和模式稳定时长排序。

### 5. 时序状态机

每个模式独立维护 `ABSENT → CANDIDATE → ACTIVE → FADING → ABSENT`：

- 分数达到进入门槛连续 3 次后进入 `ACTIVE`。
- `ACTIVE` 低于退出门槛连续 3 次后进入 `FADING` 并退出可见列表。
- 分数位于两门槛之间时保持当前状态，形成迟滞区。
- 低分辨率灰度帧差表明场景发生实质切换时，清除旧候选并立即允许新结果进入候选。
- 第一次分析允许高可信、高匹配模式直接显示，避免启动后长时间空白。

### 6. 目标构图推荐

推荐器不对所有模式强行生成动作。每个模式声明其可执行动作和前置条件：

- 三分法、平衡式、动态对称：基于焦点与目标锚点的差值给出平移方向。
- 横线、垂直线、对角线、斜线：只有存在强主方向时才给出小幅旋转方向。
- 放射式、向心式、隧道式、框式：只有结构已存在且主体接近结构中心时，才建议平移主体与中心对齐。
- 当主主体占画面不足 8%，且放大主体不会破坏已有框架/隧道/平衡证据时，可建议 `MOVE_CLOSER`；当主体占画面超过 45%、发生裁切或遮蔽关键结构时，可建议 `MOVE_BACK`。距离动作必须有可靠主主体，并通过候选变换验证预期匹配度提升。
- 三角形、曲线、棋盘式、十字形：首期只识别或提示保持，不凭单帧推断如何重排现实场景。

候选效用由预期分数提升、证据可信度和调整成本共同决定。若当前已有高可信强构图，或所有候选效用不足，则输出 `KEEP` 或无推荐。

### 7. Analyzer 与 UI 集成

- `CameraQAnalyzer` 创建一个长生命周期 `CompositionEngine`，在主体融合后调用，使评分器能够复用主体与显著性信息。
- 构图分析使用独立 `composition_analysis_interval_s=0.15`，不复用默认 `analysis_throttle_n=5`；基准测试按完成时间统计 10 秒窗口内的实际更新数，确保不低于 5Hz。
- 结果写入 `AnalysisResult.composition_analysis`，不改变现有总分计算；构图建议作为独立低干扰提示，不通过现有 `STYLE` feedback 反向抬高总分。
- `MINIMAL` 只显示首个稳定模式；`COACH` 显示 Top 3 和一个动作；`PRO` 额外显示匹配度、可信等级和证据几何。
- 设置侧栏增加 `composition_detection_enabled`、`composition_diagnostics_enabled` 和“清除构图诊断”操作；关闭识别后引擎停止重算且覆盖层不显示构图结果，清除操作同时清空内存缓冲和持久化诊断文件。

### 8. Interface Contract

[composition-analysis.schema.json](./contracts/composition-analysis.schema.json) 定义分析器到覆盖层/离线 UI 的稳定结果形状。契约只含结构化结果和归一化证据坐标，不含原始帧或网络字段。

## Phase 2: Implementation Sequence

1. 先建立实体、JSON 契约与合成图测试辅助函数。
2. 实现共享几何纯函数和特征提取器，并锁定 25ms 性能基线。
3. 依次实现位置、线性、拓扑三组评分器；每组完成正例、困难反例和退化输入测试。
4. 实现 Top 3 与可信等级。
5. 实现目标推荐与动作约束，先消费高可信当前结果，验证“无可靠证据则不建议”。
6. 实现时序状态机和场景切换重置；推荐器随后消费时序层标记的可见结果。
7. 接入 Analyzer、Settings、Diagnostics 和 Overlay，确保旧 `AnalysisResult` 构造仍兼容。
8. 增加完整管线、离线、稳定性和性能测试，最后执行 [quickstart.md](./quickstart.md) 的手工场景。

## Verification Plan

### Automated

- 15 类评分器各自至少包含：清晰正例、临界正例、困难反例、空白帧和纹理噪声。
- 实体和契约测试验证分数范围、枚举完整性、Top 3 上限和归一化坐标。
- 推荐测试验证动作方向、不可执行模式抑制、强构图保持和低证据不建议。
- 时序测试使用可控分数序列验证进入、退出、迟滞、首次显示和场景重置。
- Analyzer 集成测试禁用网络和重模型，验证缓存、150ms 更新门、10 秒实际更新率与向后兼容。
- 性能测试预热后测量 50 次 720p 随机/结构帧，断言构图模块平均耗时 <25ms，并监控 p95。
- 端到端基准在 Apple M1 8 核/8GB 或等效 CPU-only 设备上运行 1280×720 取景 5 分钟，记录平均 FPS、p95 帧间隔和拍摄/设置操作 p95 响应时间。
- 推荐验收集至少包含 50 个近目标场景并覆盖平移、旋转、靠近、后退，统计一次动作后的改善率。

### Manual

- 断网运行实时取景，按 [quickstart.md](./quickstart.md) 验证三分、平衡、线性、放射/向心、框/隧道和弱证据场景。
- 在 `MINIMAL`、`COACH`、`PRO` 间切换，确认信息密度和证据覆盖符合设计。
- 固定相机 30 秒并轻微晃动，确认标签不闪烁；快速换景后确认 1 秒内更新。

## Post-Design Constitution Check

- [x] 离线边界仍成立，契约中没有网络依赖或原始图像字段。
- [x] 共享特征和三组评分器避免重复计算，性能预算有独立自动测试。
- [x] 数据模型将匹配度、可信等级和推荐优先级分开。
- [x] 评分、推荐、时序和覆盖层均有独立接口与测试边界。
- [x] 未引入首期模型权重、训练管线或新依赖。
- [x] 复杂度与 15 类识别需求匹配，无额外服务或无关重构。

**Re-check 结果**: PASS。

## Complexity Tracking

无 Constitution gate 违规，无需豁免记录。
