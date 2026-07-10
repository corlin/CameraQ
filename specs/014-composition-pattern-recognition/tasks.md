# Tasks: 实时构图模式识别与引导

**Input**: `specs/014-composition-pattern-recognition/` 下的 spec、plan、research、data model、contract 与 quickstart

**Prerequisites**: [plan.md](./plan.md)、[spec.md](./spec.md)、[research.md](./research.md)、[data-model.md](./data-model.md)、[contracts/](./contracts/)

**Tests**: 014 规格和计划明确要求测试先行、15 类验收、时序稳定和性能门禁，因此每个用户故事均包含先失败后实现的测试任务。

**Organization**: 任务按用户故事组织。US1 是可独立交付的识别 MVP；US2、US3、US4 的核心模块可在基础层完成后并行开发，其最终编排依赖 US1 的结果契约。时序状态只由 `temporal.py`/engine 拥有，Analyzer 仅负责时间门与完整结果缓存。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可在不同文件中并行执行，且不依赖同阶段尚未完成的任务
- **[Story]**: 对应 `spec.md` 中的用户故事
- 每项任务都包含明确文件路径

## Phase 1: Setup（共享结构）

**Purpose**: 建立构图域和测试夹具结构，不修改现有分析行为

- [x] T001 Create composition package and scorer package skeletons in `src/core/composition/__init__.py` and `src/core/composition/scorers/__init__.py`
- [x] T002 [P] Create deterministic synthetic composition image factory for lines, grids, contours, focal points, blur, and noise in `tests/fixtures/composition/factory.py`
- [x] T003 [P] Define fixture metadata, ground-truth multi-label format, and provenance rules in `tests/fixtures/composition/README.md` and `tests/fixtures/composition/manifest.json`
- [x] T004 [P] Add shared composition pytest fixtures and assertion helpers in `tests/unit/core/composition/conftest.py`

---

## Phase 2: Foundational（阻塞基础）

**Purpose**: 建立四个用户故事共同依赖的实体、几何函数、阈值和共享特征提取器

**⚠️ CRITICAL**: 此阶段完成前不得开始用户故事实现

### Tests first

- [x] T005 [P] Write failing public-entity invariant tests for 15 unique modes, score ranges, normalized coordinates, Top 3 limits, and recommendation constraints in `tests/unit/core/composition/test_entities.py`
- [x] T006 [P] Write failing geometry tests for normalized distances, line angles, bounded intersections, point-to-line distance, contour enclosure, and weighted orientation bins in `tests/unit/core/composition/test_geometry.py`
- [x] T007 [P] Write failing shared-extractor tests for downscaling, immutable feature snapshots, primary-subject focus plus all-subject visual-mass contribution, visual-mass fallback, line filtering, contour hierarchy, evidence quality, and empty frames in `tests/unit/core/composition/test_extractor.py`

### Foundational implementation

- [x] T008 Implement `CompositionMode`, confidence/evidence/action enums, normalized geometry, mode results, recommendation, and `CompositionAnalysis` with validation in `src/core/entities.py`
- [x] T009 [P] Implement internal immutable line, contour, focal-node, convergence, and `CompositionFeatures` records in `src/core/composition/features.py`
- [x] T010 [P] Implement normalized geometry, intersection filtering, orientation clustering, contour containment, and visual-mass helper functions in `src/core/composition/geometry.py`
- [x] T011 [P] Centralize analysis size, mode weights, evidence gates, enter/exit thresholds, and quality thresholds in `src/core/composition/thresholds.py`
- [x] T012 Implement the single-pass 320px grayscale, edge, gradient, line, contour, corner, convergence, visual-mass, and evidence-quality pipeline in `src/core/composition/extractor.py`

**Checkpoint**: 构图实体与共享特征快照可独立构造和验证，T005–T007 全部通过

---

## Phase 3: User Story 1 - 识别当前构图模式 (Priority: P1) 🎯 MVP

**Goal**: 对 15 种非互斥构图分别输出证据匹配度、可信等级与证据，并默认显示稳定 Top 3

**Independent Test**: 运行 15 类合成正例、困难反例和多标签组合图；同一画面可命中“三分法 + 对角线”，弱结构画面显示证据不足，Top 3 永不超过 3 个

