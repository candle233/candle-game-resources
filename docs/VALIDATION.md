# 本次整理验证记录

本报告记录当前 Windows 工作区的实际检查，不沿用原始压缩包自带的 Linux 通过报告。最终结果将在项目安装后补齐。

## 已确认范围

- 用户原始压缩包路径与归档成员已检查，按独立目录安全解压；原始 MANIFEST 的 SHA256 一致。
- 读取并审查框架、任务/素材/Unity CLI、客户端配置、测试与 CI；不在原下载目录执行脚本。
- 模板回归测试在整理后执行；初次因 `configure.py` 导入顺序错误失败，已修复，随后 72 项通过。最终版本仍需重跑。
- 第三方候选只做公开元数据核验，不下载或执行实现。

## 最终检查

实际在 Windows / Python 3.13.9 执行，未在 Linux 或 GitHub runner 执行。

| 检查 | 实际结果 |
| --- | --- |
| `python -I -X utf8 tools/resources.py verify` | 通过：67 个安装文件、6 Skill、13 JSON、2 TOML、1 catalog、48 个本地 Markdown 链接 |
| `python -I -X utf8 -m unittest discover -s tests -v` | 50 项全部通过，无 skip |
| `python -I -X utf8 -m unittest discover -s templates/unity-workflow/harness/tests -v` | 82 项全部通过，无 skip |
| 游戏安装后的 Harness 测试 | 82 项全部通过，无 skip；这是相同框架在安装位置的回归，不额外宣称 214 个独立测试 |
| 资源安装 | bootstrap 成功；未覆盖游戏 README，未创建 Unity Packages/ProjectSettings；再次预览 0 个新文件 |
| 文件摘要 | 最终 67 个源文件及游戏目标文件逐个匹配清单 SHA256，游戏 snapshot 保存清单及其摘要 |
| Unity `.meta` | 模板和游戏各 11 份，GUID 格式、唯一性及文件/目录配对通过 |
| 跨平台换行 | 根与游戏 `.gitattributes` 固定 LF，避免 checkout 自动转换破坏摘要 |
| ZIP | 6 个 Skill ZIP 布局/原字节一致；测试中两个输出目录重复生成逐字节一致；实际输出至 `dist/skills/` |
| 双仓敏感内容与本机路径检查 | 对私钥头、常见 GitHub/provider/AWS token 模式与个人目录模式未发现匹配；不是专业完整 secret audit |
| Git diff | 两仓 `git diff --check` 通过，未提交/推送 |
| 游戏 Unity doctor | **退出码 2**：缺 `Packages/manifest.json`、`ProjectSettings/ProjectVersion.txt`、`UNITY_EDITOR`；真实引擎验证未运行 |

最终清单摘要：`485374ef9084b63aed9780f8cbe621320eaa3dbbad2c0c57d0e3ce91f024dacd`。清单是完整性记录，不认证作者或批准发布。

检查中发现并修复了导入顺序错误、观测 JSON 被误当成统一 catalog schema、示例个人路径残留和自动换行风险；最后一次对应检查通过。

## 未执行，不得视为 PASS

- 真实 Unity Editor 编译、EditMode / PlayMode、Player Build 或游戏体验验收。
- 真实 Eagle 库访问或提示卡写入。
- Codex / ZCode 原生客户端 hook runtime 验证。
- 第三方 Skill/MCP/插件安装、连接、付费生成或外部上传。
- GitHub Actions 实际运行、GitHub push、tag 或 Release。
- 原始框架再分发权利的确认。

离线/mock PASS 不代表上述项目通过；doctor 是文件/配置预检，不证明授权或实际启动正常。
