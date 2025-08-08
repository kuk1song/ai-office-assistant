# 生产就绪手册（Internal Production Readiness)

本手册面向公司内网部署与运维，指导将本项目以企业级标准上线运行。适用于单团队或多团队使用的内部工具场景。

---

## 1. 架构与上线形态（决策建议）

- 部署形态：容器化镜像 + 内网部署
- 身份认证：公司统一 SSO（OIDC/SAML，对接 Azure AD/Entra ID、Okta、Google Workspace、Keycloak 等）
- 授权模型：应用内轻量 RBAC（admin/user），敏感操作可二次确认
- 日志与审计：结构化日志（JSON），登录与关键操作留痕
- 持久化与备份：挂载 `var/persistent_storage` 为卷，定期快照

最小可行方案（推荐起步）：
- 一份 Docker 镜像
- 反向代理（Nginx/Traefik）+ OAuth2-Proxy 对接公司 IdP
- 应用读取代理注入的用户信息请求头（如 `X-Email`、`X-User`、`X-Groups`）进行轻量 RBAC

---

## 2. 部署选型

### 2.1 方案A：Docker Compose（小团队 / 快速落地）

- 组成：`app`（本项目镜像）+ `oauth2-proxy` + `nginx`
- 优点：简单、部署快、易维护
- 适用：单实例、低并发、单团队内部使用

Compose 关键点：
- 将 `var/persistent_storage` 映射为持久卷
- 所有配置改为环境变量注入
- 反代层完成 TLS 与 SSO，应用仅处理业务

### 2.2 方案B：Kubernetes（中大型团队 / 高可用）

- 组成：Deployment + Service + Ingress + OAuth2-Proxy + HPA + PVC
- 优点：弹性伸缩、运维标准化、与平台生态整合
- 适用：多团队、多实例、对高可用与观测有需求的团队

K8s 关键点：
- 使用 Ingress + OAuth2-Proxy/OIDC Plugin 对接 SSO
- 使用 PVC 挂载 `var/persistent_storage`
- 集中化日志与指标（ELK/Prometheus/Grafana）

---

## 3. 配置与密钥管理

- 配置统一走环境变量（12-Factor）
- 推荐引入集中化配置模块（如 `src/core/config.py` + Pydantic BaseSettings）
- 典型变量：
  - `OPENAI_API_KEY`
  - `MODEL_NAME`（如 `gpt-4o-mini`）
  - `EMBEDDING_MODEL`（如 `text-embedding-3-small`）
  - `STORAGE_DIR`（运行时自动设置为项目根下 `var/persistent_storage`）
- 密钥管理：不写入镜像、不落盘，使用平台密钥服务或 Vault/Secret Manager

---

## 4. 身份认证与授权（SSO + RBAC）

- 认证：统一接入公司 IdP（OIDC/SAML）
  - 反向代理层（OAuth2-Proxy/Nginx+auth_request）完成登录
  - 登录后注入用户信息到请求头，应用读取并做 RBAC
- 授权：
  - 轻量角色：admin/user
  - 可按知识库（或文件标签）做访问控制（后续扩展）
- 审计：
  - 登录成功/失败记录
  - 重要操作（创建/删除知识库、上传/删除文件、导出）

---

## 5. 持久化与备份策略

- 持久化路径：`var/persistent_storage`
  - 向量索引：FAISS 本地目录 `vector_store`
  - 元数据：`metadata.json`
- 卷挂载：Docker volume 或 K8s PVC
- 备份策略：
  - 定期快照（rsync/rclone 到对象存储或共享盘）
  - 版本留存策略（如 7/30/180 天）
  - 恢复演练：定期做恢复测试

---

## 6. 日志与可观测性

- 日志：
  - 使用 Python `logging` 替代 `print`
  - 结构化（JSON），包含 `trace_id`/`user`/`action` 等字段
  - 落地到 stdout（容器友好），由平台采集
- 指标：
  - QPS、延迟、错误率、成功率、上下游 API 调用耗时
  - 资源：CPU、内存、磁盘占用
- 告警：
  - 错误率/延迟突增、磁盘占用超阈值、外部依赖超时

---

## 7. 测试策略与目录

- 测试框架：`pytest`
- 目录：`tests/`
- 建议优先覆盖：
  - 工具层：知识库问答、摘要、规格提取、链路预算计算
  - 知识库生命周期：创建、添加、删除、加载、清除
  - 编排层：RAG 检索路径、工具选择路径（mock LLM）
- 增量准则：每添加一项核心功能，配套最小可行单测

---

## 8. CI/CD 建议

- CI（GitHub Actions 示例）：
  - 步骤：安装依赖 → 代码风格检查（ruff/black --check）→ 运行 pytest → 构建镜像（可选）
- CD：
  - Compose：手工或简单脚本上线
  - K8s：ArgoCD/Flux 声明式发布

---

## 9. 安全清单（上线前自检）

- [ ] 仅内网访问，入口有反代与 WAF（如需）
- [ ] 强制 SSO，关闭匿名访问
- [ ] 细化最小权限（RBAC）
- [ ] 日志不记录敏感数据；密钥不落盘
- [ ] 镜像扫描（SCA）、依赖漏洞扫描
- [ ] HTTPS/TLS 配置正确，安全响应头开启
- [ ] 备份与恢复流程可用

---

## 10. 运行与维护

- 滚动升级：优先蓝绿/金丝雀（K8s），或短暂停机（Compose）
- 变更记录：通过 ADR 记录关键决策
- 资源评估：根据 QPS/文档规模和向量库大小做容量规划

---

## 11. 与当前项目的衔接

- 已完成：
  - `var/persistent_storage` 规范化与绝对路径统一
  - 文档与图表（diagrams）标准化
  - 工具命名与结构化（knowledge_base/document/extractors/calculators）
- 待完成（建议优先级）：
  1) 引入 `logging` 全面替换 `print`
  2) 建立 `tests/` 与 `pytest` 骨架，覆盖核心路径
  3) 新建 `src/core/config.py`，集中化配置（Pydantic Settings）
  4) 添加最小 CI（lint+test）
  5) 方案A 上线：Compose + OAuth2-Proxy + Nginx
  6) 扩展 RBAC 与审计字段

---

## 附录：工程质量与成熟度审查（合并自原文）

### 成熟度评估（摘要）

- 项目结构与命名：达标（高内聚、低耦合，命名清晰）
- 代码质量与架构：达标（模块化 + Facade + 依赖注入）；待补日志系统、错误分层、外化 Prompt
- 文档：达标（技术架构、ADR、图表即代码）；待补 Docstrings、CONTRIBUTING
- 工作流与工具：有基础（依赖、ignore）；待补测试与 CI、格式化与 Linting

### 差距与路线图（摘要）

1) 测试（pytest）与日志（logging）立刻引入；2) 配置集中化；3) 统一格式化与 Lint；4) CI 最小流水线；5) 权限与审计增强。

---

## 12. FAQ

- persistent_storage 是什么？
  - 用于存放知识库的持久化数据（FAISS 向量索引 + 元数据）。已统一为项目根下 `var/persistent_storage`，并在 `.gitignore` 中忽略。
- 是否要自己实现登录？
  - 不建议。优先接入公司 SSO，应用内仅做轻量 RBAC 与审计；复杂权限在后续迭代。
- 是否必须用 K8s？
  - 非必须。小团队/早期验证，Compose 足够；需要高可用/多环境时再迁移 K8s。