### Tests for User Story 1

- [x] T013 [P] [US1] Write failing JSON-contract parity tests for all required fields, 15 mode enums, normalized evidence coordinates, and no raw-image fields in `tests/unit/core/composition/test_contract.py`
- [x] T014 [P] [US1] Write failing tests for thirds, dynamic symmetry, balance, and triangle positive/negative boundaries in `tests/unit/core/composition/test_position_scorers.py`
- [x] T015 [P] [US1] Write failing tests that distinguish diagonal/oblique and horizontal/vertical/cross while rejecting short texture noise in `tests/unit/core/composition/test_linear_scorers.py`
- [x] T016 [P] [US1] Write failing tests that distinguish radial/centripetal and frame/tunnel plus curve/checkerboard false positives in `tests/unit/core/composition/test_topology_scorers.py`
- [x] T017 [P] [US1] Write failing engine tests for exactly 15 results, evidence gates, match-score/confidence separation, insufficient evidence, and Top 3 ordering in `tests/unit/core/composition/test_engine.py`

### Implementation for User Story 1

- [x] T018 [P] [US1] Implement thirds, dynamic symmetry, balanced, and triangle scorers with localized evidence in `src/core/composition/scorers/position.py`
- [x] T019 [P] [US1] Implement diagonal, horizontal, oblique, cross, and vertical scorers with span and texture-noise gates in `src/core/composition/scorers/linear.py`
- [x] T020 [P] [US1] Implement curve, radial, checkerboard, centripetal, tunnel, and frame scorers with topology gates in `src/core/composition/scorers/topology.py`
- [x] T021 [US1] Implement scorer registry, evidence-quality gating, 15-result completeness, match/confidence separation, and Top 3 selection in `src/core/composition/engine.py`
- [x] T022 [P] [US1] Write failing analyzer integration tests for optional `composition_analysis`, deterministic primary selection with multiple subjects, subject/saliency reuse, multi-label output, weak-evidence fallback, and backward-compatible `AnalysisResult` construction in `tests/unit/core/test_analyzer.py`
- [x] T023 [US1] Instantiate and invoke `CompositionEngine` after subject fusion without changing the existing five-axis score in `src/core/analyzer.py`
- [x] T024 [P] [US1] Write failing overlay tests for no-result, insufficient-evidence, single-result, and Top 3 result states in `tests/unit/ui/test_overlay.py`
- [x] T025 [US1] Render current composition names and bounded Top 3 summaries by coaching level in `src/ui/overlay.py`

**Checkpoint**: US1 可独立演示；15 类结果完整，多标签与弱证据行为符合规格，当前 Top 3 可见

---

## Phase 4: User Story 2 - 推荐可达的目标构图 (Priority: P1)

**Goal**: 从当前可靠证据中选择最多一个可通过小幅镜头动作达到的目标构图；强构图保持，低证据不建议

**Independent Test**: 使用人工构造的 `CompositionModeResult` 和焦点位置运行推荐器；靠近三分点时给出正确平移方向，强构图返回 `KEEP`，曲线/棋盘等不可执行场景不编造动作

### Tests for User Story 2

- [x] T026 [P] [US2] Write failing recommendation unit tests for action allowlists, adjustment cost, projected improvement, direction correctness, `MOVE_CLOSER` below 8% subject area, `MOVE_BACK` above 45% or clipping, `KEEP`, and low-confidence suppression in `tests/unit/core/composition/test_recommender.py`
- [x] T027 [P] [US2] Write failing recommendation journey tests for near-thirds, dominant-line rotation, existing tunnel alignment, too-small/too-large subjects, strong-current-composition, and no-actionable-candidate cases in `tests/integration/test_composition_recommendation.py`
- [x] T028 [P] [US2] Write failing overlay tests for movement, rotation, keep, aligned, and no-recommendation states in `tests/unit/ui/test_overlay.py`

### Implementation for User Story 2

- [x] T029 [US2] Implement per-mode action allowlists, candidate utility, adjustment cost, projected score, and one-result selection in `src/core/composition/recommender.py`
- [x] T030 [US2] Connect recommendation generation to high-confidence current mode results and expose at most one recommendation; leave temporal visibility filtering to T036 in `src/core/composition/engine.py`
- [x] T031 [US2] Render concise target mode, action, alignment target, and `KEEP` state without obscuring current Top 3 in `src/ui/overlay.py`

