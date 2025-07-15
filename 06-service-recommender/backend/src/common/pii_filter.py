from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine


analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()


def remove_pii(text: str) -> str:
    # Check to see if the text has any PII fields we are looking for (entities)
    # Default entities are person, email, phone number, ssn, credit card, iban code, ip address, date_time, location
    results = analyzer.analyze(text=text, entities=[], language="en")
    if results:
        scrubbed_results = anonymizer.anonymize(text=text, analyzer_results=results)
        return scrubbed_results.text
    return text


class PresidioFilter(logging.Filter):
    def filter(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = remove_pii(record.msg)
        return True