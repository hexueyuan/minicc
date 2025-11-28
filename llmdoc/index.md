# MiniCC 文档索引

极简教学版 AI 编程助手，约 1800 行代码实现核心功能（已扩展以对标 Claude Code）。

## 快速导航

| 文档类型 | 路径 | 说明 |
|---------|------|------|
| 概述 | [/llmdoc/overview/](./overview/) | 项目背景、设计目标、技术选型 |
| 指南 | [/llmdoc/guides/](./guides/) | 安装使用、开发调试指南 |
| 架构 | [/llmdoc/architecture/](./architecture/) | 系统架构、模块设计、TUI 布局 |
| 参考 | [/llmdoc/reference/](./reference/) | API 规范、数据模型 |

## 最近更新

### 工具系统重构完成 (v1.1 - 2025-11-28)
- **新增依赖**: ripgrepy (高性能搜索), wcmatch (高级 glob), nbformat (Jupyter 支持)
- **tools.py 扩展**: 760 行 → 1162 行，新增 10+ 工具
  - edit_file: 替代 update_file，精确替换 + 空白容错
  - glob_files: 替代 search_files，支持高级 glob 模式
  - grep_search: 替代 grep，使用 ripgrepy 高性能
  - bash_output / kill_shell: 后台任务管理
  - task / todo_write: 子任务和任务追踪
  - notebook_edit: Jupyter notebook 编辑
- **schemas.py 扩展**: 128 行 → 176 行
  - 新增 PromptCache (Anthropic 缓存配置)
  - 新增 TodoItem, BackgroundShell 模型
  - 扩展 AgentTask: 添加 description, subagent_type
  - 扩展 MiniCCDeps: 添加 todos, background_shells, on_todo_update
- **UI 新增**: TodoDisplay 组件 (任务列表显示)
- 详见：
  - [/llmdoc/overview/project.md](./overview/project.md) - 核心能力更新
  - [/llmdoc/architecture/modules.md](./architecture/modules.md) - 模块详细说明

### TUI 首页重构完成 (v1.0 - 2025-11-28)
- 移除侧边栏（SidePanel）和可折叠面板，采用单行简洁设计
- 新增 BottomBar 组件（模型/目录/分支/Token 显示）
- ToolCallLine/SubAgentLine: 单行简洁格式 `🔧 name (param) ✅/❌`
- 精简 ui/widgets.py: 434 行 → 230 行 (已更新为 272 行)
- 精简 schemas.py: 164 行 → 128 行 (已扩展为 176 行)

## 核心模块

```
minicc/
├── schemas.py   # 数据模型定义
├── config.py    # 配置管理
├── tools.py     # 工具函数实现
├── agent.py     # Agent 定义
├── app.py       # TUI 主应用
└── ui/          # UI 组件
```

## 技术栈

- **pydantic-ai**: Agent 框架，提供工具注册、流式输出
- **Textual**: TUI 框架，提供终端界面
- **Pydantic**: 数据验证和序列化
