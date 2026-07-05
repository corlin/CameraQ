# Quickstart: 014 构图模式识别验证指南

**Feature**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Contract**: [composition-analysis.schema.json](./contracts/composition-analysis.schema.json)

## 1. Prerequisites

- macOS 摄像头，或可由测试夹具读取的本地图像。
- Python 3.12 与项目现有 uv 环境。
- 不需要网络，也不需要 `GEMINI_API_KEY`。

```bash
uv sync
```

## 2. Automated Validation

### 2.1 构图域单元测试

```bash
uv run pytest tests/unit/core/composition -q
```

预期：15 种模式的合成正例、困难反例、空白帧和噪声帧全部通过。

### 2.2 Analyzer 与 Overlay 集成

```bash
uv run pytest \
  tests/unit/core/test_analyzer.py \
  tests/unit/ui/test_overlay.py \
  tests/integration/test_composition_pipeline.py -q
```

预期：`AnalysisResult` 向后兼容，Top 3 不超过 3 个，推荐最多一个，普通/专业覆盖层均能渲染。

### 2.3 性能与完整回归

```bash
uv run pytest tests/integration/test_performance.py -q
uv run pytest tests/ -q
```

预期：构图模块预热后的平均处理耗时低于 25ms，10 秒窗口实际更新率不低于 5Hz，原有测试无回归。

## 3. Offline Camera Validation

确保没有可用 Gemini 密钥后启动：

```bash
env -u GEMINI_API_KEY uv run python src/ui/camera_app.py
```

按 `c` 切换到 `COACH` 或 `PRO`，按 `TAB` 打开设置并确认构图识别已启用。

| 场景 | 操作 | 预期结果 |
|------|------|----------|
| 三分法 + 对角线 | 把人物放在左上三分点，并让道路斜穿画面 | Top 3 同时允许出现“三分法”和“对角线” |
| 横线 | 对准地平线、栏杆或水平层次 | “横线”稳定出现，证据线贴合主水平结构 |
| 垂直线 | 对准建筑立柱或树干列 | “垂直线”稳定出现，不因少量横向纹理消失 |
| 放射/向心 | 对准道路汇聚、天花板辐条或中心主体 | 存在多方向汇聚线；仅有中心主体而无周边收束时不得高分命中放射式 |
| 框式 | 通过门框或窗框拍摄内部主体 | 显示“框式”，证据边界包围主体 |
| 隧道式 | 对准重复门洞、走廊或桥洞 | 显示“隧道式”，同时可出现框式但需有嵌套纵深证据 |
| 棋盘式 | 对准规则窗格或地砖网格 | 两组正交重复线成立时显示“棋盘式” |
| 弱结构 | 对准纯色墙面或严重失焦场景 | 显示证据不足，不强行输出高匹配模式或方向建议 |

## 4. Recommendation Validation

1. 将人物放在三分点附近但不对齐，观察推荐方向。
2. 按提示只移动一次镜头，确认三分法匹配度提高。
3. 对已形成强构图的画面保持相机不动，确认系统输出“保持”或不再要求调整。
4. 对曲线、棋盘或三角形场景，确认系统不会在缺乏可靠可执行变换时编造移动建议。
5. 在至少 50 个近目标回放场景上统计一次提示后的匹配度变化，覆盖平移、旋转、靠近、后退各至少 5 例，改善率应达到 80%。

## 5. Stability Validation

1. 固定同一场景 30 秒，仅做轻微手持晃动。
2. 记录 Top 3 可见标签的进入/退出次数。
3. 预期因阈值波动造成的无意义变化不超过 1 次。
4. 快速转向结构明显不同的新场景，预期 1 秒内替换旧标签。

## 6. UI Level Validation

- `MINIMAL`：只显示首个稳定构图名称。
- `COACH`：显示 Top 3 和最多一个动作建议。
- `PRO`：额外显示匹配度、可信等级、关键点/线/轮廓证据。
- 关闭构图识别：所有构图覆盖消失，取景和其他 CameraQ 功能保持工作。

在无法自动控制 OpenCV 原生窗口时，可先生成不含摄像头画面的确定性 UI 证据：

```bash
uv run python scripts/render_composition_ui_evidence.py
```

该命令输出 MINIMAL、COACH、PRO、关闭构图和侧栏五张 1280×720 图片，以及记录行数、推荐、
证据几何和控件清单的 JSON。它只验证渲染状态，不替代上述真实取景和键鼠手工验收。

## 7. Acceptance Evidence

### 7.1 五分钟端到端性能

在 Apple M1 8 核/8GB、macOS 14 或等效 CPU-only 设备上，以 1280×720 输入连续运行 5 分钟：

- 记录硬件、系统版本、输入尺寸和启用模块。
- 记录平均显示 FPS 与 p95 帧间隔。
- 期间重复切换设置并触发拍摄操作，记录控制事件到界面响应的延迟。
- 预期平均 FPS ≥25，p95 帧间隔 ≤80ms，拍摄/设置操作 p95 响应时间 ≤100ms。

### 7.2 结构化诊断隐私

1. 默认关闭构图诊断记录，确认磁盘没有新增诊断文件。
2. 启用后确认 NDJSON 写入 `~/.cameraq/diagnostics/composition/`，且单条记录不含图像字节或路径。
3. 通过设置侧栏的清除操作验证 300 条内存上限、20MB 文件轮转、7 天清理和内存/文件同步清除。

### 7.3 Evidence to retain

完成验证时保留：

- pytest 输出与性能统计。
- 不含原始图像的结构化 `CompositionAnalysis` 样例。
- 每类验收集的真值清单与误判摘要。
- 手工测试中标签稳定性、推荐前后匹配度和离线运行记录。
- 5 分钟端到端 FPS/p95 帧间隔与操作响应记录。
- 退化专项集的 95% 弃权统计和 50 场景推荐改善率。

不得把规则匹配度描述为“模型概率”。
