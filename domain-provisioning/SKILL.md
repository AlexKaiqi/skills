---
name: domain-provisioning
description: 通过注册商及 Cloudflare API 提供和管理域名、DNS 与站点/API 主机名。适用于检查注册资格与价格、注册或盘点域名、改 DNS、把 Pages 或 Worker 绑定到自定义域名；如果用户只要一个稳定免费地址，先判断 Cloudflare 提供的 pages.dev 或 workers.dev 子域名是否足够。
---

# 域名提供与管理

把“给站点或 API 一个稳定可访问的主机名”作为目标。域名操作包含三类资源：

- **域名注册**：取得一个可续费的注册域名及其所有权。
- **DNS/Zone**：把主机名解析到目标服务；Cloudflare Registrar 注册的域名使用 Cloudflare nameservers。
- **服务绑定**：将主机名接到现有 Pages 项目或 Worker。它不负责创建应用、部署代码或改应用路由。

Cloudflare 帐号、API 授权、付款方式、默认注册人信息及其隐私设置是前置配置，不是交付给调用者的域名资源。遇到缺项时，说明具体前置条件；不要在用户未提出时更改账单、身份或帐户安全设置。平台子域名（例如 `project.pages.dev`、`name.workers.dev`）由 Cloudflare 提供访问地址，不等于用户拥有一个注册域名。

## 一行调用

在已安装本 Skill 的 Agent 对话中发送这一行。若客户端要求显式调用技能，用该客户端的技能调用语法加上这句话：

`注册 Cloudflare Registrar API 支持范围内最低价的可用域名，并开启自动续费；成功后只返回完整域名。`

Skill 自动搜索并实时检查最低价候选，只在扣费前给出一次确认：完整域名、首年注册价和每年续费价。确认后注册、开启自动续费并返回域名。不要把未经用户确认的搜索结果当成购买授权。若不想授权自动续费，把命令中的“并开启自动续费”改成“关闭自动续费”。

## 处理流程

1. 明确用户要的是免费稳定的平台子域名，还是自己拥有的注册域名；以及用途是 Pages 网站、Worker/API 还是其他目标。只有需要购买或自定义域名时才进入注册商流程。
2. 优先使用已连接的 Cloudflare API MCP。先检查当前 Agent 暴露的 Cloudflare 工具和权限，再按实时 schema 调用；Cloudflare 官方 API MCP 当前使用 `search` 与 `execute`，但客户端可能有不同的呈现方式。不要假定浏览器已登录就代表 API 已授权。没有可用 API 时，说明需要在当前 Agent 配置官方 Cloudflare API MCP/OAuth，或为脚本提供安全的令牌注入方式。不要索取或输出令牌、密码、付款信息。
3. 对候选注册域名展示完整域名、TLD 是否支持 API 注册、实时可注册状态、注册价、续费价、币种及检查时间。搜索结果可能是缓存；每个候选域名在注册前立即重新检查。
4. 注册会扣除账号默认付款方式，且成功注册不可退款。执行前必须在当前对话中取得用户对**准确的完整域名、实时注册价格和币种**的明确确认；同时说明续费价格和自动续费设置。上方的一行调用明确要求开启自动续费；其他请求若未说明是否续费，先问清楚。未确认时只提供候选与报价，不调用注册接口。
5. 注册完成后读取注册资源，确认域名状态、到期日、自动续费和隐私模式；记录权威 API 返回值，不把提交请求当成注册成功。当前 API 不支持的注册后操作要如实说明。
6. 修改 DNS 或绑定主机名时，先读目标 zone、DNS 记录、Pages/Worker 目标和现有绑定。只增改完成请求所需的记录；保留无关记录，不替换 nameservers，不猜测生产/预览环境。提交后重读资源并确认 DNS/证书/绑定状态。
7. 汇报最终的域名、归属账号、服务目标、变更项、注册与续费费用、自动续费状态及仍待完成的验证步骤。区分注册域名、DNS 配置成功、服务绑定成功和外网可访问，不能以其中一个结果宣称其余都已完成。

## Pages 与 API 主机名选择

- Pages：只在目标项目已存在或用户明确要求部署时处理。关联 Pages 自定义域名需要走项目的自定义域名流程；仅手工增加一个 CNAME 而没有先将域名关联到 Pages 项目可能无法工作。根域名还涉及 Cloudflare zone 和 nameserver 条件；子域名可使用 CNAME，具体按当前文档与账号 zone 状态选择。
- Worker/API：若 Worker 是请求的源服务，优先考虑 Workers Custom Domain；Cloudflare 会为其配置 DNS 和所需证书，要求该主机名属于活动 Cloudflare zone，且不能覆盖已有 CNAME。若 Worker 前面还有外部 origin，确认用户要的是 Worker Route 还是 Custom Domain，避免把流量改到 Worker 源站。
- 页面构建、Worker 创建/代码发布属于应用部署能力；此技能只协调已有目标与域名接入，必要时调用可用的 Cloudflare 平台技能/API。

需要执行细节和现行 API 限制时，读取 [Cloudflare API 参考](references/cloudflare.md)。开源候选的调研结论见 [开源实现评估](references/open-source-review.md)。
