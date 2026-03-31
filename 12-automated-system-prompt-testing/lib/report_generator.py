from __future__ import annotations

"""Generate markdown comparison reports from evaluation results."""
from datetime import datetime
from collections import defaultdict


def safe_avg(lst):
    return sum(lst) / len(lst) if lst else 0


def compute_metrics(eval_results: list[dict], versions: list[str]) -> dict:
    """Compute per-version aggregate metrics."""
    metrics = {}

    for version in versions:
        m = {
            'valid_json': 0,
            'total': len(eval_results),
            'resource_counts': [],
            'flag_counts': [],
            'flags': defaultdict(int),
            'grounding_pcts': [],
            'readability_grades': [],
            'has_duplicates': 0,
            'has_broken_urls': 0,
            'has_cross_state': 0,
            'has_above_8th_grade': 0,
            'contact_missing_count': 0,
        }

        for r in eval_results:
            v = r.get(version, {})
            flags = v.get('flags', [])

            if 'INVALID_JSON' not in flags and 'API_ERROR' not in flags and 'EMPTY_OUTPUT' not in flags:
                m['valid_json'] += 1

            m['resource_counts'].append(v.get('resource_count', 0))
            m['flag_counts'].append(v.get('flag_count', 0))

            for f in flags:
                m['flags'][f] += 1

            if 'DUPLICATE_RESOURCE' in flags:
                m['has_duplicates'] += 1
            if 'BROKEN_URL' in flags:
                m['has_broken_urls'] += 1
            if 'CROSS_STATE' in flags:
                m['has_cross_state'] += 1
            if 'ABOVE_8TH_GRADE' in flags:
                m['has_above_8th_grade'] += 1

            for f in flags:
                if f.startswith('MISSING_CONTACT_'):
                    m['contact_missing_count'] += 1
                    break

            grounding = v.get('details', {}).get('rag_grounding', {})
            if grounding.get('total', 0) > 0:
                m['grounding_pcts'].append(grounding.get('grounding_pct', 0))

            read = v.get('details', {}).get('readability', {})
            gl = read.get('grade_level')
            if gl is not None:
                m['readability_grades'].append(gl)

        metrics[version] = m

    return metrics


def compute_per_query(eval_results: list[dict], versions: list[str]) -> list[dict]:
    """Compute per-query comparison."""
    per_query = []

    for r in eval_results:
        entry = {
            'trace_id': r.get('query_id', r.get('trace_id', '')),
            'query': r.get('user_query', '')[:80],
        }

        for v in versions:
            vdata = r.get(v, {})
            entry[f'{v}_resources'] = vdata.get('resource_count', 0)
            entry[f'{v}_flags'] = vdata.get('flag_count', 99)
            entry[f'{v}_flag_list'] = vdata.get('flags', [])

        flag_counts = {v: entry[f'{v}_flags'] for v in versions}
        min_flags = min(flag_counts.values())
        winners = [v for v, fc in flag_counts.items() if fc == min_flags]
        entry['best'] = winners[0] if len(winners) == 1 else 'tie'

        entry['pairwise'] = {}
        for i in range(len(versions)):
            for j in range(i + 1, len(versions)):
                va, vb = versions[i], versions[j]
                a_f = entry[f'{va}_flags']
                b_f = entry[f'{vb}_flags']
                if a_f < b_f:
                    entry['pairwise'][f'{va}_vs_{vb}'] = va
                elif b_f < a_f:
                    entry['pairwise'][f'{va}_vs_{vb}'] = vb
                else:
                    entry['pairwise'][f'{va}_vs_{vb}'] = 'tie'

        per_query.append(entry)

    return per_query


