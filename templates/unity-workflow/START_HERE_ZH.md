# 从这里开始

本目录提供 Unity 游戏开发工作流，不包含完整游戏工程。先读 `harness/README.md` 和 `harness/RESOURCE_ORIGIN.md`。

1. 若缺少 `Packages/manifest.json` / `ProjectSettings/ProjectVersion.txt`，先由负责人选定 Editor、渲染管线和平台，使用 Unity Hub 在独立目录创建工程，审核后合并项目文件。不要手写假版本来让 doctor 通过。
2. 完成包解析，确认 Unity Test Framework 和 `.meta`，添加实际场景，关闭交互 Editor。
3. Python 3.11+，设置 `UNITY_EDITOR` 为实际授权的 Unity 可执行文件。
4. 运行 `python -I harness/scripts/workflow.py check`、`python -I -m unittest discover -s harness/tests -v`。
5. 运行 `python -I harness/scripts/unity_cli.py doctor`，预检通过后再运行 `verify`。
6. 按 `docs/ADAPTERS.md` 配置客户端。第三方 Skill/MCP/插件尚未安装，不能因清单中有名称就认为已启用。
7. 选定或创建任务，填好合同，获得真实批准后进入实现。流程详见 `WORKFLOW.md`。

原始框架未提供许可证；在公开分发/上传前，确认有权分享。不要把离线测试、mock 或预检当成游戏编译和实际验收。
