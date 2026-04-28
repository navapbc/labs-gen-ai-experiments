from __future__ import annotations

"""Check if output resources are grounded in RAG context.

When web search is NOT used:
- LOW_GROUNDING: grounding percentage falls below threshold (default 70%)
- HALLUCINATION_RISK: low grounding + no web search + more output resources
  than input RAG resources (likely fabricated from training data)

When web search IS used:
- Ungrounded resources are expected (they came from web search, not RAG)
- Neither flag is raised
"""
from difflib import SequenceMatcher
from dimensions.base import EvalDimension, DimensionResult


class RagGroundingDimension(EvalDimension):
    name = 'rag_grounding'

    def evaluate(self, resources: list[dict], context: dict) -> DimensionResult:
        flags = []
        rag_context = context.get('resources_context', '')
        web_search_used = context.get('web_search_used', False)
        min_grounding_pct = self.config.get('min_grounding_pct', 70)

        if not resources or not rag_context:
            return DimensionResult(
                flags=flags,
                details={'grounded': 0, 'ungrounded': 0, 'total': 0,
                         'grounding_pct': 0, 'web_search_used': web_search_used},
            )

        grounded = 0
        ungrounded = 0
        ungrounded_names = []

        rag_lower = rag_context.lower()

        # Count RAG input resources for hallucination check
        rag_resource_count = sum(
            1 for line in rag_context.split('\n')
            if line.strip().lower().startswith('name:')
        )

        for res in resources:
            if not isinstance(res, dict):
                continue
            name = res.get('name', '')
            if not name:
                continue

            name_lower = name.lower().strip()

            if _is_grounded(name_lower, rag_lower):
                grounded += 1
            else:
                ungrounded += 1
                ungrounded_names.append(name)

        total = grounded + ungrounded
        grounding_pct = round(grounded / total * 100, 1) if total > 0 else 0

        # Only flag grounding issues when web search was NOT used
        if total > 0 and not web_search_used:
            if grounding_pct < min_grounding_pct:
                flags.append('LOW_GROUNDING')

            # Hallucination risk: low grounding + output count > input count
            if (grounding_pct < min_grounding_pct
                    and total > rag_resource_count
                    and total > 3):
                flags.append('HALLUCINATION_RISK')

        return DimensionResult(
            flags=flags,
            details={
                'grounded': grounded,
                'ungrounded': ungrounded,
                'total': total,
                'ungrounded_names': ungrounded_names,
                'grounding_pct': grounding_pct,
                'web_search_used': web_search_used,
                'rag_resource_count': rag_resource_count,
            },
        )


def _is_grounded(name_lower: str, rag_lower: str) -> bool:
    """Check if a resource name is grounded in the RAG context.

    Uses three matching strategies (in order):
    1. Direct substring match
    2. Fuzzy word overlap (>=40% of significant words found)
    3. SequenceMatcher ratio (>=0.6) against each reference name
    """
    # Strategy 1: Direct substring
    if name_lower in rag_lower:
        return True

    # Strategy 2: Significant word overlap
    words = [w for w in name_lower.split() if len(w) > 3]
    if words:
        matched_words = sum(1 for w in words if w in rag_lower)
        if matched_words / len(words) >= 0.4:
            return True

    # Strategy 3: SequenceMatcher against each "Name: ..." line
    for line in rag_lower.split('\n'):
        if line.startswith('name:'):
            ref_name = line[5:].strip()
            ratio = SequenceMatcher(None, name_lower, ref_name).ratio()
            if ratio >= 0.6:
                return True

    return False
