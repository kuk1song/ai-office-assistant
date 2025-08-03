"""
CSS Styles for AI Office Assistant

This module contains all custom CSS styling definitions for the application.
Separated for better maintainability and future theming support.
"""

import streamlit as st

def inject_custom_css():
    """Inject custom CSS for styling the application."""
    st.markdown("""
    <style>
        /* Main container styling */
        .main {
            background-color: #f0f2f6;
        }
        
        /* Chat bubbles styling */
        .st-emotion-cache-1c7y2kd {
            border-radius: 20px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        /* User message */
        .st-emotion-cache-1c7y2kd[data-testid="stChatMessage"]:has(.st-emotion-cache-1f1d6gn) {
            background-color: #dcf8c6;
        }
        
        /* AI message */
        .st-emotion-cache-1c7y2kd[data-testid="stChatMessage"]:not(:has(.st-emotion-cache-1f1d6gn)) {
            background-color: #ffffff;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Center align the text in st.info */
        .stAlert {
            text-align: center;
        }
        
        /* Future: Layer navigation styles will be added here */
        .layer-nav-container {
            /* Placeholder for future layer navigation */
        }
        
        .kb-hub-card {
            /* Placeholder for future KB hub cards */
        }
        
        .breadcrumb-nav {
            /* Placeholder for future breadcrumb navigation */
        }
    </style>
    """, unsafe_allow_html=True) 