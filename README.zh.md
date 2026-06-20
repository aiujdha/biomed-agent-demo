# BioMed Knowledge API

**基于 FastAPI 的生物医药文档检索、RAG 问答、结构化信息抽取与 Agent 工作流服务。**

本地优先架构，默认配置无需外部依赖或 API key — 克隆、安装、即可使用。

---

## 功能特性

- **文档入库** — 将生物医药样例文档加载到内存 FAISS 向量索引中
- **检索增强问答** — 检索相关文档片段，基于原文生成带来源引用的回答
- **结构化试验抽取** — 从临床试验文档中抽取结构化字段（期别、适应症、终点、样本量、入排标准），经 Pydantic schema 校验
- **Agent 报告生成** — 多步骤工作流串联检索、抽取、汇总，每一步的状态和摘要均可追溯
- **零配置运行** — 内置基于哈希的 Embedding 和 FakeLLM，无需任何 API key 即可跑通全流程；可随时切换为 OpenAI 兼容接口

---

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

---

## API 文档

### 健康检查

```bash
curl http://localhost:8000/health
```

```json
{"status":"ok","service":"biomed-agent-demo"}
```

### 入库文档

将内置的三份生物医药样例文档加载到内存 FAISS 索引中。重复请求会重建索引，不会追加重复 chunk。

```bash
curl -X POST http://localhost:8000/documents/ingest \
  -H "Content-Type: application/json" \
  -d '{"source":"samples"}'
```

```json
{"document_count":3,"chunk_count":12,"vector_store_path":".local/faiss"}
```

### RAG 问答

基于已入库的文档索引进行问答。返回结果包含检索到的来源片段及其相似度分数。

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"该ADC试验的主要终点是什么？","top_k":3}'
```

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
  "disclaimer": "This project is intended for development and research workflow prototyping. It does not provide medical advice."
}
```

如果未入库文档，接口返回空 `sources` 列表，并说明无法从现有资料中判断。

### 临床试验结构化抽取

从文档中抽取结构化临床试验字段：

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

不存在的文档返回 `404`。错误响应使用统一格式：

```json
{
  "error": "not_found",
  "message": "Document not found: samples/missing_trial.md",
  "request_id": null
}
```

### Agent 报告生成

生成一段带来源引用的简短报告，工作流步骤可追溯：

```bash
curl -X POST http://localhost:8000/agent/report \
  -H "Content-Type: application/json" \
  -d '{"topic":"ADC clinical trial"}'
```

```json
{
  "report": "Summary for ADC clinical trial. ... Extracted trial design: phase Phase II; primary endpoint: Objective response rate; sample size: 120.",
  "steps": [
    {"name": "retrieve_documents", "status": "success", "summary": "Retrieved 3 source chunks."},
    {"name": "extract_trial_fields", "status": "success", "summary": "Extracted structured trial fields from trial_adc_001: Phase II, primary endpoint Objective response rate."},
    {"name": "summarize_findings", "status": "success", "summary": "Generated a source-grounded report summary."},
    {"name": "return_response", "status": "success", "summary": "Returned report, steps, and source references."}
  ],
  "sources": ["trial_adc_001.md#0", "pubmed_adc_summary.md#1"]
}
```

如果检索不到来源，或检索到的内容不是临床试验文档，`extract_trial_fields` 步骤标记为 `skipped`。

---

## 项目结构

```
app/
├── api/routes/         # HTTP 路由（health, documents, query, extract, agent）
├── core/               # 配置、依赖容器、错误处理
├── ingestion/          # 文档加载与文本切分
├── rag/               # Embedding、FAISS 向量库、检索、提示词
├── extraction/         # Pydantic schema 与结构化字段抽取
├── llm/               # LLM 客户端（默认 FakeLLM，可切换为 OpenAI 兼容）
├── agent/             # 工具函数与报告工作流编排
├── services/          # 业务逻辑编排
└── schemas/           # 请求/响应模型
```

服务层位于 HTTP 路由与领域模块之间。每个模块职责单一，可独立替换 — 例如 FAISS 向量库可切换为远程向量数据库，无需改动路由层。

---

## 技术栈

| 层 | 技术 |
|----|------|
| API | FastAPI, Uvicorn |
| 校验 | Pydantic v2 |
| 向量库 | FAISS（内存） |
| Embedding | HashEmbedding（默认，无需 key）/ OpenAI 兼容 |
| LLM | FakeLLM（默认）/ OpenAI 兼容 |
| 测试 | pytest, FastAPI TestClient |
| 包管理 | uv |
| 容器 | Docker |

---

## 样例数据

仓库内置三份合成的生物医药文档用于演示：

| 文件 | 类型 | 内容 |
|------|------|------|
| `samples/sop_cell_culture.md` | 标准操作规程 | 细胞培养解冻、传代、冻存 |
| `samples/pubmed_adc_summary.md` | 文献综述 | ADC 肿瘤学综述与临床试验结果 |
| `samples/trial_adc_001.md` | 临床试验摘要 | II 期 ADC-101 试验设计与终点 |

以上数据均为虚构内容，不包含真实患者信息或专有数据。

---

## 限制说明

- **本地向量库** — 内存 FAISS 索引在重启后不持久化，不支持多租户或分布式查询。生产环境应使用远程向量数据库。
- **无鉴权** — API 不包含内置认证层。非本地环境部署时应置于反向代理或 VPN 之后。
- **研究原型** — 系统设计用于开发工作流原型验证，未经验证不可用于临床决策支持，不得用于医疗诊断或治疗决策。
- **合成数据** — 所有内置文档均为虚构。实际评估应替换为真实（脱敏）数据。

---

## 项目状态

v0.1.0 — 核心检索、抽取、Agent 工作流已在内置样例文档上通过验证。