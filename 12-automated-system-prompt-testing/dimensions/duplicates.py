from __future__ import annotations

"""Check for duplicate resources via fuzzy name/address matching."""
from difflib import SequenceMatcher
from dimensions.base import EvalDimension, DimensionResult


class DuplicatesDimension(EvalDimension):
    name = 'duplicates'

    def evaluate(self, resources: list[dict], context: dict) -> DimensionResult:
        flags = []
        name_threshold = self.config.get('name_threshold', 0.8)

        if len(resources) < 2:
            return DimensionResult(flags=flags, details={'duplicates': []})

        duplicates = []
        for i in range(len(resources)):
            for j in range(i + 1, len(resources)):
                ri = resources[i] if isinstance(resources[i], dict) else {}
                rj = resources[j] if isinstance(resources[j], dict) else {}

                name_i = ri.get('name', '').lower().strip()
                name_j = rj.get('name', '').lower().strip()

                # Name similarity
                if name_i and name_j:
                    ratio = SequenceMatcher(None, name_i, name_j).ratio()
                    if ratio > name_threshold:
                        duplicates.append({
                            'resource_a': ri.get('name', ''),
                            'resource_b': rj.get('name', ''),
                            'similarity': round(ratio, 2),
                            'match_type': 'name',
                        })
                        continue

                # Address similarity (require some name overlap too)
                addr_i = ri.get('addresses', [])
                addr_j = rj.get('addresses', [])
                if isinstance(addr_i, list) and addr_i:
                    addr_i = addr_i[0]
                if isinstance(addr_j, list) and addr_j:
                    addr_j = addr_j[0]
                if isinstance(addr_i, str) and isinstance(addr_j, str) and addr_i and addr_j:
                    addr_ratio = SequenceMatcher(None, addr_i.lower(), addr_j.lower()).ratio()
                    name_ratio = SequenceMatcher(None, name_i, name_j).ratio() if name_i and name_j else 0
                    if addr_ratio > 0.9 and name_ratio > 0.4:
                        duplicates.append({
                            'resource_a': ri.get('name', ''),
                            'resource_b': rj.get('name', ''),
                            'similarity': round(addr_ratio, 2),
                            'match_type': 'address',
                        })

        if duplicates:
            flags.append('DUPLICATE_RESOURCE')

        return DimensionResult(flags=flags, details={'duplicates': duplicates})
