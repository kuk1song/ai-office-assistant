# 003: Fix Summarize Language Parameter Issue

**Status**: Accepted

## Context

The summarize functionality was not respecting the user-specified language. When users input "中文" or "italiano", the summary would always be generated in English. This was occurring despite having language-specific prompts in the backend.

### Root Cause Analysis

1. **Tool Schema Mismatch**: The `summarize_document` tool uses `DocumentInput` schema which only defines `file_name`, but the function signature includes a `language` parameter.

2. **Direct Tool Invocation**: The UI was calling `chat_engine.summarize_document.invoke()` directly instead of going through the agent system, which may cause parameter passing issues.

3. **Parameter Serialization**: LangChain tools may not correctly handle additional parameters when the schema doesn't match the function signature.

## Decision

We will fix this issue by:

1. **Creating a proper schema** for the summarize tool that includes both `file_name` and `language` parameters.
2. **Ensuring robust parameter passing** from UI to the tool.
3. **Adding debugging output** to verify language parameter transmission.

## Implementation

1. Create a new `SummarizeInput` Pydantic model that includes both required parameters.
2. Update the `summarize_document` tool to use this new schema.
3. Add logging to verify language parameter is correctly received.

## Consequences

### Positive
- **Language Specificity**: Users will get summaries in their requested language.
- **Better User Experience**: Multi-language support works as expected.
- **Robust Parameter Handling**: Proper schema ensures reliable parameter transmission.

### Negative
- **Minor Code Change**: Requires updating the tool definition and schema.
