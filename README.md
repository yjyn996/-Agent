# 扫地机器人智能客服 Agent

基于 LangChain 1.x `create_agent` 的 **ReAct 智能体**：模型不再是"查完知识库就回答"的固定流程，而是**自主决定调用哪个工具、调几次、什么时候停**，并能根据场景**动态切换提示词**。

> 这是上一个 RAG 项目的自然进阶：RAG 是"固定流水线"，Agent 是"让模型自己决策"。核心新东西只有三样——**工具、中间件、动态提示词切换**。

---

## 与上一个 RAG 项目的关系

| 维度 | RAG 项目 | 本项目（Agent） |
|---|---|---|
| 决策方式 | 固定流程：检索 → 拼 prompt → 生成 | 模型自主决策：调哪个工具、调几次、何时停 |
| 能力 | 只能查知识库回答 | 查知识库 + 查天气 + 查用户数据 + 生成报告 |
| 提示词 | 固定一个 | 按场景**动态切换** |
| 工程化 | 单个 `config_data.py` | yaml 配置 + 工厂模式 + 分层目录 |

RAG 在这里**降级成了一个工具**（`rag_summarize`），被 Agent 按需调用——这是理解 Agent 的关键视角。

---

## 项目结构

```
Agent项目/
├── app.py                      # 入口：Streamlit 前端，流式输出
├── agent/
│   ├── react_agent.py          # Agent 层：create_agent 组装模型+工具+中间件
│   └── tools/
│       ├── agent_tools.py      # 7 个工具（@tool 装饰）
│       └── middleware.py       # 3 个中间件（监控/日志/动态提示词）
├── rag/
│   ├── vector_store.py         # 向量库：Chroma + 切割 + md5 去重入库
│   └── rag_service.py          # RAG 子服务：检索 + 总结（被包成工具）
├── model/
│   └── factory.py              # 模型工厂（抽象工厂模式）
├── utils/
│   ├── config_handler.py       # 加载 yaml 配置
│   ├── prompt_loader.py        # 加载外部提示词
│   ├── path_tool.py            # 绝对路径
│   ├── logger_handler.py       # 日志
│   └── file_handler.py         # 文件读取 + md5
├── config/                     # yaml 配置（rag/chroma/prompts/agent）
├── prompts/                    # 提示词抽成 txt
└── data/                       # 知识库文件 + external/records.csv
```

分层：`app.py → agent → (tools, middleware, rag) → model → utils`，每一层只干一件事。

---

## 核心流程：ReAct 循环

Agent 的核心是 **「思考 → 行动 → 观察 → 再思考」** 的循环：

```
用户问题
  → 模型思考：信息够不够直接回答？
      ├─ 不够 → 决定调某个工具，生成 tool_call
      │        → 中间件 monitor_tool 包裹执行工具
      │        → 拿回 ToolMessage（观察结果）
      │        → 再思考：现在够不够？
      │             ├─ 还不够 → 再调工具（最多 5 次）
      │             └─ 够了 → 生成最终回答
      └─ 够 → 直接生成最终回答
```

关键点：**调什么工具、调几次，是模型自己决定的**，不是代码写死的。这就是 Agent 和普通程序的区别。

---

## 三个核心新东西

### 1. 工具（`@tool` 装饰器）

把普通函数变成模型能调用的工具：

```python
@tool(description="从向量存储中检索参考资料")
def rag_summarize(query: str) -> str:
    return rag.rag_summarize(query)
```

- `description` 是**给模型看的"工具说明书"**，模型靠它判断什么时候该调、入参是什么
- 入参、返回值都是字符串（模型能处理的类型）
- RAG 服务、模拟天气、模拟用户 ID、CSV 外部数据……统统包成工具，模型按需取用

### 2. 中间件（middleware）

横切关注点（日志、监控、提示词切换）和工具/模型逻辑**解耦**，不污染业务代码：

| 装饰器 | 函数 | 作用 | 触发时机 |
|---|---|---|---|
| `@wrap_tool_call` | `monitor_tool` | 记录工具调用日志 + 检测标记 | 每次工具执行前后 |
| `@before_model` | `log_before_model` | 记录模型调用日志 | 每次模型调用前 |
| `@dynamic_prompt` | `report_prompt_switch` | **动态切换提示词** | 每次生成提示词前 |

### 3. 动态提示词切换（本项目最精妙的地方）

