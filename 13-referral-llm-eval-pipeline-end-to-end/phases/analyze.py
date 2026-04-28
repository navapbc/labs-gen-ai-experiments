from __future__ import annotations

"""Phase 4: Statistical analysis of evaluation results."""
import json
import logging
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

from lib.stats import wilson_ci, flag_distribution, stratified_stats
from lib.report_generator import generate_eval_report

logger = logging.getLogger(__name__)


def run_analyze(config: dict, eval_results: list[dict] | None = None) -> dict:
    """Run statistical analysis on eval results.

    Returns analysis dict.
    """
    output_dir = Path(config['extraction']['output_dir'])
    analysis_config = config.get('analysis', {})

    # Load data
    if eval_results is None:
        eval_path = output_dir / 'eval_results.json'
        if not eval_path.exists():
            raise FileNotFoundError(f"Eval results not found: {eval_path}. Run evaluate phase first.")
        with open(eval_path) as f:
            eval_results = json.load(f)

    traces = []
    traces_path = output_dir / 'traces.json'
    if traces_path.exists():
        with open(traces_path) as f:
            traces = json.load(f)

    logger.info(f"Analyzing {len(eval_results)} results")

    # Build analysis
    analysis = _analyze_automated(eval_results)

    # Traces metadata
    traces_meta = {'total': len(traces), 'date_range': 'N/A'}
    if traces:
        timestamps = [t['timestamp'] for t in traces if t.get('timestamp')]
        if timestamps:
            traces_meta['date_range'] = f"{min(timestamps)} to {max(timestamps)}"

    # Save analysis JSON
    analysis_output = {
        'generated_at': str(datetime.now()),
        'automated_analysis': analysis,
        'traces_meta': traces_meta,
    }

    analysis_path = output_dir / 'analysis.json'
    with open(analysis_path, 'w') as f:
        json.dump(analysis_output, f, indent=2, default=str)
    logger.info(f"Saved analysis to {analysis_path}")

    # Generate report
    report = generate_eval_report(analysis, traces_meta)
    report_path = Path(analysis_config.get('output_path', output_dir / 'eval_report.md'))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(report)
    logger.info(f"Saved report to {report_path}")

    _print_key_findings(analysis)
    return analysis_output


def _analyze_automated(results: list[dict]) -> dict:
    """Analyze automated check results."""
    total = len(results)
    flagged = sum(1 for r in results if r.get('flag_count', 0) > 0)

    analysis = {
        'total_traces': total,
        'flagged_traces': flagged,
        'flag_distribution': flag_distribution(results),
        'by_prompt_type': stratified_stats(results, 'prompt_type'),
        'by_web_search': stratified_stats(results, 'web_search_used'),
    }

    # RAG grounding summary
    grounding_pcts = []
    for r in results:
        gp = r.get('details', {}).get('rag_grounding', {}).get('grounding_pct')
        if gp is not None:
            grounding_pcts.append(gp)

    if grounding_pcts:
        analysis['rag_grounding'] = {
            'traces_with_data': len(grounding_pcts),
            'mean_pct': round(sum(grounding_pcts) / len(grounding_pcts), 1),
            'median_pct': round(sorted(grounding_pcts)[len(grounding_pcts) // 2], 1),
            'min_pct': round(min(grounding_pcts), 1),
            'max_pct': round(max(grounding_pcts), 1),
            'below_50_pct': sum(1 for g in grounding_pcts if g < 50),
            'below_80_pct': sum(1 for g in grounding_pcts if g < 80),
        }

    return analysis


def _print_key_findings(analysis: dict):
    """Print key findings to console."""
    logger.info("=" * 50)
    logger.info("KEY FINDINGS")
    logger.info("=" * 50)
    logger.info(f"Total: {analysis.get('total_traces', 0)}")
    logger.info(f"Flagged: {analysis.get('flagged_traces', 0)}")

    top_flags = sorted(analysis.get('flag_distribution', {}).items(),
                       key=lambda x: -x[1]['count'])[:5]
    if top_flags:
        logger.info("Top flags:")
        for flag, stats in top_flags:
            logger.info(f"  {flag}: {stats['count']} ({stats['pct']}%)")
