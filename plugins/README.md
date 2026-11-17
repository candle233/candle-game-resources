# Plugins 与客户端适配

原始框架没有给出独立插件市场 ID、完整插件包或可直接安装的插件仓库；因此本目录不虚构插件实现，也不复制本机已安装插件。

| 能力 | 资源所在位置 | 本次状态 |
| --- | --- | --- |
| Codex Skills / hooks / rules | 模板 `.agents/skills` 的安装映射与 `.codex/`；[客户端说明](../templates/unity-workflow/docs/ADAPTERS.md) | 文件已整理，原生客户端尚未运行验证 |
| ZCode Skill 导入 / 用户 hook 合并片段 | `skills/`；模板 `harness/scripts/configure.py` | 只生成片段，不改全局配置 |
| Unity Editor 自动化与测试 | 模板 `Assets/Editor/WorkflowHarness/`、`Assets/Tests/WorkflowHarness/` | 源码与稳定 `.meta`，未在真实 Editor 编译 |
| Eagle HTTP 适配 | 模板 `harness/scripts/assets.py` | 可选本机接口，无 Eagle 软件或 MCP 源码 |
| Blender / VFX / 图像生成 | [资源目录](../catalog/README.md) | 能力占位；未指定 bridge/插件、未连接 |

如果未来加入插件，先记录准确 publisher、市场/仓库 ID、版本、许可证、权限与审核证据，再提供安装说明；不得只凭 SoundCraft、VectorCraft、PhotoCraft 等名称选一个同名包。插件源码与生成/下载素材的权利是两回事。

客户端自身更新后应做无害 smoke test。本次没有真实 Codex/ZCode Hook runtime 测试；JSON/TOML 可解析不证明客户端接受 schema。
