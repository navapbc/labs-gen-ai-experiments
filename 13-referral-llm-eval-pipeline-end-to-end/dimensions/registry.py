from __future__ import annotations

"""Load enabled dimensions from config."""
from dimensions.base import EvalDimension
from dimensions.output_structure import OutputStructureDimension
from dimensions.resource_count import ResourceCountDimension
from dimensions.url_validity import UrlValidityDimension
from dimensions.readability import ReadabilityDimension
from dimensions.duplicates import DuplicatesDimension
from dimensions.contact_completeness import ContactCompletenessDimension
from dimensions.rag_grounding import RagGroundingDimension
from dimensions.location_match import LocationMatchDimension

DIMENSION_CLASSES = {
    'output_structure': OutputStructureDimension,
    'resource_count': ResourceCountDimension,
    'url_validity': UrlValidityDimension,
    'readability': ReadabilityDimension,
    'duplicates': DuplicatesDimension,
    'contact_completeness': ContactCompletenessDimension,
    'rag_grounding': RagGroundingDimension,
    'location_match': LocationMatchDimension,
}


def load_dimensions(config: dict) -> list[EvalDimension]:
    """Load enabled dimensions from evaluation config.

    Args:
        config: The 'evaluation.dimensions' section of the YAML config.

    Returns:
        List of instantiated EvalDimension objects.
    """
    dimensions = []
    for name, dim_config in config.items():
        if not dim_config.get('enabled', True):
            continue
        cls = DIMENSION_CLASSES.get(name)
        if cls is None:
            continue
        dimensions.append(cls(config=dim_config))
    return dimensions
