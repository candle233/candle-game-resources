# 第三方出处与许可记录

核验日期：**2026-11-17**。完整 SHA、许可证证据和 README 来源见 [resources.json](catalog/resources.json)、[Skill 核验记录](catalog/skill-observations.json)与[工具核验记录](catalog/tool-observations.json)。

> 下列第三方 Skill / MCP / 图标库**没有复制源码、安装或连接**。当前仅保存来源链接与必要元数据；观察到的 HEAD 不是批准依赖。不得把软件许可证等同于 API 服务条款、返回素材的商用权或安全认证。

## 用户提供的框架与六个本地 Skill

- 输入：`Unity_GameDev_Workflow_Complete_Clean.zip`，由用户提供。
- 原始归档 SHA256：`13f3f43348e5f4e1ae7d43962facf40564c33a1992d4617a5b7b8b75d9b30b4c`。
- 本地内容：`skills/` 六个工作流 Skill 与 `templates/unity-workflow/` 的 Harness/文档/C#，经过本次整理与加固。
- 原始作者、上游仓库、许可证：**包内未提供**。不擅自写成原创、MIT 或公有领域。
- 再分发许可是公开发布前未决条件；见 [许可说明](docs/LICENSING.md) 和 [来源说明](provenance/README.md)。

## 外部 Skill 仓库

| 上游 / 原作者账户 | 观察到的提交前缀 | 许可证核验结果 | 当前处理 |
| --- | --- | --- | --- |
| [Unity-Technologies/skills](https://github.com/Unity-Technologies/skills) | `5841a34846f3` | 根 `LICENSE.md` 指向 **Unity Companion License**；GitHub SPDX 为 `NOASSERTION` | 仅引用；不能当 MIT/Apache |
| [gamedev-skills/awesome-gamedev-agent-skills](https://github.com/gamedev-skills/awesome-gamedev-agent-skills) | `c6ca6c41c839` | Apache-2.0，另有 `NOTICE` | 仅引用；将来复制须保留许可/NOTICE |
| [Yuki001/game-dev-skills](https://github.com/Yuki001/game-dev-skills) | `ef297c3b2e04` | API license=null，未发现 LICENSE | 许可待确认，不复制 |
| [Hanjo92/roguelike-game-designer-skill](https://github.com/Hanjo92/roguelike-game-designer-skill) | `360533660b7f` | README 声称 MIT，但无 LICENSE，API license=null | 如实保留差异，不补猜 SPDX |
| [861172923/Unity-Skills](https://github.com/861172923/Unity-Skills) | `6093d0586210` | Apache-2.0 | 14 份技能 Markdown，非即装即用标准 Skill 包 |
| [MuharremTozan/unity-agent-skills](https://github.com/MuharremTozan/unity-agent-skills) | `79bec6baaf41` | API license=null，未发现 LICENSE | 许可待确认，不复制 |
| [Logiiiii/unity-agent-skills](https://github.com/Logiiiii/unity-agent-skills) | 未知 | 公开 API 与页面返回 404，无法核验 | 保留原候选地址，不猜替代来源 |

公开元数据不提供法律结论。许可证缺失不等于允许再分发；404 不证明仓库永久不存在。安装方式仅记录在对应固定提交 README 证据中，本仓库不执行浮动分支安装命令。

## MCP 服务器候选

| 原始候选 / 上游 | 观察到的提交前缀 | 代码许可证信息 |
| --- | --- | --- |
| [arielshad/3d-asset-server](https://github.com/arielshad/3d-asset-server) | `49eb855e3cc0` | Apache-2.0 |
| [neno-is-ooo/mcp-openverse](https://github.com/neno-is-ooo/mcp-openverse) | `3146cfe4ae04` | MIT |
| [jeanpfs/stock-images-mcp](https://github.com/jeanpfs/stock-images-mcp) | `fa0da9b69d45` | MIT |
| [jezweb/nasa-mcp-server](https://github.com/jezweb/nasa-mcp-server) | `0b003ad5fb66` | API license=null，license API 404；未取得许可证依据 |

仅核验仓库/版本/许可证元数据，尚未审核具体传输、入口、权限与服务条款。接入前阅读该固定版本 README 和实现，参见 [MCP 说明](mcp/README.md)。服务器代码许可不赋予其搜索或返回的图片/模型/音频使用权。

`freesound-mcp`、`pixabay-mcp`、`vfx-mcp`、`Iconify MCP`、`SoundCraft`、`VectorCraft`、`PhotoCraft`：原包未给出唯一上游，保持 **unresolved**。不臆造仓库、包名或许可证。

## 图标、软件与原生能力

| 名称 | 准确来源 | 许可/边界 |
| --- | --- | --- |
| Lucide | [lucide-icons/lucide](https://github.com/lucide-icons/lucide) | API SPDX `NOASSERTION`；具体条款见固定提交 LICENSE，不能直接简化成 MIT |
| Tabler Icons | [tabler/tabler-icons](https://github.com/tabler/tabler-icons) | MIT；实际导入时保留许可 |
| Heroicons | [tailwindlabs/heroicons](https://github.com/tailwindlabs/heroicons) | MIT；实际导入时保留许可 |
| Eagle | [官方网站](https://eagle.cool/)；[list API](https://api.eagle.cool/item/list)、[addFromPath API](https://api.eagle.cool/item/add-from-path) | 项目只提供本机 HTTP 适配；没有分发 Eagle 软件或私有库；软件/素材权利分别处理 |
| Blender | [blender.org](https://www.blender.org/) | 只记录软件名，未指定或分发 MCP bridge、插件或软件二进制；使用遵循官方许可 |
| Unity 原生 VFX / particles | [Unity 文档](https://docs.unity3d.com/Manual/ParticleSystems.html) | 引擎能力，不是随包提供的第三方 MCP |
| image-generation / image-to-flipbook pipeline | 无具体实现 | 仅能力占位，不推断供应商或生成内容权利 |

## GitHub Actions

YAML 仅引用上游 Action，没有复制其源码。固定引用来自对应 tag 的公开 commits API，**不是完整实现安全审计**。

| 上游 | tag → 固定 commit | 许可证 |
| --- | --- | --- |
| [actions/checkout](https://github.com/actions/checkout) | v4 → `11d5960a326750d5838078e36cf38b85af677262` | MIT |
| [actions/setup-python](https://github.com/actions/setup-python) | v5 → `a26af69be951a213d495a4c3e4e4022e16d87065` | MIT |
| [actions/upload-artifact](https://github.com/actions/upload-artifact) | v4 → `ea165f8d65b6e75b540449e92b4886f43607fa02` | MIT |

以上 Action 的具体 LICENSE URL 与固定版本记录在工具核验 JSON 中。启用自托管 Unity CI 仍须 GitHub environment 审批、主分支保护和隔离 runner；本地 YAML 无法代替平台权限设置。

## 以后复制第三方内容时

逐文件记录原作者/账户、原仓库与路径、固定版本、许可证/NOTICE、复制范围和本地修改。保留原版权头。未经允许的文件不要上传；注明出处不替代许可。若只是参考文档或链接目录，应明确“仅引用”，不要宣称实现来自本项目原创。