一条完整链路，靠**运行时上下文 `runtime.context` 当"通信桥梁"**：

```
1. 用户说"生成我的使用报告"
   → 初始 system prompt（main_prompt.txt）里有强约束：
     报告场景必须依次调 get_user_id → get_current_month
     → fill_context_for_report → fetch_external_data

2. 模型按约束调到 fill_context_for_report 这个"空工具"
   → monitor_tool 拦截，检测到工具名
   → 执行 request.runtime.context["report"] = True   ← 种下标记

3. 下一次模型调用前，@dynamic_prompt 的 report_prompt_switch 触发
   → 读到 runtime.context["report"] == True
   → 返回 report_prompt.txt（"报告写手"提示词）

4. 从这一刻起，模型切换身份，用报告专用提示词继续工作
```

**为什么这么设计**：`fill_context_for_report` 本身不干实事（无入参无返回值），它的作用就是**触发中间件在运行时上下文里种标记**，让 `dynamic_prompt` 据此切换提示词。这是"工具调用"和"提示词切换"之间的解耦桥梁——把"该切换了"这个状态，从代码里搬到运行时上下文里。

初始值在 `execute_stream` 里传入：`context={"report": False}`。

---

## 数据类型流转

### Agent 执行主链路

```
用户输入 prompt: str
  → execute_stream(query: str)
      input_dict = {"messages": [{"role": "user", "content": query}]}
      → agent.stream(input_dict, stream_mode="values", context={"report": False})
         内部 ReAct 循环：
            AIMessage(含 tool_calls) ⇄ ToolMessage（观察结果）
           … 直到生成最终 AIMessage(content=回答)
      → 每个 chunk 是 dict → chunk["messages"][-1].content → str
      → yield str（流式输出）
```

### 工具调用链路

```
模型输出 tool_call {name, args} → ToolCallRequest
  → monitor_tool 拦截（打日志 + 检测标记）
  → handler(request) 执行真实函数
  → ToolMessage 返回给模型
```

### RAG 工具内部（rag_summarize）

```
query: str
  → retriever.invoke(query) → list[Document]
  → 拼成 context: str
  → chain.invoke({"input": query, "context": context})
      PromptTemplate → print_prompt → chat_model → StrOutputParser
  → str
```

（这条链和上一个 RAG 项目几乎一样，只是被整体塞进了一个工具里。）

---

## 关键设计决策（为什么）

| 决策 | 为什么 |
|---|---|
| 用 `create_agent` 而非手写 LangGraph | 高层 API，一行配置 model+tools+middleware 就是 ReAct agent |
| RAG 包成工具而非固定调用 | 让模型自主决定"要不要查知识库"，普通闲聊不浪费检索 |
| 用中间件而非写死在工具里 | 日志/监控/切换是横切逻辑，和业务解耦，增删不影响工具 |
| 用 `runtime.context` 传标记 | 工具和提示词之间不直接耦合，靠运行时上下文通信 |
| 抽象工厂造模型 | 聊天模型和嵌入模型统一创建入口，换模型只改一处 |
| 配置/提示词抽到 yml/txt | 改提示词、改参数不动代码 |

---

## 7 个工具一览

| 工具 | 入参 | 真实还是模拟 | 作用 |
|---|---|---|---|
| `rag_summarize` | query | 真实（接向量库） | RAG 检索+总结 |
| `get_weather` | city | 模拟 | 返回固定天气 |
| `get_user_location` | 无 | 模拟 | 随机城市 |
| `get_user_id` | 无 | 模拟 | 随机用户 ID |
| `get_current_month` | 无 | 模拟 | 随机月份 |
| `fetch_external_data` | user_id, month | 读 CSV | 查用户使用记录 |
| `fill_context_for_report` | 无 | **空工具** | 只做"标记"，触发提示词切换 |

`fill_context_for_report` 是理解整个项目的钥匙：它存在的意义不在"做什么"，而在"触发什么"。

---

## 离生产还差什么

| 缺失 | 说明 |
|---|---|
| 真实工具 | 天气/用户/月份都是模拟，要接真实 API |
| 工具返回类型 | `fetch_external_data` 实际返回 dict，description 却写 str，应统一 |
| 错误恢复 | 工具失败后 Agent 的自愈策略没验证 |
| 评测 | 报告质量、工具调用准确率没有量化指标 |
| 会话记忆 | 当前无多轮历史，纯单轮 |
