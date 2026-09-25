# 开源方案调研

检查日期：2026-09-25。目标是复用可维护的 Agent Skill/MCP 与官方 API；没有把社区实现作为本能力的必要运行依赖。

## 结论

此能力由自有的 `domain-provisioning` Skill 描述工作流，运行时优先使用 Cloudflare 托管 API MCP 的 OAuth 授权。Skill 是决策与操作说明；MCP 是真实 API 工具；Account ID、权限和账单/注册联系人配置是环境前置条件。通过这一分层，技能可以独立存放与安装，不需要另造一层自定义 Cloudflare API 服务。

Cloudflare 的官方 [Skills 仓库](https://github.com/cloudflare/skills) 为 Cloudflare API MCP 与平台产品提供 Agent 指南，但没有发现覆盖“Registrar 购买 + DNS + Pages/Worker 主机名接入”完整生命周期的专用技能。官方托管 [Cloudflare API MCP](https://developers.cloudflare.com/agents/model-context-protocol/cloudflare/servers-for-cloudflare/) 用 `search()` 和 `execute()` 暴露 Cloudflare API，并支持 OAuth；这是账号操作的首选接入。账号操作要求相应 OAuth/API 权限。

Vercel 的 [skills.sh](https://skills.sh/) 是开源 Agent Skills 目录与 CLI 生态入口。此仓库采用兼容的 `SKILL.md` 格式；合并到默认分支后可用 `npx skills add AlexKaiqi/skills --skill domain-provisioning --full-depth --global` 安装该技能。这里使用 `--full-depth` 是因为技能目前放在仓库顶层独立目录。CLI 可把同一技能安装到多个兼容 Agent；技能已在自有仓库，不依赖发布到目录才可使用。

## 源码核对

下列 GitHub `HEAD` 提交在检查时被固定，用于复核实现判断；这是源码检查，不等同于运行测试或安全审计：

- `cloudflare/skills`：`6dc7604903127485e7e4cb26314651ebd4a4df19`。官方技能库覆盖 Workers、Pages 等产品指南及 API MCP 用法；没有看到 Registrar 注册到应用主机名绑定的完整工作流。
- `cloudflare/cloudflare-typescript`：`faaaf89ed8064a9fb54de538ec3e89487f1302b0`（包版本 7.1.0）。SDK 暴露 Registrar Search/Check/Register、Pages 和 Worker Domains 操作；其 API-shape 测试是后续做代码集成时的可复用验证参考。本次只检查源码与测试用例，没有执行它们。
- `oso95/domain-suite-mcp`：`7083ebed3cf2d9e8fa039cb36b306e7732ec3181`（包版本 0.1.0）。实际查看了 Cloudflare Provider/Client：`supports()` 把 Registration、Renewal、Pricing 标为不支持；`registerDomain()` 也因 Enterprise 限制直接报错。DNS zone/记录 CRUD 有实现，仓库包含 Vitest 单测，但本次没有运行。实现与官方 Registrar API beta 不同步，因此不采用。
- `likw99/agent-skills`：`b1b31473295b23a78d5b06df40d6a8e0ea45091f`。`domain-research` 的 Cloudflare 参考介绍 MCP 查询和注册前检查，并把注册、DNS 改动放在单独授权边界之外；它偏研究/可用性查询，不覆盖资源全生命周期。

## 候选评估

| 候选 | 作用与来源 | 与本能力的契合度 |
|---|---|---|
| [cloudflare/skills](https://github.com/cloudflare/skills) | Cloudflare 官方技能仓库及 API MCP 接入说明 | 最佳平台指南来源；搭配官方 API MCP 使用，不重复实现 MCP 客户端。没有发现 Registrar 到服务绑定完整流程的专用 Skill。 |
| [domain-suite-mcp](https://github.com/oso95/domain-suite-mcp) | MIT 多注册商 DNS/域名管理 MCP | README 与 Provider 源码都把 Cloudflare 注册/续费标为 Enterprise only；实现没有接 Registrar beta 的价格查询/注册端点。DNS zone/记录 CRUD 有实现。对于 Cloudflare 注册路径不采用为底层执行器。 |
| [agent-skills/domain-research](https://github.com/likw99/agent-skills/tree/main/skills/domain-research) | 社区域名研究 Skill，其中有 Cloudflare MCP 查询参考 | 适合找候选、查可注册性和价格；文档强调注册/DNS变更需另行授权，不是完整域名购买与托管能力，因此不直接复制。 |
| [cloudflare/cloudflare-typescript](https://github.com/cloudflare/cloudflare-typescript) | Cloudflare 官方 TypeScript API SDK | 若后续实现需要嵌入式程序化调用，可作为官方 SDK 候选；本 Skill 直接调用官方 MCP/API，不必增加 npm 依赖。 |

## 维护边界

- 外部 API 状态、价格、可用 TLD 和权限均以执行时 Cloudflare 官方文档及 API 响应为准；本评估中的社区项目能力仅反映检查时其公开文档，不代表本地验证或安全审计。
- 不复制社区 MCP 源码、schema 或许可证内容。本仓库只新增自有 Skill 文档，并保留上述上游来源链接。
- 新增多注册商后端前，先确认确有跨注册商需求；分别研究账户授权、付费、可回滚操作和许可，再决定是否添加 Provider 抽象。