**Checkpoint**: US2 的推荐器可用构造结果独立测试，并能与 US1 结果集成；无可靠可执行候选时保持安静

---

## Phase 5: User Story 3 - 获得稳定且可解释的反馈 (Priority: P2)

**Goal**: 标签在轻微抖动中保持稳定、换景后及时更新，并在 PRO 模式显示可定位证据

**Independent Test**: 向状态机输入门槛附近波动和实质换景序列；固定场景不逐帧闪烁，新场景 1 秒内替换旧标签，每个可见标签至少有一条可绘制证据

### Tests for User Story 3

- [x] T032 [P] [US3] Write failing temporal-state tests for first-frame display, three-sample entry/exit, hysteresis hold, recovery, and material-scene reset in `tests/unit/core/composition/test_temporal.py`
- [x] T033 [P] [US3] Write failing evidence-rendering tests for normalized points, lines, simplified contours, confidence badges, and coaching-level visibility in `tests/unit/ui/test_overlay.py`
- [x] T034 [P] [US3] Write failing 30-second jitter, rapid-scene-change, and 90-degree displayed-frame orientation-change replay tests with deterministic timestamps in `tests/integration/test_composition_stability.py`

### Implementation for User Story 3

- [x] T035 [US3] Implement per-mode `ABSENT/CANDIDATE/ACTIVE/FADING` records, score smoothing, dual thresholds, consecutive counts, and scene-reset behavior in `src/core/composition/temporal.py`
- [x] T036 [US3] Integrate temporal visibility, stable duration, first-frame exception, and scene-change detection into `src/core/composition/engine.py`
- [x] T037 [US3] Draw normalized evidence points, lines, contours, match score, and confidence only at permitted coaching levels in `src/ui/overlay.py`
- [x] T038 [US3] Integrate the engine-owned stable result as an opaque `CompositionAnalysis`; do not duplicate per-mode temporal state in Analyzer in `src/core/analyzer.py`

**Checkpoint**: US3 状态机可独立验证；轻微抖动不闪烁，实质换景不残留，PRO 证据与结果一一对应

---

## Phase 6: User Story 4 - 完全离线地保持实时取景 (Priority: P2)

**Goal**: 构图功能断网可用、独立 5Hz 更新、平均分析 <25ms、实时取景不受阻，并可由用户关闭

**Independent Test**: 禁用网络客户端和构图外重模型，连续输入 720p 帧；构图结果至少 5Hz 更新，缓存帧不重复分析，关闭开关后无构图工作，平均耗时低于 25ms

### Tests for User Story 4

- [x] T039 [P] [US4] Write failing settings tests for `composition_detection_enabled`, `composition_analysis_interval_s=0.15`, and `composition_diagnostics_enabled` validation, persistence, toggle, and defaults in `tests/unit/core/test_settings.py`
- [x] T040 [P] [US4] Write failing analyzer timing tests for immediate first analysis, 150ms monotonic time gate, 10-second actual update rate ≥5Hz, cache reuse, disabled bypass, and detector-failure fallback in `tests/unit/core/test_analyzer.py`
- [x] T041 [P] [US4] Write failing offline/privacy integration tests that prohibit Gemini/network calls, verify a 300-record ring buffer, default no-disk behavior, opt-in NDJSON without raw frames, 20MB rotation, 7-day retention, and clear operation in `tests/integration/test_composition_pipeline.py`
- [x] T042 [P] [US4] Extend performance coverage with warmed 720p average <25ms/p95 reporting, 10-second update-rate measurement, and a slow 5-minute 1280×720 end-to-end average FPS ≥25/p95 frame interval ≤80ms/p95 control response ≤100ms benchmark in `tests/integration/test_performance.py`

### Implementation for User Story 4

- [x] T043 [US4] Implement the 300-record session ring buffer, opt-in NDJSON writer, 20MB rotation, 7-day cleanup, clear operation, and failure isolation in `src/core/composition/diagnostics.py`
- [x] T044 [US4] Add composition enablement, 0.15-second interval, diagnostics opt-in defaults, validation, persistence, and sidebar toggle metadata in `src/core/settings.py`
- [x] T045 [US4] Add monotonic 150ms gating, cached-result reuse, disabled bypass, exception isolation, diagnostics handoff, and processing-time measurement in `src/core/analyzer.py`
- [x] T046 [US4] Add composition/diagnostics toggles and a user-accessible clear-diagnostics control; ensure disabled state clears only composition overlays in `src/ui/overlay.py`

