# WSL2 具身智能开发环境完整搭建指南

> **环境**：Windows 11 + WSL2 / Ubuntu 24.04 LTS + NVIDIA GPU + ROS 2 Jazzy + LeRobot + PushT + Isaac Sim + ChatGPT/Codex + CC Switch  
> **编写日期**：2026-10-13  
> **定位**：可复现的个人具身智能学习、实验与工程开发工作站。内容兼顾中国大陆镜像加速、图形可视化、GPU 计算、AI 辅助开发与常见故障排查。  
> **使用方法**：逐阶段执行，每步确认“验收”后再继续；不要一次性复制整篇运行。

## 目录

1. [总体架构与版本选择](#1-总体架构与版本选择)
2. [Windows 预检查与 WSL2 安装](#2-windows-预检查与-wsl2-安装)
3. [WSL2 配置与国内镜像源](#3-wsl2-配置与国内镜像源)
4. [Linux 基础工具、Python、Conda 与数据缓存](#4-linux-基础工具pythonconda-与数据缓存)
5. [NVIDIA CUDA 与 WSLg 图形验收](#5-nvidia-cuda-与-wslg-图形验收)
6. [VS Code、ChatGPT/Codex 和 CC Switch](#6-vs-codechatgptcodex-和-cc-switch)
7. [ROS 2 Jazzy、colcon 与 RViz2](#7-ros-2-jazzycolcon-与-rviz2)
8. [LeRobot、PyTorch、PushT 模拟](#8-lerobotpytorchpusht-模拟)
9. [PushT 到 ROS 2 的可视化通信](#9-pusht-到-ros-2-的可视化通信)
10. [Windows 原生 Isaac Sim 与国内资产](#10-windows-原生-isaac-sim-与国内资产)
11. [推荐项目规范与日常工作流](#11-推荐项目规范与日常工作流)
12. [常见错误与排查](#12-常见错误与排查)
13. [最终验收表](#13-最终验收表)
14. [官方参考资料](#14-官方参考资料)

---

## 1. 总体架构与版本选择

### 1.1 推荐架构：Windows 原生图形仿真 + WSL2 Linux 算法开发

```text
Windows 11
├── ChatGPT / Codex 桌面端（可视化 AI 工作流）
├── VS Code + WSL 扩展 + Codex 扩展
├── CC Switch（自定义 Codex API 提供方管理，可选）
├── NVIDIA Windows 驱动
├── Isaac Sim Windows Standalone（RTX / 物理仿真 / 3D GUI）
└── WSL2: Ubuntu 24.04
    ├── Codex CLI / git / uv / Miniforge
    ├── ROS 2 Jazzy / colcon / RViz2 / rosbridge
    ├── conda 环境 lerobot：Python 3.12 + LeRobot + PyTorch
    ├── PushT Gym 环境与二维可视化
    └── ~/workspace：代码、数据、权重、日志
```

**关键原则**：

- **WSL2** 适合 Linux CLI、深度学习训练、ROS 2 开发和轻量 GUI，不应默认视为 Isaac Sim 完整 RTX / Vulkan 图形工作站。
- **Isaac Sim** 优先在 Windows 原生运行；如果未来以 Isaac Lab 大规模并行训练为主，原生 Ubuntu 可能更合适。
- **Windows Isaac Sim + ROS 2**：新版官方推荐 Windows 原生 **Pixi/RoboStack ROS 2 Jazzy**；基于 WSL2 的 Isaac Sim ROS 集成属于已弃用或受限路线。不要把 WSL ROS 的成功等同于 Isaac Sim 所有桥接教程均受支持。
- **LeRobot 的 PushT** 是二维机械操作环境，可在没有 Isaac Sim、没有 ROS 2 的情况下先独立跑通。
- **隔离 Python**：ROS 2 使用系统 Python；LeRobot 使用独立 Conda 环境；两者通过 rosbridge 等方式通信。

### 1.2 版本推荐

| 模块 | 建议版本 | 说明 |
|---|---|---|
| Windows | Windows 11 x64 | WSL2 / WSLg / Isaac Sim Windows |
| Linux | Ubuntu 24.04 LTS | 与 ROS 2 Jazzy 对应 |
| ROS 2 | Jazzy | 官方 Ubuntu 24.04 二进制安装 |
| Python | LeRobot 环境 3.12 | 当前 LeRobot 文档推荐；其依赖可能随更新变化 |
| GPU | NVIDIA RTX + 兼容的 Windows 驱动 | 需要按 Isaac Sim 版本单独核对显存要求 |
| CUDA | Windows 驱动 + WSL CUDA 接口 | **不要在 WSL 内安装 Linux NVIDIA 显卡驱动** |
| Codex | 官方当前安装版本 | CLI / 桌面应用 / VS Code 扩展 |
| Isaac Sim | 安装时选官方最新稳定版本 | 具体安装脚本、最低显存会变化 |

> **资源预算**：至少预留数十 GB 的 WSL 虚拟磁盘增长空间；Isaac Sim 下载、解压、缓存、模型数据总量很容易超过 100GB。优先保证 SSD 空间，并用独立数据目录存放数据集与模型权重。若是笔记本 RTX 4050 / 4060 / 4070，请先跑 Isaac Sim Compatibility Checker，不能仅凭“有 RTX”判断兼容性。

---

## 2. Windows 预检查与 WSL2 安装

**本小节在 Windows PowerShell（管理员）运行。**

### 2.1 检查硬件与驱动

```powershell
# NVIDIA GPU、驱动与报告的 CUDA 支持版本
nvidia-smi

# 当前 WSL 信息
wsl --version
wsl --status
wsl -l -v

# 可选：系统信息
systeminfo
```

如果 `nvidia-smi` 失败，先从 [NVIDIA 官方驱动下载](https://www.nvidia.com/Download/index.aspx) 安装匹配的 Windows 驱动。BIOS 中启用 Intel VT-x / AMD SVM。若 Windows 虚拟机平台未启用，参照 [Microsoft WSL 安装](https://learn.microsoft.com/windows/wsl/install) 启用。

### 2.2 安装 WSL2 与 Ubuntu

```powershell
wsl --update
wsl --set-default-version 2
wsl --install -d Ubuntu-24.04
```

按提示重启并设置 Ubuntu 用户名及密码。

```powershell
wsl -l -v
wsl -d Ubuntu-24.04
```

**以下开始默认使用 Ubuntu Bash，除非明确标注 PowerShell。**

```bash
cat /etc/os-release
uname -r
whoami
pwd
```

**验收**：Ubuntu 24.04、WSL2 正常启动。

### 2.3 WSL 的资源配置

**回到 Windows PowerShell：**

```powershell
notepad "$env:USERPROFILE\.wslconfig"
```

以下为 **64GB 内存、足够多 CPU 线程** 的示例，不是通用固定值：

```ini
[wsl2]
memory=24GB
processors=8
swap=8GB
networkingMode=mirrored
dnsTunneling=true
autoProxy=true

[experimental]
autoMemoryReclaim=gradual
```

32GB RAM 机器可将 `memory` 改为 12–16GB；处理器数量根据实际电脑调整。`mirrored` 能改善部分 Windows localhost 与 VPN 场景，**不保证 ROS DDS 跨 Windows/WSL 自动发现可靠**。

```powershell
wsl --shutdown
wsl -d Ubuntu-24.04
```

如果 mirrored 模式引发网络冲突，可先改回 `networkingMode=nat` 再测试；不要为了代理而反复修改 ROS 配置。

### 2.4 systemd

```bash
ps -p 1 -o comm=
```

如果不是 `systemd`：

```bash
sudo nano /etc/wsl.conf
```

```ini
[boot]
systemd=true
```

在 Windows PowerShell 中执行 `wsl --shutdown` 后重启 Ubuntu。WSL 有时会报告部分 systemd 服务 `degraded`；需按实际失败服务检查，不必因为这个词直接重装。

---

## 3. WSL2 配置与国内镜像源

### 3.1 Ubuntu APT：清华 TUNA 镜像

Ubuntu 24.04 主要使用 Deb822 `ubuntu.sources`，不宜照抄 Ubuntu 20.04 的 `/etc/apt/sources.list` 教程。

```bash
sudo cp /etc/apt/sources.list.d/ubuntu.sources \
  /etc/apt/sources.list.d/ubuntu.sources.bak
cat /etc/apt/sources.list.d/ubuntu.sources
```

如果是标准 Ubuntu 官方源，可编辑文件，把 `URIs` 改为镜像站对应路径，同时**保留签名、组件和安全更新**。以下是完整示例（执行前确认机器是 Ubuntu 24.04 Noble）：

```bash
sudo tee /etc/apt/sources.list.d/ubuntu.sources >/dev/null <<'EOF'
Types: deb
URIs: https://mirrors.tuna.tsinghua.edu.cn/ubuntu/
Suites: noble noble-updates noble-backports
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg

Types: deb
URIs: https://mirrors.tuna.tsinghua.edu.cn/ubuntu/
Suites: noble-security
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg
EOF

sudo apt update
sudo apt upgrade -y
```

错误后可以用备份回退。镜像帮助：[清华 Ubuntu 镜像](https://mirrors.tuna.tsinghua.edu.cn/help/ubuntu/)。

### 3.2 pip 与 uv

```bash
python3 -m pip config set global.index-url \
  https://pypi.tuna.tsinghua.edu.cn/simple
python3 -m pip config list
```

安装 `uv`，优先官方脚本；网络失败时可在 Conda 环境内用 pip 国内源安装：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
cat >> ~/.bashrc <<'EOF'
export UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple
EOF
source ~/.bashrc
```

**注意**：PyTorch CUDA wheel 和部分 NVIDIA 包有专属索引，不能假设任何 PyPI 镜像都包含它们。若官方项目明确要求 `--index-url https://download.pytorch.org/whl/cuXXX`，优先遵循项目兼容矩阵。

### 3.3 ROS 2 仓库国内镜像

ROS 2 安装有两条**互斥**路径：

- **A. 国内镜像模式**：人工添加 ROS 2 GPG Key 和镜像地址，下文第 7 节给出命令。
- **B. 官方模式**：按 ROS 文档安装 `ros2-apt-source`，由它管理源和签名，适合 GitHub 可直连环境。

**不要同时配置多个重复的 ROS apt 源。**

### 3.4 Conda、Hugging Face、模型与资产

- Conda/Miniforge：优先 `conda-forge`；访问慢时按 [清华 Anaconda 镜像帮助](https://mirrors.tuna.tsinghua.edu.cn/help/anaconda/) 配置。镜像的可用频道与平台可能变化。
- Hugging Face：设置 `HF_HOME` 自定义缓存目录；第三方加速镜像要自行验证许可证、隐私、完整性与同步情况。
- GitHub：源码仓库建议优先官方 HTTPS/SSH；不建议把未知镜像作为 Git 凭据代理。
- Isaac Sim：使用 NVIDIA 官方提供的区域资产服务配置，而不是搜索来历不明的二次打包安装包。

---

## 4. Linux 基础工具、Python、Conda 与数据缓存

### 4.1 必备包

```bash
sudo apt install -y \
  git git-lfs curl wget ca-certificates \
  vim nano htop tmux tree jq unzip zip \
  build-essential cmake ninja-build pkg-config \
  software-properties-common \
  python3-dev python3-pip python3-venv \
  ffmpeg libgl1 libegl1 libsm6 libxext6 \
  libevdev-dev x11-apps mesa-utils

git lfs install
```

推荐目录，所有 Linux 训练源码放 WSL `~/workspace`，避免把成千上万的小文件放在 `/mnt/c`：

```bash
mkdir -p ~/workspace/{robotics,ros2_ws,experiments,datasets,checkpoints}
mkdir -p ~/workspace/robotics/{lerobot,isaac,ros2,pusht}
```

### 4.2 安装 Miniforge

```bash
cd ~
wget -O miniforge.sh \
  "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash miniforge.sh
```

按提示初始化 shell，重新打开终端：

```bash
conda --version
conda config --set auto_activate_base false
```

如果 `conda: command not found`，运行 `~/miniforge3/bin/conda init bash` 并重新打开终端。

### 4.3 缓存与 Git 身份

```bash
mkdir -p ~/workspace/datasets/hf-cache
cat >> ~/.bashrc <<'EOF'
export HF_HOME="$HOME/workspace/datasets/hf-cache"
EOF
source ~/.bashrc

git config --global user.name "你的 GitHub 显示名"
git config --global user.email "你的 GitHub 提交邮箱"
```

不要把真实 Token、API Key、SSH 私钥或浏览器凭据写入公开仓库。大模型权重和数据集也不要直接全部推送 Git 仓库。

### 4.4 可选的额外软件

- Docker Desktop + WSL Integration：后期用于容器化仿真/服务；首轮 PushT 并不需要。
- `ripgrep`、`fd-find`、`bat`：本地代码检索。
- `pre-commit`、`ruff`、`pytest`、`mypy`：工程质量工具。
- `tmux`、`htop`、`nvtop`：远程训练与资源监控（`nvtop` 的 WSL GPU 支持视版本而定）。

---

## 5. NVIDIA CUDA 与 WSLg 图形验收

### 5.1 Windows GPU

**Windows PowerShell**：

```powershell
nvidia-smi
```

如果失败，先安装/更新 Windows NVIDIA 官方驱动。**不要**在 WSL Ubuntu 中安装 `nvidia-driver-xxx` 来解决这个问题：WSL CUDA 使用 Windows 宿主驱动暴露的接口。

**WSL Bash**：

```bash
nvidia-smi
# 命令找不到时试：
/usr/lib/wsl/lib/nvidia-smi
```

`nvidia-smi` 所显示的 “CUDA Version” 表示驱动支持的上限，不等于当前 Conda 环境中的 PyTorch CUDA runtime 版本。

### 5.2 WSLg GUI

```bash
echo "$DISPLAY"
echo "$WAYLAND_DISPLAY"
xeyes
glxinfo -B
```

**验收**：Windows 桌面弹出 Linux `xeyes` 窗口。`glxinfo` 若能显示 Mesa/D3D12 信息，说明部分 Linux OpenGL 图形转发工作；这**不能**证明 Isaac Sim RTX/Vulkan 完整受支持。

### 5.3 WSL 内核与 GPU 故障的最小排查

```bash
uname -r
ls -l /dev/dxg
ls -l /usr/lib/wsl/lib/nvidia-smi
```

无法识别 GPU 时依序检查 Windows 驱动 → `wsl --update` → `wsl --shutdown` → 重新进入 WSL。一般不需要先安装 Linux CUDA Toolkit；**仅当编译 CUDA 源码、使用 `nvcc` 时**才按 NVIDIA WSL 指南选择兼容工具链，避免安装包含 Linux 驱动的 CUDA 元包。

---

## 6. VS Code、ChatGPT/Codex 和 CC Switch

### 6.1 Windows 编辑器与客户端

**Windows PowerShell**：

```powershell
winget install Microsoft.VisualStudioCode
winget install Microsoft.WindowsTerminal
winget install Git.Git
```

Windows 安装 [ChatGPT 桌面端](https://chatgpt.com/download/)。VS Code 安装 `WSL`（Microsoft）、`Codex`（OpenAI）、Python、Pylance、Jupyter、CMake Tools；ROS 扩展按实际版本选用。

**WSL Bash**：

```bash
cd ~/workspace/robotics
code .
```

确认 VS Code 左下角显示连接到 WSL，集成终端内：

```bash
echo "$WSL_DISTRO_NAME"
which python3
pwd
```

项目目录应是 `/home/<Linux用户>/workspace/...`，而不是误操作 Windows 的其他 Python 环境。

### 6.2 安装 Codex CLI（WSL 内）

官方安装脚本（先保存与检查，再执行）：

```bash
curl -fsSL https://chatgpt.com/codex/install.sh -o /tmp/install-codex.sh
less /tmp/install-codex.sh
sh /tmp/install-codex.sh

codex --version
codex
```

或使用系统已安装的兼容 Node.js/npm：

```bash
npm install -g @openai/codex
```

不要把 Windows 全局 Node.js/npm 误当成 WSL 本地环境。使用 ChatGPT 登录时，授权与订阅规则按官方客户端实际提示处理；ChatGPT 订阅、官方 API 计费、第三方转发的计费互不等价。

### 6.3 给 Codex 的第一条环境检查指令

```text
你现在位于 WSL2 Ubuntu 24.04。请只运行只读诊断命令，汇报：
1. Ubuntu、内核、WSL 版本；
2. GPU 与 CUDA 状态；
3. Git、Python、Conda、uv、cmake 版本；
4. ROS 2 是否安装及是否 source；
5. 当前工作目录、内存、磁盘剩余空间。
不要自动安装、卸载或覆盖任何软件。先生成检查报告与风险清单。
```

### 6.4 CC Switch（Windows 侧）

项目地址：[farion1231/cc-switch](https://github.com/farion1231/cc-switch)。优先从官方仓库发行页下载安装。连接 WSL Codex 配置时，路径通常是：

```text
\\wsl.localhost\Ubuntu-24.04\home\<Linux用户名>\.codex
```

在 WSL 先保证配置目录存在：

```bash
mkdir -p ~/.codex
ls -la ~/.codex
```

**关于国内 API 中转**：

1. 在 CC Switch 新增 Codex 提供商；填写服务商真实 Base URL、模型 ID、协议类型、API Key。
2. 验证中转服务支持 Codex 所需的 **Responses API、流式输出、工具调用、足够的上下文**，而不是只兼容传统 Chat Completions。
3. 不要在文档、日志或 Git 仓库保存明文 Key；不把 ChatGPT 网页登录态、账户密码交给第三方。
4. 中转商可能处理请求内容，保密论文、未公开代码、工作项目应优先使用可信官方服务。
5. CC Switch 更适于管理可配置的 CLI Provider，**不应推断 ChatGPT 桌面应用会自动采用所有第三方 API 中转设置**。

配置结构示例，**仅作字段说明，不能直接运行**：

```toml
model_provider = "custom"
model = "your-supported-model"

[model_providers.custom]
name = "custom"
base_url = "https://your-provider.example/v1"
wire_api = "responses"
```

如果 CC Switch 开启本地代理端口，可在 WSL mirrored 网络下测试（把端口换成真实值）：

```bash
curl -v http://127.0.0.1:<实际端口>/
```

返回 HTTP 响应说明该 TCP 端口可能可达，但不等于 API 鉴权或模型工具调用成功；`Connection refused` 优先检查 Windows 防火墙、CC Switch 监听地址、端口和 WSL 网络模式。

---

## 7. ROS 2 Jazzy、colcon 与 RViz2

### 7.1 安装准备

```bash
sudo apt install -y locales gnupg2 software-properties-common
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LANG=en_US.UTF-8
sudo add-apt-repository universe -y
```

### 7.2 选项 A：国内 ROS 2 镜像（推荐中国大陆网络先尝试）

先查看是否已经由 `ros2-apt-source` 管理仓库；**如果已经安装，就不要重复加下列文件**：

```bash
dpkg -l | grep ros2-apt-source || true
ls /etc/apt/sources.list.d/ | grep -i ros || true
```

若没有配置，添加 ROS 官方公钥并使用 TUNA 镜像：

```bash
curl -fsSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /tmp/ros.key
sudo gpg --dearmor --yes \
  -o /usr/share/keyrings/ros-archive-keyring.gpg \
  /tmp/ros.key

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] https://mirrors.tuna.tsinghua.edu.cn/ros2/ubuntu noble main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list

sudo apt update
```

如果 GitHub Raw 被阻断，不要绕过 GPG 签名。通过可信网络下载官方 `ros.key`、核验后放入 `/tmp/ros.key` 再继续。镜像地址以 [清华 ROS 2 镜像帮助](https://mirrors.tuna.tsinghua.edu.cn/help/ros2/) 为准。

### 7.3 选项 B：ROS 官方推荐仓库配置（与 A 二选一）

官方推荐用 `ros2-apt-source` 包管理源和签名，具体发布文件名与版本随官方更新变化：

- [ROS 2 Jazzy Ubuntu Debian Packages](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)
- [ros-apt-source releases](https://github.com/ros-infrastructure/ros-apt-source/releases)

按该页取得最新 `.deb` 包并安装后执行 `sudo apt update`；如果已经选了 A，不需再执行 B。

### 7.4 安装 ROS 2 桌面与开发工具

```bash
sudo apt install -y \
  ros-jazzy-desktop \
  ros-dev-tools \
  python3-colcon-common-extensions \
  python3-rosdep

source /opt/ros/jazzy/setup.bash
ros2 --help
```

只在系统 ROS 的 Bash 终端 source：

```bash
echo 'source /opt/ros/jazzy/setup.bash' >> ~/.bashrc
```

如果之后 Conda 的 Python 跟系统 ROS 扩展发生动态库冲突，请分别打开终端，按任务显式激活环境。避免在 LeRobot 的 Conda 环境内直接运行依赖系统 `rclpy` 的脚本。

### 7.5 ROS GUI / 节点通信验收

**终端 A**：

```bash
source /opt/ros/jazzy/setup.bash
ros2 run turtlesim turtlesim_node
```

**终端 B**：

```bash
source /opt/ros/jazzy/setup.bash
ros2 run turtlesim turtle_teleop_key
```

继续测试：

```bash
rviz2
```

可以额外运行官方 demo `talker/listener`，验证 ROS 2 节点发布/订阅。如果 `turtlesim` 正常、RViz 异常，优先检查 WSLg / OpenGL 而非重装 ROS。

### 7.6 建立 ROS 2 工作区

```bash
mkdir -p ~/workspace/ros2_ws/src
cd ~/workspace/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

---

## 8. LeRobot、PyTorch、PushT 模拟

### 8.1 单独创建 Python 3.12 环境

```bash
conda create -n lerobot python=3.12 -y
conda activate lerobot
conda install -c conda-forge ffmpeg evdev -y
```

### 8.2 获取 LeRobot 源码

```bash
cd ~/workspace/robotics
git clone https://github.com/huggingface/lerobot.git
cd lerobot
python -m pip install -e ".[pusht,training,diffusion]"
```

这里的 extras 要与**当前检出的 LeRobot 版本**相匹配；安装前可以先读 `pyproject.toml`。官方当前文档支持 Python 3.12，并将 `pusht`、`training` 和 `diffusion` 列为可选择项。

**建议在第一次成功后记录版本**：

```bash
python --version
python -m pip freeze > ~/workspace/experiments/lerobot-requirements.lock.txt
git rev-parse HEAD
```

### 8.3 CUDA PyTorch 验证

```bash
python - <<'PY'
import torch
print('Torch:', torch.__version__)
print('PyTorch CUDA runtime:', torch.version.cuda)
print('CUDA available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('GPU:', torch.cuda.get_device_name(0))
PY
```

如果 CUDA 为 `False`，先确认 `nvidia-smi` 在 WSL 中可用。需要替换 PyTorch 时，按 [PyTorch 官方安装选择器](https://pytorch.org/get-started/locally/) 和当前驱动版本选择匹配的 CUDA wheel，不要盲目强行安装指定版本，也不要把 CPU-only 包混入 CUDA 环境。

### 8.4 用 Gym PushT 先运行二维可视化

`gym-pusht` 通常会被 `[pusht]` extra 作为依赖安装；若没安装，可以在 `lerobot` 环境中额外执行：

```bash
python -m pip install gym-pusht
```

创建 `~/workspace/robotics/pusht/test_pusht.py`：

```python
import gymnasium as gym
import gym_pusht  # noqa: F401：注册 PushT 环境

env = gym.make(
    "gym_pusht/PushT-v0",
    obs_type="state",
    render_mode="human",
)

obs, info = env.reset(seed=42)
try:
    for step in range(1000):
        action = env.action_space.sample()  # 随机基线，不是训练策略
        obs, reward, terminated, truncated, info = env.step(action)
        env.render()
        if step % 50 == 0:
            print(f"step={step}, reward={reward:.3f}")
        if terminated or truncated:
            obs, info = env.reset()
finally:
    env.close()
```

执行：

```bash
conda activate lerobot
cd ~/workspace/robotics/pusht
python test_pusht.py
```

**验收**：Windows 桌面经 WSLg 弹出二维 PushT GUI，推杆随机移动并可看到 T 字块。此时只是随机动作测试；训练 Diffusion Policy、使用 demonstration dataset、评估成功率是后续里程碑。

**为什么先做 PushT？** 因为它独立于 Isaac Sim 和 ROS 2，能单独定位 Python、Gym、图形渲染、动作/观测和策略训练问题。

---

## 9. PushT 到 ROS 2 的可视化通信

### 9.1 方案：通过 rosbridge 解耦 Python 环境

```text
Conda Python 3.12: gym-pusht + roslibpy
              ↓ WebSocket (127.0.0.1:9090)
System ROS 2 Jazzy: rosbridge_server
              ↓ ROS 2 topics
ros2 topic echo / 自定义 Marker 节点 / RViz2
```

这样无须把 ROS 系统 Python 的 `rclpy` 强行装入 LeRobot 的 Conda 环境。

### 9.2 安装并运行桥接器

**ROS 2 系统终端 A**：

```bash
sudo apt install -y ros-jazzy-rosbridge-suite
source /opt/ros/jazzy/setup.bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml \
  address:=127.0.0.1
```

如果 ROS package 版本使用了不同的 launch 参数或文件名，先运行 `ros2 pkg prefix rosbridge_server` 并查找其 `share/.../launch`，按当前实际版本替换。只需本机访问时优先绑定 loopback，避免把未鉴权 WebSocket 服务暴露到局域网。

**LeRobot 环境终端 B**：

```bash
conda activate lerobot
python -m pip install roslibpy
```

### 9.3 发布 PushT 状态到 ROS 2

创建 `~/workspace/robotics/pusht/pusht_rosbridge.py`：

```python
import time
import gymnasium as gym
import gym_pusht  # noqa: F401
import roslibpy

ros = roslibpy.Ros(host="127.0.0.1", port=9090)
ros.run(timeout=10)
if not ros.is_connected:
    raise RuntimeError("rosbridge 未连接，请先启动 ROS 2 rosbridge_server")

block_topic = roslibpy.Topic(ros, "/pusht/block_pose", "geometry_msgs/Pose2D")
agent_topic = roslibpy.Topic(ros, "/pusht/agent_pose", "geometry_msgs/Pose2D")

env = gym.make("gym_pusht/PushT-v0", obs_type="state", render_mode="human")
obs, info = env.reset(seed=42)

try:
    for step in range(1000):
        obs, reward, terminated, truncated, info = env.step(
            env.action_space.sample()
        )
        env.render()
        # state 模式的预期排列（以实际 gym_pusht 版本为准）：
        # [agent_x, agent_y, block_x, block_y, block_angle]
        if len(obs) < 5:
            raise ValueError(f"非预期 PushT 观测格式: shape={obs.shape}")
        agent_topic.publish(roslibpy.Message({
            "x": float(obs[0]), "y": float(obs[1]), "theta": 0.0,
        }))
        block_topic.publish(roslibpy.Message({
            "x": float(obs[2]), "y": float(obs[3]), "theta": float(obs[4]),
        }))
        if terminated or truncated:
            obs, info = env.reset()
        time.sleep(0.03)
finally:
    env.close()
    block_topic.unadvertise()
    agent_topic.unadvertise()
    ros.terminate()
```

运行：

```bash
conda activate lerobot
cd ~/workspace/robotics/pusht
python pusht_rosbridge.py
```

**ROS 2 系统终端 C**：

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic list
ros2 topic echo /pusht/block_pose
```

**验收**：Topic 不断输出 `x/y/theta`。这是 PushT 与 ROS 2 消息联通验证，不是完整 RViz 三维复原。**RViz 不能直接将 `Pose2D` 显示成 T 字模型**；要显示它，需要编写 `visualization_msgs/MarkerArray` 转换节点，对圆形推杆和 T 字块使用正确的几何组合、比例/坐标变换，并在 RViz 添加 MarkerArray 显示。PushT 自带窗口则已提供原生二维可视化。

---

## 10. Windows 原生 Isaac Sim 与国内资产

### 10.1 先查硬件兼容性

- Isaac Sim 是 GPU / RTX / Vulkan 要求较高的三维仿真器；不能简单等同普通 PyTorch CUDA。
- 安装前阅读 [Isaac Sim Requirements](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/requirements.html)。
- 优先运行安装包自带的 Compatibility Checker；低显存显卡可能只能运行极简场景，甚至不被当前版本支持。

### 10.2 Windows Standalone 安装

根据 [Isaac Sim Quick Install](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/quick-install.html) 下载 Windows 独立安装包，建议解压至：

```text
C:\isaacsim
```

**Windows PowerShell**：

```powershell
cd C:\isaacsim
.\isaac-sim.compatibility_check.bat
# 通过硬件检查后：
.\isaac-sim.bat
```

若安装包不包含该脚本，请以对应发布版本文档/目录为准，不要运行从其他版本随意复制的启动脚本。首次启动会生成着色器缓存，可能显著慢于后续启动。

### 10.3 中国区域 Isaac Sim Asset Profile

一些新版版本提供 `china` 区域资产选项。使用前核对对应版本的 [Accessing Assets](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_assets.html) 文档：

```powershell
cd C:\isaacsim
$env:ISAACSIM_ASSET_REGION_PROFILE = "china"
.\isaac-sim.bat
```

该环境变量（在支持它的版本中）用于 Isaac Sim 资产区域选择，不等于 PyPI/GitHub/NVIDIA 所有下载自动加速。资源未覆盖时可考虑官方离线资产包并配置对应版本的本地资产根目录。

### 10.4 Isaac Sim 与 ROS 2 桥接的路线

**新版本 Windows 推荐 Windows 原生 Pixi + RoboStack Jazzy**，而不是默认使用 WSL2 ROS 2 运行完整官方教程。官方明确指出一些自定义接口、launch、Navigation 等流程不支持或不完全支持 Windows WSL 方案。

Windows PowerShell：

```powershell
winget install prefix-dev.pixi

git clone --recurse-submodules `
  https://github.com/isaac-sim/IsaacSim-ros_workspaces.git `
  C:\IsaacSim-ros_workspaces

cd C:\IsaacSim-ros_workspaces\jazzy_ws
pixi install
pixi run build
```

**重要**：Pixi workspace 的文件结构与任务名会随着仓库版本变化，先读 README/pixi.toml。Windows 原生 ROS 2 开发还可能需要 Visual Studio 2022 C++ Build Tools。安装前保持 Isaac Sim 与 workspace 的发布版本匹配；不要把这套独立 Pixi ROS 环境与 WSL 系统 ROS 环境混为一谈。

### 10.5 后续三维仿真里程碑

1. Isaac Sim 独立打开场景、加载资产并运行物理步进。
2. 在 Isaac Sim 内创建简化桌面/机械臂场景，验证关节/接触动力学。
3. 用官方 ROS 2 Bridge 发布 TF、传感器或关节状态。
4. 在支持的 ROS 环境中验证控制指令闭环。
5. 再考虑从 PushT 过渡到三维抓取、模仿学习或 Isaac Lab 并行训练。

---

## 11. 推荐项目规范与日常工作流

### 11.1 目录结构

```text
~/workspace/
├── robotics/
│   ├── lerobot/               # 上游 LeRobot 源码
│   ├── pusht/                 # 个人 PushT 代码、ROS 桥接代码
│   ├── ros2/                  # 个人 ROS 节点源码
│   └── isaac/                 # 仿真配置与脚本（非整个 Windows Isaac Sim）
├── ros2_ws/src/              # colcon 工作空间
├── experiments/              # 记录环境、版本、实验日志
├── datasets/                 # 大型数据集与 HF 缓存
└── checkpoints/              # 模型权重（通常 Git 忽略）
```

### 11.2 AGENTS.md（给 Codex 的环境操作规范）

```markdown
# Robotics Development Rules

## Environment
- OS: Windows 11 + WSL2 Ubuntu 24.04
- ROS 2: Jazzy; system apt installation
- LeRobot: Conda Python 3.12, separate from ROS 2
- Isaac Sim: Windows native installation
- Workspace: ~/workspace/robotics

## Rules
1. Before installing packages, print which Python and which environment are active.
2. Do not mix system ROS 2 Python with LeRobot Conda unless an integration plan is documented.
3. Prefer trustworthy domestic package mirrors where appropriate.
4. Verify Windows NVIDIA driver and WSL GPU before modifying PyTorch.
5. Do not expose, echo, commit, or upload passwords/API keys/tokens.
6. Require approval before system-wide package changes, deleting environments, or changing drivers.
7. Preserve existing datasets and checkpoints.
8. After every change, run the smallest relevant test and record results.
9. Record package versions and git commit SHAs for reproducibility.
10. Do not claim an installation or test succeeded unless actual command output confirms it.

## Goal
Reproducible LeRobot PushT, ROS 2 visualization and Isaac Sim development environment.
```

### 11.3 Git 与版本记录

```bash
# 在个人项目（而不是上游 LeRobot 仓库）内执行
git init
git status
```

`.gitignore` 建议至少包含：

```gitignore
.env
*.key
*.pem
.venv/
__pycache__/
*.pyc
.conda/
checkpoints/
datasets/
wandb/
runs/
*.log
```

示例环境导出：

```bash
conda activate lerobot
python -m pip freeze > ~/workspace/experiments/pip-freeze.txt
conda env export --from-history > ~/workspace/experiments/lerobot-history.yml
nvidia-smi > ~/workspace/experiments/gpu-driver.txt
```

如果导出的文件包含用户名、私有索引地址或 Token，发布前必须检查脱敏。

---

## 12. 常见错误与排查

| 症状 | 优先检查 | 建议处理 |
|---|---|---|
| `wsl --install` 失败 | BIOS 虚拟化、Windows 虚拟机平台、WSL 版本 | 开启虚拟化，`wsl --update`，重启 |
| Ubuntu `apt update` 超时 | APT URIs、DNS、代理、镜像站状态 | 测试 `curl -I`，必要时恢复备份源 |
| VS Code 误用 Windows Python | VS Code 左下角、`which python`、工作目录 | `code .` 从 WSL 启动，选择 WSL 解释器 |
| WSL `nvidia-smi` 不可用 | Windows 驱动、`/dev/dxg`、WSL 更新 | 优先修复 Windows 驱动，不装 Linux 显卡驱动 |
| `torch.cuda.is_available() == False` | wheel 是否 CPU-only、驱动是否兼容 | 按 PyTorch 官方索引安装匹配 CUDA wheel |
| `xeyes` 不弹出 | `DISPLAY`、WSLg、WSL 更新 | 优先完成简单 GUI 验收，再运行 RViz |
| `rviz2` 黑屏/崩溃 | WSLg OpenGL/Mesa/驱动 | 测试 `glxinfo -B`，检查 RViz 终端日志 |
| ROS 2 找不到包 | `/opt/ros/jazzy/setup.bash`、仓库配置 | 正确 source；避免 Conda Python 污染 |
| `rosdep update` 下载失败 | GitHub Raw/rosdistro 访问 | 用可信网络与明确可用的 rosdep 镜像，不关签名/校验 |
| Conda 解依赖卡住 | conda-forge 速度、频道优先级 | 优先减少频道和冗余依赖，必要时配置官方文档支持的镜像 |
| PushT 无窗口 | Gym 渲染模式、WSLg、DISPLAY | 先运行 `xeyes`，再检查版本 API |
| rosbridge 连接拒绝 | WebSocket 服务是否运行/端口 9090 | 检查进程、监听地址、ROS 终端日志 |
| CC Switch 无法连接 | 本地路由、WSL networking、URL/端口 | mirrored/nat 分别测试，检查服务是否监听 |
| Codex API 模型报错 | 模型 ID、Responses API、Key/套餐权限 | 在服务商文档中确认工具调用和协议支持 |
| Isaac Sim 无法启动 | 显存、驱动、硬件检查、日志 | 先运行 Compatibility Checker；别把 WSL CUDA 正常当作 RTX GUI 正常 |
| Isaac Sim 场景资产缺失 | 资产区域、服务连通性、离线包 | 对应版本开启中国资产 Profile 或本地资源 |

---

## 13. 最终验收表

- [ ] `wsl -l -v` 显示 Ubuntu 24.04 且为 WSL2
- [ ] `sudo apt update` 使用预期 Ubuntu 镜像，正常更新
- [ ] `nvidia-smi` 在 Windows 和 WSL 都能识别 GPU
- [ ] `xeyes` 可经 WSLg 弹出窗口
- [ ] WSL 内 `codex --version` 成功，Codex 能在指定项目执行只读诊断
- [ ] VS Code 使用 `WSL: Ubuntu-24.04`，Python 解释器正确
- [ ] `source /opt/ros/jazzy/setup.bash` 后 `ros2 --help` 成功
- [ ] `turtlesim` 和 `rviz2` 都能启动 GUI
- [ ] LeRobot Conda 环境 Python 3.12；`torch.cuda.is_available()` 为 `True`（如需 GPU）
- [ ] `python test_pusht.py` 弹出 PushT 可视化窗口
- [ ] rosbridge 正常启动；`ros2 topic echo /pusht/block_pose` 收到状态
- [ ] Isaac Sim Compatibility Checker 通过，Windows 侧可以启动图形程序
- [ ] 记录 Git SHA、软件版本、驱动版本与成功/失败日志

**推荐安装顺序**：

1. **底层稳定**：WSL2 → APT 镜像 → Windows NVIDIA 驱动 → WSLg 和 CUDA。
2. **AI 编辑与运维**：VS Code WSL → Codex CLI → ChatGPT/CC Switch。
3. **轻量仿真**：ROS 2 + RViz → LeRobot/PyTorch → PushT → rosbridge。
4. **三维与研究**：Isaac Sim → 官方资产加速 → Windows Pixi ROS → Isaac Sim Bridge → 具身智能训练。

---

## 14. 官方参考资料

- [Microsoft：Install WSL](https://learn.microsoft.com/windows/wsl/install)
- [Microsoft：Advanced settings configuration in WSL](https://learn.microsoft.com/windows/wsl/wsl-config)
- [Microsoft：WSLg](https://github.com/microsoft/wslg)
- [NVIDIA：CUDA on WSL User Guide](https://docs.nvidia.com/cuda/wsl-user-guide/index.html)
- [清华开源软件镜像站：Ubuntu](https://mirrors.tuna.tsinghua.edu.cn/help/ubuntu/)
- [清华开源软件镜像站：PyPI](https://mirrors.tuna.tsinghua.edu.cn/help/pypi/)
- [清华开源软件镜像站：ROS 2](https://mirrors.tuna.tsinghua.edu.cn/help/ros2/)
- [清华开源软件镜像站：Anaconda](https://mirrors.tuna.tsinghua.edu.cn/help/anaconda/)
- [OpenAI Codex 官方仓库](https://github.com/openai/codex)
- [OpenAI Codex 文档](https://developers.openai.com/codex/)
- [CC Switch 官方仓库](https://github.com/farion1231/cc-switch)
- [ROS 2 Jazzy 官方 Ubuntu 安装](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)
- [ROS 2 官方 Tutorials](https://docs.ros.org/en/jazzy/Tutorials.html)
- [LeRobot 官方仓库](https://github.com/huggingface/lerobot)
- [LeRobot 官方安装指南](https://github.com/huggingface/lerobot/blob/main/docs/source/installation.mdx)
- [Gym PushT](https://github.com/huggingface/gym-pusht)
- [rosbridge_suite](https://github.com/RobotWebTools/rosbridge_suite)
- [Isaac Sim Quick Install](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/quick-install.html)
- [Isaac Sim ROS 2 Installation](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_ros.html)
- [Isaac Sim ROS Workspaces](https://github.com/isaac-sim/IsaacSim-ros_workspaces)

> **版本提示**：本指南记录 2026-10-13 的推荐路线，但软件依赖、脚本参数、仓库分支和镜像状态会变化。发生冲突时优先遵循与已安装软件版本匹配的官方文档，记录自己的实测差异后再更新本笔记。
