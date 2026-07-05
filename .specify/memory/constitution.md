<!--
Sync Impact Report
- Version change: template (unratified) -> 1.0.0
- Added principles:
  - I. 本地实时核心
  - II. 证据优先与语义诚实
  - III. 性能预算与优雅降级
  - IV. 测试先行与可复现验收
  - V. 模块边界与向后兼容
- Added sections:
  - 技术、隐私与数据约束
  - 开发流程与质量门禁
- Removed sections: none (template placeholders replaced)
- Templates:
  - ✅ .specify/templates/plan-template.md
  - ✅ .specify/templates/spec-template.md
  - ✅ .specify/templates/tasks-template.md
  - ✅ .specify/templates/checklist-template.md (compatible; no change required)
  - ✅ .specify/templates/commands/ (directory absent; Codex skills mode is used)
- Runtime guidance:
  - ✅ README.md (existing run/test guidance remains compatible)
- Deferred items: none
-->

# CameraQ Constitution

## Core Principles

### I. 本地实时核心

所有影响取景、构图、快门时机和基础摄影建议的核心能力 MUST 在无网络条件下可用。
联网生成式能力 MAY 提供补充解释，但 MUST 异步执行、可关闭、可超时，并且不得阻塞相机、
本地分析或拍摄操作。新增核心能力必须明确其离线路径和网络降级行为。

**Rationale**: 摄影辅助发生在瞬时取景中；网络延迟、配额或中断不能破坏基础功能。

### II. 证据优先与语义诚实

面向用户的分数、标签和建议 MUST 有可检查的本地证据、清晰定义和适用边界。规则加权分
不得被称为概率；未经标定的模型输出不得被描述为置信概率。系统证据不足时 MUST 明确弃权、
降低可信等级或保持安静，不得为了总有答案而制造高置信结论。

**Rationale**: 摄影审美允许多解，产品可信度来自证据、边界和诚实的不确定性表达。

### III. 性能预算与优雅降级

每项实时分析能力 MUST 在规格中声明可测量的延迟、更新频率和端到端取景目标，并在基准设备
上验证。昂贵工作 MUST 采用共享特征、节流、缓存或后台线程隔离。性能预算超限时，系统 MUST
优先降低分析频率、分辨率或非核心覆盖层，而不是阻塞显示线程或拍摄操作。

**Rationale**: 可持续的实时体验比单帧算法的峰值精度更重要。

### IV. 测试先行与可复现验收

所有行为变更和缺陷修复 MUST 先建立能够失败的自动化测试，再实施代码。视觉规则 MUST 同时
覆盖清晰正例、临界样例、困难反例和退化输入；性能与稳定性要求 MUST 有独立基准或可重复回放。
网络能力测试 MUST 可被替身隔离，默认测试套件不得依赖真实外部服务、密钥或摄像头。

**Rationale**: 视觉阈值容易随局部优化漂移，固定夹具和回放证据是防止回归的最低保障。

### V. 模块边界与向后兼容

特征提取、领域判断、时序状态、推荐决策和 UI 渲染 MUST 通过明确实体或契约通信，不得在多个
层级重复拥有同一状态。新增结果字段 SHOULD 默认可选以保护现有调用者；公共枚举、JSON 契约
或设置键发生破坏性变化时 MUST 提供迁移说明。重构 MUST 限于当前功能所需范围。

**Rationale**: 清晰所有权使本地算法可独立测试、替换和优化，也能避免大型 Analyzer/UI 文件继续耦合。

## 技术、隐私与数据约束

- 项目运行基线为 Python 3.12、OpenCV、NumPy、Pydantic 与现有 Ultralytics 模型；新增依赖
  MUST 说明必要性、许可证、包体与性能影响。
- API 密钥、认证信息、原始相机帧和用户可识别数据 MUST NOT 写入版本库、规格、普通日志或
  测试夹具。
- 原始帧 MUST NOT 默认持久化。任何保存或导出 MUST 由用户主动触发，并明确路径、格式、
  保留时间与删除方式。
- 诊断记录 SHOULD 优先保存结构化指标和归一化几何，不保存原始图像；记录格式和留存策略
  MUST 在对应规格中定义。
- 测试图像 MUST 具备可追溯来源和再分发许可，或由项目可复现地合成。
- 性能结论 MUST 记录硬件、系统、输入尺寸、样本数、预热方式、平均值与尾延迟，不能用单次
  最快结果代替基准。

## 开发流程与质量门禁

CameraQ 采用以下顺序管理功能开发：

1. `specify`：定义用户价值、边界、可测量需求与成功标准。
2. `clarify`：解决会改变范围、隐私、性能或体验的关键歧义。
3. `plan`：给出技术上下文、Constitution Check、研究、数据模型、契约和验证方法。
4. `tasks`：按用户故事拆分测试先行、带精确路径和依赖的可执行任务。
5. `analyze`：在实施前检查规格、计划、任务和 Constitution 一致性。
6. `implement`：按任务顺序实施；不得跳过阻塞基础和测试红灯阶段。
7. `converge`：对实现与 FR、SC、契约、任务逐项取证，追加剩余工作直至闭环。

进入实现前 MUST 满足：无 CRITICAL/HIGH 一致性问题、无未解释占位符、关键性能/隐私要求有
专项任务、公共契约有效。宣布完成前 MUST 运行相关单元、集成、性能与回归测试，执行适用的
手工取景场景，记录未验证项，并通过 `git diff --check`。环境限制导致的缺口 MUST 如实报告，
不得以窄测试替代广泛完成声明。

## Governance

本 Constitution 优先于项目中的计划、任务、实现便利和临时约定。修订必须：

1. 说明变更原因、影响的原则和迁移需求；
2. 同步检查 Spec Kit 模板、活动规格和运行指导；
3. 按语义化版本管理：原则删除或不兼容重定义为 MAJOR，新增原则或实质扩展为 MINOR，
   澄清和非语义修订为 PATCH；
4. 在计划、代码评审和收敛验证中显式检查合规性；
5. 对必要例外记录范围、理由、风险、负责人和到期条件，例外不得静默延续。

**Version**: 1.0.0 | **Ratified**: 2026-07-03 | **Last Amended**: 2026-07-03
