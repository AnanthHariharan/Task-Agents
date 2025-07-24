# Universal Dataset Adapters for Task-Agents
# This module provides dataset-agnostic interfaces for embodied AI datasets

from .base_adapter import UniversalDatasetAdapter
from .teach_adapter import TeachDatasetAdapter
from .alfred_adapter import ALFReDatasetAdapter

__all__ = ['UniversalDatasetAdapter', 'TeachDatasetAdapter', 'ALFReDatasetAdapter']