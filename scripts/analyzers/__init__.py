# AIOS Analyzers Package
"""
Modular analyzers for scanning project codebases.
Each analyzer extracts structured data from specific file types/patterns.
"""

from .base import BaseAnalyzer
from .python_analyzer import PythonAnalyzer
from .javascript_analyzer import JavaScriptAnalyzer
from .database_analyzer import DatabaseAnalyzer
from .api_analyzer import ApiAnalyzer
from .infrastructure_analyzer import InfrastructureAnalyzer
from .git_analyzer import GitAnalyzer
from .security_analyzer import SecurityAnalyzer
from .generic_analyzer import GenericAnalyzer

ALL_ANALYZERS = [
    PythonAnalyzer,
    JavaScriptAnalyzer,
    DatabaseAnalyzer,
    ApiAnalyzer,
    InfrastructureAnalyzer,
    GitAnalyzer,
    SecurityAnalyzer,
    GenericAnalyzer,
]

__all__ = [
    "BaseAnalyzer",
    "PythonAnalyzer",
    "JavaScriptAnalyzer",
    "DatabaseAnalyzer",
    "ApiAnalyzer",
    "InfrastructureAnalyzer",
    "GitAnalyzer",
    "SecurityAnalyzer",
    "GenericAnalyzer",
    "ALL_ANALYZERS",
]