**Checkpoint**: US4 在无网络环境独立可用；时间门、缓存、关闭开关和性能门禁全部通过

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 校准真实场景、完成文档和执行全量验收

- [x] T047 Define an annotation rubric and license/provenance audit; then curate at least 20 redistributable real positive examples and 20 hard negatives per mode, a 100-sample degraded set with 25 per required category, and at least 50 controlled recommendation scenes covering each action. Require source-independent labels (never algorithm self-labels), explicit ambiguous/rejected cases, reviewer status, dataset-split/leakage checks, multi-label truth, and provenance in `tests/fixtures/composition/README.md`, `tests/fixtures/composition/images/`, and `tests/fixtures/composition/manifest.json`
- [ ] T048 Calibrate centralized evidence weights and enter/exit thresholds against the acceptance manifest, then record per-mode precision/recall with abstentions counted as false negatives, Top 3 coverage, degraded-set abstention rate, and recommendation improvement rate in `src/core/composition/thresholds.py` and `specs/014-composition-pattern-recognition/validation.md`
- [x] T049 [P] Document offline composition recognition, 15 supported modes, match-score semantics, diagnostic retention/privacy, coaching-level behavior, and controls in `README.md`
- [ ] T050 Run unit, integration, contract, full regression, 10-second update-rate, slow 5-minute end-to-end benchmark, and `quickstart.md` manual scenarios; append baseline hardware, environment, timings, failures, and evidence to `specs/014-composition-pattern-recognition/validation.md`
- [x] T051 Verify all FR-001–FR-016 and SC-001–SC-009 against implementation evidence, confirm JSON contract compatibility and `git diff --check`, and record remaining gaps in `specs/014-composition-pattern-recognition/validation.md`

**Progress evidence (2026-07-03)**:

- T047: complete. The manifest contains 523 unique licensed Commons candidates plus 150 deterministic cases. The temporary Codex visual pass records 328 accepted real cases, 173 rejected decisions, and 22 pending cases without representing the reviewer as human ground truth. All 15 modes now meet at least 20 accepted positives and 20 accepted hard negatives; the manifest has zero duplicate sources, orphan files, hash failures, split leakage, or count issues. A deterministic source-family-aware stratifier assigns 134 accepted real cases to calibration and 194 to untouched acceptance while preserving all 30 core mode/class strata and 82 joint mode/class/source-family strata.
- T048: degraded abstention, recommendation improvement, and recommendation action metrics remain 100% after the evaluator was aligned with runtime saliency and restricted to the untouched acceptance split. TDD scorer work now covers thirds, dynamic symmetry, triangle, curve, radial, centripetal, frame, cross, balance mirror evidence, quiet tunnel balance, smooth low/vertical thirds, horizontal band fallback, shallow corridor dynamic symmetry, radial texture fallback, centered arch curves, checkerboard fallback/regularity boundaries, high-confidence underrepresented-mode Top 3 ranking protection, and strong-centripetal ranking protection; confidence is relative to per-mode thresholds. The 0.80-precision-constrained proposal now reaches 80.50% acceptance macro precision and 70.36% recall, so SC-003 passes. Candidate-threshold Top 3 case coverage improved to 77/138 (55.80%) but SC-004 still fails; proposed thresholds remain diagnostic and T048 stays open.
- T050: full regression, the full 300-second synthetic engine/overlay benchmark, and a no-save 30-second live-camera run pass. Five retained non-camera UI evidence images now cover MINIMAL/COACH/PRO, disabled composition, and the settings sidebar; their JSON assertions cover line counts, recommendation, evidence geometry, and all composition controls. Visual review fixed missing-glyph emoji and overlapping composition sidebar labels. OpenCV exposes zero accessible windows to macOS Accessibility, so real coaching-level/sidebar interaction and named-scene quickstart checks remain manual; minimum-device verification is also pending.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖，可立即开始。
- **Foundational (Phase 2)**: 依赖 Setup，阻塞全部用户故事。
- **US1 (Phase 3)**: 依赖 Foundational；构成 MVP。
- **US2 (Phase 4)**: 推荐器核心可在 Foundational 后用构造结果开发；T030–T031 的产品集成依赖 US1 的 T021 与 T025。
- **US3 (Phase 5)**: 状态机核心可在 Foundational 后开发；T036–T038 的产品集成依赖 US1 的 T021、T023 与 T025。
- **US4 (Phase 6)**: 设置、诊断与时间门测试可在 Foundational 后开发；完整性能和离线集成验收依赖 US1 完成。
- **Polish (Phase 7)**: 依赖计划交付范围内的所有用户故事完成。

