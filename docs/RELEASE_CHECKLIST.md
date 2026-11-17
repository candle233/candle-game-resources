# GitHub 发布清单

目标：<https://github.com/candle233/candle-game-resources>

## 阻塞项

- [ ] 原始框架与本地 Skill 的作者、来源和再分发许可已确认，见 [许可证说明](LICENSING.md)。当前未完成，不应把本地整理结果直接宣传为已获开源授权。

## 发布前

- [ ] 核查 `THIRD_PARTY_NOTICES.md` 与 `catalog/resources.json`，保留所有第三方出处。
- [ ] 没有第三方未授权源码、付费素材、客户端全局配置或私有 Eagle 库。
- [ ] 没有 `.env`、tokens、Unity license、账户信息、下载缓存或构建产物。
- [ ] `manifest` 后 `verify` 成功，两个离线测试套件通过，Skill ZIP 可重复生成。
- [ ] 确认版本号、README、来源记录及游戏资源快照一致。
- [ ] README 区分离线 PASS 与 Unity / Eagle / 原生客户端 / MCP 的未执行项目。
- [ ] Unity 自托管 runner 未向不可信 fork 开放；environment 设置审核者和分支限制。
- [ ] 从干净 clone 验证安装预览、冲突拒绝和首次使用说明。

## 所有者执行

先审阅 `git status` 与 diff，再决定提交、推送、打 tag 和 GitHub Release。公开仓库中的内容可能被缓存；发布前解决授权问题，不能依赖“之后再删除”。不需要更改游戏仓库的 origin，也不应把两个 Git 历史合并。

建议 release 附件为 `package-skills` 生成的 6 个 ZIP；源码由 GitHub 的 tag 源码包提供。不要上传原始用户压缩包或其中旧测试报告来代替本次记录。
