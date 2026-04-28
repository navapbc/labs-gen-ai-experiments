from __future__ import annotations

"""Check if output resources match the query location."""
import re
from dimensions.base import EvalDimension, DimensionResult


class LocationMatchDimension(EvalDimension):
    name = 'location_match'

    def evaluate(self, resources: list[dict], context: dict) -> DimensionResult:
        flags = []
        location = context.get('location', '')
        user_query = context.get('user_query', '')

        if not resources:
            return DimensionResult(flags=flags)

        # Build state patterns from config or defaults
        state_patterns = self.config.get('state_patterns', {})
        if not state_patterns:
            state_patterns = {
                'TX': r'\bTX\b|\bTexas\b',
                'PA': r'\bPA\b|\bPennsylvania\b',
            }

        expected_state = self._extract_state(location, state_patterns)
        if not expected_state:
            expected_state = self._extract_state(user_query, state_patterns)
        if not expected_state:
            return DimensionResult(flags=flags)

        cross_state_count = 0
        for res in resources:
            if not isinstance(res, dict):
                continue
            addresses = res.get('addresses', [])
            if isinstance(addresses, str):
                addresses = [addresses]
            for addr in addresses:
                if not addr:
                    continue
                res_state = self._extract_state(addr, state_patterns)
                if res_state and res_state != expected_state:
                    cross_state_count += 1
                    break

        if cross_state_count > 0:
            flags.append('CROSS_STATE')

        return DimensionResult(
            flags=flags,
            details={'expected_state': expected_state, 'cross_state_count': cross_state_count},
        )

    def _extract_state(self, text: str, patterns: dict) -> str | None:
        if not text:
            return None
        for state, pattern in patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return state
        return None
