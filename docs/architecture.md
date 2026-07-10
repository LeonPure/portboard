# PortBoard 架构

本文档定义 PortBoard 的目标架构和演进边界。实现可以分阶段落地，但模块职责和依赖方向应遵循本文档；若需要改变这些约束，应先更新文档并说明原因。

## 架构目标

PortBoard 的核心能力是把来自操作系统和外部工具的信息整理成一份统一的本地服务快照。终端界面、JSON 输出和后续可能出现的其他界面，都只是这份快照的消费者。

架构需要保证：

- 不启动 TUI 也能发现和检查服务。
- macOS、Linux 以及不同系统数据源可以独立适配。
- psutil、Git、Docker 或 HTTP 探测的单点失败不会中断整次扫描。
- JSON 输出和 TUI 使用相同的应用用例与领域模型。
- 危险操作必须经过应用层校验和用户确认，展示层不能直接结束进程。

## 依赖方向

```text
                         bootstrap
                        /         \
              presentation       adapters
                        \         /
                        application
                             |
                           domain
```

依赖只能指向图中更内层的模块：

- `domain` 不依赖项目内其他层，也不导入 Textual、psutil 或 HTTPX。
- `application` 依赖 `domain`，并通过抽象契约声明它需要的外部能力。
- `adapters` 实现应用层契约，封装操作系统、命令行程序和网络库。
- `presentation` 调用应用用例并展示结果，不直接访问 psutil、Docker 或操作系统进程 API。
- `bootstrap` 是组合根，负责选择具体适配器并把它们注入应用用例。

## 目标目录结构

目录按实际里程碑逐步创建，不为尚未实现的功能预建空文件。

```text
src/portboard/
├── __main__.py                 # 最小程序入口
├── cli.py                      # 参数解析，选择 TUI 或 JSON 模式
├── bootstrap.py                # 组合应用用例和具体适配器
│
├── domain/
│   ├── models.py               # Listener、Process、Project、Service、Snapshot
│   └── errors.py               # 可呈现的领域错误和警告
│
├── application/
│   ├── contracts.py            # Scanner、Resolver、Probe、Controller 等协议
│   ├── discover.py             # 发现并组装本地服务快照
│   ├── inspect.py              # HTTP 健康检查和服务详情
│   └── actions.py              # 打开 URL、复制地址和停止进程
│
├── adapters/
│   ├── system/
│   │   ├── psutil_scanner.py   # 监听端口和进程信息
│   │   └── process_controller.py
│   ├── project/
│   │   └── git_resolver.py     # 从工作目录查找最近的 Git 仓库
│   ├── http/
│   │   └── httpx_probe.py      # HTTP 识别、状态和延迟
│   ├── containers/
│   │   └── docker_cli.py       # 可选 Docker CLI 集成
│   └── desktop.py              # 浏览器和剪贴板操作
│
└── presentation/
    ├── json_output.py          # 稳定、可版本化的机器输出
    └── tui/
        ├── app.py
        ├── state.py
        ├── screens/
        ├── widgets/
        └── portboard.tcss

tests/
├── unit/                       # 领域模型和应用用例，使用假适配器
├── integration/                # psutil、Git、Docker 等边界集成
├── contract/                   # CLI 和 JSON 格式兼容性
└── fixtures/
```

## 核心模型

领域模型应表达事实，不携带 UI 状态或第三方库对象。

- `Listener`：监听地址、端口和传输协议。
- `ProcessInfo`：PID、进程名、命令和工作目录；受权限限制的字段允许为空。
- `ProjectInfo`：项目名、根目录和 Git 元数据。
- `HealthInfo`：协议、状态、延迟和最近一次检查时间。
- `ContainerInfo`：容器身份和端口映射；仅在 Docker 可用时存在。
- `Service`：把监听端点与进程、项目、健康状态和容器信息关联起来。
- `ServiceSnapshot`：一次扫描的时间、服务集合和非致命警告。

模型优先使用不可变 dataclass、枚举和标准库类型。展示需要的选中行、排序方式、颜色和刷新状态属于 `presentation`，不能进入领域模型。

## 发现流程

一次发现操作按以下顺序执行：

1. 系统扫描器读取 TCP 监听端点以及可获得的进程信息。
2. 项目解析器从进程工作目录向上查找最近的 Git 仓库。
3. 应用层合并并规范化数据，生成 `Service`。
4. 后续版本可并发加入 HTTP 和 Docker enrichment，但它们不改变基础发现契约。
5. 应用层返回完整的 `ServiceSnapshot`。
6. JSON 输出或 TUI 消费快照；两者不得重复实现发现逻辑。

刷新由展示层触发，扫描间隔是运行配置。应用层的单次发现用例不维护永久后台任务，也不保存 UI 状态。

## 失败处理

本地进程天然存在竞态：端口可能在扫描期间关闭，进程可能退出，部分字段也可能因权限不可读。因此：

- 单个端点解析失败时保留仍然可信的字段，并向快照加入 warning。
- Git、Docker 和 HTTP 探测失败均视为可降级错误。
- 缺少可选工具不应显示为程序错误。
- 只有无法开始基础系统扫描或内部契约被破坏时，命令才以失败状态退出。
- 停止进程必须显示目标 PID、命令和端口并获得明确确认；PID 在执行前需要重新验证。

## 稳定输出契约

JSON 是脚本接口和问题报告格式，顶层必须包含 `schema_version`、`observed_at`、`services` 和 `warnings`。新增可选字段可以保持当前版本；删除字段、改变含义或改变类型需要提升 schema 版本。

第一版目标形态：

```json
{
  "schema_version": 1,
  "observed_at": "2026-07-12T02:00:00Z",
  "services": [
    {
      "host": "127.0.0.1",
      "port": 3000,
      "transport": "tcp",
      "pid": 12345,
      "process_name": "node",
      "command": "npm run dev",
      "cwd": "/code/example",
      "project_root": "/code/example"
    }
  ],
  "warnings": []
}
```

时间使用带时区的 ISO 8601 字符串；不可读取的值使用 `null`，不使用空字符串伪装未知值。

## 实施顺序

### 第一个纵向切片：Discover JSON

第一步只实现：

```text
portboard --json
```

它应列出本机 TCP 监听端口、PID、进程名、命令、工作目录和最近的 Git 项目，并在部分信息不可读时继续返回其余结果。

这个切片仅需要：

- `domain/models.py`
- `application/contracts.py`
- `application/discover.py`
- `adapters/system/psutil_scanner.py`
- `adapters/project/git_resolver.py`
- `presentation/json_output.py`
- 对应的单元、集成和 JSON 契约测试

验收标准：

- 使用假扫描器可以确定性测试服务组装和 warning 行为。
- macOS 和 Linux 上至少各有一条系统扫描集成验证路径。
- 没有 Git 仓库、进程扫描中退出或部分字段无权限时不导致整次失败。
- JSON 输出符合版本 1 契约，且不包含日志或终端控制字符。

### 后续切片

1. Textual TUI 消费同一个发现用例，并提供周期刷新、过滤和排序。
2. HTTP 探测作为可选 enrichment 加入快照。
3. 打开、复制和停止进程通过应用层 action 实现。
4. Docker、局域网地址和二维码按 Roadmap 加入独立适配器。

## 暂不引入

首批版本不引入插件框架、数据库、持久缓存、事件总线、后台守护进程或 PortBoard 专用项目配置。这些能力只有在已有用例无法通过当前边界清晰实现时才重新评估。
