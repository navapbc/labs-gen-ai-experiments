from __future__ import annotations

"""Phoenix API client for trace extraction."""
import os
import time
import logging
from datetime import datetime, timedelta, timezone

import httpx

logger = logging.getLogger(__name__)


class PhoenixClient:
    """Client for Phoenix observability API."""

    def __init__(self, url: str | None = None, api_key: str | None = None,
                 project_name: str = 'default'):
        self.url = (url or os.environ.get('PHOENIX_URL', '')).rstrip('/')
        self.api_key = api_key or os.environ.get('PHOENIX_API_KEY', '')
        self.project_name = project_name

        if not self.url:
            raise ValueError("Phoenix URL required. Set PHOENIX_URL env var or pass url parameter.")
        if not self.api_key:
            raise ValueError("Phoenix API key required. Set PHOENIX_API_KEY env var or pass api_key parameter.")

    def fetch_spans(self, days_back: int = 60, max_pages: int = 100) -> list[dict]:
        """Fetch all spans from Phoenix API with pagination.

        Args:
            days_back: Number of days to look back.
            max_pages: Maximum number of API pages to fetch.

        Returns:
            List of span dicts.
        """
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)

        headers = {"Authorization": f"Bearer {self.api_key}"}
        all_spans = []
        cursor = None
        page = 1

        while page <= max_pages:
            url = f"{self.url}/v1/projects/{self.project_name}/spans"
            if cursor:
                url += f"?cursor={cursor}"

            try:
                response = None
                for attempt in range(3):
                    try:
                        response = httpx.get(url, headers=headers, verify=False, timeout=120.0)
                        break
                    except (httpx.RemoteProtocolError, httpx.ReadTimeout, httpx.ConnectError) as e:
                        if attempt < 2:
                            logger.warning(f"Retry {attempt+1}/3 on page {page}: {e}")
                            time.sleep(5 * (attempt + 1))
                        else:
                            raise

                if response is None or response.status_code != 200:
                    status = response.status_code if response else 'no response'
                    logger.error(f"HTTP {status}")
                    break

                data = response.json()
                spans = data.get('data', [])
                if not spans:
                    break

                # Filter by date range
                for span in spans:
                    start_time_str = span.get('start_time')
                    if start_time_str:
                        try:
                            from dateutil.parser import parse as parse_date
                            span_date = parse_date(start_time_str)
                            if span_date.tzinfo is None:
                                span_date = span_date.replace(tzinfo=timezone.utc)
                            if start_date <= span_date <= end_date:
                                all_spans.append(span)
                        except Exception:
                            all_spans.append(span)

                logger.info(f"Page {page}: {len(spans)} spans, total collected: {len(all_spans)}")

                cursor = data.get('next_cursor')
                if not cursor:
                    break
                page += 1
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Error on page {page}: {e}")
                break

        logger.info(f"Total spans fetched: {len(all_spans)}")
        return all_spans
