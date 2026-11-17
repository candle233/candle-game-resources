# 来源与整理记录

## 原始输入

- 文件名：`Unity_GameDev_Workflow_Complete_Clean.zip`
- 提供方式：用户本次上传的本地附件
- SHA256：`13f3f43348e5f4e1ae7d43962facf40564c33a1992d4617a5b7b8b75d9b30b4c`
- 归档检查：62 个文件，解压声明总大小 141,780 bytes；路径经过逃逸、符号链接及重复检查。
- 原始 MANIFEST 中列出的文件逐个重算 SHA256 匹配。该清单仅证明包内一致性，不认证作者。
- 原始作者、上游地址及许可证：包内未提供，待权利方确认。
- 机器可读记录：[import.json](import.json)。

## 本次整理

1. 将 6 个本地 Skill 的规范源放进 `skills/`，项目文件放进 `templates/unity-workflow/`。
2. 游戏安装使用项目内副本和来源锁定信息，不依赖个人绝对路径或跨仓符号链接。
3. 合并有效 `.gitignore`；为现有 Unity 集成分配稳定 `.meta` GUID；不虚构完整 Unity 工程或 Editor 版本。
4. Python 入口与 hook 使用隔离模式；任务写操作加锁，禁止重开 done 任务并复查单 writer；收紧 NUnit 计数和实际 test-case、日志版本证据。
5. create-only 安装默认预览，显式 apply；新增来源目录、无凭据示例与可重复 Skill ZIP 构建工具。
6. 未分发原始 ZIP、重复 Skill ZIP、旧测试报告或任何第三方候选实现；没有复制本机全局 Skill / MCP / 插件库。

具体行为以当前文件与实际测试为准，见 [验证记录](../docs/VALIDATION.md)。新增整理说明不是原始作者的署名或授权声明，原框架的许可仍待确认。