def generate_report(metrics: dict, per_query: list[dict],
                    eval_results: list[dict], versions: list[str],
                    title: str = 'Prompt A/B Test Results',
                    model: str = '', temperature: float = 0) -> str:
    """Generate markdown comparison report."""
    n = metrics[versions[0]]['total']

    lines = []
    ver_str = ' vs '.join(versions)
    lines.append(f'# {title}')
    lines.append('')
    lines.append(f'**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    lines.append(f'**Test queries:** {n}')
    if model:
        lines.append(f'**Model:** {model} (temp={temperature})')
    lines.append(f'**Versions:** {", ".join(versions)}')
    lines.append('')

    # Executive Summary
    lines.append('## Executive Summary')
    lines.append('')
    for i in range(len(versions)):
        for j in range(i + 1, len(versions)):
            va, vb = versions[i], versions[j]
            a_wins = sum(1 for q in per_query if q.get('pairwise', {}).get(f'{va}_vs_{vb}') == va)
            b_wins = sum(1 for q in per_query if q.get('pairwise', {}).get(f'{va}_vs_{vb}') == vb)
            ties = sum(1 for q in per_query if q.get('pairwise', {}).get(f'{va}_vs_{vb}') == 'tie')
            lines.append(f'**{va} vs {vb}:** {va} wins {a_wins}, {vb} wins {b_wins}, tied {ties}')
    lines.append('')

    # Overall Metrics
    lines.append('## Overall Metrics')
    lines.append('')
    header = '| Metric | ' + ' | '.join(versions) + ' |'
    lines.append(header)
    lines.append('|--------' + '|-----' * len(versions) + '|')

    cells = [f'{metrics[v]["valid_json"]}/{n}' for v in versions]
    lines.append(f'| Valid JSON | ' + ' | '.join(cells) + ' |')

    cells = [f'{safe_avg(metrics[v]["resource_counts"]):.1f}' for v in versions]
    lines.append(f'| Avg resources | ' + ' | '.join(cells) + ' |')

    cells = [f'{safe_avg(metrics[v]["flag_counts"]):.1f}' for v in versions]
    lines.append(f'| Avg flags | ' + ' | '.join(cells) + ' |')
    lines.append('')

    # Per-Dimension
    lines.append('## Per-Dimension Comparison')
    lines.append('')
    header = '| Dimension | ' + ' | '.join(versions) + ' |'
    lines.append(header)
    lines.append('|-----------|' + '-----|' * len(versions))

    cells = [f'{metrics[v]["has_duplicates"]}/{n}' for v in versions]
    lines.append(f'| Duplicate resources | ' + ' | '.join(cells) + ' |')

    cells = [f'{safe_avg(metrics[v]["readability_grades"]):.1f}' for v in versions]
    lines.append(f'| Avg grade level | ' + ' | '.join(cells) + ' |')

    cells = [f'{metrics[v]["has_above_8th_grade"]}/{n}' for v in versions]
    lines.append(f'| Above 8th grade | ' + ' | '.join(cells) + ' |')

    cells = [f'{safe_avg(metrics[v]["grounding_pcts"]):.1f}%' for v in versions]
    lines.append(f'| Avg grounding % | ' + ' | '.join(cells) + ' |')

    cells = [f'{metrics[v]["has_broken_urls"]}/{n}' for v in versions]
    lines.append(f'| Broken URLs | ' + ' | '.join(cells) + ' |')

    cells = [f'{metrics[v]["has_cross_state"]}/{n}' for v in versions]
    lines.append(f'| Cross-state errors | ' + ' | '.join(cells) + ' |')

    cells = [f'{metrics[v]["contact_missing_count"]}/{n}' for v in versions]
    lines.append(f'| Missing contact info | ' + ' | '.join(cells) + ' |')
    lines.append('')

    # Flag Distribution
    lines.append('## Flag Distribution')
    lines.append('')
    all_flags = set()
    for v in versions:
        all_flags.update(metrics[v]['flags'].keys())
    header = '| Flag | ' + ' | '.join(versions) + ' |'
    lines.append(header)
    lines.append('|------|' + '-----|' * len(versions))
    for flag in sorted(all_flags):
        cells = [str(metrics[v]['flags'].get(flag, 0)) for v in versions]
        lines.append(f'| {flag} | ' + ' | '.join(cells) + ' |')
    lines.append('')

    # Per-Query
    lines.append('## Per-Query Results')
    lines.append('')
    header = '| # | Query |'
    for v in versions:
        header += f' {v} Res | {v} Flags |'
    header += ' Best |'
    lines.append(header)
    sep = '|---|-------|'
    for _ in versions:
        sep += '---------|-----------|'
    sep += '------|'
    lines.append(sep)

    for i, q in enumerate(per_query):
        query_text = q['query'][:40]
        row = f'| {i+1} | {query_text}... |'
        for v in versions:
            row += f' {q.get(f"{v}_resources", 0)} | {q.get(f"{v}_flags", 0)} |'
        row += f' **{q.get("best", "tie")}** |'
        lines.append(row)
    lines.append('')

    # Regressions
    if len(versions) >= 2:
        latest = versions[-1]
        baseline = versions[0]
        regressions = [q for q in per_query
                       if q.get(f'{latest}_flags', 0) > q.get(f'{baseline}_flags', 0)]
        if regressions:
            lines.append(f'## Regressions ({latest} worse than {baseline})')
            lines.append('')
            for q in regressions:
                lines.append(f'### {q["trace_id"][:20]}')
                lines.append(f'- **Query:** {q["query"][:80]}')
                for v in versions:
                    lines.append(f'- **{v} flags ({q.get(f"{v}_flags", 0)}):** '
                                 f'{", ".join(q.get(f"{v}_flag_list", [])) or "none"}')
                lines.append('')
        else:
            lines.append(f'## Regressions ({latest} vs {baseline})')
            lines.append('')
            lines.append(f'No regressions. {latest} equal to or better than {baseline} on all queries.')
            lines.append('')

    return '\n'.join(lines)
