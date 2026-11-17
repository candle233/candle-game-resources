# 外部资源目录

[resources.json](resources.json) 是本仓库自定义资源索引，不是 MCP 客户端或插件市场配置。目录来自用户框架候选名单，联网核验只能证明核验时可见的公开元数据，不能替代安全审查或许可证复核。

每项包含 ID、类型、来源、状态、是否随包分发、观察到的上游版本及授权情况。所有外部候选默认 `installed: false`，`approved_commit/version: null`。`observed_commit` **不是批准锁定版本**。

- `reference_only`：上游已定位，仅记录链接与元数据。
- `unresolved`：原包只有名称，不能唯一确定实现，不提供臆造安装命令。
- `unavailable`：该上游核验失败；不推断删除、私有或许可证状态。
- 本地能力如 Unity 原生 VFX、图像生成流程不是独立 MCP 实现。

软件许可、服务条款、生成内容权利与素材许可证分开判断。保留候选项目不代表推荐其安全性，也不表示这些资源都被游戏实际使用。

便于阅读的出处汇总见 [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)。维护流程见 [MAINTENANCE.md](../docs/MAINTENANCE.md)。
