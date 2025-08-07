# Technical Specification Extractor Tool

## Overview

The technical specification extractor tool performs structured data extraction from documents, focusing on specific technical parameters. It uses JSON-mode LLM output for reliable, parseable results.

## Purpose

- **Primary use case**: Extracting specific technical data points from documents
- **Output format**: Structured JSON with parameter names and values
- **Use scenario**: Gathering data before performing engineering calculations

## How It Works

1. **Parameter Definition**: User specifies list of technical parameters to extract
2. **Document Selection**: User provides exact file name from knowledge base
3. **Content Processing**: Document text processed (up to 16,000 characters)
4. **Structured Extraction**: GPT-4o-mini extracts data in JSON format

## Tool Signature

```python
def extract_technical_specifications(
    file_name: str, 
    parameters_to_extract: List[str]
) -> Dict[str, Any]
```

### Parameters

- **file_name** (str): Exact name of document in knowledge base
- **parameters_to_extract** (List[str]): List of specific parameters to find

### Returns

- **Dict[str, Any]**: JSON object with parameter names as keys and extracted values

## Usage Examples

### Communication System Parameters
```python
Input:
  file_name = "antenna_specs.pdf"
  parameters_to_extract = [
    "Transmitter Power (dBm)",
    "Antenna Gain (dBi)", 
    "Operating Frequency (MHz)",
    "Cable Loss (dB)"
  ]

Output:
{
  "Transmitter Power (dBm)": 30,
  "Antenna Gain (dBi)": 15.2,
  "Operating Frequency (MHz)": 2400,
  "Cable Loss (dB)": 1.5
}
```

### Missing Parameters
```python
Input:
  file_name = "incomplete_spec.pdf"
  parameters_to_extract = ["Power", "Gain", "Unknown Parameter"]

Output:
{
  "Power": "25 dBm",
  "Gain": "12 dBi",
  "Unknown Parameter": null
}
```

## Parameter Naming Best Practices

### Recommended Formats
- **Include Units**: "Power (dBm)", "Frequency (MHz)"
- **Be Specific**: "Transmitter Power" vs "Power"
- **Standard Terms**: Use industry-standard terminology

### Examples by Domain

#### RF/Microwave
- "EIRP (dBm)"
- "Return Loss (dB)"
- "VSWR"
- "Bandwidth (MHz)"

#### Network Equipment
- "Data Rate (Mbps)"
- "Latency (ms)"
- "Port Count"
- "Power Consumption (W)"

#### Antenna Systems
- "Beamwidth (degrees)"
- "Front-to-Back Ratio (dB)"
- "Polarization"
- "Impedance (Ohms)"

## JSON Output Format

### Successful Extraction
```json
{
  "parameter_name_1": "extracted_value_1",
  "parameter_name_2": 42.5,
  "parameter_name_3": "text_value"
}
```

### Missing Parameters
```json
{
  "found_parameter": "value",
  "missing_parameter": null
}
```

### Error Response
```json
{
  "error": "Failed to extract or parse data for filename.pdf. Reason: [error details]"
}
```

## Implementation Details

- **Location**: `src/core/tools/technical/spec_extractor.py`
- **Factory Function**: `create_tech_spec_extractor_tool(engine)`
- **Schema**: `TechSpecInput` extending `DocumentInput`
- **JSON Mode**: Uses LLM JSON response format for structured output

## Error Handling

### File Not Found
```json
{
  "error": "The file 'filename.pdf' was not found. Available files: file1.pdf, file2.pdf"
}
```

### Extraction Failure
```json
{
  "error": "Failed to extract or parse data for filename.pdf. Reason: JSON parsing failed"
}
```

### Processing Limits
- Document content limited to 16,000 characters
- Large documents may have truncated content

## Integration with Other Tools

### Link Budget Calculation Workflow
1. **Extract Parameters**: Use this tool to gather technical specifications
2. **Verify Data**: Check for null values or missing parameters
3. **Calculate**: Pass extracted values to `calculate_link_budget` tool

### Example Workflow
```python
# Step 1: Extract parameters
specs = extract_technical_specifications(
    "site_A.pdf", 
    ["Transmitter Power (dBm)", "Antenna Gain (dBi)"]
)

# Step 2: Use in calculation
link_budget = calculate_link_budget(
    transmitter_power_dBm=specs["Transmitter Power (dBm)"],
    transmitter_antenna_gain_dBi=specs["Antenna Gain (dBi)"],
    # ... other parameters
)
```

## Best Practices

1. **Parameter Consistency**: Use consistent parameter naming across documents
2. **Unit Specification**: Always include units in parameter names
3. **Error Checking**: Check for null values before using extracted data
4. **Iterative Extraction**: Extract from multiple documents if needed
5. **Validation**: Verify extracted values make technical sense

## Common Use Cases

- **Link Budget Preparation**: Gathering parameters for RF calculations
- **Compliance Checking**: Extracting regulatory specifications
- **Performance Analysis**: Collecting measurement data
- **System Integration**: Getting interface specifications

## Related Tools

- **calculate_link_budget**: Uses extracted technical specifications
- **knowledge_base_qa**: For general technical questions
- **summarize_document**: For comprehensive document overview
