"""
Phoenix Arize API Client
Handles all interactions with the Phoenix REST API
"""
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import pyarrow as pa
import io
import pandas as pd
import json
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PhoenixClient:
    """Client for interacting with Phoenix Arize REST API"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Initialize Phoenix client
        
        Args:
            base_url: Base URL for Phoenix API (e.g., https://your-instance.arize.com)
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request to Phoenix API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            # Check if response is Arrow format
            content_type = response.headers.get('Content-Type', '')
            if 'application/x-pandas-arrow' in content_type or 'application/vnd.apache.arrow.stream' in content_type:
                # Parse Arrow format
                arrow_data = pa.ipc.open_stream(io.BytesIO(response.content)).read_all()
                # Convert to pandas DataFrame then to list of dicts
                df = arrow_data.to_pandas()
                return {'data': df.to_dict('records')}
            else:
                # Assume JSON
                return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
    
    def get_projects(self) -> List[Dict]:
        """Get all projects"""
        try:
            response = self._make_request('GET', '/v1/projects')
            return response.get('data', [])
        except Exception as e:
            logger.error(f"Failed to fetch projects: {e}")
            return []
    
    def get_spans(
        self, 
        project_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
        cursor: Optional[str] = None
    ) -> Dict:
        """
        Get spans/traces from Phoenix using GraphQL
        
        Args:
            project_id: Optional project ID to filter by
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum number of spans to return
            cursor: Pagination cursor
            
        Returns:
            Dictionary containing spans data and pagination info
        """
        if not project_id:
            logger.warning("project_id is required for fetching spans")
            return {'data': [], 'next_cursor': None}
        
        # Build GraphQL query for spans with all attributes
        after_clause = f', after: "{cursor}"' if cursor else ''
        
        # Build time filter.
        # We prefer server-side filtering for efficiency. If the filter format is rejected by Phoenix,
        # we will retry without the filter and let get_all_spans apply client-side filtering.
        filter_str = ''
        if start_time or end_time:
            try:
                # Phoenix expects ISO timestamps; normalize to UTC.
                def _iso_utc(dt: datetime) -> str:
                    if dt is None:
                        return ''
                    if dt.tzinfo is None:
                        # Assume UTC if naive
                        from datetime import timezone as _tz
                        dt = dt.replace(tzinfo=_tz.utc)
                    return dt.astimezone(timedelta(0)).isoformat().replace('+00:00', 'Z')

                start_iso = _iso_utc(start_time) if start_time else ''
                end_iso = _iso_utc(end_time) if end_time else ''
                # Best-effort: pass through as args Phoenix commonly accepts. If it errors, we fallback.
                # (We keep this isolated so failures are handled cleanly.)
                if start_iso:
                    filter_str += f', startTime: "{start_iso}"'
                if end_iso:
                    filter_str += f', endTime: "{end_iso}"'
            except Exception:
                filter_str = ''
        
        graphql_query = f'''
        {{
          node(id: "{project_id}") {{
            ... on Project {{
              spans(first: {limit}{after_clause}{filter_str}) {{
                pageInfo {{
                  endCursor
                  hasNextPage
                }}
                edges {{
                  node {{
                    name
                    spanKind
                    statusCode
                    statusMessage
                    startTime
                    endTime
                    parentId
                    context {{
                      spanId
                      traceId
                    }}
                    attributes
                    events {{
                      name
                      message
                      timestamp
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
        '''
        
        def _post(query_text: str) -> Dict:
            url = f"{self.base_url}/graphql"
            headers = self.session.headers.copy()
            headers['Content-Type'] = 'application/json'
            response = requests.post(
                url,
                headers=headers,
                json={'query': query_text},
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        try:
            data = _post(graphql_query)

            # If time-filtered query errors, retry without filter and let client-side filtering handle it.
            if 'errors' in data and filter_str:
                logger.warning("GraphQL rejected time filter; retrying without server-side time filtering.")
                graphql_query_no_filter = graphql_query.replace(filter_str, '')
                data = _post(graphql_query_no_filter)

            if 'errors' in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return {'data': [], 'next_cursor': None}
            
            # Parse GraphQL response
            node = data.get('data', {}).get('node', {})
            spans_data = node.get('spans', {})
            edges = spans_data.get('edges', [])
            page_info = spans_data.get('pageInfo', {})
            
            # Convert to flat format
            spans = []
            for edge in edges:
                node_data = edge.get('node', {})
                context = node_data.get('context', {})
                
                # Parse attributes if it's a JSON string
                attributes = node_data.get('attributes', {})
                if isinstance(attributes, str):
                    try:
                        attributes = json.loads(attributes)
                    except Exception:
                        attributes = {}
                
                span = {
                    'span_id': context.get('spanId', ''),
                    'trace_id': context.get('traceId', ''),
                    'name': node_data.get('name', ''),
                    'span_kind': node_data.get('spanKind', ''),
                    'status_code': node_data.get('statusCode', ''),
                    'status_message': node_data.get('statusMessage', ''),
                    'start_time': node_data.get('startTime', ''),
                    'end_time': node_data.get('endTime', ''),
                    'parent_id': node_data.get('parentId', ''),
                    'attributes': attributes,
                    'events': node_data.get('events', [])
                }
                spans.append(span)
            
            next_cursor = page_info.get('endCursor') if page_info.get('hasNextPage') else None
            
            return {'data': spans, 'next_cursor': next_cursor}
            
        except Exception as e:
            logger.error(f"Failed to fetch spans: {e}")
            import traceback
            traceback.print_exc()
            return {'data': [], 'next_cursor': None}
    
    def get_all_spans(
        self,
        project_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_spans: int = 10000
    ) -> List[Dict]:
        """
        Get all spans with pagination
        
        Args:
            project_id: Optional project ID to filter by
            start_time: Optional start time filter (applied client-side)
            end_time: Optional end time filter (applied client-side)
            max_spans: Maximum total number of spans to fetch
            
        Returns:
            List of all spans
        """
        all_spans = []
        cursor = None
        started = time.time()
        page = 0
        
        while len(all_spans) < max_spans:
            page += 1
            response = self.get_spans(
                project_id=project_id,
                # Prefer server-side filtering; get_spans will retry without it if Phoenix rejects the filter.
                start_time=start_time,
                end_time=end_time,
                cursor=cursor,
                limit=min(1000, max_spans - len(all_spans))
            )
            
            spans = response.get('data', [])
            if not spans:
                break
            
            # Apply client-side time filtering
            filtered_spans = spans
            if start_time or end_time:
                filtered_spans = []
                for span in spans:
                    span_time_str = span.get('start_time', '')
                    if not span_time_str:
                        continue
                    
                    try:
                        # Parse ISO format datetime (timezone-aware)
                        span_time = pd.to_datetime(span_time_str)
                        
                        # Convert filter times to timezone-aware if span_time is timezone-aware
                        filter_start = start_time
                        filter_end = end_time
                        
                        if span_time.tz is not None:
                            # Span time is timezone-aware, make filter times aware too
                            if filter_start and filter_start.tzinfo is None:
                                # Assume UTC if not specified
                                from datetime import timezone
                                filter_start = filter_start.replace(tzinfo=timezone.utc)
                            if filter_end and filter_end.tzinfo is None:
                                from datetime import timezone
                                filter_end = filter_end.replace(tzinfo=timezone.utc)
                        else:
                            # Span time is naive, make filter times naive
                            if filter_start and filter_start.tzinfo is not None:
                                filter_start = filter_start.replace(tzinfo=None)
                            if filter_end and filter_end.tzinfo is not None:
                                filter_end = filter_end.replace(tzinfo=None)
                        
                        # Apply filters
                        if filter_start and span_time < filter_start:
                            continue
                        if filter_end and span_time > filter_end:
                            continue
                        
                        filtered_spans.append(span)
                    except Exception as e:
                        # If parsing fails, log and skip the span
                        logger.debug(f"Failed to parse span time {span_time_str}: {e}")
                        continue
            
            all_spans.extend(filtered_spans)
            cursor = response.get('next_cursor')
            
            if not cursor:
                break
            
            elapsed = time.time() - started
            logger.info(
                f"Fetched {len(all_spans)} spans so far... "
                f"(page={page}, elapsed={elapsed:.1f}s, cursor={'set' if cursor else 'none'})"
            )
            if elapsed > 60 and page % 5 == 0:
                logger.warning(
                    f"Span fetch running long: {elapsed:.1f}s elapsed, {len(all_spans)} spans fetched (page={page})."
                )
        
        return all_spans[:max_spans]
    
    def get_trace(self, trace_id: str) -> Dict:
        """Get a specific trace by ID"""
        try:
            response = self._make_request('GET', f'/v1/traces/{trace_id}')
            return response
        except Exception as e:
            logger.error(f"Failed to fetch trace {trace_id}: {e}")
            return {}
    
    def get_datasets(self) -> List[Dict]:
        """Get all datasets"""
        try:
            response = self._make_request('GET', '/v1/datasets')
            return response.get('data', [])
        except Exception as e:
            logger.error(f"Failed to fetch datasets: {e}")
            return []
    
    def search_spans(
        self,
        query: str,
        project_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search spans by text query
        
        Args:
            query: Search query text
            project_id: Optional project ID to filter by
            limit: Maximum number of results
            
        Returns:
            List of matching spans
        """
        params = {
            'query': query,
            'limit': limit
        }
        
        if project_id:
            params['project_id'] = project_id
        
        try:
            response = self._make_request('GET', '/v1/spans/search', params=params)
            return response.get('data', [])
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
