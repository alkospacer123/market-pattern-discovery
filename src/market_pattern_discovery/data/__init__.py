"""Strict read-only ingestion."""
from .finam import IngestionError, LoadResult, discover_finam_sources, stitch_finam

__all__ = ["IngestionError", "LoadResult", "discover_finam_sources", "stitch_finam"]
