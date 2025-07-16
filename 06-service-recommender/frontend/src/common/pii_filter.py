import logging

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
    def filter(self, record: logging.LogRecord):
        if record.msg:
            # get the full log message (include args)
            full_message = record.getMessage()
            record.msg = remove_pii(full_message)
            record.args = ()  # these should now be in the full_message and we want to protect them from getting logged
        return True
