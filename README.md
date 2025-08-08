# TelcoLink Agent — Autonomous Link Budget AI (Open-Source Test Build)

_A telecom-focused, privacy-first AI that reads your docs, automates link budget analysis, and reasons with tools to get work done._

> ⚠️ Test Build: For local/intranet evaluation only. Do not deploy as-is to public production.

## What it is

- 🤖 **Autonomous Vertical AI Agent** — Built for telecom workflows; orchestrates LLM reasoning + tools to automate link budget and domain tasks end-to-end
- 📚 **RAG Knowledge Base** — Private, document-grounded answers (FAISS vector search)
- 🧰 **Multi-Tool AI** — Document Summarizer, Technical Spec Extractor, Link Budget Calculator
- 🧩 **Modular AI Stack** — Models, Knowledge layer, Orchestration, Tool ecosystem

## 🚀 Quick Start (Local)
1) Install
```bash
pip install -r requirements.txt
```
2) Configure
```bash
export OPENAI_API_KEY=YOUR_KEY
```
3) Run
```bash
streamlit run app.py
```
Open the app → upload documents → create the knowledge base → chat.

## 🧠 Architecture (High-Level)
- `src/core/models/` — LLM + Embeddings providers & manager
- `src/core/knowledge/` — Document processing, vector store, persistence
- `src/core/orchestration/` — Agent orchestration (reasoning + tools)
- `src/core/tools/` — Knowledge Q&A, Document Summarizer, Extractors, Calculators
- `var/persistent_storage/` — Vector index + metadata (mount this in containers)
- `docs/` — Technical architecture, ADRs, production readiness, diagrams

## ✨ Why it’s different
- **Telco-first**: Purpose-built for telecom link budget and spec-driven workflows
- **Tool-native reasoning**: The agent plans, selects tools, and executes with context
- **Private by design**: Local persistence; easy to deploy inside the company network

## 🏁 Path to Production
- Containerized image + internal reverse proxy (TLS)
- Company SSO (OIDC/SAML) via OAuth2-Proxy; light RBAC + auditing
- Structured logging, tests (pytest), CI (lint + test)
- See `docs/production-readiness.md`

## ⚠️ Status & Limitations
- Active test build; APIs and behavior may change
- Not tuned for public internet or external multi-tenant scenarios

## 🔒 Use & Risk Notice
- Provided as-is for learning and internal evaluation only
- Review security, privacy, and compliance before real-world use
