# Data Model: 实时构图模式识别与引导

**Feature**: [spec.md](./spec.md)

## Public Entities

公开实体放入 `src/core/entities.py`，继续使用 Pydantic；所有几何坐标归一化到 `[0, 1]`。

### `CompositionMode`

15 个稳定枚举值：

```text
RULE_OF_THIRDS
DYNAMIC_SYMMETRY
BALANCED
TRIANGLE
DIAGONAL
HORIZONTAL
OBLIQUE
CURVE
RADIAL
CHECKERBOARD
CENTRIPETAL
TUNNEL
FRAME_WITHIN_FRAME
CROSS
VERTICAL
```

显示中文由 UI 映射维护，枚举值不随文案变化。

### `CompositionConfidence`

| 值 | 含义 |
|----|------|
| `LOW` | 证据少、场景质量差或子分冲突；不得产生方向建议 |
| `MEDIUM` | 证据基本完整但仍有不确定性；可进入专业结果 |
| `HIGH` | 必备证据完整、覆盖充分且子分一致；可进入 Top 3 和推荐候选 |

### `CompositionEvidenceType`

```text
SUBJECT_POSITION
SALIENCY_FOCUS
LINE
LINE_INTERSECTION
CONTOUR
NESTED_CONTOUR
VANISHING_POINT
VISUAL_MASS
REPETITION
SYMMETRY
CURVATURE
```

### `NormalizedPoint`

| Field | Type | Validation |
|-------|------|------------|
| `x` | float | `0.0 <= x <= 1.0` |
| `y` | float | `0.0 <= y <= 1.0` |

### `NormalizedLine`

| Field | Type | Validation |
|-------|------|------------|
| `p1` | `NormalizedPoint` | required |
| `p2` | `NormalizedPoint` | required; must differ from `p1` |

### `CompositionEvidence`

| Field | Type | Validation / Meaning |
|-------|------|----------------------|
| `evidence_type` | `CompositionEvidenceType` | required |
| `strength` | float | `0.0..1.0` |
| `description` | str | 简短中文证据说明，不得为空 |
| `points` | list[`NormalizedPoint`] | 默认空；交点、焦点、质心 |
| `lines` | list[`NormalizedLine`] | 默认空；结构线、框线、对角线 |
| `contour` | list[`NormalizedPoint`] | 默认空；最多保留覆盖层所需简化点 |

一条证据至少包含 `points`、`lines`、`contour` 之一，或明确描述仅为全局质量证据。

### `CompositionModeResult`

| Field | Type | Validation / Meaning |
|-------|------|----------------------|
| `mode` | `CompositionMode` | 唯一模式 |
| `match_score` | float | `0..100`，证据匹配度，非概率 |
| `confidence` | `CompositionConfidence` | 与匹配度独立 |
| `evidence` | list[`CompositionEvidence`] | 显示模式至少 1 条 |
| `is_visible` | bool | 是否通过时序状态进入当前列表 |
| `stable_for_ms` | int | 非负 |

单次 `CompositionAnalysis` 中每个枚举模式只能出现一次。

### `CompositionAction`

```text
MOVE_LEFT
MOVE_RIGHT
TILT_UP
TILT_DOWN
ROTATE_CLOCKWISE
ROTATE_COUNTERCLOCKWISE
MOVE_CLOSER
MOVE_BACK
KEEP
```

### `TargetCompositionRecommendation`

| Field | Type | Validation / Meaning |
|-------|------|----------------------|
| `target_mode` | `CompositionMode` | required |
| `action` | `CompositionAction` | required |
| `reason` | str | 简短、可执行 |
| `current_score` | float | `0..100` |
| `projected_score` | float | `0..100`，不得低于 `current_score` |
| `adjustment_cost` | float | `0..1`，越低越容易达到 |
| `priority` | float | `0..1`，仅用于候选排序，不向用户表述为概率 |
| `target_points` | list[`NormalizedPoint`] | 可选目标锚点 |
| `aligned` | bool | 已达到目标时为 true，动作应为 `KEEP` |

### `CompositionAnalysis`

