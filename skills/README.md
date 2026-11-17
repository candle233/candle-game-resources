# 本地工作流 Skills

以下 6 项来自用户提供框架的 `.agents/skills/`，规范源保存在此目录。出处和待确认许可见 [来源记录](../provenance/README.md)。没有复制其他候选 GitHub 仓库的 Skill 源码。

| Skill | 用途 |
| --- | --- |
| [`workflow-orchestrator`](workflow-orchestrator/SKILL.md) | 分流请求、任务合同、审批、恢复与交接 |
| [`design-change`](design-change/SKILL.md) | 设计变更、影响分析与重新审批 |
| [`unity-implementation`](unity-implementation/SKILL.md) | 在批准范围内实现 Unity 功能 |
| [`unity-verification`](unity-verification/SKILL.md) | 真实编译、EditMode / PlayMode 与证据 |
| [`asset-production`](asset-production/SKILL.md) | Eagle 优先、素材来源与生成待办 |
| [`release-review`](release-review/SKILL.md) | 构建、素材权利、人工及目标设备验收 |

`tools/resources.py install` 将六项复制到游戏 `.agents/skills/`。`package-skills` 可以生成独立导入 ZIP。不要把本 README 当成第 7 个 Skill。

所有命令以**游戏项目根目录**为上下文，不能以本目录为游戏根。Skill 依赖项目的 AGENTS、WORKFLOW、docs 与 Harness；单独导入不会安装 Unity 或 MCP。客户端是否发现/启用 Skill 需在实际会话检查。
