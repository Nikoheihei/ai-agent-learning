# AI Agent Learning

Week-by-week notes, demos, and experiments for learning how LLMs, workflows, and agents work.

---

## Week 1 Demo - Interactive LLM / Workflow / Agent Concept Page

**Artifact:** [`demos/llm-agent-quiz/index.html`](demos/llm-agent-quiz/index.html)

Open the file directly in a browser. It does not require dependencies or a local server.

### What's Included

| Module | Content |
|--------|---------|
| Concept cards | Six flippable cards for LLM, Workflow, Agent, Tool Use, Memory, and Prompt |
| Flow diagrams | Four text-based diagrams: single LLM call, workflow chain, agent ReAct loop, and their relationship |
| Comparison table | Eight comparison dimensions, including decision style, controllability, cost, and risk |
| Quiz | Eight multiple-choice questions with instant feedback, explanations, and a final score |

## What I Asked the Agent to Do

I gave Claude Code (`claude-sonnet-4-6`) the following instruction:

> Choose the Week 1 concept "LLM / Workflow / Agent" and generate an interactive artifact with concept cards, flow diagrams, a comparison table, and a quiz. Put it into the GitHub repository and update the README.

The agent completed:

- Inspected the existing GitHub repository structure.
- Designed and generated a complete single-file HTML page.
- Built six flippable concept cards with CSS animation.
- Wrote eight quiz questions with explanations.
- Created text-based flow diagrams and a comparison table.
- Cloned the repository, wrote the file, committed, pushed, and updated this README.

## Repository Structure

```
ai-agent-learning/
├── demos/
│   └── llm-agent-quiz/
│       └── index.html      # Week 1 interactive artifact
├── logs/
├── notes/
├── prompts/
├── resources.md
└── README.md
```

---

# 中文版

# AI Agent Learning

这是一个按周记录的 AI Agent 学习仓库，用来沉淀我对 LLM、Workflow、Agent、工具调用、记忆和提示词等概念的学习笔记、演示页面和实验过程。

---

## Week 1 Demo - LLM / Workflow / Agent 交互概念页

**产物位置：** [`demos/llm-agent-quiz/index.html`](demos/llm-agent-quiz/index.html)

直接用浏览器打开该文件即可，无需任何依赖或服务器。

### 产物包含四个模块

| 模块 | 内容 |
|------|------|
| 概念卡片 | 6 张可翻转卡片：LLM、Workflow、Agent、Tool Use、Memory、Prompt |
| 流程图 | 4 张文字流程图：LLM 单次调用、Workflow 链式执行、Agent ReAct 循环、三者关系 |
| 对比表 | 从决策方式、可控性、成本、风险等 8 个维度横向对比三者 |
| Quiz | 8 道选择题，含即时反馈与解释，最后给出得分 |

## 我让 Agent 做了什么

向 Claude Code (`claude-sonnet-4-6`) 发出一条指令：

> 选择 Week 1 概念 “LLM / Workflow / Agent”，生成一个可交互产物：包含概念卡片、流程图、对比表和 Quiz，放入 GitHub repo 并更新 README。

Agent 完成了：

- 查看 GitHub repo 现有结构。
- 设计并生成完整的单文件 HTML 页面。
- 构建 6 张翻转概念卡片的内容与 CSS 动画。
- 编写 8 道 Quiz 题目及解析。
- 创建文字版流程图和对比表。
- 克隆 repo、写入文件、提交并推送。
- 更新本 README。

## 目录结构

```
ai-agent-learning/
├── demos/
│   └── llm-agent-quiz/
│       └── index.html      # Week 1 交互产物
├── logs/
├── notes/
├── prompts/
├── resources.md
└── README.md
```
