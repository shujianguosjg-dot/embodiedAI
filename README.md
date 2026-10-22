# Embodied AI｜具身智能学习笔记

记录面向机器人感知、控制、模仿学习与 VLA 的持续学习、工程实操和复现结果。主要开发路线为 **Windows 11 + WSL2 Linux + AI Agent（DSH / Codex）**，逐步完成 **ROS 2、LeRobot、PushT、Isaac Sim** 可视化实验。

> **重要约定**：规划 ≠ 已实测；实际命令输出、依赖版本、失败原因和验证结果会记录到实操随笔中。仓库目前含搭建指南，尚不表示所有仿真已经在个人设备跑通。

## 📒 学习笔记目录

1. [WSL2 具身智能开发环境完整搭建指南](学习笔记/WSL2%20%E5%85%B7%E8%BA%AB%E6%99%BA%E8%83%BD%E5%BC%80%E5%8F%91%E7%8E%AF%E5%A2%83%E5%AE%8C%E6%95%B4%E6%90%AD%E5%BB%BA%E6%8C%87%E5%8D%97.md) — 总体架构、国内镜像、GPU、ROS 2、LeRobot、PushT、Isaac Sim、Codex。
2. [WSL2 安装与配置实操随笔（2026-10-22）](学习笔记/WSL2%20%E5%AE%89%E8%A3%85%E4%B8%8E%E9%85%8D%E7%BD%AE%E5%AE%9E%E6%93%8D%E9%9A%8F%E7%AC%94%EF%BC%882026-10-22%EF%BC%89.md) — 源自实际操作补充记录，梳理 WSL 命令、Ubuntu 22.04 镜像源、XRDP 闪退、Git/Python/Node、工作目录与备份，并标注待核验项。
3. [DeepSeek Harness（DSH）在 WSL2 中的配置与具身智能开发实践](学习笔记/DeepSeek%20Harness%EF%BC%88DSH%EF%BC%89%E5%9C%A8%20WSL2%20%E4%B8%AD%E7%9A%84%E9%85%8D%E7%BD%AE%E4%B8%8E%E5%85%B7%E8%BA%AB%E6%99%BA%E8%83%BD%E5%BC%80%E5%8F%91%E5%AE%9E%E8%B7%B5.md) — 安装 Node、启动 DSH Web UI、配置模型和工作区、Agent 安全约束、分阶段安装 ROS 2/LeRobot/PushT、浏览器插件与故障排查。

## 🎯 分阶段学习目标

| 阶段 | 目标 | 当前状态 |
| --- | --- | --- |
| P0 | Windows + WSL2 基础环境、镜像、备份、Git、Python | 已记录个人操作；真实输出待核验 |
| P1 | nvm / Node / DSH Web UI + Linux 工作区只读验收 | 已完成指导文档；待实操 |
| P2 | NVIDIA GPU、WSLg、Python 环境隔离 | 待核验 |
| P3 | ROS 2 + turtlesim + RViz2 | 待实操 |
| P4 | LeRobot + PushT 可视化、随机基线与策略训练 | 待实操 |
| P5 | ROS 2 → PushT 状态桥接与可视化 | 待实操 |
| P6 | Isaac Sim / 多视角感知 / VLA 复现 | 后续目标 |

## 🧭 重要版本说明

- 本人现有补充笔记以 **Ubuntu 22.04 的相关命令**为例，尚未附系统信息输出。
- 总体搭建指南计划使用 **Ubuntu 24.04 + ROS 2 Jazzy**；如实际使用 Ubuntu 22.04，通常应选择对应的 **ROS 2 Humble**。
- **DSH 是 AI Agent，不是机器人框架**：Windows 浏览器显示它的 Web UI，而工具和项目运行于 WSL2 Linux。
- 轻量 PushT 可先完成；Isaac Sim 需要另行满足 GPU、驱动与图形兼容条件。

## 📌 记录规范

每次增加练习笔记，建议写明：日期、OS/WSL/GPU/依赖版本、目标、执行命令、关键输出、遇到的问题、原因、解决方法、复测证据、下一步。实际成功用截图或日志佐证，不推测未执行步骤。

**请勿提交**：API Key、Token、SSH 私钥、Cookie、公司/研究敏感数据、个人隐私、模型训练大文件。

## 🔗 官方入口

- [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)
- [Microsoft WSL](https://learn.microsoft.com/zh-cn/windows/wsl/)
- [ROS 2](https://docs.ros.org/)
- [Hugging Face LeRobot](https://github.com/huggingface/lerobot)
- [NVIDIA Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/latest/)

最后更新：2026-10-22。
