"""Custom exceptions for the NXP health dashboard project."""


class DashboardError(Exception):
    """Base exception for dashboard-related failures."""


class DataLoadError(DashboardError):
    """Raised when a required dataset cannot be loaded."""


class MetadataFetchError(DashboardError):
    """Raised when World Bank metadata cannot be retrieved."""


class PipelineError(DashboardError):
    """Raised when an ETL or analysis pipeline step fails."""
