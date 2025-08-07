"""
Link Budget Calculator Tool

This tool performs point-to-point communication link budget calculations.
"""
import math
from langchain.tools import tool
from pydantic.v1 import BaseModel, Field
from typing import Dict, Any


class LinkBudgetInput(BaseModel):
    distance_km: float = Field(description="The distance between the two sites in kilometers.")
    transmitter_power_dBm: float = Field(description="The output power of the transmitter in dBm.")
    transmitter_cable_loss_dB: float = Field(description="The cable and connector loss at the transmitter side in dB.")
    transmitter_antenna_gain_dBi: float = Field(description="The gain of the transmitter's antenna in dBi.")
    receiver_antenna_gain_dBi: float = Field(description="The gain of the receiver's antenna in dBi.")
    receiver_cable_loss_dB: float = Field(description="The cable and connector loss at the receiver side in dB.")
    frequency_MHz: float = Field(description="The operating frequency in Megahertz.")


@tool(args_schema=LinkBudgetInput)
def calculate_link_budget(
    distance_km: float, 
    transmitter_power_dBm: float, 
    transmitter_cable_loss_dB: float, 
    transmitter_antenna_gain_dBi: float, 
    receiver_antenna_gain_dBi: float, 
    receiver_cable_loss_dB: float, 
    frequency_MHz: float
) -> Dict[str, Any]:
    """
    Calculates the link budget for a point-to-point communication link based on provided parameters.
    This is a pure calculation tool and does not read from documents. All parameters must be provided.
    Returns a dictionary with all calculated values, including the final Link Margin.
    """
    # EIRP Calculation
    eirp_dBm = transmitter_power_dBm - transmitter_cable_loss_dB + transmitter_antenna_gain_dBi
    
    # Free Space Path Loss (FSPL) Calculation
    # FSPL (dB) = 20 * log10(d) + 20 * log10(f) + 20 * log10(4π/c)
    # 20 * log10(4π/c) where f is in MHz and d is in km is approx -27.55
    fspl_dB = 20 * math.log10(distance_km) + 20 * math.log10(frequency_MHz) + 27.55
    
    # Received Power Calculation
    received_power_dBm = eirp_dBm - fspl_dB + receiver_antenna_gain_dBi - receiver_cable_loss_dB
    
    return {
        "Effective Isotropic Radiated Power (EIRP) dBm": round(eirp_dBm, 2),
        "Free Space Path Loss (FSPL) dB": round(fspl_dB, 2),
        "Calculated Received Power dBm": round(received_power_dBm, 2)
        # Note: True Link Margin requires Receiver Sensitivity, which the user must provide for the final comparison.
        # The agent will need to compare this received power with the sensitivity.
    }
