# 安装与首次使用

## 1. 下载与审核

从 <https://github.com/candle233/candle-game-resources> 下载或 clone。建议选择已审核的 release/tag；当前 `0.1.0` 尚未发布。查看 `THIRD_PARTY_NOTICES.md` 与 `docs/LICENSING.md`。下载 ZIP 后先在单独目录解压，不直接覆盖游戏工程，也不在未审核的下载目录中执行脚本。

工具只使用 Python 3.11+ 标准库。Windows 可将 `python` 换成 `py -3`，macOS/Linux 可换成 `python3`，保留 `-I`。保持 Python、Editor 与项目处于同一操作系统，避免直接混用 WSL 和 Windows 路径。

## 2. 确定项目阶段

- **已有 Unity 工程**：包含 `Assets/`、`Packages/manifest.json`、`ProjectSettings/ProjectVersion.txt`，使用普通安装。
- **空游戏仓库**：增加 `--bootstrap`。这只建立工作流，不选择引擎版本，不生成完整 Unity 工程。

```powershell
python -I candle-game-resources/tools/resources.py verify
python -I candle-game-resources/tools/resources.py install --project "C:\Projects\MyGame" --bootstrap
# 看完预览，再显式应用。
python -I candle-game-resources/tools/resources.py install --project "C:\Projects\MyGame" --bootstrap --apply
```

安装是 create-only：预先发现所有内容冲突；相同文件跳过，不同文件拒绝覆盖；不修改游戏 README、不删除旧文件、不写用户全局配置。`.gitignore` 已有内容时需人工合并。不要把游戏放进资源仓库里面，也不要将资源仓库放进游戏目录。

## 3. 准备真实 Unity 工程

若还没有工程，先确定团队批准的 Editor 版本、渲染管线、目标平台，再用 Unity Hub 在**独立临时目录**创建真实工程。不要让 Hub 覆盖本仓库；审查后将其 `Packages/`、`ProjectSettings/` 与需要的 `Assets/` 合并进游戏，保留已存在 GUID 和 `.meta`。

安装兼容的 Unity Test Framework，完成包解析，检查框架 `.meta`，建立至少一个场景和启用的 Build Scenes。把选定的 Editor/包版本与工程设置提交到游戏仓库。连接实际授权的 Editor：

```powershell
$env:UNITY_EDITOR = "C:\Program Files\Unity\Hub\Editor\<实际版本>\Editor\Unity.exe"
# 这里的 <实际版本> 不能原样使用。
python -I harness/scripts/unity_cli.py doctor
python -I harness/scripts/unity_cli.py verify
```

以上命令从**游戏根目录**执行。doctor 是配置预检，不证明授权有效或 Editor 能启动；verify 必须真正启动 Editor，检查日志、版本、编译与测试 XML。连通性测试不代表功能或目标设备验收。

## 4. 配置客户端

- Codex：审核项目 `AGENTS.md`、`.agents/skills/` 和 `.codex/`；模型/身份沿用自己的客户端配置。
- ZCode：导入游戏 `.agents/skills/` 中的 Skill，确认当前会话可见。不要用跨仓符号链接。运行 `python -I harness/scripts/configure.py --adapter zcode`，只生成 `Artifacts/harness/zcode-user-hooks.json`；人工检查并合并事件数组，勿覆盖全局配置。
- MCP：依照 [MCP 接入说明](../mcp/README.md) 一次审查一项；本仓库不自动运行 `npx`、`uvx`、Docker 或远程 MCP。

客户端 schema 会变化；原生客户端未做本次运行验证，不要把 JSON 解析成功当成接入成功。

## 5. 开始开发

```powershell
python -I harness/scripts/workflow.py check
python -I -m unittest discover -s harness/tests -v
python -I harness/scripts/workflow.py new --id TASK-001 --kind prototype --title "一个小的可玩交互"
```

填写任务范围、非目标、假设、验收、计划、验证 gates 和评审要求，真实负责人批准后才进入实现。参见游戏内 `WORKFLOW.md`。AI 不代签 ready/review；发布是独立授权。

## 6. 更新资源

不要把最新模板直接解压覆盖工程。切换到审核后的资源版本，重新生成清单并 dry-run；对冲突做三方比较和人工合并。游戏实际依赖记录在 `harness/resources.lock.json`，保留源版本/清单摘要及本地改动说明。完整流程见 [维护说明](MAINTENANCE.md)。
