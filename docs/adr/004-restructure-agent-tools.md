# 004: Restructure Agent Tools for Better Maintainability

**Status**: Accepted

## Context

Our current `engine.py` file has grown to 538 lines and contains multiple responsibilities:
1. RAG engine initialization and management
2. Agent orchestration 
3. Four different tool implementations
4. Pydantic schemas for tool inputs

This monolithic structure is becoming difficult to maintain and test. Additionally, our roadmap indicates we will be adding more specialized tools for telecommunications engineering calculations, making the current structure unsustainable.

### Current Tools Analysis
- **`knowledge_base_qa`**: Core RAG functionality for document Q&A
- **`summarize_document`**: Multi-language document summarization
- **`extract_technical_specifications`**: Domain-specific data extraction
- **`calculate_link_budget`**: Telecommunications engineering calculation

### Industry Best Practices Research
Analysis of mature projects (LangChain, AutoGPT, CrewAI) shows:
- **Small projects (<10 tools)**: Tools in main file with clear function separation
- **Medium projects (10-50 tools)**: Dedicated `tools/` directory with functional grouping
- **Large projects (>50 tools)**: Complete tool ecosystem with independent packages

## Decision

We will restructure our project to use a **dedicated tools architecture**:

```
src/core/tools/
├── __init__.py              # Tool registry and exports
├── knowledge_base/
│   ├── __init__.py
│   └── qa.py               # knowledge_base_qa tool
├── document/
│   ├── __init__.py
│   └── summarizer.py       # summarize_document tool
├── technical/
│   ├── __init__.py
│   └── spec_extractor.py   # extract_technical_specifications tool
└── calculations/
    ├── __init__.py
    └── link_budget.py      # calculate_link_budget tool
```

Additionally, we will create corresponding documentation:
```
docs/tools/
├── knowledge-base-qa.md
├── document-summarizer.md
├── technical-spec-extractor.md
└── link-budget-calculator.md
```

## Implementation Strategy

1. **Phase 1**: Create the new directory structure
2. **Phase 2**: Extract tools one by one, ensuring no functionality is broken
3. **Phase 3**: Update `engine.py` to import and register tools from the new structure
4. **Phase 4**: Create comprehensive tool documentation
5. **Phase 5**: Update all relevant project documentation

## Consequences

### Positive
- **Maintainability**: Each tool is isolated and easier to understand/modify
- **Testability**: Individual tools can be unit tested independently
- **Scalability**: Easy to add new tools without bloating core files
- **Documentation**: Each tool gets dedicated documentation explaining its purpose and usage
- **Code Clarity**: `engine.py` becomes focused purely on orchestration
- **Team Collaboration**: Different developers can work on different tools without conflicts

### Negative
- **Initial Complexity**: More files to navigate initially
- **Import Management**: Need to carefully manage tool imports and registration
- **One-time Effort**: Requires careful extraction to avoid breaking existing functionality

## Benefits for Our Communication Engineering Focus

This structure particularly benefits our domain specialization:
- **Easy Addition**: New telecom calculation tools can be added without touching core RAG logic
- **Domain Grouping**: Technical tools can be logically grouped (RF calculations, antenna calculations, etc.)
- **Documentation**: Each tool can have comprehensive technical documentation with formulas and examples
