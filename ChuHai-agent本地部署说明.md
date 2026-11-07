# ChuHai-agent 本地开发环境

代码目录：`E:\Agent_project\Yuxi-main\ChuHai-agent`。

从同级`Yuxi-main`当前工作目录复制，包含原有本地源码和未提交文件；没有复制原Git元数据、node_modules、虚拟环境和构建缓存。应用目录保持YUXi结构，许可证保留。后续竞赛功能请修改本目录的`backend`与`web`。

## 访问地址

| 入口 | 原YUXi | ChuHai-agent |
|---|---|---|
| Web | http://localhost:5173 | http://localhost:25173 |
| API文档 | http://localhost:5050/docs | http://localhost:25050/docs |
| 就绪检查 | http://localhost:5050/api/system/ready | http://localhost:25050/api/system/ready |

账号、模型配置、知识库、智能体及工作区通过停机后的完整状态目录副本迁移；登录使用原账号和密码。新环境有独立JWT签名、实例标识和沙盒token，应重新登录，不依赖原登录令牌。

复制后的两套数据从此独立：在一套环境修改知识库或对话不会同步另一套。模型服务凭证仍是复制来的原凭证，调用外部模型使用原供应商账户的额度。

## 常用操作

在本目录打开PowerShell：

```powershell
.\运行ChuHai.ps1 start
.\运行ChuHai.ps1 status
.\运行ChuHai.ps1 logs
.\运行ChuHai.ps1 stop
```

`stop`只停止新项目并保留数据。不要删除`docker/volumes`，不要执行`docker compose down -v`。

`.env`配置了独立project name和Compose文件组合。通常在本目录运行`docker compose up -d --no-build`即可；不要指定原项目名称。`.env`含凭证，不上传到公开代码库。

## 开发与镜像

API、worker和Web源码挂载均指向ChuHai-agent。API有热重载，Web是Vite开发服务器；worker沿用本机稳定配置，修改Python后可运行：

```powershell
docker compose restart worker
```

首次部署复用原环境已构建镜像，并用chuhai-agent前缀独立打标签，避免不必要下载。不是将代码挂载到原容器。修改依赖、Dockerfile或构建期文件后执行：

```powershell
.\运行ChuHai.ps1 build
docker compose up -d --no-build
```

## 隔离与数据核验

- 新容器、应用网络和本地镜像使用`chuhai-agent`前缀。
- 新数据目录为本目录`docker/volumes`，不挂载旧YUXi状态目录。
- PostgreSQL、Redis、MinIO、Milvus、Neo4j均为新容器和数据副本。
- 沙盒独立命名、地址池和工作区路径。
- `deployment/data_copy_verification.json`记录停机复制时逐文件SHA256核验；`source_snapshot.json`记录原代码来源及原.env指纹，不包含密钥内容。
- `deployment/首次复制数据.ps1`仅用于首次复制；目标数据存在时拒绝执行，不能用来覆盖后续开发数据。

Docker当前分配内存约8GB，两套服务并行会占用更多内存。新Neo4j设定了较小缓存，worker并发也降低；如需节省资源，可在不用某一套时进入对应目录执行`docker compose stop`，数据保留。

## 原项目

原项目仍位于`E:\Agent_project\Yuxi-main\Yuxi-main`，继续使用原端口。此次操作不修改其应用源码或.env。复制时短暂停机，完成后恢复服务。
