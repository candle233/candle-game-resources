# 资源工具

Python 3.11+ 标准库，从自己的项目/工具目录运行；无需 pip、npm、uv 或网络。命令不会安装任何第三方软件、启动 MCP、修改 GitHub 或全局配置。

```powershell
# 从资源根目录执行；任意目录也可以给 resources.py 的绝对路径。
python -I tools/resources.py manifest
python -I tools/resources.py verify
python -I tools/resources.py install --project "C:\Projects\MyGame"
python -I tools/resources.py install --project "C:\Projects\MyGame" --apply
python -I tools/resources.py install --project "C:\Projects\EmptyGame" --bootstrap --apply
python -I tools/resources.py package-skills
python -I -m unittest discover -s tests -v
python -I -m unittest discover -s templates/unity-workflow/harness/tests -v
```

- `manifest`：为项目模板与六个 Skill 生成源路径→游戏路径的 SHA256 清单；不 hash 清单自身。
- `verify`：离线检查结构、清单、配置与文档链接；不声明游戏运行正常或已获分发授权。
- `install`：默认 dry-run；`--apply` 才写入。先检测全部冲突，拒绝覆盖，保留游戏 README。`--bootstrap` 仅允许安装到非 Unity 仓库，不伪造引擎文件。
- `package-skills`：生成顺序/时间戳固定的六个独立 ZIP 至 `dist/skills/`；该目录不提交。

SHA256 是完整性记录，不是上游身份认证。真正发布前必须确认 [授权状态](../docs/LICENSING.md)，并审核固定 Git 版本。
