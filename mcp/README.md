# MCP 接入目录

本仓库**没有捆绑或自动安装第三方 MCP 服务器**。原包的 `harness/integrations.json` 仅描述素材路由，不能直接粘贴成客户端配置。

## 提供的示例

- [mcp.example.json](mcp.example.json)：常见 `mcpServers` 空表，仅作为显式禁用基线；不同客户端 schema 需以官方文档为准。
- [codex.example.toml](codex.example.toml)：空 `mcp_servers`，没有远程 URL、启动包或凭据。
- [review-template.json](review-template.json)：本仓库自定义审查记录，**不是客户端可执行配置**。

示例未提供名称不清或未审核的 `npx`/`uvx` 命令，也不自动从 GitHub 拉取/运行代码。精确上游见 [资源目录](../catalog/README.md)；未解析的 freesound-mcp、pixabay-mcp、vfx-mcp、Iconify MCP 等保持关闭。

## 启用一项之前

1. 确定唯一上游及精确 commit/发布版本，审核 LICENSE、依赖、入口及供应链。
2. 依照**该版本** README 确认传输类型和真实启动方式，不从显示名称猜 npm/PyPI 包。
3. 列出允许的工具、文件根、读写权限、网络目的地、API key 环境变量名称和费用上限。MCP 权限不受普通 shell sandbox 自动保护。
4. 先在独立、无私密数据的环境验证；只允许所需工具。让负责人批准安装与接入后再配置自己的客户端。
5. 在游戏的 `harness/integrations.json` 记录批准版本及工具白名单；密钥值不写进仓库，实际客户端配置保留本机。
6. 保存无敏感信息的连通性验证结果。未验证不得标成 ready/connected。

Eagle 使用项目内 Python 对本机 `127.0.0.1:41595` 的 HTTP 适配，不是第三方 MCP；未获得授权时不查询或写入私有库。上游 API 返回的素材也必须独立检查素材许可证。
