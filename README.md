# Candle Game Resources

面向 Unity 游戏项目的 AI 开发工作流、Skills 与工具集成目录。

- 资源仓库：<https://github.com/candle233/candle-game-resources>
- 示例游戏仓库：<https://github.com/candle233/7th-chamber>
- 当前整理版本：`0.1.0`（本地准备版本，尚未发布 tag）

> **不是完整 Unity 工程，也不是一键安装全部 MCP 的脚本。** 本仓库包含 6 个本地工作流 Skill 和项目覆盖层；第三方工具仅登记来源，默认未安装、未连接、未授权。原始用户提供框架未附许可证；公开分发前必须完成[许可证与发布检查](docs/LICENSING.md)。标注出处不能替代授权。

## 内容分布

| 目录 | 用途 |
| --- | --- |
| [`skills/`](skills/README.md) | 6 个工作流 Skill 的唯一维护源，安装到游戏的 `.agents/skills/` |
| [`templates/unity-workflow/`](templates/unity-workflow/harness/README.md) | AGENTS、工作流、Unity Editor 自动化、连通性测试、任务与素材工具 |
| [`catalog/`](catalog/README.md) | 第三方资源的上游、版本、许可证与接入状态 |
| [`mcp/`](mcp/README.md) | MCP 连接说明和默认空配置，不下载服务器 |
| [`plugins/`](plugins/README.md) | Codex / ZCode / Unity / Eagle / Blender 适配边界 |
| [`provenance/`](provenance/README.md) | 输入压缩包摘要与来源记录 |
| [`tools/`](tools/README.md) | 生成清单、结构验证、create-only 安装及 Skill ZIP 打包 |
| [`docs/`](docs/QUICKSTART.md) | 使用、维护、贡献与发布指南 |

游戏自身的策划、任务、场景、素材授权证据和实际启用状态不放在本仓库。安装后的游戏可以独立运行 Harness，不依赖维护者机器上的资源目录路径，不使用跨仓符号链接。

## 快速开始

需要 Python **3.11+**、Git。先阅读来源与脚本，再运行；没有自动安装 Python 包、Unity、第三方插件或服务。

```powershell
git clone https://github.com/candle233/candle-game-resources.git
python -I candle-game-resources/tools/resources.py verify

# 默认只预览；资源仓库与游戏工程必须互不包含。
python -I candle-game-resources/tools/resources.py install --project "C:\Projects\MyGame"
# 确认没有冲突后才创建文件；已有不同内容绝不覆盖。
python -I candle-game-resources/tools/resources.py install --project "C:\Projects\MyGame" --apply
```

尚未创建 Unity 工程时可显式增加 `--bootstrap`，只安装工作流，不伪造 `Packages/manifest.json`、Editor 版本或场景。已有项目如与 `.gitignore`、AGENTS 等文件冲突，请人工合并；不要删掉自己的文件以强行安装。

进入游戏目录后：

```powershell
python -I harness/scripts/workflow.py check
python -I -m unittest discover -s harness/tests -v
python -I harness/scripts/unity_cli.py doctor
```

缺少 Unity 工程或 Editor 时，doctor 会失败；这不是可以忽略的游戏验证成功。完整步骤见[安装与首次使用](docs/QUICKSTART.md)。

## 获取独立 Skill ZIP

```powershell
python -I candle-game-resources/tools/resources.py package-skills
```

生成至 `dist/skills/`，可在客户端导入。ZIP 是规范源的构建产物，不重复提交源码版本。Skill 依赖游戏内 Harness，不是单独的游戏生成器。

## 安全与来源

- [第三方出处与许可摘要](THIRD_PARTY_NOTICES.md)
- [MCP 审查与凭据边界](mcp/README.md)
- [许可证未决项](docs/LICENSING.md)
- [贡献规范](CONTRIBUTING.md)
- [本次实际验证记录](docs/VALIDATION.md)

不提交密钥、客户端全局配置、Eagle 私有库、真实素材库、Unity 授权文件或构建产物；不代替用户发布和推送。
