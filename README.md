# AI Agent Learning

Week-by-week notes, demos, and experiments as I learn how LLMs, workflows, and agents work.

---

## Week 1 Demo — LLM / Workflow / Agent 交互概念页

**产物位置：** [`demos/llm-agent-quiz/index.html`](demos/llm-agent-quiz/index.html)

直接用浏览器打开该文件即可，无需任何依赖或服务器。

### 产物包含四个模块

| 模块 | 内容 |
|------|------|
| 📇 概念卡片 | 6 张可翻转卡片：LLM、Workflow、Agent、Tool Use、Memory、Prompt |
| 🔀 流程图 | 4 张文字流程图：LLM 单次调用 → Workflow 链式 → Agent ReAct 循环 → 三者关系 |
| 📊 对比表 | 从决策方式、可控性、成本、风险等 8 个维度横向对比三者 |
| 🧠 Quiz | 8 道选择题，含即时反馈与解释，最后给出得分 |

---

## 我让 Agent 做了什么

向 Claude Code (claude-sonnet-4-6) 发出一条指令：

> 选择 Week 1 概念"LLM / Workflow / Agent"，生成一个可交互产物：包含概念卡片、流程图、对比表和 Quiz，放入 GitHub repo 并更新 README。

Agent 完成了：
- 查看 GitHub repo 现有结构
- 设计并生成完整的单文件 HTML 页面（~500 行）
- 构建 6 张翻转概念卡片的内容与 CSS 动画
- 编写 8 道 Quiz 题目及解析
- 创建文字版流程图和对比表
- 克隆 repo、写入文件、提交并推送
- 更新本 README

---

## 目录结构

```
ai-agent-learning/
├── demos/
│   └── llm-agent-quiz/
│       └── index.html      ← Week 1 交互产物
├── logs/
├── notes/
├── prompts/
├── resources.md
└── README.md
```