| Field | Type | Validation / Meaning |
|-------|------|----------------------|
| `analysis_version` | str | 首期固定 `1.0` |
| `timestamp` | float | 单调时间或结果时间戳 |
| `frame_width` | int | 原始帧宽，正整数 |
| `frame_height` | int | 原始帧高，正整数 |
| `evidence_quality` | float | `0..1` |
| `mode_results` | list[`CompositionModeResult`] | 恰好 15 个、模式唯一 |
| `top_modes` | list[`CompositionMode`] | 最多 3 个，必须引用 `is_visible=true` 的结果 |
| `recommendation` | `TargetCompositionRecommendation | None` | 最多一个 |
| `insufficient_evidence` | bool | true 时不得产生方向性推荐 |
| `processing_time_ms` | float | 非负；用于性能验证 |

### `AnalysisResult` modification

新增字段：

```text
composition_analysis: Optional[CompositionAnalysis] = None
```

默认 `None` 保持现有测试、Gradio、覆盖层和调用者兼容。

### `CompositionDiagnosticRecord`

| Field | Type | Validation / Meaning |
|-------|------|----------------------|
| `timestamp` | float | 非负单调/会话时间 |
| `visible_modes` | list[`CompositionMode`] | 最多 3 个，不重复 |
| `mode_summaries` | list[object] | 仅含模式、匹配度、可信等级和证据摘要 |
| `recommendation` | object or null | 仅含目标模式、动作和理由 |
| `evidence_quality` | float | `0..1` |
| `scene_changed` | bool | 本次结果是否发生实质换景 |

记录 MUST NOT 包含原始帧、编码图像、主体裁剪或可逆热图。

### `CompositionDiagnosticsBuffer`

- 内存环形缓冲区固定最多 300 条 `CompositionDiagnosticRecord`。
- `composition_diagnostics_enabled=false` 时不得写磁盘。
- 启用时按 NDJSON 写入 `~/.cameraq/diagnostics/composition/`；单文件达到 20MB 后轮转。
- 启动和显式清理时删除超过 7 天的文件；用户可清空内存缓冲和持久化文件。
- 写入失败不得影响分析结果或取景线程。

## Internal Entities

内部实体放在 `src/core/composition/features.py`，不进入公共 JSON 契约。

### `CompositionFeatures`

- 原始帧尺寸与分析帧尺寸
- 灰度图、边缘图、梯度幅值和方向
- 过滤后的线段及长度加权方向直方图
- 平行线族、有效交点和汇聚中心候选
- 简化轮廓、轮廓层级、嵌套深度和近矩形标记
- 主体中心、主体权重、显著焦点和视觉质量图
- 质量质心、四象限质量、左右/上下镜像差异
- 角点与重复间距候选
- 曝光、模糊、边缘覆盖和总体证据质量

数组为只读约定；评分器不得原地修改。

### `ModeTemporalRecord`

| Field | Meaning |
|-------|---------|
| `state` | `ABSENT`, `CANDIDATE`, `ACTIVE`, `FADING` |
| `smoothed_score` | 当前平滑匹配度 |
| `above_enter_count` | 连续达到进入门槛次数 |
| `below_exit_count` | 连续低于退出门槛次数 |
| `state_since` | 当前状态开始时间 |
| `last_evidence` | 最近稳定证据 |

## Relationships

```text
AnalysisResult
└── CompositionAnalysis (0..1)
    ├── CompositionModeResult (exactly 15)
    │   └── CompositionEvidence (0..n; visible result >=1)
    └── TargetCompositionRecommendation (0..1)
        └── target_mode -> CompositionModeResult.mode
```

## State Transitions

```text
ABSENT
  └─ score >= enter threshold ─> CANDIDATE

CANDIDATE
  ├─ 3 consecutive enters ─────> ACTIVE
  └─ score < exit threshold ───> ABSENT

ACTIVE
  └─ 3 consecutive exits ──────> FADING

FADING
  ├─ score recovers ───────────> ACTIVE
  └─ next stable output ───────> ABSENT

Any state
  └─ material scene change ────> ABSENT (high-confidence first-frame exception allowed)
```

## Validation Invariants

1. `top_modes` 长度不得超过 3，且不能重复。
2. `mode_results` 必须覆盖全部 15 个模式且不能重复。
3. `insufficient_evidence=true` 时，`recommendation` 必须为 `None` 或 `KEEP`。
4. 非 `KEEP` 推荐必须来自 `MEDIUM` 或 `HIGH` 可信候选，且 `projected_score > current_score`。
5. 所有公开证据坐标都必须在 `[0,1]` 内。
6. 显示结果必须至少有一条可解释证据。
7. 匹配度、可信等级和推荐优先级字段不得互相替代。
8. 诊断缓冲区最多 300 条；磁盘诊断仅在用户启用时写入，且不得包含原始图像。
