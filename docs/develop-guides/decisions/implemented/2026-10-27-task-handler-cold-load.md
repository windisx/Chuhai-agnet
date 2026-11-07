# Durable Task 冷加载在领取租约前完成

状态：implemented
类型：bug-fix
Owner：backend/package/yuxi/services/task_service.py

## 问题

首次导入知识处理模块会阻塞事件循环。领取 30 秒租约后再同步加载 Handler，会消耗租约且阻止心跳，导致正常模型请求期间任务被判为失联。

## 决策

### 实现方案

`process_task` 在线程中惰性加载注册 Handler 与终态回调，加载完成后通过 repository 领取执行租约，再启动 Handler 和心跳。加载失败仍在领取后通过原有失败终态路径收敛。加载本身不执行任务领域副作用，数据库 claim 继续保证单一执行 Owner。

## 替代方案

- 延长租约：冷加载仍阻塞其他任务的心跳，且无法确定足够的固定时长。
- 启动时加载全部 Handler：改变按需加载边界，并增加不相关服务的启动依赖。

## 验证

| 验收主张 | 失败面 | 语义 Owner | 直接证据 / 命令 | 负向案例 | 当前结果 |
|---|---|---|---|---|---|
| 冷加载期间事件循环可调度且任务未领取租约 | 同步导入阻塞心跳或提前 claim | process_task | test_cold_loader_keeps_task_pending_and_event_loop_responsive | 加载阶段核对 pending 与零 attempt | Passed |
| 加载完成后真实 PostgreSQL Task 正常收敛 | 租约过期或丢失终态回调 | TaskRepository / process_task | 同一隔离 Schema integration 回读 success 与一次 attempt | 冷加载不能提前消费 lease | Passed |

任务行为单元测试 17 项通过，新增冷加载 integration 通过。完整同文件 integration 未通过：后续 16 项在 fixture 建立阶段遇到 PostgreSQL 连接中断，不能作为完整集成验证成功。负向恢复旧实现尚未执行。

## 风险

导入在线程中执行；取消等待不强制终止 Python 导入，但取消发生在领取租约之前，不启动领域任务。
