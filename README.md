# Agent Skills

个人 Agent Skills 技能集合，核心内容不绑定某一个 Agent。

- [module-design](module-design/SKILL.md)：从问题推导责任边界，检查拆分的收益与成本。
- [domain-provisioning](domain-provisioning/SKILL.md)：通过 Cloudflare API 提供、管理域名，并将主机名绑定到 Pages 或 Workers。

`SKILL.md` 是跨 Agent 共用的能力说明。`agents/openai.yaml` 只提供 Codex 的界面元数据；其他 Agent 可忽略它。Cloudflare MCP 连接要在选用的 Agent 中单独配置。

从本地仓库安装单项技能：

`npx skills add . --skill domain-provisioning --full-depth --global`

在提示中选择要安装的 Agent；也可用 `--agent` 指定客户端。当前版本已推送到 `codex/domain-provisioning-skill` 分支；合并到默认分支后，可以从 GitHub 安装：

`npx skills add AlexKaiqi/skills --skill domain-provisioning --full-depth --global`

安装并连接 Cloudflare API MCP 后，在对应 Agent 中发送这一行：

`注册 Cloudflare Registrar API 支持范围内最低价的可用域名，并开启自动续费；成功后只返回完整域名。`

本仓库采用 Agent Skills 格式，可通过 [skills CLI](https://github.com/vercel-labs/skills) 安装到 Codex、Claude Code、Cursor、OpenCode 等兼容客户端，也可在 [skills.sh](https://skills.sh/) 搜索技能。
