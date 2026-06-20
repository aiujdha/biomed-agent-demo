# BioMed Agent Demo

**基于 FastAPI 的生物医药 RAG、结构化抽取与 Agent 工作流演示项目。**

克隆后 10 分钟内可跑通所有接口示例，适合简历展示与面试讲解。

## 快速开始

```bash
uv sync
uv run uvicorn app.main:app --reload
```

打开 http://localhost:8000/docs 查看 Swagger 接口文档。

运行测试：

```bash
uv run pytest
```

使用 Docker（可选）：

```bash
docker compose up --build
```

API 服务运行在 http://localhost:8000。本地开发推荐直接用 `uv` 方式，迭代更快。

## 健康检查

```bash
curl http://localhost:8000/health
```

预期返回：

```json
{"status":"ok","service":"biomed-agent-demo"}
```

## 入库样例文档

将内置的三份生物医药样例文档加载到内存 FAISS 索引中：

```bash
curl -X POST http://localhost:8000/documents/ingest \
  -H "Content-Type: application/json" \
  -d '{"source":"samples"}'
```

预期返回：

```json
{"document_count":3,"chunk_count":12,"vector_store_path":".local/faiss"}
```

重复请求会重建内存索引，不会追加重复 chunk。

## RAG 问答

基于已入库的文档索引进行问答：

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"该ADC试验的主要终点是什么？","top_k":3}'
```

预期返回结构：

```json
{
  "answer": "...",
  "sources": [
    {
      "document_id": "trial_adc_001",
      "source": "trial_adc_001.md",
      "chunk_index": 2,
      "score": 0.1396,
      "text": "..."
    }
  ],
  "disclaimer": "This demo is for software engineering evaluation only and does not provide medical advice."
}
```

如果未入库文档，`/query` 返回空 `sources` 列表，并说明无法从现有资料中判断。

## 临床试验结构化抽取

从样例文档中抽取结构化临床试验字段：

```bash
curl -X POST http://localhost:8000/extract/trial \
  -H "Content-Type: application/json" \
  -d '{"document_id":"trial_adc_001"}'
```

也支持直接传入文本：

```bash
curl -X POST http://localhost:8000/extract/trial \
  -H "Content-Type: application/json" \
  -d '{"text":"A Phase II trial of ADC-101 in HER2-positive advanced solid tumors with primary endpoint objective response rate."}'
```

预期返回结构：

```json
{
  "result": {
    "trial_id": "trial_adc_001",
    "phase": "Phase II",
    "indication": "HER2-positive solid tumors",
    "intervention": "ADC-101",
    "primary_endpoint": "Objective response rate",
    "secondary_endpoints": ["Progression-free survival", "Safety"],
    "sample_size": 120,
    "inclusion_criteria": ["Adult patients", "ECOG performance status 0-1"],
    "exclusion_criteria": ["Uncontrolled infection"]
  },
  "validation_status": "valid"
}
```

不存在的文档返回 `404`。

错误响应使用统一格式：

```json
{
  "error": "not_found",
  "message": "Document not found: samples/missing_trial.md",
  "request_id": null
}
```

## Agent 报告生成

生成一段带来源引用的简短报告，工作流步骤可追溯：

```bash
curl -X POST http://localhost:8000/agent/report \
  -H "Content-Type: application/json" \
  -d '{"topic":"ADC clinical trial"}'
```

预期返回结构：

```json
{
  "report": "Summary for ADC clinical trial. ... Extracted trial design: phase Phase II; primary endpoint: Objective response rate; sample size: 120.",
  "steps": [
    {"name": "retrieve_documents", "status": "success", "summary": "..."},
    {"name": "extract_trial_fields", "status": "success", "summary": "..."},
    {"name": "summarize_findings", "status": "success", "summary": "..."},
    {"name": "return_response", "status": "success", "summary": "..."}
  ],
  "sources": ["trial_adc_001.md#0", "pubmed_adc_summary.md#1"]
}
```

先调用 `/documents/ingest` 确保索引中有数据。如果检索不到来源，或检索到的内容不是临床试验文档，工作流仍返回所有步骤，但将 `extract_trial_fields` 标记为 `skipped`。

当前版本使用显式 Python 工作流，保证可观测性和本地可靠性。后续可升级为 LangGraph，API 契约不变。

## 项目状态

MVP1 就绪 — 支持本地 RAG 问答、结构化临床试验抽取、显式 Agent 报告工作流、统一错误响应和 Docker 打包。内置三份生物医药样例文档。

## 技术栈

| 层 | 技术 |
|----|------|
| API | FastAPI, Uvicorn |
| Schema | Pydantic v2 |
| 向量库 | FAISS |
| Embedding | 本地 HashEmbedding（无需 API key，可替换为 OpenAI-compatible） |
| LLM | FakeLLM（默认，无需 key）/ OpenAI-compatible |
| 测试 | pytest, FastAPI TestClient |
| 包管理 | uv |
| 部署 | Docker |

## 项目结构

```
biomed-agent-demo/
├── app/
│   ├── api/routes/     # HTTP 路由
│   ├── core/           # 配置、容器、错误处理
│   ├── ingestion/      # 文档加载与切分
│   ├── rag/            # Embedding、向量库、检索
│   ├── extraction/     # Pydantic schema 与结构化抽取
│   ├── llm/            # LLM 客户端封装
│   ├── agent/          # 工具函数与工作流编排
│   ├── services/       # 业务逻辑编排
│   └── schemas/        # 请求响应模型
├── samples/            # 3 份内置样例文档
├── tests/              # 25 个测试
└── README.md
```

## 限制说明

- 本 Demo 仅供软件工程评估使用，**不提供医疗建议**。
- 内置样例数据为虚构内容，不包含真实患者隐私信息。
- 无用户鉴权，不适用于生产环境。
- 向量库为本地内存 FAISS，不支持多租户和持久化。