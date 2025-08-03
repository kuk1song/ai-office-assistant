"""
UI Package for AI Office Assistant

This package contains all user interface components and layouts:
- Components: Reusable UI components (chat, sidebar, upload, etc.)
- Styles: CSS and styling definitions
- Layout: Main layout management

Designed to support future layer-based navigation system.
"""

from .styles import inject_custom_css
from .layout import render_sidebar, render_main_chat

# Import component modules for easy access
from . import components

__all__ = [
    'inject_custom_css',
    'render_sidebar', 
    'render_main_chat',
    'components'
] 