# <Project Name> — 软件需求规格说明书

**日期**: YYYY-MM-DD
**状态**: 已批准
**标准**: 对齐 ISO/IEC/IEEE 29148
**输入档位**: L1 / L2 / L3

## 1. 目的与范围
[要解决的核心问题。系统边界。]

### 1.1 范围内
[本版本系统将要完成的内容]

### 1.2 范围外
[明确排除的内容 -- 延期或不在计划内]
[如果在粒度分析过程中有需求被延期，请引用延期积压清单：
"延期需求记录在 [延期积压清单](YYYY-MM-DD-<topic>-deferred.md) 中"]

### 1.3 问题陈述

**根因分析（5-Whys）**:
```
Symptom: [user-stated problem in their words]
Why 1: [first cause]
Why 2: [cause of Why 1]
Why 3: [deepest supported cause]
Root Cause: [systemic cause requirements must address]
```

**待完成任务（Jobs-to-be-Done）**: 当 [情景] 时，我希望 [动机]，以便 [期望结果]。

**痛点地图**:
| 痛点 | 当前替代方案 | 频率 | 严重程度 | 评分 |
|---|---|---|---|---|

**对齐验证**: [PASS / PARTIAL / FAIL -- 由对齐验证步骤填写]

[L2/L3 输入（完全指定的增量规约）§1.3 可整体标 `[不适用]` 并附一句理由（如"已给硬精确规约，无需 5-Whys"）]

### 1.4 存量系统上下文
[仅适用于存量系统项目。新建项目标记"[不适用]"。]

**变更类型**: [新增能力 / 修改现有 / 替换现有 / 扩展现有]

**存量系统清单**:
| 维度 | 现有实现 | 本次变更影响 |
|------|---------|------------|

**变更摘要**: [1-3 句话：什么变了、什么不变]
**涉及模块**: [本次变更涉及的现有模块/目录]
**不涉及模块**: [不受影响的关键模块]

## 2. 术语表与定义
| 术语 | 定义 | 勿与以下混淆 |
|------|-----------|---------------------|
[每个领域特定或有歧义的术语。若无则省略本节。]

## 3. 干系人与用户画像
| 画像 | 技术水平 | 关键需求 | 访问级别 |
|---------|----------------|-----------|--------------|
[若无 UI / 面向终端用户的功能则省略]

### 3.1 用例视图

```mermaid
graph LR
    %% Replace this placeholder with actual content during Step 4c
    %% Actors: use Actor((Name)) syntax as external nodes
    %% Use cases: place inside subgraph System Boundary
    %% Edges: Actor --> UseCaseNode for each participation

    Actor1((Persona Name))
    subgraph System Boundary
        UC1[FR-001: Use Case Title]
        UC2[FR-002: Use Case Title]
    end
    Actor1 --> UC1
    Actor1 --> UC2
```

[若不存在面向用户的功能需求则省略本节]

## 4. 功能需求

> **硬精确条目 1:1 复现约束**：用户原话 / 输入文档中出现的技术标识符（camelCase / snake_case 参数名、文件路径、类型范围、默认值、枚举集合、XML 节点名）必须**原样保留**在 FR / AC / IFR 主体中，大小写、路径分隔符、范围记号完全一致。**禁本地化美化**（例,不得把 `UrbanBuildingSearchRadius` 改成"城市建筑搜索半径配置项"）。这些是**技术契约**不是"原话痕迹"，不计入 Group P 原话痕迹扫描。

### FR-001: <标题>
**优先级**: Must
**EARS**: 当 <触发条件> 时，系统应 <执行动作>。
**验收标准**:
- 给定 <上下文>，当 <执行动作>，则 <预期结果>
- 给定 <错误上下文>，当 <执行动作>，则 <错误处理>

[对每个功能需求重复上述格式]

### 4.1 流程图

[针对包含 3 个以上步骤或分支逻辑的每个功能领域绘制一张流程图 -- 在 Step 4c 期间生成]

#### 流程: <工作流名称>

```mermaid
flowchart TD
    %% Replace this placeholder with actual content during Step 4c
    %% Start/End: ([label]) rounded stadium nodes
    %% Decisions: {condition?} with -- YES --> and -- NO --> labeled branches
    %% Include error/boundary paths from acceptance criteria

    S([Start: trigger])
    D{Decision?}
    B1[Action on YES]
    B2[Action on NO]
    E([End: outcome])

    S --> D
    D -- YES --> B1
    D -- NO --> B2
    B1 --> E
    B2 --> E
```

[为每个独立的功能领域添加额外的 #### 流程节]
[若所有需求都是单步且无分支则省略本节]

## 5. 接口需求

> §4 硬精确条目 1:1 复现约束同样适用于本节：外部系统名、协议标识、数据格式字段名必须原样保留。

| ID | 外部系统 | 方向 | 协议 | 数据格式 |
|----|----------------|-----------|----------|-------------|
| IFR-001 | Payment Gateway | Outbound | REST/HTTPS | JSON |
[若无外部接口则省略]

## 6. 约束
| ID | 约束 | 依据 |
|----|-----------|-----------|
| CON-001 | Must run on Python 3.8+ | Corporate standard |
[若无，填写"未发现"]

## 7. 假设与依赖
| ID | 假设 | 若不成立的影响 |
|----|-----------|------------------|
| ASM-001 | JWT validation handled by API Gateway | Business layer must add validation |
[若无，填写"未发现"]

## 8. 验收标准汇总
[将每个 FR 与其通过/失败标准关联的汇总表或列表]

## 9. 可追溯性矩阵
| 需求 ID | 来源（干系人需求） | 对应痛点 | 验证方法 |
|---------------|-------------------------|---------------------|-------------------|
| FR-001 | User story: "As a user, I want to..." | [痛点地图行标签 或 "无 -- 新增能力"] | Automated test |
[每个需求都必须出现在此矩阵中]

## 10. 待解决问题
[需在设计阶段解决的所有事项。若无，填写"无"。]
