# 双仓维护与资源更新

## 职责边界

`candle-game-resources` 维护通用 Skill、项目模板、候选工具目录、适配说明与来源。`7th-chamber` 维护游戏代码/场景、选定依赖、当前设计、任务、素材权利与实际审批。

模板不是游戏任务的权威副本。不要把游戏的 `tasks/*.json`、设计草稿、Eagle 提示词记录、批准预算或私人证据同步回公共模板。项目的 integrations 状态也不能自动变成所有下载者的授权。

## 修改通用框架

1. 优先编辑本仓库 `skills/` 或 `templates/unity-workflow/`。
2. 执行 `python -I tools/resources.py manifest`，更新根 `MANIFEST.json`。
3. 执行 `python -I tools/resources.py verify`、`python -I -m unittest discover -s tests -v` 和 `python -I -m unittest discover -s templates/unity-workflow/harness/tests -v`。
4. 安装到单独测试工程并预览冲突，不覆盖真实项目文件。
5. 记录改动与授权来源；Skill ZIP 由 `package-skills` 重新生成，`dist/` 不提交。

根清单只管理安装到游戏的文件（源路径 → 目标路径 + SHA256），不是整个 Git 仓库的签名；仓库版本身份依靠审核的 Git commit/tag。SHA256 只能检测字节变化，不能认证作者。根与模板 `.gitattributes` 固定文本为 LF，防止 Windows checkout 的自动 CRLF 转换让清单失效；不要通过改摘要来掩盖意外换行转换。

## 同步到游戏

安装后游戏持有受控副本，不依赖其他 checkout。`harness/resources.lock.json` 表明来源仓库与整理版本；初次本地准备阶段没有发布 commit/tag，不伪造一个 SHA。游戏根的 `harness/resource-snapshot.json` 记录实际安装所用资源清单的摘要，可与对应版本的资源根清单重算比对。

更新前备份或提交现有游戏变更，对比旧资源版本、当前游戏副本、新资源版本。create-only installer 不做 merge，不提供 `--force`。把人工合并的文件、理由和资源 commit 记入游戏更新任务，然后重新验证。不要靠更新摘要隐藏本地改动。

## 第三方目录

维护 `catalog/resources.json`：保留上游 URL、核验版本、许可证依据、状态与权限需求。不将“观察到的上游 HEAD”解释成“批准安装的版本”。真正启用时在游戏 `harness/integrations.json` 写入已审查的版本和工具白名单，凭据值只放本机密钥管理中。

## 发布

先完成 [许可证检查](LICENSING.md) 和 [发布清单](RELEASE_CHECKLIST.md)。创建 tag、release、push 和更改 GitHub 权限都由所有者另行执行；本次整理没有这些操作。
