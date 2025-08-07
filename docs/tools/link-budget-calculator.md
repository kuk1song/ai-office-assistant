# Link Budget Calculator Tool

## Overview

The link budget calculator performs point-to-point communication link analysis using standard RF engineering formulas. It calculates key link parameters including EIRP, path loss, and received power.

## Purpose

- **Primary use case**: RF link budget calculations for communication systems
- **Engineering domain**: Telecommunications, wireless communications, satellite links
- **Calculation type**: Pure mathematical tool (no document dependency)

## How It Works

1. **Parameter Input**: All required RF parameters provided by user or extracted from documents
2. **EIRP Calculation**: Effective Isotropic Radiated Power computation
3. **Path Loss Calculation**: Free Space Path Loss using Friis equation
4. **Received Power**: Final received power at destination

## Tool Signature

```python
def calculate_link_budget(
    distance_km: float,
    transmitter_power_dBm: float,
    transmitter_cable_loss_dB: float,
    transmitter_antenna_gain_dBi: float,
    receiver_antenna_gain_dBi: float,
    receiver_cable_loss_dB: float,
    frequency_MHz: float
) -> Dict[str, Any]
```

## Parameters

### Required Inputs

| Parameter | Type | Unit | Description |
|-----------|------|------|-------------|
| **distance_km** | float | km | Distance between transmitter and receiver |
| **transmitter_power_dBm** | float | dBm | Output power from transmitter |
| **transmitter_cable_loss_dB** | float | dB | Cable/connector losses at transmitter |
| **transmitter_antenna_gain_dBi** | float | dBi | Transmitter antenna gain |
| **receiver_antenna_gain_dBi** | float | dBi | Receiver antenna gain |
| **receiver_cable_loss_dB** | float | dB | Cable/connector losses at receiver |
| **frequency_MHz** | float | MHz | Operating frequency |

### Output Results

```json
{
  "Effective Isotropic Radiated Power (EIRP) dBm": 42.5,
  "Free Space Path Loss (FSPL) dB": 125.2,
  "Calculated Received Power dBm": -35.7
}
```

## Engineering Formulas

### EIRP (Effective Isotropic Radiated Power)
```
EIRP = Transmitter_Power - Transmitter_Cable_Loss + Transmitter_Antenna_Gain
```

### Free Space Path Loss (FSPL)
```
FSPL (dB) = 20 × log₁₀(distance_km) + 20 × log₁₀(frequency_MHz) + 27.55
```

The constant 27.55 comes from:
```
20 × log₁₀(4π/c) where c = 3×10⁸ m/s
```

### Received Power
```
Received_Power = EIRP - FSPL + Receiver_Antenna_Gain - Receiver_Cable_Loss
```

## Usage Examples

### Basic Link Budget
```python
Input:
  distance_km = 10.0
  transmitter_power_dBm = 30.0
  transmitter_cable_loss_dB = 2.0
  transmitter_antenna_gain_dBi = 15.0
  receiver_antenna_gain_dBi = 12.0
  receiver_cable_loss_dB = 1.5
  frequency_MHz = 2400.0

Output:
{
  "Effective Isotropic Radiated Power (EIRP) dBm": 43.0,
  "Free Space Path Loss (FSPL) dB": 100.03,
  "Calculated Received Power dBm": -46.53
}
```

### Satellite Link (High Frequency, Long Distance)
```python
Input:
  distance_km = 36000.0  # Geostationary orbit
  transmitter_power_dBm = 50.0
  transmitter_cable_loss_dB = 1.0
  transmitter_antenna_gain_dBi = 45.0
  receiver_antenna_gain_dBi = 35.0
  receiver_cable_loss_dB = 2.0
  frequency_MHz = 12000.0  # Ku-band

Output:
{
  "Effective Isotropic Radiated Power (EIRP) dBm": 94.0,
  "Free Space Path Loss (FSPL) dB": 206.04,
  "Calculated Received Power dBm": -79.04
}
```

## Parameter Guidelines

### Typical Value Ranges

#### Transmitter Power
- **WiFi/Bluetooth**: 0-20 dBm
- **Cellular Base Station**: 40-50 dBm
- **Satellite**: 30-60 dBm

#### Antenna Gain
- **Omnidirectional**: 0-3 dBi
- **Directional**: 6-20 dBi
- **High-gain dish**: 20-60 dBi

#### Cable Loss
- **Short runs (<10m)**: 0.5-2 dB
- **Long runs**: 2-10 dB
- **Waveguide**: 0.1-1 dB

#### Frequency Bands
- **2.4 GHz ISM**: 2400-2500 MHz
- **5 GHz WiFi**: 5150-5850 MHz
- **Cellular**: 700-2600 MHz
- **Satellite**: 1-40 GHz

## Link Budget Interpretation

### Link Margin
The received power should be compared with receiver sensitivity:
```
Link Margin = Received Power - Receiver Sensitivity
```

### Performance Guidelines
- **Excellent**: Link margin > 20 dB
- **Good**: Link margin 10-20 dB
- **Marginal**: Link margin 3-10 dB
- **Poor**: Link margin < 3 dB

### Factors Not Included
This basic calculation doesn't include:
- Atmospheric losses
- Rain fade
- Multipath effects
- Interference
- Implementation losses

## Implementation Details

- **Location**: `src/core/tools/calculations/link_budget.py`
- **Dependency**: Independent tool (no engine binding required)
- **Math Library**: Uses Python `math.log10()` function
- **Precision**: Results rounded to 2 decimal places

## Error Handling

### Input Validation
- All parameters must be positive numbers
- Frequency must be > 0 MHz
- Distance must be > 0 km

### Mathematical Constraints
- Zero distance or frequency will cause math domain errors
- Negative gains are technically valid (lossy antennas)

## Integration Workflow

### With Document Extraction
```python
# Step 1: Extract parameters from documents
site_A_specs = extract_technical_specifications(
    "site_A.pdf",
    ["Transmitter Power (dBm)", "Antenna Gain (dBi)", "Cable Loss (dB)"]
)

site_B_specs = extract_technical_specifications(
    "site_B.pdf", 
    ["Antenna Gain (dBi)", "Cable Loss (dB)"]
)

# Step 2: Get operational parameters
frequency = 2400  # MHz
distance = 15.5   # km

# Step 3: Calculate link budget
result = calculate_link_budget(
    distance_km=distance,
    transmitter_power_dBm=site_A_specs["Transmitter Power (dBm)"],
    transmitter_cable_loss_dB=site_A_specs["Cable Loss (dB)"],
    transmitter_antenna_gain_dBi=site_A_specs["Antenna Gain (dBi)"],
    receiver_antenna_gain_dBi=site_B_specs["Antenna Gain (dBi)"],
    receiver_cable_loss_dB=site_B_specs["Cable Loss (dB)"],
    frequency_MHz=frequency
)
```

## Best Practices

1. **Unit Consistency**: Ensure all inputs use specified units
2. **Parameter Validation**: Verify extracted parameters before calculation
3. **Engineering Review**: Sanity-check results against expected values
4. **Documentation**: Record assumptions and calculation basis
5. **Sensitivity Analysis**: Test with parameter variations

## Related Tools

- **extract_technical_specifications**: Provides input parameters
- **knowledge_base_qa**: For understanding system requirements
- **summarize_document**: For overall system documentation

## Future Enhancements

Potential additions to this tool:
- Atmospheric loss calculations
- Rain fade margins
- Multi-hop link analysis
- Interference calculations
- System noise temperature effects
