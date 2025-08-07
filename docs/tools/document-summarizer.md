# Document Summarizer Tool

## Overview

The document summarizer tool generates comprehensive summaries of specific documents in multiple languages. It provides high-quality, contextually aware summaries with strong language compliance.

## Purpose

- **Primary use case**: Creating detailed summaries of individual documents
- **Language support**: Multi-language output (English, Chinese, Italian, etc.)
- **Content focus**: Main topics, technical details, conclusions, and context

## How It Works

1. **Document Selection**: User specifies exact file name from knowledge base
2. **Language Selection**: User specifies desired output language
3. **Content Processing**: Full document text is processed (up to 16,000 characters)
4. **Summary Generation**: GPT-4o-mini creates comprehensive summary in specified language

## Tool Signature

```python
def summarize_document(file_name: str, language: str = "English") -> str
```

### Parameters

- **file_name** (str): Exact name of document in knowledge base
- **language** (str): Target language for summary (default: "English")

### Returns

- **str**: Comprehensive document summary in specified language

## Supported Languages

### Fully Tested
- **English**: Default language
- **中文** (Chinese): Complete Chinese character output
- **italiano** (Italian): Full Italian language output

### Language Input Variations
- English: "English", "english"
- Chinese: "中文", "Chinese", "chinese"  
- Italian: "italiano", "Italian", "italian"

## Language Compliance Features

### Strict Language Enforcement
- **Single Language Output**: Never mixes languages in response
- **No Translations**: Avoids bilingual or translation content
- **Complete Compliance**: All text including headers in target language

### Quality Assurance
- **Debug Logging**: Tracks language parameter transmission
- **Enhanced Prompts**: Multiple layers of language instruction
- **Compliance Verification**: LLM self-checks language compliance

## Usage Examples

### English Summary
```
Input: file_name="report.pdf", language="English"
Output: "This technical report presents findings on antenna performance..."
```

### Chinese Summary
```
Input: file_name="specification.pdf", language="中文"
Output: "这份技术规范文档详细描述了天线的性能参数..."
```

### Italian Summary
```
Input: file_name="manual.pdf", language="italiano"
Output: "Questo manuale tecnico descrive le specifiche dell'antenna..."
```

## Summary Content Structure

1. **Main Topics**: Key themes and subject areas
2. **Technical Details**: Important data, numbers, specifications
3. **Conclusions**: Findings and recommendations
4. **Context**: Document purpose and overall significance

## Implementation Details

- **Location**: `src/core/tools/document/summarizer.py`
- **Factory Function**: `create_summarize_document_tool(engine)`
- **Schema**: `SummarizeInput` with file_name and language fields
- **Content Limit**: 16,000 characters for processing efficiency

## Error Handling

### File Not Found
```
"Error: The file 'filename.pdf' was not found in the knowledge base. 
Please use one of the available files: [list of available files]"
```

### Debug Information
- Language parameter verification logged to console
- Format: `[DEBUG] Summarize tool called with: file_name='x.pdf', language='中文'`

## Best Practices

1. **Exact File Names**: Use precise file names as they appear in knowledge base
2. **Language Specification**: Use clear language identifiers
3. **Content Verification**: Check debug logs to ensure correct parameter passing
4. **Language Consistency**: Expect entire response in specified language

## UI Integration

- **Direct Access**: Available via `engine.summarize_document` for UI calls
- **Agent Access**: Available as tool #1 in agent tool list
- **Parameter Binding**: Factory pattern ensures proper engine binding

## Related Tools

- **knowledge_base_qa**: For specific questions about document content
- **extract_technical_specifications**: For extracting structured data