### User Story Dependency Graph

```text
Setup
  └── Foundational
      ├── US1 当前构图识别 (MVP)
      │   ├── US2 产品集成
      │   ├── US3 产品集成
      │   └── US4 完整性能/离线验收
      ├── US2 推荐器核心
      ├── US3 时序核心
      └── US4 设置与时间门核心

US1 + US2 + US3 + US4
  └── Polish / acceptance calibration
```

### Within Each User Story

- 测试任务必须先完成并确认因缺失功能而失败，再写实现。
- 纯函数与实体先于编排器，编排器先于 Analyzer/UI 集成。
- 同一文件的任务不得并行修改；标有 `[P]` 的任务只在文件不冲突且前置已满足时并行。
- 每个 Checkpoint 必须能独立运行对应测试，不依赖下一用户故事。

## Parallel Opportunities

### Foundational

完成 T001 后，可并行执行：

```text
T005 entity invariant tests
T006 geometry tests
T007 extractor tests
```

完成测试后，T009、T010、T011 可在不同文件并行，T012 等待三者。

### User Story 1

完成 Foundational 后，可并行执行：

```text
T013 contract tests
T014 position scorer tests
T015 linear scorer tests
T016 topology scorer tests
T017 engine tests
```

随后 T018、T019、T020 可并行，T021 等待三个 scorer 组。

### User Story 2

T026、T027、T028 可并行；T029 等待 T026，T030 等待 T029 与 US1 engine，T031 等待 overlay 测试和推荐结果契约。

### User Story 3

T032、T033、T034 可并行；T035 等待 T032，T036 等待 T035 与 US1 engine，T037 与 T038 在不同文件中可并行。

### User Story 4

T039、T040、T041、T042 可并行编写；T043 与 T044 可在不同文件并行，T045 等待二者及 US1 engine，T046 等待设置契约。

## Implementation Strategy

### MVP First：US1 Only

1. 完成 Phase 1 Setup。
2. 完成 Phase 2 Foundational。
3. 完成 Phase 3 US1。
4. 停止扩展并验证：15 类结果完整、多标签、弱证据弃权、Top 3 和 UI 显示。
5. MVP 通过后再引入推荐、时序和性能控制，避免一次调试四层行为。

### Incremental Delivery

1. **Foundation**：实体 + 共享特征 + 几何工具。
2. **US1/MVP**：15 评分器 + Top 3 + 当前构图显示。
3. **US2**：可执行推荐 + 保持/不建议。
4. **US3**：迟滞稳定 + 证据可视化。
5. **US4**：离线、节流、缓存、开关和性能门禁。
6. **Polish**：真实验收集校准与完整 SC 验证。

## Task Summary

| Area | Tasks |
|------|-------|
| Setup | T001–T004 (4) |
| Foundational | T005–T012 (8) |
| US1 | T013–T025 (13) |
| US2 | T026–T031 (6) |
| US3 | T032–T038 (7) |
| US4 | T039–T046 (8) |
| Polish | T047–T051 (5) |
| **Total** | **51** |

## Notes

- `[P]` 仅表示在前置满足后可由不同执行者并行，不表示可以跳过依赖。
- 每个测试任务都应先观察到与目标功能对应的失败，再实现通过。
- 不得把规则匹配度重命名为模型概率。
- 不得在构图模块中引入网络调用或默认保存原始帧。
- 不得在实现期间顺带重写现有五轴评分、Gemini Coach 或非 014 UI。
- 每个用户故事完成后运行其独立测试并形成小而清晰的提交边界。
