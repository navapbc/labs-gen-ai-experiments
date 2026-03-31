from __future__ import annotations

"""Check output has valid JSON structure with expected keys."""
from dimensions.base import EvalDimension, DimensionResult


class OutputStructureDimension(EvalDimension):
    name = 'output_structure'

    def evaluate(self, resources: list[dict], context: dict) -> DimensionResult:
        flags = []
        parsed = context.get('parsed_json')
        parse_error = context.get('parse_error')

        if parse_error:
            flags.append('INVALID_JSON')
            return DimensionResult(flags=flags)

        if not parsed:
            flags.append('EMPTY_OUTPUT')
            return DimensionResult(flags=flags)

        required_keys = self.config.get('required_keys', [])
        if required_keys:
            missing = [k for k in required_keys if k not in parsed]
            # Also check nested in list items (e.g. logs -> resources)
            if missing and isinstance(parsed, dict):
                for key, val in parsed.items():
                    if isinstance(val, list):
                        for item in val:
                            if isinstance(item, dict):
                                missing = [k for k in missing if k not in item]

            if missing:
                flags.append(f'MISSING_KEYS_{",".join(missing)}')

        if not resources:
            flags.append('ZERO_RESOURCES')

        return DimensionResult(flags=flags)
