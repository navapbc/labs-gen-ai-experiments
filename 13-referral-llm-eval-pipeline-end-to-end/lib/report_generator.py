from __future__ import annotations

"""Generate markdown evaluation reports."""
from datetime import datetime


def generate_eval_report(auto_analysis: dict, traces_meta: dict,
                         deep_analysis: dict | None = None,
                         correlation: dict | None = None) -> str:
    """Generate markdown evaluation report from analysis results."""
    lines = [
        "# LLM Evaluation Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "---",
        "",
        "## 1. Dataset Overview",
        "",
        f"- **Total traces:** {traces_meta.get('total', 0)}",
        f"- **Date range:** {traces_meta.get('date_range', 'N/A')}",
    ]

    # Prompt type distribution
    by_type = auto_analysis.get('by_prompt_type', {})
    if by_type:
        lines.append("- **Prompt types:**")
        for pt, stats in sorted(by_type.items()):
            lines.append(f"  - {pt}: {stats['total']}")

    lines.extend(["", "---", "", "## 2. Automated Evaluation Results", ""])
    lines.append(f"- **Traces checked:** {auto_analysis.get('total_traces', 0)}")
    total = max(auto_analysis.get('total_traces', 1), 1)
    flagged = auto_analysis.get('flagged_traces', 0)
    lines.append(f"- **Traces with flags:** {flagged} ({flagged/total*100:.1f}%)")

    # Flag distribution table
    flag_dist = auto_analysis.get('flag_distribution', {})
    if flag_dist:
        lines.extend(["", "### Flag Distribution", "",
                       "| Flag | Count | Rate | 95% CI |",
                       "|------|-------|------|--------|"])
        for flag, stats in sorted(flag_dist.items(), key=lambda x: -x[1]['count']):
            lines.append(f"| {flag} | {stats['count']} | {stats['pct']}% | "
                         f"[{stats['ci_95'][0]}%, {stats['ci_95'][1]}%] |")

    # By prompt type
    if by_type:
        lines.extend(["", "### By Prompt Type", "",
                       "| Type | Total | Flagged | Rate | 95% CI |",
                       "|------|-------|---------|------|--------|"])
        for pt, stats in sorted(by_type.items()):
            lines.append(f"| {pt} | {stats['total']} | {stats['flagged']} | "
                         f"{stats['flagged_pct']}% | [{stats['ci_95'][0]}%, {stats['ci_95'][1]}%] |")

    # RAG grounding
    rag = auto_analysis.get('rag_grounding', {})
    if rag:
        lines.extend(["", "### RAG Grounding", "",
                       f"- **Mean:** {rag.get('mean_pct', 0)}%",
                       f"- **Median:** {rag.get('median_pct', 0)}%",
                       f"- **Below 50%:** {rag.get('below_50_pct', 0)} traces"])

    # Correlation section
    if correlation and 'total_overlapping' in correlation:
        lines.extend(["", "---", "",
                       "## 3. Auto Flag — Deep Review Correlation", "",
                       f"- **Overlapping traces:** {correlation['total_overlapping']}",
                       f"- **Flagged → Fail rate:** {correlation.get('flagged_fail_rate', 0)}%",
                       f"- **Unflagged → Fail rate:** {correlation.get('unflagged_fail_rate', 0)}%"])

    lines.extend(["", "---", "",
                   f"_Report generated on {datetime.now().strftime('%Y-%m-%d')}_"])
    return '\n'.join(lines)
