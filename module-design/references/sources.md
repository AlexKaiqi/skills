# 研究依据与取舍

本技能围绕“agent 从需求拆出问题，再推导合理模块”的目标编写，没有安装或复制其他技能。以下为 2026-09-24 查阅的原始方法与技能作者仓库；它们提供不同层面的依据，不是一套必须全部执行的架构流程。

## 重点参考：Anthropic Knowledge Work Plugins

已读取 [knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) 的实际技能内容；本次核对版本为 `1c7187c4fc17feefa6cde39517f12dae1249e6c4`。重点是产品问题澄清、规格化与架构决策之间的工作衔接，不能只凭 `design` 或 `system-design` 的名称判断适用性。

| 实际读取的文件 | 对当前痛点的价值 | 本技能的吸收与边界 |
| --- | --- | --- |
| [product-brainstorming](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/product-management/skills/product-brainstorming/SKILL.md) | 区分问题探索、方案生成和假设检验，先质疑前提再收敛 | 按输入状态选择起点，补上解决方向与关键假设验证；不照搬固定 5–7 个方案、全部框架或暂停交付 |
| [write-spec](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/product-management/skills/write-spec/SKILL.md) | 把想法约束为用户结果、范围、可验收行为与待决问题 | 子问题必须有依据及验收；区分决定性未知与可稍后解决的细节。不强制写完整 PRD 或先连接外部工具 |
| [architecture](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/engineering/skills/architecture/SKILL.md) | 让决定包含上下文、备选、取舍和后果 | 边界选择必须有明确推荐、接受的代价和重新评估条件；不强制每个模块一份 ADR |
| [system-design](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/engineering/skills/system-design/SKILL.md) | 提醒纳入规模、成本、可用性等现实约束 | 当前内容从需求转入组件、接口、存储等技术设计，没有细化从子问题推导职责边界的方法；不能直接替代本技能的模块推导主线 |
| [brainstorm command](https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/product-management/commands/brainstorm.md) | 根据输入调整工作方式，利用已有上下文，避免一次抛出大量问题 | 先查资料再澄清，持续推进；保留用户要求落地时完成工作的责任，不照搬其仅讨论、不主动产出总结的规则 |

另外核对了 `design-critique`、`research-synthesis`、`process-optimization` 与 `sprint-planning`：分别偏界面评审、研究证据、流程优化与交付排期，不把这些对象的分解直接等同于业务模块分解。

本地方法是针对用户目标的组合：从这些技能吸收 **输入判断、问题澄清、假设验证、范围与验收、决定后果**；用下述模块设计原理补齐 **共同知识的封装、拆合成本和变化检验**。这些依据指导判断，不规定模块数量、目录形式或文档模板。上游提供的是工作方法参考，没有证明照用它就能自动得到高质量模块设计。

## 直接支撑问题分解与模块推导的方法

| 原始材料 | 解决哪一步 | 在本技能中的转化 |
| --- | --- | --- |
| [Parnas：On the Criteria To Be Used in Decomposing Systems into Modules](https://www.cs.lafayette.edu/~gexia/cs301/resources/parnas.html)（1972 论文的大学网页转载） | 如何选择拆模块的依据 | 封装重要且可能变化的设计知识；不能从执行步骤直接生成模块。要求说明模块隐藏什么，以及变化被限制在哪里 |
| [John Ousterhout：Stanford CS190 Modular Design](https://web.stanford.edu/~ouster/cgi-bin/cs190-winter18/lecture.php?topic=modularDesign) | 如何避免拆成大量浅薄组件 | 检查接口给调用者增加的知识负担；对关键边界比较实质不同的方案；不以大小或模块数量为优劣标准 |
| [Domain Storytelling Quick-Start Guide](https://domainstorytelling.org/quick-start-guide) 与 [DDD 应用说明](https://domainstorytelling.org/domain-driven-design) | 如何把含糊需求变成可讨论的具体行为 | 用参与者、活动与工作对象描述具体场景，记录假设；场景提供分解证据，不机械地一步一个模块 |

从可验证问题识别共同知识、比较边界成本、回到场景与变化检验，并在当前承诺已清楚时收敛，是本技能的综合方法。不要求固定表格或逐步产出文件，也不声称任何来源提供了自动发现模块的算法。

## DDD 方法的取舍

| 材料 | 吸收的判断 | 没有照搬的部分 |
| --- | --- | --- |
| [DDD Starter Modelling Process](https://github.com/ddd-crew/ddd-starter-modelling-process) | 从业务理解推导候选边界，允许反复修正 | 不把建模变成固定串行仪式，不强制所有战术模式 |
| [Bounded Context Canvas](https://github.com/ddd-crew/bounded-context-canvas) | 用业务目的、语言、决定、输入输出与假设检验边界；尝试调整责任归属 | 不要求为每个目录填完整画布，不把目录自动认作上下文 |
| [Refactoring Module Dependencies](https://martinfowler.com/articles/refactoring-dependencies.html) | 从变化影响判断模块边界，降低完成局部工作需要理解的范围 | 不用图上依赖数量替代业务判断 |

## 类似技能的实际对照

| 已查看的技能 | 有帮助的做法 | 与本次目标的差距/不采用的约束 |
| --- | --- | --- |
| [ddd-agent-skill](https://github.com/aristorinjuang/ddd-agent-skill/blob/main/SKILL.md) | 简单需求避免过量 DDD；先业务建模，再实现 | 侧重完整 DDD 流程；不采纳集中写入 docs、每阶段固定提问、强制完整类图或一上下文默认一服务 |
| [ZSL domain-modeling](https://github.com/ZunoSmartLabs/zsl-superpowers/blob/main/skills/engineering/domain-modeling/SKILL.md) | 模块围绕业务责任组织，检查外部模型含义与公开契约 | 规则集合较多；不引入整套书籍规则和依赖技能，不能以规则清单替代问题推导 |
| [Clairvoyance module-boundaries](https://github.com/codybrom/clairvoyance/blob/main/skills/module-boundaries/SKILL.md) | 双向检查拆与合、共同知识与独立理解 | 从已有代码和模块出发，更偏边界评审；本技能补上前面的目标和子问题分解，不自动抽取共享模块 |
| [software-design-philosophy](https://github.com/wondelai/skills/blob/main/software-design-philosophy/SKILL.md) | 信息隐藏、接口负担、按知识而非时间顺序组织 | 不采用固定分数和目标满分，不把一般设计原则直接当作可执行的问题拆解步骤 |

本技能的“单一业务使用者内容必须内聚”是针对本次设计偏好的明确约束；不能借来源之名把它泛化成“所有单调用者的业务模块都必须消失”。工具只提供可核对的声明证据，领域语义、独立变化原因与规则完整性由场景推演判断。
