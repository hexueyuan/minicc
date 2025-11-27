# MiniCC 文档索引

极简教学版 AI 编程助手，约 1400 行代码实现核心功能。

## 快速导航

| 文档类型 | 路径 | 说明 |
|---------|------|------|
| 概述 | [/llmdoc/overview/](./overview/) | 项目背景、设计目标、技术选型 |
| 指南 | [/llmdoc/guides/](./guides/) | 安装使用、开发调试指南 |
| 架构 | [/llmdoc/architecture/](./architecture/) | 系统架构、模块设计、TUI 布局 |
| 参考 | [/llmdoc/reference/](./reference/) | API 规范、数据模型 |

## 最近更新

### TUI 首页重构完成 (v1.0 - 2025-11-28)
- 移除侧边栏（SidePanel）和可折叠面板，采用单行简洁设计
- 新增 BottomBar 组件（模型/目录/分支/Token 显示）
- ToolCallLine/SubAgentLine: 单行简洁格式 `🔧 name (param) ✅/❌`
- 精简 ui/widgets.py: 434 行 → 230 行
- 精简 schemas.py: 164 行 → 128 行
- 修复 token 使用量不更新问题（usage 是方法）
- 详见：
  - [/llmdoc/architecture/tui-layout.md](./architecture/tui-layout.md) - 布局详细说明
  - [/llmdoc/architecture/ui-refactor-2025.md](./architecture/ui-refactor-2025.md) - 重构记录
  - [/llmdoc/reference/ui-components.md](./reference/ui-components.md) - 组件接口参考

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
