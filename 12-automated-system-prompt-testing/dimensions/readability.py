from __future__ import annotations

"""Check readability of output text (Flesch-Kincaid grade level).

Uses textstat library (robust, handles short text well).
"""
import re
from dimensions.base import EvalDimension, DimensionResult


class ReadabilityDimension(EvalDimension):
    name = 'readability'

    def evaluate(self, resources: list[dict], context: dict) -> DimensionResult:
        flags = []
        max_grade = self.config.get('max_grade_level', 8.0)

        # Collect description text from resources
        descriptions = []
        for res in resources:
            if isinstance(res, dict):
                desc = res.get('description', '')
                if desc:
                    descriptions.append(desc)

        if not descriptions:
            return DimensionResult(flags=flags, details={})

        text = '\n\n'.join(descriptions)
        cleaned = _clean_text(text)

        word_count = len(cleaned.split()) if cleaned else 0
        if not cleaned or word_count < 20:
            return DimensionResult(flags=flags, details={'word_count': word_count})

        scores = _calculate_readability(cleaned)

        grade = scores.get('grade_level')
        if grade is not None:
            if grade > max_grade:
                flags.append('ABOVE_8TH_GRADE')

        return DimensionResult(flags=flags, details={'readability': scores})


def _clean_text(text: str) -> str:
    """Clean text for readability analysis by removing markdown, URLs, addresses."""
    if not text:
        return ''

    # Handle markdown links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
    # Replace URLs
    text = re.sub(r'https?://[^\s\)\]]+', '', text)
    # Remove markdown bold
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'\*\*', '', text)
    # Remove markdown italic
    text = re.sub(r'(?<![*\w])\*([^*]+)\*(?![*\w])', r'\1', text)
    # Remove markdown headers
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    # Remove bullet points
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    # Remove numbered lists
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    # Remove parenthetical citations
    text = re.sub(r'\([^)]*[\w.-]+\.(com|org|gov|edu|net)[^)]*\)', '', text)
    # Remove phone numbers
    text = re.sub(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '', text)
    # Clean whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'  +', ' ', text)

    return text.strip()


def _calculate_readability(text: str) -> dict:
    """Calculate readability metrics using textstat."""
    try:
        import textstat
        grade = textstat.flesch_kincaid_grade(text)
        return {
            'flesch_ease': round(textstat.flesch_reading_ease(text), 1),
            'flesch_grade': round(grade, 1),
            'gunning_fog': round(textstat.gunning_fog(text), 1),
            'smog_index': round(textstat.smog_index(text), 1),
            'grade_level': round(grade, 1),
        }
    except ImportError:
        pass

    # Fallback to readability library
    try:
        from readability import getmeasures
        sentences = re.split(r'(?<=[.!?])\s+', text)
        text_split = '\n'.join(s.strip() for s in sentences if s.strip())
        measures = getmeasures(text_split, lang='en')
        grades = measures.get('readability grades', {})
        grade = round(grades.get('Kincaid', 0), 1)
        return {
            'flesch_ease': round(grades.get('FleschReadingEase', 0), 1),
            'flesch_grade': grade,
            'gunning_fog': round(grades.get('GunningFogIndex', 0), 1),
            'smog_index': round(grades.get('SMOGIndex', 0), 1),
            'grade_level': grade,
        }
    except Exception:
        return {}
