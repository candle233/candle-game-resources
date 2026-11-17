# Candle Unity Workflow — 项目内运行副本

来自 <https://github.com/candle233/candle-game-resources> 的 `templates/unity-workflow/` 与 `skills/`。来源版本见 `harness/resources.lock.json`；原始框架许可待确认，详见 `harness/RESOURCE_ORIGIN.md`。

这是工作流覆盖层，不是完整 Unity 工程。已有源码、策划、Unity 版本、场景和项目设置不应被模板覆盖。Skill 的规范源在资源仓库，游戏持有审核后的普通文件副本；项目不依赖另一台机器的资源目录。

## 游戏根目录常用命令

```powershell
python -I harness/scripts/workflow.py check
python -I -m unittest discover -s harness/tests -v
python -I harness/scripts/workflow.py status
python -I harness/scripts/workflow.py handoff
python -I harness/scripts/unity_cli.py doctor
python -I harness/scripts/unity_cli.py verify
```

Python 3.11+，Windows 可用 `py -3 -I`，POSIX 可用 `python3 -I`。缺少真实 Unity 工程/匹配 Editor 时 doctor 失败，验证保持 NOT_RUN，不是 PASS。准备工程见 `START_HERE_ZH.md` 和 `docs/ENVIRONMENT.md`。

## 开发步骤

1. 查看 `AGENTS.md`、`WORKFLOW.md`、`design/CURRENT.md`。
2. 创建任务，填写范围、验收、假设、计划与验证 gates；负责人真实批准后开始。
3. 单 checkout 只允许一个写入任务；工作流状态写入由独占锁串行化。遗留锁需人工确认进程，不自动清理。
4. 真正运行编译/测试/构建，保留日志和证据。连通性测试不能代替游戏行为测试。
5. 负责人记录所需评审，完成任务；发布、上传、付费操作须独立批准。

## 客户端与素材

`docs/ADAPTERS.md` 说明 Codex / ZCode。`configure.py --adapter zcode` 只生成本机合并片段，不改全局设置；不要提交生成的绝对路径。

`harness/integrations.json` 是自定义路由与状态，不是原生 MCP 配置。外部工具默认断开，预算为零。Eagle 是可选本地软件，只有经批准时才查询或写入；不使用它时保存本地素材待办并说明缺口。素材权利记录放 `harness/assets/registry.json`，API/代码许可证不等于素材商用许可。

## 更新

从审核后的资源版本使用 `tools/resources.py install` 预览。它拒绝不同内容的覆盖；已有工程的升级需人工三方比较、合并并重新验证。不要直接运行这里的 `install.py` 而忘记指定完整资源根 `--source`，统一使用资源仓库入口。
