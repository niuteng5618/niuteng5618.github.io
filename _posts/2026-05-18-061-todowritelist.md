---
layout: post
title: "TodoWriteList"
date: 2026-05-18
tags: ["人工智能技术", "智能体应用开发", "codex_cc-使用"]
toc: true
comments: false
author: niuteng5618
---
> **背景：**
>
> 给 Agent 一个复杂任务："把所有 Python 文件改成 snake_case 命名，然后跑测试，修好失败。"
>
> Agent 开始干活，改了 3 个文件，跑了个测试，发现 2 个失败，开始修。修着修着，它忘了最初是"改成 snake_case"，测试失败把注意力全吸走了。
>
> 对话越长越严重：工具结果不断填满上下文，系统提示的影响力被稀释。一个 10 步重构，做完 1-3 步就开始即兴发挥，因为 4-10 步已经被挤出注意力了。
>

**CC中提供todo_write工具和 reminder 机制**

## todo_write工作原理
todo_write 工具，接收一个带状态的列表，**保存在当前进程内存中，同时在终端显示进度**：

```python
CURRENT_TODOS: list[dict] = []

def run_todo_write(todos: list) -> str:
    global CURRENT_TODOS
    CURRENT_TODOS = todos

    lines = ["\n## Current Tasks"]
    for t in CURRENT_TODOS:
        icon = {"pending": " ", "in_progress": "▸", "completed": "✓"}[t["status"]]
        lines.append(f"  [{icon}] {t['content']}")
    print("\n".join(lines))
    return f"Updated {len(CURRENT_TODOS)} tasks"
```

工具定义和其他 5 个工具一起加入 dispatch map：

```python
TOOLS = [
    {"name": "bash",       ...},
    {"name": "read_file",  ...},
    {"name": "write_file", ...},
    {"name": "edit_file",  ...},
    {"name": "glob",       ...},
    # s05: 新增一条
    {"name": "todo_write", "description": "Create and manage a task list ...",
     "input_schema": {
         "type": "object",
         "properties": {
             "todos": {
                 "type": "array",
                 "items": {
                     "type": "object",
                     "properties": {
                         "content": {"type": "string"},
                         "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                     },
                 },
             },
         },
     },
    },
]

TOOL_HANDLERS["todo_write"] = run_todo_write
```

## reminder机制
> 提醒模型别忘了todolist，可以通过设置k轮对话内，没进行todowrite工具调用 进行检测。简单实现。
>

模型连续 3 轮没调 todo_write 时，自动注入一条提醒**（教学版机制，CC 源码中没有这个固定轮数逻辑）**：

```python
if rounds_since_todo >= 3 and messages:
      messages.append({
        "role": "user",
        "content": "<reminder>Update your todos.</reminder>",
    })
    rounds_since_todo = 0
```

  Agent 收到任务后的典型流程：先调 todo_write 列出所有步骤（全 pending）→ 做一个步骤，改成 in_progress → 做完改成 completed → 看下一个 pending → 继续。

连续 3 轮没有调用 todo_write 时，循环会在下一次 LLM 调用前追加一条 reminder。
