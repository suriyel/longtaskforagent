# 契约—实现漂移协议

## 触发条件

Green 或 Refactor 阶段发现实现的**公共符号**与 `docs/features/<id>-<slug>.md`（Feature Design；由 `scripts/feature_paths.py` 派生）对应章节不一致：

| 符号类型 | 设计节 | 典型偏离 |
|---------|-------|---------|
| 接口签名（方法名 / 参数 / 返回类型 / 抛出异常） | §4 Interface Contract | 重命名方法、增减参数、改返回类型 |
| UI 视觉选择器 / 渲染触发点 | §5 Visual Rendering Contract | 换选择器、改 DOM 结构 |
| 模块职责 / 调用链 | §6 Implementation Summary | 把 Service 职责下沉到 Controller、跨模块移动函数 |
| 数据字段（名 / 类型 / 可空性） | §8 Data Model | 改字段名、换类型、删字段 |

## 方向判据

回答一个问题：**"此次偏离是否带来独立价值或必要性？"**

| 答案 | 处置 |
|-----|-----|
| **是**（设计有歧义 / 实现方式客观更优 / 原设计在本代码库约束下不可实现） | **更新设计** |
| **否**（随意重命名 / 越权跨模块 / 为局部简便牺牲接口） | **回滚实现** |

设计是权威源：除非偏离本身承载价值，否则永远优先改实现。

## 更新设计的四步流程

1. 在 `{feature_design_path}` 中更新对应节（§4 / §5 / §6 / §8）以匹配新的实现真相
2. 复查测试清单的相应行：
   - §4 改动 → 复查 §7 Test Inventory（接口变了，测试断言也要变）
   - §5 改动 → 复查 `UI/render` 行（选择器 / 渲染触发要同步）
   - §6 改动 → 复查模块边界测试（调用链变了，单元切分可能要变）
   - §8 改动 → 复查数据断言（字段变了，assertion 要变）
3. 设计文档更新与实现代码放在**同一次 git 提交**（`commit` 同时含 `docs/features/*.md` 与 `src/*` 与测试改动）
4. 记录 drift 到 Structured Return Contract 的 `next_step_input.design_alignment.<节>`，值为 `"updated(commit:<sha>)"`

## 无法本地决策

若 SubAgent 判断不出偏离是否合理（例如涉及团队约定、跨特性影响），**不要**在本地择一而行。

- 返回 `status: blocked`
- `blockers[]` 添加前缀 `[CONTRACT-DEVIATION]` 的条目，描述两种走向的取舍
- `long-task-work-tdd` 在 Step 3d 聚合后由主 agent 组装用户裁决（approval-revise-loop 的 `[CONTRACT-DEVIATION]` 行定义了 A/B 选项）

## 理由

任何契约—实现不一致都会在下游被放大：

- **Inline Check P2**（契约一致性）会因公共符号签名漂移拒绝合入
- **Inline Check T2**（测试清单覆盖）会因 §7 未同步漂移断言而漏网
- **Inline Check D3**（数据字段）会因 §8 与 schema 不符触发
- **Inline Check U1**（UI 选择器）会因 §5 与实际 DOM 不符触发

让设计文档作为与现实保持一致的"活文档"，才能保证后续 feature-st / ST 阶段的断言始终指向正确的接口面。
