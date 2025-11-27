# MiniCC 项目概述

## 项目目标

实现一个极简版、具有教学意义的 Claude Code，帮助开发者理解 AI Agent 的核心实现原理。

## 设计原则

1. **代码精简**: 约 1400 行代码实现完整功能
2. **注释充分**: 每个函数和类都有详细文档
3. **架构清晰**: 模块职责分明，易于理解
4. **易于扩展**: 基于 pydantic-ai 的工具注册机制

## 核心能力

### 工具 (Tools)
- 文件操作: read_file, write_file, update_file
- 搜索: search_files, grep
- 命令行: bash
- 子任务: spawn_agent, get_agent_result

### 提示词 (Prompt)
- 系统提示词: ~/.minicc/AGENTS.md
- 工具描述: 从函数 docstring 自动提取

### 子代理 (SubAgent)
- 显式 spawn_agent() 工具创建子任务
- 异步执行，不阻塞主 Agent

### 用户界面 (UI)
- Textual TUI 终端界面，支持流式输出和快捷键操作
- 清晰的聊天布局：Header → 消息区 → 输入框 → 状态栏 → Footer
- 可折叠的工具调用面板（默认折叠，避免视觉噪音）
- 可折叠的 SubAgent 任务面板（显示任务状态和结果）
- 底边栏显示关键上下文（模型/目录/分支/Token统计）
- 支持 Markdown 消息渲染和颜色代码语法高亮

## 技术决策

| 决策项 | 选择 | 理由 |
|--------|------|------|
| LLM 后端 | Anthropic + OpenAI | 覆盖主流提供商 |
| 持久化 | 仅配置 | 简化实现 |
| SubAgent | 显式 spawn | LLM 控制并发 |
| Diff 显示 | 简单文本 | +/- 颜色标记 |
