from __future__ import annotations

"""Check if output resources are grounded in RAG context."""
from difflib import SequenceMatcher
from dimensions.base import EvalDimension, DimensionResult


class RagGroundingDimension(EvalDimension):
    name = 'rag_grounding'

    def evaluate(self, resources: list[dict], context: dict) -> DimensionResult:
        flags = []
        rag_context = context.get('resources_context', '')

        if not resources or not rag_context:
            return DimensionResult(
                flags=flags,
                details={'grounded': 0, 'ungrounded': 0, 'total': 0},
            )

        grounded = 0
        ungrounded = 0
        ungrounded_names = []

        rag_lower = rag_context.lower()

        for res in resources:
            if not isinstance(res, dict):
                continue
            name = res.get('name', '')
            if not name:
                continue

            name_lower = name.lower().strip()

            # Direct substring match
            if name_lower in rag_lower:
                grounded += 1
                continue

            # Fuzzy match: check significant words
            words = [w for w in name_lower.split() if len(w) > 3]
            matched_words = sum(1 for w in words if w in rag_lower)
            if words and matched_words / len(words) >= 0.5:
                grounded += 1
                continue

            ungrounded += 1
            ungrounded_names.append(name)

        total = grounded + ungrounded
        if ungrounded > 0:
            flags.append('UNGROUNDED_RESOURCE')

        return DimensionResult(
            flags=flags,
            details={
                'grounded': grounded,
                'ungrounded': ungrounded,
                'total': total,
                'ungrounded_names': ungrounded_names,
                'grounding_pct': round(grounded / total * 100, 1) if total > 0 else 0,
            },
        )
