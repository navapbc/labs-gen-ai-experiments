from __future__ import annotations

"""Statistical analysis utilities."""
import math
from collections import Counter, defaultdict


def wilson_ci(successes: int, total: int, z: float = 1.96) -> tuple[float, float, float]:
    """Wilson score confidence interval for a proportion.

    Returns:
        Tuple of (point_estimate_pct, lower_pct, upper_pct).
    """
    if total == 0:
        return 0, 0, 0
    p = successes / total
    denom = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denom
    margin = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denom
    lower = max(0, center - margin)
    upper = min(1, center + margin)
    return round(p * 100, 1), round(lower * 100, 1), round(upper * 100, 1)


def cohens_kappa(ratings1: list, ratings2: list, categories: list) -> float:
    """Compute Cohen's kappa for inter-rater reliability."""
    n = len(ratings1)
    if n == 0:
        return 0

    matrix = defaultdict(lambda: defaultdict(int))
    for r1, r2 in zip(ratings1, ratings2):
        matrix[r1][r2] += 1

    po = sum(matrix[c][c] for c in categories) / n

    pe = 0
    for c in categories:
        row_sum = sum(matrix[c][c2] for c2 in categories)
        col_sum = sum(matrix[c2][c] for c2 in categories)
        pe += (row_sum * col_sum) / (n * n)

    if pe == 1:
        return 1.0
    return round((po - pe) / (1 - pe), 3)


def flag_distribution(results: list[dict], key: str = 'flags') -> dict:
    """Count flag occurrences across results with CIs."""
    total = len(results)
    counts = Counter()
    for r in results:
        for f in r.get(key, []):
            counts[f] += 1

    dist = {}
    for flag, count in counts.most_common():
        pct, ci_low, ci_high = wilson_ci(count, total)
        dist[flag] = {
            'count': count,
            'pct': pct,
            'ci_95': [ci_low, ci_high],
        }
    return dist


def stratified_stats(results: list[dict], strata_key: str,
                     flagged_key: str = 'flags') -> dict:
    """Compute flag rates by stratum with CIs."""
    by_stratum = defaultdict(list)
    for r in results:
        by_stratum[r.get(strata_key, 'unknown')].append(r)

    stats = {}
    for stratum, group in by_stratum.items():
        n = len(group)
        flagged = sum(1 for r in group if r.get('flag_count', len(r.get(flagged_key, []))) > 0)
        pct, ci_low, ci_high = wilson_ci(flagged, n)

        top_flags = Counter()
        for r in group:
            for f in r.get(flagged_key, []):
                top_flags[f] += 1

        stats[stratum] = {
            'total': n,
            'flagged': flagged,
            'flagged_pct': pct,
            'ci_95': [ci_low, ci_high],
            'top_flags': dict(top_flags.most_common(5)),
        }

    return stats
