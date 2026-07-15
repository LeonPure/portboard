# PortBoard

[简体中文](./README.md) | [English](./README.en.md)

> 发现和管理本地开发服务的终端仪表盘。

PortBoard 想回答一个看似简单的问题：

**我的电脑上正在运行什么，又该从哪里访问它？**

现代开发环境中经常同时运行前端、API、数据库、容器，以及一些早已忘记的开发服务器。PortBoard 将它们汇总到一个快速、清晰的终端界面中。

> [!NOTE]
> PortBoard 目前仍处于早期 Alpha 阶段。核心发现能力和终端工作流已经可用，但公共接口仍可能调整。

## 当前功能

PortBoard 提供支持手动刷新、筛选和排序的实时终端仪表盘：

```bash
uv run portboard
```

仪表盘快捷键：

- `r`：立即刷新；`f` / `Esc`：聚焦或清空筛选。
- `p`、`o`、`n`：按项目、端口或进程排序；再次按下可反向排序。
- `Enter` 或 `d`：查看所选服务的完整详情。
- `w`：查看扫描警告和完整诊断信息。
- `c`：复制所选 HTTP 服务 URL；`b`：在默认浏览器中打开。
- `x`：停止所选进程。PortBoard 会显示 PID、命令和端口，要求确认，并在发送终止请求前重新验证进程。
- `q`：退出。

仪表盘启动时扫描一次，之后仅在按下 `r` 时刷新。如需定时自动刷新，可主动指定刷新间隔：

```bash
uv run portboard --refresh-seconds 3
```

HTTP 监听器会显示响应状态和探测延迟。4xx 或 5xx 响应会标记为不健康，但仍会作为可复制或打开的 HTTP 端点显示。其他 TCP 监听器会保留在列表中，状态为 `listening`，且不显示延迟。

当 Docker 可用时，PortBoard 还会为主机监听端口标记对应的运行中容器及其内部端口。未安装 Docker 或无法访问 Docker 守护进程时，只会增加警告，不会中断服务发现。

对于绑定到局域网可访问接口的 HTTP 服务，按 `l` 可显示所选局域网 URL 的二维码，供同一网络中的手机或平板扫描。

脚本和问题报告也可以使用具有版本化契约的 JSON 快照：

```bash
uv run portboard --json
```

JSON 会报告可见的 TCP 监听器、尽力获取的进程信息、最近的 Git 项目，以及服务响应本地短探测时的 HTTP 状态。如果操作系统限制访问某个进程，命令会保留其余结果并报告警告。如果两种系统监听器发现方式都不可用，JSON 模式会以非零状态退出，避免返回具有误导性的空快照。

## 界面预览

```text
┌ Project       Port    Status    Process       URL
│ my-blog       3000    healthy   node          http://localhost:3000
│ shop-api      8000    healthy   uvicorn       http://localhost:8000
│ postgres      5432    running   docker        localhost:5432
│ old-project   5173    unhealthy vite          http://localhost:5173
└
```

当前 Alpha 版本可以：

- 自动发现监听端口及其进程。
- 显示进程、工作目录、命令和 Git 仓库。
- 识别 HTTP 服务并检查健康状态。
- 在 Docker 可用时显示端口映射。
- 复制或打开服务 URL，并停止不再需要的进程。
- 在 macOS 和 Linux 上提供实时终端界面。

## 为什么选择 PortBoard？

现有命令通常只能分别回答单个问题：`lsof` 查找端口，容器工具列出映射，进程管理器监管已声明的应用。PortBoard 的目标是在无需提前配置项目的情况下，提供一个真正有用的本地服务总览。

## 安装

### curl

直接安装适用于当前平台的最新可执行文件，无需 Python 或 Node.js：

```bash
curl -fsSL https://raw.githubusercontent.com/LeonPure/portboard/main/install.sh | sh
```

安装器会识别 macOS/Linux 和 arm64/x64，使用 `SHA256SUMS` 校验发布归档，并默认安装到 `~/.local/bin`。如果尚无稳定版本，会自动使用最新的预发布版本。

### Homebrew

```bash
brew install LeonPure/tap/portboard
```

### uv

无需持久安装即可运行最新版：

```bash
uvx portboard
```

全局安装：

```bash
uv tool install portboard
```

### npm

无需持久安装即可运行最新版：

```bash
npx @leonpure/portboard
```

全局安装：

```bash
npm install -g @leonpure/portboard
```

npm 发行版支持 macOS 15+ 和兼容 Ubuntu 22.04 的 Linux 系统上的 arm64 与 x64。较旧的受支持系统仍可使用 Python 发行版。

## 开发

项目面向 Python 3.11+，主要使用：

- [Textual](https://textual.textualize.io/) 构建终端界面
- [psutil](https://psutil.readthedocs.io/) 发现进程和套接字
- [HTTPX](https://www.python-httpx.org/) 执行健康检查
- `pytest` 编写测试

本地开发命令：

```bash
uv sync
uv run portboard --json
uv run ruff check .
uv run mypy
uv run pytest
uv build
```

CI 会在 macOS 和 Linux 上使用 Python 3.11 与 3.13 执行相同检查。

## 路线图

计划中的里程碑见 [ROADMAP.md](./ROADMAP.md)，产品构想见[中文说明](./docs/idea.zh-CN.md)。

目标模块边界、依赖规则和实现顺序定义在[架构文档](./docs/architecture.md)中。

## 参与贡献

欢迎提交想法、问题报告和拉取请求。开发流程见 [CONTRIBUTING.md](./CONTRIBUTING.md)，安全漏洞请按照 [SECURITY.md](./SECURITY.md) 私下报告。

版本历史记录在 [CHANGELOG.md](./CHANGELOG.md) 中。

## 许可证

[MIT](./LICENSE)
