# 资源来源与权利边界

## 维护源

- 通用资源仓库：<https://github.com/candle233/candle-game-resources>
- 当前本地整理版本：`0.1.0`，尚未发布 Git tag，未设置批准 commit。
- 原始输入：用户提供 `Unity_GameDev_Workflow_Complete_Clean.zip`。
- 原始归档 SHA256：`13f3f43348e5f4e1ae7d43962facf40564c33a1992d4617a5b7b8b75d9b30b4c`。
- 原始框架与 6 个本地 Skill 的作者、上游 URL、许可证：包内未提供，待确认；不得推定 MIT 或公有领域。

本次整理拆分规范源与项目状态、补充安装/更新工具与文档、稳定 Unity metadata，并加固任务状态和验证。完整改动说明位于资源仓库的 `provenance/README.md`；公开分发前须完成该仓库 `docs/LICENSING.md` 检查。

## 第三方资源

`harness/integrations.json` 的候选名称来自原始包，不表示它们已安装、可用或得到授权。准确上游、核验时版本、许可证依据及待解析项位于资源仓库 `catalog/resources.json` 和 `THIRD_PARTY_NOTICES.md`。本项目未复制那些候选仓库的实现。

Unity Editor、Eagle、Blender、图标库、MCP 服务器、API 服务和最终素材分别有自己的许可条件；连接工具或取得代码许可不代表素材可商用。实际导入的游戏素材仍需项目级权利证据和署名记录。

## 本地状态

- `harness/resources.lock.json`：资源来源/整理版本和默认禁用政策，非已发布依赖锁。
- `harness/resource-snapshot.json`（安装后可由维护者建立）：所用资源清单 SHA256；本身不是签名或代码审核。
- 游戏的任务、设计与 approvals 属于游戏仓库，不回写到公共资源模板。

资源/工作流文件采用项目内副本，不依赖维护者机器上的个人目录路径。凭据、用户客户端配置与运行产物不进入 Git。
