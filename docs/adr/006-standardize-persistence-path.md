# 006: 统一持久化路径到 var/persistent_storage（绝对路径）

## 背景
- 项目有持久化数据目录 `persistent_storage`，包含 FAISS 向量索引与元数据。
- 早期实现中，多处默认参数或相对路径可能导致在项目根目录重复创建 `persistent_storage`。

## 问题
- 从不同工作目录运行应用时，相对路径会在根目录反复生成 `persistent_storage`。
- 存在两份数据的风险（根目录与 `var/` 下各一份），带来混淆与备份困难。

## 决策
- 采用“单一事实来源”的绝对路径：`PROJECT_ROOT/var/persistent_storage`。
- 路径在 `src/core/agent_system.py` 计算并下传，所有持久化模块不再自带相对路径默认值。

## 具体变更
- 在 `agent_system.py` 中：
  - 通过 `__file__` 计算 `PROJECT_ROOT`，设定 `STORAGE_DIR = PROJECT_ROOT/var/persistent_storage`。
  - 创建 `KnowledgeBaseManager(self.ai_models, STORAGE_DIR)`，显式传入路径。
- 在 `knowledge_base_manager.py` 与 `persistence_manager.py` 中：
  - 移除 `storage_dir: str = "persistent_storage"` 的默认值，改为必传。
  - 仅使用传入的 `storage_dir` 创建目录与读写文件。

## 影响
- 统一了持久化位置，避免相对路径引发的歧义。
- 便于运维：卷挂载、备份/恢复、监控与容量规划。
- 兼容性：老数据建议一次性迁移到 `var/persistent_storage`；代码已改为从起点即使用新路径。

## 备选方案
- 保留默认相对路径并在 `load()` 中迁移：复杂且容易反复产生旧目录，不采纳。

## 状态
- 已实施，后续如需更换存储后端（如对象存储、网络盘），可在此路径抽象层继续演进。
