from __future__ import annotations

"""Check resource count is within expected bounds."""
from dimensions.base import EvalDimension, DimensionResult


class ResourceCountDimension(EvalDimension):
    name = 'resource_count'

    def evaluate(self, resources: list[dict], context: dict) -> DimensionResult:
        flags = []
        count = len(resources)
        min_count = self.config.get('min', 1)
        max_count = self.config.get('max', 10)

        if count < min_count:
            flags.append('TOO_FEW_RESOURCES')
        elif count > max_count:
            flags.append('EXCESSIVE_RESOURCES')

        return DimensionResult(
            flags=flags,
            details={'resource_count': count, 'min': min_count, 'max': max_count},
        )
