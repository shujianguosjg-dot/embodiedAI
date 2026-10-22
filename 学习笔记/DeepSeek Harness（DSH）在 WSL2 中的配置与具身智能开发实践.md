# DeepSeek Harness（DSH）在 WSL2 中的配置与具身智能开发实践

> 更新：2026-10-22  
> 适用：Windows 11 + WSL2 Ubuntu + DeepSeek Harness + Linux Bash；逐步扩展到 ROS 2、LeRobot、PushT、PyTorch、Isaac Sim。  
> 目的：在 **Windows 浏览器**可视化操作 **运行于 WSL2 Linux 内的 AI Agent**，由 Agent 在受控权限下帮助配置环境、编写代码、运行测试和记录可复现结果。  
> 状态：**配置方案/可执行步骤，不是本人所有组件已经安装完成的声明**。本机 Ubuntu 版本、GPU、DSH 安装结果尚需实际命令确认。

## 0. 先认识 DSH：它负责什么，不负责什么？

[DeepSeek Harness 官方仓库](https://github.com/deepseek-ai/deepseek-harness)（简称 DSH）是一个插件化 AI Agent 执行框架。它提供 Web UI、命令执行、编辑文件、模型接入、会话等能力。**DSH 不是 ROS 2、CUDA 或 Isaac Sim 的替代品**；它是用于自动化开发和排错的工具层。

### 推荐分层

~~~text
Windows 11
├─ 浏览器（打开 DSH Web UI，http://127.0.0.1:3080）
├─ VS Code + WSL 扩展（人工阅读、调试代码）
├─ 可选：Isaac Sim Windows 原生 GUI
└─ WSL2 Ubuntu
   ├─ Node.js + DeepSeek Harness （运行 Agent、Bash 工具）
   ├─ ~/vla/ （唯一默认工作区）
   │  ├─ AGENTS.md
   │  ├─ lerobot/
   │  ├─ pusht/
   │  ├─ ros2_ws/
   │  ├─ isaac/
   │  ├─ experiments/
   │  └─ notes/
   ├─ Ubuntu 系统 Python / ROS 2 / colcon
   └─ 单独 Conda 环境 / PyTorch / LeRobot / PushT
~~~

重要区分：

1. **“在浏览器打开 DSH Web UI”**：Windows 浏览器是控制 Agent 的前端。
2. **“Agent 自己操作第三方网页”**：需要额外启用 Browser-use 插件和浏览器提供方；它不是 Web UI 自带就必然可用。
3. **ChatGPT/Codex 与 DSH 是不同的 Agent 工具**；Windows CC Switch 的配置不会自动迁移到 DSH，必须在 DSH 配置模型/网关。

> **版本提醒**：官方项目仍是 Developer Preview，Profile、插件、模型配置方式可能不兼容更新。先查 [官方 README](https://github.com/deepseek-ai/deepseek-harness)、[CLI 帮助](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/cli-help.md) 和 [安全声明](https://github.com/deepseek-ai/deepseek-harness/blob/master/SAFETY.md)。文中的安装命令按 2026-10-22 核对。

## 1. 第 0 阶段：只读确认 WSL 与运行环境

**PowerShell（Windows）**：

~~~powershell
wsl --version
wsl -l -v
wsl --status
wsl -d Ubuntu-22.04
~~~

最后一行的名称只是示例，必须以实际 `wsl -l -v` 为准。

**Bash（WSL Ubuntu）**：

~~~bash
cat /etc/os-release
uname -r
whoami
pwd
df -h ~
free -h
git --version
python3 --version
command -v node || true
command -v npm || true
nvidia-smi || /usr/lib/wsl/lib/nvidia-smi || true
~~~

**不要假设自己正在 Ubuntu 24.04**。如当前为 Ubuntu 22.04，后续 ROS 2 一般选择 Humble；Ubuntu 24.04 再选择 Jazzy。DSH 本身独立于 ROS 2 发行版。

检查 WSL 图形功能（可选）：

~~~bash
sudo apt update
sudo apt install -y x11-apps
echo "$DISPLAY"
xeyes
~~~

Windows 11 使用 WSLg 时，普通 GUI 可直接打开 Windows 窗口，不必先用 XFCE/XRDP。若你此前已经装过 XRDP，不影响先测试 WSLg；也不要因测试失败立刻卸载其他桌面软件。

## 2. 在 WSL 内安装 Node.js：优先 nvm

官方 DSH 当前运行要求：**Node.js `^22.19.0` 或 `>=24.0.0`**。不要只看到“22”就忽略小版本。

安装 nvm：到 [nvm 官方仓库](https://github.com/nvm-sh/nvm) 复制其当前发行版安装命令并执行（不建议随意使用不明镜像中的脚本）。重新打开 WSL Bash 后：

~~~bash
command -v nvm
nvm install 22
nvm use 22
node -v
npm -v
npx -v
~~~

若获得的 Node 22 小版本不足 `22.19.0`，请更新 Node 22 或直接安装兼容的 24.x。

国内 npm 包下载不稳定时：

~~~bash
npm config get registry
npm config set registry https://registry.npmmirror.com
npm ping

# 若第三方镜像同步延迟，改回官方源重试
npm config set registry https://registry.npmjs.org
~~~

注意：npm 镜像仅加速 Node 包；Ubuntu apt、pip、Hugging Face、NVIDIA 资产仍需各自配置。

## 3. DSH 最小可用：npx 启动 Web UI

建议先不要源码构建，减少额外依赖。进入专用工作区：

~~~bash
mkdir -p ~/vla/{lerobot,pusht,ros2_ws,isaac,experiments,notes}
cd ~/vla

# 官方零安装入口（该终端需要保持运行）
npx @deepseek-ai/dsh web --no-open
~~~

默认服务地址是 `http://127.0.0.1:3080`。**以终端打印的实际完整启动 URL 为准**；某些版本的 URL 带一次性启动 token，别直接公开分享。

在 Windows 浏览器打开该地址。WSL2 默认本地端口转发通常可用；如无法打开：

~~~bash
# WSL2 检查是否在监听
ss -lnt | grep ':3080' || true

# WSL2 本地探测
curl -I http://127.0.0.1:3080/
~~~

排错时先检查实际监听端口及防火墙/localhost 转发，不要为了图方便把服务对外绑定到 `0.0.0.0`。官方新版 DSH Web 明确拒绝通配监听地址。

端口已被占用：

~~~bash
npx @deepseek-ai/dsh web --port 3081 --no-open
~~~

如打算长期频繁执行，先体验无误再考虑全局安装：

~~~bash
npm install -g @deepseek-ai/dsh
dsh --help
dsh web --no-open
~~~

已使用 nvm 时请避免 `sudo npm install -g`：很容易制造 root/普通用户双份 Node 安装和权限问题。

### 从源码运行（仅需要开发 DSH 本身时）

~~~bash
git clone https://github.com/deepseek-ai/deepseek-harness.git
cd deepseek-harness
corepack enable
pnpm install
pnpm run build
pnpm dsh web --no-open
~~~

此路线会消耗更多空间和构建时间；正常具身智能学习不需要修改 DSH 内核。

## 4. 在 DSH Web UI 配模型和 API

首次打开 Web UI → **Settings / 设置 → Models / 模型**：

1. 若用 DeepSeek 官方 API，输入在 [DeepSeek 开放平台](https://platform.deepseek.com/)获取的 API Key。
2. 若用第三方中转/公司网关，选择 **Custom model API / 自定义模型 API**，填写实际支持的 Provider ID、Base URL、协议、密钥、模型 ID。
3. 自定义模型协议应与服务商真实接口一致：`openai-completions`、`openai-responses` 或 `anthropic-messages`，不能因为“都是 OpenAI 兼容”就随便选。
4. 保存后从模型选择器选择已配置模型，用一句小任务测试是否能回复。

请优先在 Web UI 的凭据界面填写密钥。官方会以受控凭据文件保存相关信息；不要把 Key 直接写进 `AGENTS.md`、Git、聊天截图或公开日志。

可选环境变量方式：

~~~bash
mkdir -p ~/.dsh
chmod 700 ~/.dsh
# 按官方文档格式创建 ~/.dsh/.env，添加 DEEPSEEK_API_KEY=实际密钥
# 不要提交这个文件；创建后执行：
chmod 600 ~/.dsh/.env
~~~

**DSH 不会因为安装了 Codex/CC Switch 就继承它们的 OAuth 登录。** 官方模型配置说明当前不支持像 Codex 这样依赖 OAuth 的提供商通过该配置直接登录。

若使用自定义网关而报错，可检查：

- `401`：密钥或端点权限。
- `MISSING_CREDENTIAL`：凭据未实际写入或环境变量未生效。
- `UNKNOWN_MODEL`：模型 ID 与网关提供的不一致。
- `400`：协议字段、`developer` 角色、`max_completion_tokens`/`max_tokens` 不兼容，按 [模型提供方官方配置文档](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/providers.zh.md) 修正。
- 模型探测无结果：端点未必有标准 `GET /models`，可手动填入服务商确认支持的模型 ID。

### 什么时候需要 CC Switch？

如果主要目的是给 Codex CLI 切换提供商，可继续用 CC Switch；如果主要使用 DSH，**优先使用 DSH 自身的 Settings → Models**。避免一开始叠加“本地路由 + 中转 + WSL 跨网络”三层代理，降低排错复杂度。

## 5. 绑定正确工作区，保证 Agent 运行在 Linux

官方 Web UI 首次打开时未必自动选中工作区，需要点击 **Choose workspace / 选择工作区**，添加：

~~~text
/home/<你的Linux用户名>/vla
~~~

然后打开新会话，发送**只读验证任务**：

~~~text
你现在运行在 Windows 11 的 WSL2 Ubuntu Linux 环境中。
默认项目目录是 ~/vla。请先只读检查：
1. pwd、uname -a、cat /etc/os-release；
2. command -v bash、git、python3、node、npm、nvidia-smi；
3. df -h、free -h；
4. 当前工作目录的一级目录列表；
5. 显示 WSL / CUDA / ROS 2 / LeRobot 各自的“已安装、未安装、尚未验证”状态。
禁止执行安装、删除、sudo、系统配置修改或打印任何密钥。
把结果存为提议的“环境报告草稿”，先等我确认再写文件。
~~~

判断真正成功的标准：模型正常响应、能读到 Linux 目录、能执行受限的只读 Bash 工具、无需手动复制整段终端输出。**网页能打开本身不代表模型/API/文件工具都成功。**

## 6. 为具身智能项目添加 AGENTS.md 约束

建议让 DSH 首先在 `~/vla/AGENTS.md` 写入如下内容（也可人工先创建）：

~~~markdown
# Embodied AI workspace instructions

## Runtime
- Host: Windows 11; agent runtime: WSL2 Ubuntu, Bash.
- Workspace: ~/vla; keep training repositories and virtual environments on Linux filesystem.
- Determine Ubuntu version using /etc/os-release; never assume 22.04 or 24.04.
- Treat ROS 2, PyTorch, CUDA, LeRobot, Isaac Sim as separate compatibility domains.

## Approvals and safety
- Always inspect first, then show a short plan, then wait for approval before:
  sudo, apt repository changes, package removals, CUDA/driver changes,
  recursive deletions, external downloads of executable scripts,
  API/provider credential edits, writes outside the workspace.
- Never print or commit credentials, SSH keys, tokens, proprietary datasets.
- Don't open network services to 0.0.0.0 without explicit review.
- Never claim a command succeeded without checking its actual output and exit code.
- Keep experimental artifacts and data out of Git.

## Development environments
- ROS 2 uses OS-matched apt distribution (22.04/Humble or 24.04/Jazzy).
- LeRobot and policies use a separate Python environment.
- Avoid importing ROS system rclpy into arbitrary Conda interpreters.
- First achieve PushT 2D baseline; Isaac Sim later after GPU compatibility check.

## Working style
- One change per step. Record exact commands, version, error and test outcome.
- Prefer read-only diagnostics before modifications.
- For tests, report pass/fail and evidence, not "should work".
- Keep concise Markdown notes in ~/vla/notes.
~~~

此文件是 **Agent 工作约定**，不是 DSH 内核权限配置的替代品。仍需注意 Web UI 的实际权限提示和插件边界。

## 7. 让 DSH 帮你安装“国内镜像 + Linux 工具”，而不是盲目一键 sudo

初次配置直接给 DSH 这个任务（先只出计划）：

~~~text
请针对当前 WSL Ubuntu 系统生成分阶段环境配置方案，目标是：
Git、Git LFS、curl、wget、build-essential、Python 管理工具、
Node/nvm、国内 apt/pip/npm 镜像、GPU 检查和 WSLg。
要求：
A. 首先探测 Ubuntu 版本和现有镜像；
B. 备份所有将修改的配置；
C. 说明每条 sudo 命令的影响；
D. 不要自动安装或修改系统；
E. 输出每阶段验收命令、预期输出、常见故障和回滚方式。
~~~

选用镜像时遵守：

| 生态 | 可优先考虑 | 验证方式 |
| --- | --- | --- |
| Ubuntu apt | 清华 TUNA Ubuntu | `sudo apt update` |
| pip | 清华 PyPI | `python -m pip config list` |
| npm | npmmirror（必要时回官方） | `npm config get registry` |
| Hugging Face | 官方可用节点/经验证第三方镜像 | 下载样本与哈希校验 |
| NVIDIA / Isaac Sim | 官方 Windows 资源与资产区域配置 | 官方 Compatibility Checker / 资产加载 |
| ROS 2 apt | 对应 Ubuntu 版本的受信任 ROS 仓库 | `apt-cache policy ros-<distro>-desktop` |

**不要把 apt 镜像地址改成一个“万能国内镜像”来替代所有生态**，更不要跳过签名核验。

## 8. ROS 2：先做版本分岔，再运行小测试

WSL Ubuntu 发行版与 ROS 2 apt 发行版的典型对应：

- Ubuntu 22.04 → ROS 2 **Humble**。
- Ubuntu 24.04 → ROS 2 **Jazzy**。

安装阶段先让 DSH 确认：

~~~bash
. /etc/os-release
echo "$VERSION_ID"
ls /opt/ros 2>/dev/null || true
apt-cache search '^ros-(humble|jazzy)-desktop$'
~~~

随后按 [ROS 2 官方 Ubuntu 安装说明](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html) 或相应 Humble 页面设置签名仓库、安装桌面包。目标命令：

~~~bash
# Ubuntu 24.04 + Jazzy，或将 jazzy 替换为真正对应的 humble
source /opt/ros/jazzy/setup.bash
ros2 --help
ros2 run turtlesim turtlesim_node
~~~

另一个终端：

~~~bash
source /opt/ros/jazzy/setup.bash
ros2 run turtlesim turtle_teleop_key
~~~

验证 RViz：

~~~bash
rviz2
~~~

如果 WSLg 普通窗口成功，但 RViz 报 OpenGL/Ogre 错误，优先检查图形驱动/WSLg、`glxinfo -B`，不要直接重装 ROS。

推荐 ROS 工作目录：

~~~bash
mkdir -p ~/vla/ros2_ws/src
cd ~/vla/ros2_ws
colcon build --symlink-install
~~~

## 9. LeRobot + PushT：轻量二维可视化与策略训练

**不要把 PushT 与 Isaac Sim 强绑定。** 第一阶段只跑 Python 的 PushT，第二阶段做策略/演示数据，第三阶段再连 ROS 2。

Conda/Miniforge 安装独立环境的建议命令：

~~~bash
# 前提：已按官方步骤安装 Miniforge，并有 conda 命令
conda create -n lerobot python=3.12 -y
conda activate lerobot

cd ~/vla
git clone https://github.com/huggingface/lerobot.git
cd lerobot
python -m pip install -e ".[pusht,training,diffusion]"
~~~

extras/版本可能变化，先检查该 checkout 的 `pyproject.toml` 和官方文档，出现解析失败不要让 Agent 自动大范围降级。

验收 CUDA：

~~~bash
python - <<'PY'
import torch
print("torch", torch.__version__)
print("cuda_available", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu", torch.cuda.get_device_name(0))
PY
~~~

安装并运行独立 PushT 最小例子：

~~~bash
python -m pip install gym-pusht
mkdir -p ~/vla/pusht
cd ~/vla/pusht
cat > demo.py <<'PY'
import gymnasium as gym
import gym_pusht

env = gym.make(
    "gym_pusht/PushT-v0",
    obs_type="state",
    render_mode="human",
)
obs, info = env.reset(seed=42)
try:
    for step in range(300):
        obs, reward, terminated, truncated, info = env.step(
            env.action_space.sample()
        )
        env.render()
        if terminated or truncated:
            obs, info = env.reset()
finally:
    env.close()
PY
python demo.py
~~~

验收结果：Windows 桌面显示 PushT 仿真，T 字方块和推杆可以动；此时仅是**随机动作基线**，还不是训练好的策略。任何渲染失败先报告完整异常和 `render_mode` 支持情况。

**建议让 DSH 自动生成的附加产物**：

1. `requirements-lock/`（项目依赖和实际版本）
2. `tests/test_pusht_smoke.py`（环境 reset/step/shape）
3. `notes/pusht_baseline.md`（脚本、奖励、成功率和截图路径）
4. 下一步的 imitation / diffusion policy 训练计划（先看当前 LeRobot CLI，不凭旧教程猜参数）

## 10. ROS 2 + PushT 的集成：把边界隔离开

推荐先用 `rosbridge_server`（ROS 端）+ `roslibpy`（Conda 端）连接：

~~~bash
# ROS 系统终端：安装时替换 Humble/Jazzy 对应包
sudo apt install ros-jazzy-rosbridge-suite
source /opt/ros/jazzy/setup.bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml address:=127.0.0.1
~~~

~~~bash
# 独立 Conda 终端
conda activate lerobot
python -m pip install roslibpy
~~~

让 DSH 生成一个可验证桥接模块，按以下 Topic 约定：

| Topic | 消息 | 描述 |
| --- | --- | --- |
| `/pusht/agent_pose` | `geometry_msgs/Pose2D` | 推杆位置 |
| `/pusht/block_pose` | `geometry_msgs/Pose2D` | T 字方块位姿 |
| `/pusht/reward` | `std_msgs/Float32` | 当前回报（可选） |

验收：

~~~bash
source /opt/ros/jazzy/setup.bash
ros2 topic list
ros2 topic echo /pusht/block_pose
~~~

只看到 Topic ≠ 数据已经发布，要确认 `ros2 topic echo` 输出随仿真变化。RViz 要看到形状需额外转换为 `Marker`/`MarkerArray`，因为 `Pose2D` 本身不是 3D 物体可视化。

## 11. Isaac Sim：图形端先放 Windows，别让 DSH 在 WSL 强装一遍

首期工作建议：DSH 在 WSL 负责代码、依赖检查、控制消息和日志；Isaac Sim 先走 Windows 官方支持的原生安装。先核查 RTX GPU、显存、驱动、磁盘，再通过 [Isaac Sim 官方安装文档](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/quick-install.html) 安装。

**不要因为普通 WSLg GUI 成功，就让 Agent 在 WSL 内强行安装完整 Isaac Sim RTX 图形工作站。**

Isaac Sim / ROS 2 集成在 Windows、Linux 和 WSL 环境的支持策略随版本变化，必须针对实际安装的 Isaac Sim 版本选择官方方案，不能机械照搬旧版桥接教程。

## 12. Browser-use：让 DSH 真正操作网页（进阶可选）

DSH Web UI 只是“人在浏览器里操作 Agent”。如果希望 Agent 帮忙**打开下载文档、阅读 ROS wiki、查 GitHub 页面或自动点击网页**，则需要安装浏览器操作插件。

官方提供的浏览器操作体系涉及：

- `dsh-browser-use` 共享服务。
- **且只选择一个**后端：Playwright MCP、Chrome DevTools MCP 或 Stagehand（均属于实验性提供方）。
- 明确通过 Profile/Patch 激活，并在 DSH 的工具列表中确认浏览器工具已注册。

先读官方 [Browser-use 中文说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/browser-use.zh.md) 与 [CLI/Plugin 说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/cli-help.md)。

不要仅凭一个第三方插件安装命令就假定官方当前 Profile 已注册成功。实际包名、版本、配置字段和激活顺序以你安装的 DSH 版本官方资料为准。可先检查：

~~~bash
npx @deepseek-ai/dsh plugin --help
npx @deepseek-ai/dsh --profile web --dump-config
~~~

**安全边界**：不要让实验性浏览器插件直接附加包含已登录银行、邮件、科研平台的日常 Chrome 用户配置；推荐隔离 Chromium Profile。不要随意对公网暴露 CDP 调试端口（例如 9222）或 DSH Web UI。

## 13. 实际使用的 Agent 提示词：分阶段，不要一键乱装

### 提示词 A：只做环境审计

~~~text
请以 Linux 工程师和具身智能算法工程师的标准检查当前 WSL2 工作站：
输出系统版本、发行版名称、CPU/RAM/GPU、WSLg、APT、Git、Python、
Node/npm、Conda、ROS 2、PyTorch/CUDA、LeRobot、Isaac Sim 的状态。
必须区分已检测、未检测、不可用、存在风险。
不允许安装或修改任何东西，不读取、不展示秘密信息。
~~~

### 提示词 B：执行最小可行修复

~~~text
根据已确认的环境审计，选出最小依赖路径：
1) Bash/Node/npm/DSH；
2) Git/Python/Conda；
3) 与 Ubuntu 版本对应的 ROS 2；
4) LeRobot/PushT。
对每一步先提出命令和回滚方法，等待我明确批准后才执行。
不要升级系统内核/GPU 驱动，不要删除已有环境。
执行后写入 ~/vla/notes/setup-log.md：
日期、命令、实际退出码、错误输出摘要、验收结果。
~~~

### 提示词 C：PushT 项目交付

~~~text
请在 ~/vla/pusht 中实现一个最小可复现 PushT Demo：
能显示 2D 窗口、有随机动作基线、支持停止与清理资源、
支持简单 smoke test、保存依赖及日志。
然后设计下一步 Diffusion Policy 模仿学习实验：
数据集来源、训练脚本、可测指标、可视化和结果复现步骤。
不可声称已跑通没有执行过的测试。
~~~

### 提示词 D：ROS 2 话题与 RViz 可视化

~~~text
以当前 Ubuntu 正确对应的 ROS 2 发行版为前提，
搭建 PushT -> rosbridge -> ROS Topic -> RViz Marker 的最小链路。
不要把 LeRobot Conda 的 Python 混入系统 ROS Python。
先给 Topic/消息 schema，再写脚本，再分别验收数据与 GUI。
请报告每一步的实际输出和失败原因。
~~~

## 14. DSH 常用命令速记与故障定位

~~~bash
# Web 控制台
npx @deepseek-ai/dsh web --no-open

# 改端口
npx @deepseek-ai/dsh web --no-open --port 3081

# 查看帮助
npx @deepseek-ai/dsh --help
npx @deepseek-ai/dsh web --help

# 单任务无界面执行（先确认模型和权限设置已完成）
npx @deepseek-ai/dsh headless "只读列出当前项目的顶层目录，并说明结构"

# 检查组合配置
npx @deepseek-ai/dsh --profile web --dump-config
~~~

| 症状 | 先检查 | 不建议 |
| --- | --- | --- |
| `npx` 找不到 | Node/npm/nvm shell 初始化 | 直接 `sudo npm` 乱装 |
| Node 版本不兼容 | `node -v`，是否满足最低版本 | 只根据“22”大版本猜测 |
| 浏览器打开不了 3080 | 进程是否启动、`ss -lnt`、WSL localhost 转发 | 无鉴权暴露公网 |
| Web UI 能打开但无法对话 | 是否选择 Workspace、模型和凭据 | 把 API Key 发到公开 issue |
| 401/400/模型不存在 | 协议、密钥、模型 ID、兼容参数 | 反复猜测模型名称 |
| DSH 找到 Windows 路径 | `pwd`/`which node`/`echo $HOME` | 混用 Windows Node 与 WSL Node |
| ROS GUI 崩溃 | `DISPLAY`/WSLg/`glxinfo -B` | 把 Isaac Sim 与 WSLg 等同 |
| GPU 不可用 | Windows 驱动、WSL `nvidia-smi`、PyTorch CUDA wheel | 在 WSL 装 Linux NVIDIA 显卡驱动 |
| 22.04 上安装 Jazzy 失败 | 发行版不匹配 | 强行混用 apt 软件源 |
| DSH 浏览器插件没工具 | 是否激活 Browser-use 及恰好一个 Provider | 安装多个冲突 Provider |

## 15. 最终验收表

- [ ] `node -v` 满足官方 DSH 最低版本要求
- [ ] `npx @deepseek-ai/dsh web --no-open` 无启动报错
- [ ] Windows 浏览器能打开实际启动 URL
- [ ] 在 Settings → Models 成功选择一个可调用模型
- [ ] 已添加 `~/vla` Workspace，能通过只读环境诊断
- [ ] Agent 写入受控且可复核的项目笔记，未泄露凭据
- [ ] Ubuntu 国内镜像更新正常
- [ ] NVIDIA GPU / WSLg（如需）按预期可用
- [ ] ROS 2 匹配实际 Ubuntu 发行版且 `turtlesim` 能运行
- [ ] LeRobot 在独立 Python/Conda 环境中可导入
- [ ] PushT 独立 demo 实际弹出并更新画面
- [ ] `/pusht/block_pose` 有实时 ROS 2 数据
- [ ] 后续按硬件条件逐步引入 Isaac Sim

## 16. 官方资料

- [DeepSeek Harness GitHub](https://github.com/deepseek-ai/deepseek-harness)
- [DSH 使用 Web UI](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/index.zh.md)
- [DSH 模型提供方](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/providers.zh.md)
- [DSH CLI Help](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/cli-help.md)
- [DSH Browser-use](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/browser-use.zh.md)
- [DSH Safety](https://github.com/deepseek-ai/deepseek-harness/blob/master/SAFETY.md)
- [Microsoft WSL Commands](https://learn.microsoft.com/zh-cn/windows/wsl/basic-commands)
- [ROS 2 Jazzy Ubuntu Install](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)
- [Hugging Face LeRobot](https://github.com/huggingface/lerobot)
- [Isaac Sim Installation](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/quick-install.html)

---

**建议实践原则**：先在 WSL 完成 DSH → Bash → Linux 工作区 → PushT → ROS 2 的闭环，再扩展 PyTorch 模型训练和 Isaac Sim。每一步以真实命令输出、GUI 演示或测试日志作为成果，而不以“安装教程写完了”作为成功标准。
