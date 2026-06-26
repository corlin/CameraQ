# Research: Professional Performance & UX Deep Optimization

## Phase 0 Findings

### Decision 1: Render Pipeline Optimization Strategy
- **Decision**: Cache fonts at init; throttle expensive per-frame operations; eliminate redundant image copies.
- **Rationale**: Profiling shows the PIL conversion chain (BGR→RGBA→composite→RGB→BGR) is unavoidable for Chinese text rendering, but we can minimize the overhead around it. Font file lookup (`os.path.exists` × 4) every frame is pure waste.
- **Alternatives considered**: Migrating to PyQt/Tkinter was rejected — too heavy and breaks the existing architecture. Pre-rendering text to textures was considered but adds complexity for marginal gain.

### Decision 2: Multi-Dimensional Scoring Model
- **Decision**: Use the existing `CompositionScore` Pydantic model (5 sub-scores) and implement both positive and negative factors.
- **Rationale**: A deduction-only system (start at 100, subtract) provides no positive reinforcement. Professional photography coaching requires recognizing good technique, not just penalizing mistakes.
- **Alternatives considered**: ML-based scoring was rejected — requires training data and model serving infrastructure that's out of scope.

### Decision 3: Thread Safety Approach
- **Decision**: Use `threading.Lock` in `SettingsManager` for shared state protection.
- **Rationale**: The settings object is read in the analysis thread and written in the UI thread. A simple lock is sufficient given the low contention (settings change infrequently).
- **Alternatives considered**: `threading.RLock` (unnecessary — no re-entrant access patterns), `queue.Queue` for message passing (over-engineering for boolean/float state).
