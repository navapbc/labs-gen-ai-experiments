from __future__ import annotations

"""Check if resources have adequate contact information."""
from dimensions.base import EvalDimension, DimensionResult


class ContactCompletenessDimension(EvalDimension):
    name = 'contact_completeness'

    def evaluate(self, resources: list[dict], context: dict) -> DimensionResult:
        flags = []
        missing_contact = 0

        for res in resources:
            if not isinstance(res, dict):
                continue
            phones = res.get('phones', [])
            addresses = res.get('addresses', [])
            has_phone = isinstance(phones, list) and any(p for p in phones if p)
            has_address = isinstance(addresses, list) and any(a for a in addresses if a)
            if not has_phone and not has_address:
                missing_contact += 1

        if missing_contact > 0:
            flags.append(f'MISSING_CONTACT_{missing_contact}')

        return DimensionResult(
            flags=flags,
            details={'missing_contact_count': missing_contact, 'total': len(resources)},
        )
