# Cloudflare API 运行参考

按执行当天的官方文档确认 API 路径、必需字段、权限和状态枚举。本页记录域名提供流程的关键约束，不替代实时 API schema。

## API 与认证

本 Skill 的 `SKILL.md` 和参考文档采用通用 Agent Skills 格式；`agents/openai.yaml` 仅是 Codex 的可选界面元数据。安装 Skill 不会自动给 Agent Cloudflare 账号权限，也不会传递 MCP 配置。

Cloudflare 的托管 API MCP 使用 Streamable HTTP 地址 `https://mcp.cloudflare.com/mcp`。在所选 Agent 的 MCP 设置中配置此远程服务并完成 Cloudflare OAuth，按任务选择权限。官方 MCP 当前提供 `search()` 发现 API 操作、`execute()` 执行调用；先检查客户端实际暴露的工具 schema，不要依赖某个 Agent 的专属配置格式。若客户端无法使用 OAuth，可在安全的 API client / SDK 工作流中使用最小权限 API Token，并放在 secret/environment 中；不要把令牌放在 Skill 文件或提示词里。

注册域名之前，Cloudflare Registrar API 要求：Account ID、Registrar Write 权限、有效默认付款方式、账号默认注册联系人，以及接受域名注册协议。不能从已登录 dashboard 推断这些前置条件已满足。

## Registrar 注册流程

当前 beta 流程为 Search → Check → Register：

1. `GET /accounts/{account_id}/registrar/domain-search` 发现候选。搜索结果可能缓存，且只显示 API beta 支持的扩展名。
2. `POST /accounts/{account_id}/registrar/domain-check` 对最终选中的完整域名实时复核可注册状态和价格。记录注册价、续费价、币种、资格结果、时间戳；支持状态与 dashboard 支持情况可能不同。
3. 只有取得用户对明确域名和当前金额的确认后，才调用 `POST /accounts/{account_id}/registrar/registrations`。成功注册向默认付款资料收费，不能退款。
4. 通过 `GET /accounts/{account_id}/registrar/registrations/{domain_name}` 核验最终状态和到期日。

当前 API 文档说明 `auto_renew` 默认为 `false`；隐私模式在 TLD 支持时默认为 redaction。调用时显式依据用户选择设定。若用户的一行命令明确要求开启自动续费，在展示注册价与续费价后取得确认，再设置 `auto_renew: true`；这会允许按续费价每年扣款。关闭续费时，应告知用户当前 Registrar API 不支持手动续费。

**Registrar API beta 的当前限制**：仅部分 TLD 可通过 API 注册；Search/Check 会区分 dashboard 支持与 API 不支持的扩展名；续费、转入和联系人更新目前未开放 API 操作。非标准/高级价格域名需单独处理，不能把普通价格套用到 premium 域名。重新检视官方文档，API beta 限制可能变动。

Cloudflare Registrar 注册域名要求 Cloudflare nameservers，无法把它作为注册商却改用第三方 DNS nameservers。非 ASCII 国际化域名目前不受支持；账户邮箱需要验证。

## 服务绑定

### Pages

Pages API 可以管理 Pages 项目和部署；Pages 自定义域名需经项目级自定义域名关联流程。根域名接入要求相应 Cloudflare zone 和 nameservers 配置。外部 DNS 托管下的子域名通常使用指向 `<project>.pages.dev` 的 CNAME，但应先在 Pages 项目中关联该主机名，再按文档配置 DNS。

### Workers / API

Cloudflare Workers API 提供 Worker Domains 的列出、读取、绑定及解绑操作：

- `GET /accounts/{account_id}/workers/domains`
- `PUT /accounts/{account_id}/workers/domains`
- `DELETE /accounts/{account_id}/workers/domains/{domain_id}`

Workers Custom Domain 适合 Worker 本身作为 origin 的场景；Cloudflare 会创建 DNS 记录并签发所需证书。前置条件是活动 Cloudflare zone 和现有 Worker。不能附着在已有 CNAME 主机名上。若后端源站在 Cloudflare 外部，检查用户是否需要的是 Route，而不是 Custom Domain。

## 官方来源

- [Cloudflare API MCP](https://developers.cloudflare.com/agents/model-context-protocol/cloudflare/servers-for-cloudflare/)
- [Registrar API](https://developers.cloudflare.com/registrar/registrar-api/)
- [Registrar 域名注册要求](https://developers.cloudflare.com/registrar/get-started/register-domain/)
- [Pages REST API](https://developers.cloudflare.com/pages/configuration/api/)
- [Pages 自定义域名](https://developers.cloudflare.com/pages/configuration/custom-domains/)
- [Workers Custom Domains](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/)
- [Workers Domains API](https://developers.cloudflare.com/api/resources/workers/subresources/domains/)
