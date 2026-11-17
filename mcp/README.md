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

## 已实际验证的本地安装方式（2026-11-17）

以下命令在 Windows / Node 24.6.0 / Python 3.13.9 上实际执行，四个服务均完成 MCP `initialize` 与 `tools/list` 握手；**没有调用外部素材 API**。命令是可复现配方，不是对他人机器的安装授权；先审阅对应固定 commit 的 README 与源码。

### 3D Asset Server

```powershell
git clone https://github.com/arielshad/3d-asset-server.git
cd 3d-asset-server
npm ci --ignore-scripts
npm run build:server
# MCP stdio 入口；下载目录按需修改
$env:ASSET_DOWNLOAD_DIR = "C:\path\to\game\Artifacts\assets"
$env:ASSET_SERVER_TELEMETRY = "0"
node dist/cli.js mcp
```

工具：`search_assets`、`get_asset`、`download_asset`、`list_providers`。下载的模型/贴图/HDR 仍需逐个核对许可证。

### Openverse

```powershell
git clone https://github.com/neno-is-ooo/mcp-openverse.git
cd mcp-openverse
npm install --ignore-scripts
npm run build
node dist/index.js
```

工具：`search_images`、`get_image_details`、`get_related_images`、`get_image_stats`、`search_images_for_essay`。结果自带署名要求，不等于可无条件商用。

### Stock Images（需要 Key）

```powershell
git clone https://github.com/jeanpfs/stock-images-mcp.git
cd stock-images-mcp
npm ci --ignore-scripts
npm run build
$env:PEXELS_API_KEY = "..."; $env:UNSPLASH_API_KEY = "..."; $env:PIXABAY_API_KEY = "..."
node dist/index.js
```

至少配置 Pexels、Unsplash、Pixabay 中一个 Key。没有 Key 时不要把它登记成可用服务。

### NASA

```powershell
git clone https://github.com/jezweb/nasa-mcp-server.git
cd nasa-mcp-server
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:API_KEY = "DEMO_KEY"   # 约 30 次/小时、50 次/天；正常使用请申请免费 Key
.venv\Scripts\python.exe nasa_server.py
```

工具覆盖 APOD、火星车照片、近地天体与 NASA 媒体库。上游没有 LICENSE 文件，使用前自行确认授权。

客户端配置片段（`mcpServers` 风格；不同客户端字段可能不同）：

```json
{
  "mcpServers": {
    "3d-asset": {
      "command": "node",
      "args": ["C:/tools/3d-asset-server/dist/cli.js", "mcp"],
      "env": { "ASSET_DOWNLOAD_DIR": "C:/game/Artifacts/assets", "ASSET_SERVER_TELEMETRY": "0" }
    }
  }
}
```

不要把真实 Key、个人绝对路径或客户端备份提交到仓库。
