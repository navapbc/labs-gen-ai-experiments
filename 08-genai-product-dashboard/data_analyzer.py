"""
Data Analysis Module
Processes and analyzes Phoenix trace data
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Set
from datetime import datetime
from collections import Counter, defaultdict
import logging
import json
import re

logger = logging.getLogger(__name__)

# Users to exclude from *all* trace counts/analytics (internal/testing).
# - Any @navapbc.* email
# - Specific known test/admin accounts
EXCLUDED_USER_EMAILS: Set[str] = {
    'kasminscott@gmail.com',
    'nava.product@gwctx.com',
    'excluded.user@gwctx.org',
}

NAVAPBC_EMAIL_DOMAIN_PATTERN = r'@navapbc\.[a-z0-9.-]+$'


class TraceAnalyzer:
    """Analyzes trace data from Phoenix"""
    
    def __init__(
        self,
        spans: List[Dict],
        exclude_user_emails: Optional[Set[str]] = None,
        exclude_navapbc_domain: bool = True,
    ):
        """Initialize analyzer with spans data"""
        self.spans = spans
        self.df = self._create_dataframe(spans)
        self.traces_df = self._create_traces_dataframe(spans)
        self._apply_excluded_user_filter(
            exclude_user_emails=exclude_user_emails,
            exclude_navapbc_domain=exclude_navapbc_domain,
        )

    def _apply_excluded_user_filter(
        self,
        exclude_user_emails: Optional[Set[str]] = None,
        exclude_navapbc_domain: bool = True,
    ) -> None:
        """
        Remove internal/test users from all analytics by dropping entire traces (trace_id)
        whose user_email matches the exclusion list.
        """
        if self.traces_df is None or self.traces_df.empty:
            return
        if 'user_email' not in self.traces_df.columns or 'trace_id' not in self.traces_df.columns:
            return

        excluded_emails = {e.lower().strip() for e in (exclude_user_emails or set())}
        excluded_emails |= {e.lower() for e in EXCLUDED_USER_EMAILS}

        emails = self.traces_df['user_email'].astype(str).str.lower().str.strip()
        is_excluded = emails.isin(excluded_emails)
        if exclude_navapbc_domain:
            is_excluded = is_excluded | emails.str.contains(
                NAVAPBC_EMAIL_DOMAIN_PATTERN, regex=True, na=False
            )

        if not bool(is_excluded.any()):
            return

        excluded_trace_ids = set(
            self.traces_df.loc[is_excluded, 'trace_id'].dropna().astype(str)
        )
        if not excluded_trace_ids:
            return

        traces_before = len(self.traces_df)
        self.traces_df = self.traces_df[
            ~self.traces_df['trace_id'].astype(str).isin(excluded_trace_ids)
        ].copy()

        if self.df is not None and not self.df.empty and 'trace_id' in self.df.columns:
            self.df = self.df[
                ~self.df['trace_id'].astype(str).isin(excluded_trace_ids)
            ].copy()

        spans_before = len(self.spans) if self.spans else 0
        self.spans = [
            s for s in (self.spans or [])
            if str(s.get('trace_id', '')) not in excluded_trace_ids
        ]

        logger.info(
            'Excluded %s traces (%s spans) for internal/test users',
            traces_before - len(self.traces_df),
            spans_before - len(self.spans),
        )
    
    def _create_dataframe(self, spans: List[Dict]) -> pd.DataFrame:
        """Convert spans to pandas DataFrame for analysis"""
        if not spans:
            return pd.DataFrame()
        
        processed_spans = []
        for span in spans:
            processed = {
                'span_id': span.get('span_id', span.get('id', '')),
                'trace_id': span.get('trace_id', ''),
                'name': span.get('name', ''),
                'span_kind': span.get('span_kind', ''),
                'status_code': span.get('status_code', ''),
                'start_time': span.get('start_time', ''),
                'end_time': span.get('end_time', ''),
                'parent_id': span.get('parent_id', ''),
            }
            
            # Extract attributes
            attributes = span.get('attributes', {})
            processed['input'] = attributes.get('input', attributes.get('llm.input_messages', ''))
            processed['output'] = attributes.get('output', attributes.get('llm.output_messages', ''))
            processed['model'] = attributes.get('llm.model_name', attributes.get('model', ''))
            processed['token_count_prompt'] = attributes.get('llm.token_count.prompt', 0)
            processed['token_count_completion'] = attributes.get('llm.token_count.completion', 0)
            processed['token_count_total'] = attributes.get('llm.token_count.total', 0)
            
            # Extract latency (in seconds)
            if processed['start_time'] and processed['end_time']:
                try:
                    start = pd.to_datetime(processed['start_time'])
                    end = pd.to_datetime(processed['end_time'])
                    processed['latency_s'] = (end - start).total_seconds()
                except Exception:
                    processed['latency_s'] = None
            else:
                processed['latency_s'] = None
            
            processed_spans.append(processed)
        
        df = pd.DataFrame(processed_spans)
        
        # Convert timestamps
        if 'start_time' in df.columns:
            df['start_time'] = pd.to_datetime(df['start_time'], errors='coerce')
        if 'end_time' in df.columns:
            df['end_time'] = pd.to_datetime(df['end_time'], errors='coerce')
        
        return df
    
    def get_user_facing_traces(self) -> pd.DataFrame:
        """
        Return traces that represent actual user questions (what users experience).
        Filters out traces without a real query/user and without a positive duration.
        """
        if self.traces_df is None or self.traces_df.empty:
            return pd.DataFrame()

        df = self.traces_df.copy()

        # Query must exist and not be placeholder "."
        if 'query' in df.columns:
            q = df['query'].astype(str).str.strip()
            query_ok = (q != '') & (q != '.')
        else:
            query_ok = pd.Series(True, index=df.index)

        # User must be present (avoid unknown_* placeholders)
        if 'user_email' in df.columns:
            ue = df['user_email'].astype(str).str.strip().str.lower()
            user_ok = (~ue.str.startswith('unknown_')) & (ue != 'unknown') & (ue != '')
        else:
            user_ok = pd.Series(True, index=df.index)

        # Duration must be positive
        if 'trace_duration_s' in df.columns:
            d = pd.to_numeric(df['trace_duration_s'], errors='coerce')
            duration_ok = d.notna() & (d > 0)
        else:
            duration_ok = pd.Series(True, index=df.index)

        return df[query_ok & user_ok & duration_ok].copy()
    
    def get_macro_statistics(self) -> Dict:
        """Calculate high-level statistics for leadership reporting"""
        if self.traces_df is None or self.traces_df.empty:
            return {}
        
        user_facing = self.get_user_facing_traces()
        latency_source = user_facing if not user_facing.empty else self.traces_df
        durations = pd.to_numeric(latency_source.get('trace_duration_s'), errors='coerce')
        durations = durations.dropna()
        durations = durations[durations > 0]
        
        # Count traces by type (referrals vs action plans vs email_results)
        trace_counts = {'referrals': 0, 'action_plans': 0, 'email_results': 0, 'other': 0}
        if 'trace_type' in self.traces_df.columns:
            counts = self.traces_df['trace_type'].fillna('other').value_counts().to_dict()
            for k in trace_counts.keys():
                trace_counts[k] = int(counts.get(k, 0))
            known = set(trace_counts.keys())
            trace_counts['other'] += int(sum(v for t, v in counts.items() if t not in known))
        
        stats = {
            # NOTE: historically this key was span-level; we now treat it as trace-level
            # (the unit that users experience end-to-end).
            'total_requests': len(self.traces_df),
            'unique_traces': self.traces_df['trace_id'].nunique() if 'trace_id' in self.traces_df.columns else 0,
            'trace_counts': trace_counts,
            'date_range': {
                'start': self.traces_df['trace_start'].min() if 'trace_start' in self.traces_df.columns else None,
                'end': self.traces_df['trace_start'].max() if 'trace_start' in self.traces_df.columns else None
            },
            # Latency is computed at trace-level (end-to-end) and filtered to user-facing traces when possible.
            'avg_latency_s': float(durations.mean()) if len(durations) else 0,
            'median_latency_s': float(durations.median()) if len(durations) else 0,
            'p95_latency_s': float(durations.quantile(0.95)) if len(durations) else 0,
            'p99_latency_s': float(durations.quantile(0.99)) if len(durations) else 0,
            'total_tokens': int(self.traces_df['total_tokens'].sum()) if 'total_tokens' in self.traces_df.columns else 0,
            'avg_tokens_per_request': float(self.traces_df['total_tokens'].mean()) if 'total_tokens' in self.traces_df.columns else 0,
            'error_rate': (self.traces_df['status'] == 'ERROR').sum() / len(self.traces_df) * 100 if 'status' in self.traces_df.columns else 0,
            'success_rate': (self.traces_df['status'] == 'OK').sum() / len(self.traces_df) * 100 if 'status' in self.traces_df.columns else 0,
            'user_facing_traces': len(user_facing)
        }
        
        # Model usage
        if 'model' in self.df.columns:
            stats['models_used'] = self.df['model'].value_counts().to_dict()
        
        return stats
    
    def get_time_series_data(self, freq: str = 'H') -> pd.DataFrame:
        """
        Get time series data for visualization
        
        Args:
            freq: Frequency for grouping ('H' for hourly, 'D' for daily, etc.)
        """
        if self.df.empty or 'start_time' not in self.df.columns:
            return pd.DataFrame()
        
        df_time = self.df.set_index('start_time')
        
        time_series = df_time.groupby(pd.Grouper(freq=freq)).agg({
            'span_id': 'count',
            'latency_s': ['mean', 'median'],
            'token_count_total': 'sum'
        }).reset_index()
        
        time_series.columns = ['timestamp', 'request_count', 'avg_latency', 'median_latency', 'total_tokens']
        
        return time_series
    
    def get_latency_distribution(self) -> Dict:
        """Get latency distribution data"""
        if self.traces_df is None or self.traces_df.empty:
            return {}
        
        user_facing = self.get_user_facing_traces()
        source = user_facing if not user_facing.empty else self.traces_df

        if 'trace_duration_s' not in source.columns:
            return {}

        latency_data = pd.to_numeric(source['trace_duration_s'], errors='coerce').dropna()
        latency_data = latency_data[latency_data > 0]
        
        if latency_data.empty:
            return {}
        
        return {
            'min': latency_data.min(),
            'max': latency_data.max(),
            'mean': latency_data.mean(),
            'median': latency_data.median(),
            'std': latency_data.std(),
            'percentiles': {
                'p50': latency_data.quantile(0.50),
                'p75': latency_data.quantile(0.75),
                'p90': latency_data.quantile(0.90),
                'p95': latency_data.quantile(0.95),
                'p99': latency_data.quantile(0.99),
            },
            'histogram': latency_data.tolist(),
            'population': 'user_facing' if not user_facing.empty else 'all_traces'
        }
    
    def get_error_analysis(self) -> Dict:
        """Analyze errors and failures"""
        if self.df.empty:
            return {}
        
        error_df = self.df[self.df['status_code'] == 'ERROR']
        
        return {
            'total_errors': len(error_df),
            'error_rate': len(error_df) / len(self.df) * 100 if len(self.df) > 0 else 0,
            'errors_by_type': error_df['name'].value_counts().to_dict() if 'name' in error_df.columns else {},
            'errors_over_time': error_df.groupby(pd.Grouper(key='start_time', freq='D')).size().to_dict() if 'start_time' in error_df.columns else {}
        }
    
    def get_quality_insights(self) -> pd.DataFrame:
        """
        Get data for qualitative analysis
        Returns dataframe with prompts, outputs, and metadata for review
        """
        if self.df.empty:
            return pd.DataFrame()
        
        quality_df = self.df[[
            'span_id', 'trace_id', 'start_time', 'name', 
            'input', 'output', 'model', 'latency_s', 
            'token_count_total', 'status_code'
        ]].copy()
        
        # Add derived metrics for quality assessment
        if 'output' in quality_df.columns:
            quality_df['output_length'] = quality_df['output'].astype(str).str.len()
        
        if 'latency_s' in quality_df.columns:
            # Flag slow responses
            quality_df['is_slow'] = quality_df['latency_s'] > quality_df['latency_s'].quantile(0.90)
        
        return quality_df
    
    def search_interactions(self, query: str) -> pd.DataFrame:
        """
        Search through prompts and outputs
        
        Args:
            query: Search term
        """
        if self.df.empty:
            return pd.DataFrame()
        
        mask = (
            self.df['input'].astype(str).str.contains(query, case=False, na=False) |
            self.df['output'].astype(str).str.contains(query, case=False, na=False)
        )
        
        return self.df[mask]
    
    def get_token_usage_analysis(self) -> Dict:
        """Analyze token usage patterns"""
        if self.df.empty:
            return {}
        
        return {
            'total_tokens': self.df['token_count_total'].sum(),
            'total_prompt_tokens': self.df['token_count_prompt'].sum(),
            'total_completion_tokens': self.df['token_count_completion'].sum(),
            'avg_tokens_per_request': self.df['token_count_total'].mean(),
            'median_tokens_per_request': self.df['token_count_total'].median(),
            'max_tokens_single_request': self.df['token_count_total'].max(),
            'tokens_by_model': self.df.groupby('model')['token_count_total'].sum().to_dict() if 'model' in self.df.columns else {}
        }
    
    def get_model_performance_comparison(self) -> pd.DataFrame:
        """Compare performance across different models"""
        if self.df.empty or 'model' not in self.df.columns:
            return pd.DataFrame()
        
        comparison = self.df.groupby('model').agg({
            'span_id': 'count',
            'latency_s': ['mean', 'median'],
            'token_count_total': ['mean', 'sum'],
            'status_code': lambda x: (x == 'ERROR').sum()
        }).reset_index()
        
        comparison.columns = [
            'model', 'total_requests', 'avg_latency', 'median_latency',
            'avg_tokens', 'total_tokens', 'error_count'
        ]
        
        if len(comparison) > 0:
            comparison['error_rate'] = (comparison['error_count'] / comparison['total_requests'] * 100).round(2)
        
        return comparison

    def _extract_user_email_from_spans(
        self, trace_spans: List[Dict], root_attrs: Dict
    ) -> str:
        """
        Extract user email from trace spans, searching through multiple locations.
        Returns 'unknown_<trace_id>' if no email found.
        """
        # Get trace_id for fallback
        trace_id = trace_spans[0].get('trace_id', 'unknown') if trace_spans else 'unknown'
        
        # Try to find email in multiple locations across all spans
        email_candidates = []
        
        # 1. Check root span attributes first
        if isinstance(root_attrs, dict):
            email_candidates.extend(self._find_emails_in_attrs(root_attrs))
        
        # 2. Search through ALL spans in the trace
        for span in trace_spans:
            span_attrs = span.get('attributes', {})
            if isinstance(span_attrs, str):
                try:
                    span_attrs = json.loads(span_attrs)
                except Exception:
                    span_attrs = {}
            
            if isinstance(span_attrs, dict):
                email_candidates.extend(self._find_emails_in_attrs(span_attrs))
        
        # 3. Filter and prioritize candidates
        # Prefer non-test emails, prioritize known domains
        valid_emails = []
        for email in email_candidates:
            if not email or not isinstance(email, str):
                continue
            email = email.strip().lower()
            if '@' not in email:
                continue
            # Skip obvious non-emails
            if email.startswith('unknown_'):
                continue
            valid_emails.append(email)
        
        if valid_emails:
            # Prioritize known pilot domains
            priority_domains = ['gwctx.org', 'yourgoodwill.org']
            for domain in priority_domains:
                for email in valid_emails:
                    if domain in email:
                        return email
            # Return first valid email
            return valid_emails[0]
        
        return f'unknown_{trace_id[:8]}'

    def _find_emails_in_attrs(self, attrs: Dict) -> List[str]:
        """Find all potential email values in an attributes dict."""
        emails = []
        
        if not isinstance(attrs, dict):
            return emails
        
        # Direct email fields
        for key in ['user_email', 'email', 'user_id', 'userId', 'userEmail']:
            val = attrs.get(key)
            if val and isinstance(val, str) and '@' in val:
                emails.append(val)
        
        # Nested in 'user' dict
        user_info = attrs.get('user', {})
        if isinstance(user_info, dict):
            for key in ['email', 'id', 'user_email', 'userId']:
                val = user_info.get(key)
                if val and isinstance(val, str) and '@' in val:
                    emails.append(val)
        elif isinstance(user_info, str) and '@' in user_info:
            emails.append(user_info)
        
        # Nested in 'metadata' dict
        metadata = attrs.get('metadata', {})
        if isinstance(metadata, dict):
            for key in ['user_email', 'user_id', 'email', 'userId', 'userEmail']:
                val = metadata.get(key)
                if val and isinstance(val, str) and '@' in val:
                    emails.append(val)
        
        # Check input.value for JSON with user_email
        input_data = attrs.get('input', {})
        if isinstance(input_data, dict):
            input_value = input_data.get('value', '')
            if isinstance(input_value, str) and input_value:
                emails.extend(self._extract_emails_from_json_string(input_value))
        
        # Check output.value as well
        output_data = attrs.get('output', {})
        if isinstance(output_data, dict):
            output_value = output_data.get('value', '')
            if isinstance(output_value, str) and output_value:
                emails.extend(self._extract_emails_from_json_string(output_value))
        
        # Direct input/output string values
        for key in ['input', 'output']:
            val = attrs.get(key)
            if isinstance(val, str) and val:
                emails.extend(self._extract_emails_from_json_string(val))
        
        return emails

    def _extract_emails_from_json_string(self, text: str) -> List[str]:
        """Extract email addresses from a JSON string."""
        emails = []
        
        # Try to parse as JSON first
        try:
            if text.strip().startswith('{') or text.strip().startswith('['):
                parsed = json.loads(text)
                emails.extend(self._find_emails_in_parsed_json(parsed))
        except Exception:
            pass
        
        # Also search for email patterns in the raw text
        email_pattern = r'[\w.-]+@[\w.-]+\.\w+'
        found = re.findall(email_pattern, text)
        for email in found:
            # Filter out common false positives
            if not any(x in email.lower() for x in ['example.com', 'test.com', 'placeholder']):
                emails.append(email)
        
        return emails

    def _find_emails_in_parsed_json(self, obj, depth: int = 0) -> List[str]:
        """Recursively find emails in parsed JSON objects."""
        emails = []
        if depth > 10:  # Prevent infinite recursion
            return emails
        
        if isinstance(obj, dict):
            for key, val in obj.items():
                # Check common email field names
                if key.lower() in ['user_email', 'email', 'user_id', 'userid', 'useremail']:
                    if isinstance(val, str) and '@' in val:
                        emails.append(val)
                # Recurse into nested objects
                if isinstance(val, (dict, list)):
                    emails.extend(self._find_emails_in_parsed_json(val, depth + 1))
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    emails.extend(self._find_emails_in_parsed_json(item, depth + 1))
        
        return emails
    
    def _create_traces_dataframe(self, spans: List[Dict]) -> pd.DataFrame:
        """
        Create a DataFrame with trace-level data including user information
        Groups spans by trace_id and extracts user-level metrics
        """
        if not spans:
            return pd.DataFrame()
        
        # Group spans by trace_id
        traces = defaultdict(list)
        for span in spans:
            trace_id = span.get('trace_id', '')
            if trace_id:
                traces[trace_id].append(span)
        
        trace_records = []
        
        for trace_id, trace_spans in traces.items():
            # Find root span (spans with no parent_id or parent_id not in the trace)
            span_ids = {s.get('span_id', '') for s in trace_spans}
            root_spans = []
            for s in trace_spans:
                parent_id = s.get('parent_id', '')
                if not parent_id or parent_id not in span_ids:
                    root_spans.append(s)
            
            if not root_spans:
                continue
            
            root_span = root_spans[0]
            attrs = root_span.get('attributes', {})
            
            # Extract user information - search through multiple locations
            user_email = self._extract_user_email_from_spans(trace_spans, attrs)
            
            # Extract trace type
            root_name = root_span.get('name', '').lower()
            trace_type = 'other'
            if 'referral' in root_name:
                trace_type = 'referrals'
            elif 'action' in root_name and 'plan' in root_name:
                trace_type = 'action_plans'
            elif 'email' in root_name and 'result' in root_name:
                trace_type = 'email_results'
            elif root_name == 'pipeline.run':
                # Legacy Pipeline.run traces - categorize based on whether they have a query
                # If has query text -> referral search, if no query -> action plan
                has_query = False
                input_data = attrs.get('input', {})
                if isinstance(input_data, dict):
                    input_value = input_data.get('value', '')
                    if isinstance(input_value, str):
                        try:
                            parsed = json.loads(input_value)
                            if isinstance(parsed, dict):
                                messages = parsed.get('data', {}).get('logger', {}).get('messages_list', [])
                                if messages and isinstance(messages[0], dict):
                                    query_text = messages[0].get('query', '').strip()
                                    # Check if it's a real query (not just whitespace or a period)
                                    if query_text and query_text not in ['.', '']:
                                        has_query = True
                        except Exception:
                            pass
                trace_type = 'referrals' if has_query else 'action_plans'
            
            # Gather query/category/location context from all spans in the trace
            context = self._extract_trace_context(trace_spans)
            query = context.get('query', '')
            category = context.get('categories', [])[0] if context.get('categories') else ''
            location_preference = context.get('location', '')
            zip_codes = context.get('zip_codes', []).copy()
            
            output_data = attrs.get('output', {})
            
            # Extract zip codes from output (resources have addresses with zip codes)
            if isinstance(output_data, dict):
                output_value = output_data.get('value', '')
                if isinstance(output_value, str) and output_value:
                    try:
                        parsed_output = json.loads(output_value)
                        if isinstance(parsed_output, dict):
                            # Look for resources in output
                            llm_data = parsed_output.get('llm', {})
                            if isinstance(llm_data, dict):
                                replies = llm_data.get('replies', [])
                                if replies:
                                    # Parse the ChatMessage string to extract JSON
                                    reply_str = str(replies[0])
                                    
                                    # Find where JSON starts and ends
                                    start_idx = reply_str.find('{"resources"')
                                    if start_idx < 0:
                                        start_idx = reply_str.find('{"resource_type"')
                                    
                                    if start_idx >= 0:
                                        # Find matching closing brace
                                        end_idx = reply_str.rfind('}')
                                        if end_idx > start_idx:
                                            json_str = reply_str[start_idx:end_idx+1]
                                            
                                            # Clean up escaped characters
                                            json_str = json_str.replace('\\n', ' ').replace('\\"', '"')
                                            
                                            try:
                                                resources_data = json.loads(json_str)
                                                resources = resources_data.get('resources', [])
                                                
                                                # Extract zip codes from addresses
                                                zip_pattern = r'\b\d{5}\b'
                                                for resource in resources:
                                                    if isinstance(resource, dict):
                                                        addresses = resource.get('addresses', [])
                                                        for addr in addresses:
                                                            found_zips = re.findall(zip_pattern, str(addr))
                                                            zip_codes.extend(found_zips)
                                            except json.JSONDecodeError:
                                                # If parsing fails, try extracting zip codes directly from string
                                                zip_pattern = r'\b78\d{3}\b'  # Texas zip codes
                                                found_zips = re.findall(zip_pattern, reply_str)
                                                zip_codes.extend(found_zips)
                    except Exception as e:
                        logger.debug(f"Failed to parse output for zip codes: {e}")
            
            # Extract zip codes from query text as well
            if query:
                self._append_zip_from_text(query, zip_codes)
            
            # Categorize based on query if no explicit category selection was found
            if query and not category:
                query_lower = query.lower()
                # Comprehensive category keywords matching the UI categories
                category_keywords = {
                    'Employment & Job Training': [
                        'job', 'employment', 'work', 'career', 'hiring', 'higher-paying', 'higher paying', 'wage',
                        'cdl', 'cna', 'phlebotomy', 'medical assistant', 'janitorial', 'hospitality',
                        'drivers ed', 'driver education', 'driving school', 'drivers license', 'driver\'s license',
                        'job training', 'workforce', 'vocational', 'apprentice', 'internship',
                        'resume', 'interview', 'job search', 'career advancement', 'skill training',
                        'certification', 'gcta', 'ready to work', 'step program'
                    ],
                    'Housing & Homeless Support': [
                        'housing', 'apartment', 'rent', 'shelter', 'home', 'homeless', 'eviction', 'move-in', 'furniture',
                        'domestic violence', 'dv shelter', 'rental assistance', 'mortgage', 'foreclosure',
                        'transitional housing', 'supportive housing', 'affordable housing', 'housing voucher',
                        'section 8', 'utilities', 'electric bill', 'water bill', 'move in costs'
                    ],
                    'Food Assistance': [
                        'food', 'meal', 'groceries', 'hungry', 'hunger', 'snap', 'food bank', 'food pantry',
                        'pet food', 'home-delivered', 'meals on wheels', 'wic', 'feeding', 'nutrition',
                        'breakfast', 'lunch', 'dinner', 'food stamps', 'ebt'
                    ],
                    'Financial Assistance': [
                        'financial', 'money', 'debt', 'loan', 'student loan', 'student loans', 'credit',
                        'bankruptcy', 'financial help', 'financial aid', 'emergency funds', 'cash assistance',
                        'tanf', 'bill assistance', 'utility assistance', 'financial counseling', 'budgeting',
                        'emergency assistance', 'financial crisis', 'financial hardship', 'grants'
                    ],
                    'Healthcare & Mental Health': [
                        'health', 'medical', 'doctor', 'clinic', 'medicine', 'mental health', 'medication', 'healthcare',
                        'samaritan', 'map program', 'low-income clinic', 'therapy', 'counseling', 'dental',
                        'vision', 'prescription', 'hospital', 'insurance', 'medicaid', 'medicare',
                        'mental', 'depression', 'anxiety', 'psychiatric', 'emotional', 'wellness'
                    ],
                    'Education & GED': [
                        'education', 'school', 'ged', 'high school', 'diploma', 'esl', 'english classes',
                        'literacy', 'tutoring', 'college', 'university', 'scholarship', 'excel center',
                        'adult education', 'learning', 'study', 'academic'
                    ],
                    'Transportation': [
                        'transportation', 'bus', 'car', 'ride', 'transit', 'capital metro', 'carts',
                        'trip planning', 'bus route', 'bus pass', 'gas', 'gasoline', 'fuel',
                        'vehicle', 'auto', 'uber', 'lyft', 'rideshare'
                    ],
                    'Childcare & Family Support': [
                        'childcare', 'child care', 'daycare', 'day care', 'babysit', 'infant', 'toddler',
                        'parent support', 'family stability', 'after school', 'preschool', 'kids',
                        'children', 'parenting', 'family', 'child', 'baby', 'newborn'
                    ],
                    'Legal Services': [
                        'legal', 'lawyer', 'attorney', 'benefits issue', 'legal aid', 'court', 'law',
                        'eviction defense', 'family law', 'immigration', 'civil', 'criminal',
                        'expungement', 'legal help', 'legal advice', 'lawsuit', 'litigation',
                        'fraudulent claims', 'legal representation'
                    ],
                    'Substance Abuse Treatment': [
                        'substance', 'addiction', 'drug', 'alcohol', 'rehab', 'recovery', 'sobriety',
                        'substance abuse', 'drug treatment', 'alcohol treatment', 'detox', 'aa', 'na',
                        'sober', 'clean', 'addict', 'alcoholic', 'weed', 'marijuana', 'opioid'
                    ],
                    'Disability Services': [
                        'disability', 'disabled', 'handicap', 'wheelchair', 'accessibility', 'adaptive',
                        'special needs', 'developmental disability', 'intellectual disability',
                        'autism', 'blind', 'deaf', 'mobility', 'ssdi', 'ssi'
                    ],
                    'Veterans Services': [
                        'veteran', 'veterans', 'va', 'va benefits', 'military', 'army', 'navy', 'air force',
                        'marines', 'service member', 'gi bill', 'discharge', 'veteran housing'
                    ]
                }
                
                # Track all matching categories (some queries span multiple)
                matched_categories = []
                for cat, keywords in category_keywords.items():
                    if any(kw in query_lower for kw in keywords):
                        matched_categories.append(cat)
                
                # Use first match as primary category
                if matched_categories:
                    category = matched_categories[0]
            
            # Calculate trace-level metrics
            start_times = [pd.to_datetime(s.get('start_time', '')) for s in trace_spans if s.get('start_time')]
            end_times = [pd.to_datetime(s.get('end_time', '')) for s in trace_spans if s.get('end_time')]
            
            trace_start = min(start_times) if start_times else None
            trace_end = max(end_times) if end_times else None
            trace_duration = (trace_end - trace_start).total_seconds() if trace_start and trace_end else None
            
            # Count spans by type
            llm_spans = [s for s in trace_spans if 'llm' in str(s.get('span_kind', '')).lower()]

            def _coerce_int(value) -> int:
                """Best-effort coercion of Phoenix attribute values into ints."""
                if value is None:
                    return 0
                if isinstance(value, dict):
                    value = value.get('value', 0)
                try:
                    # Handles ints, floats, numpy scalars, and numeric strings
                    return int(float(value))
                except Exception:
                    return 0

            def _extract_span_total_tokens(span_obj: Dict) -> int:
                """Extract total token count from a span across multiple possible Phoenix schemas."""
                attrs_obj = span_obj.get('attributes', {})
                if not isinstance(attrs_obj, dict):
                    return 0

                # Common flat keys (what Phoenix often emits in this project)
                flat = (
                    attrs_obj.get('llm.token_count.total') or
                    attrs_obj.get('llm.token_count_total') or
                    attrs_obj.get('token_count_total')
                )
                flat_val = _coerce_int(flat)
                if flat_val:
                    return flat_val

                # Nested schema: {"llm": {"token_count": {"total": ...}}}
                llm_info = attrs_obj.get('llm', {})
                if isinstance(llm_info, dict):
                    token_count = llm_info.get('token_count', {})
                    if isinstance(token_count, dict):
                        return _coerce_int(token_count.get('total'))

                return 0

            # Extract token counts from spans.
            # Prefer LLM spans if they exist; otherwise fall back to any spans with token fields.
            token_source_spans = llm_spans if llm_spans else trace_spans
            total_tokens = 0
            for span in token_source_spans:
                total_tokens += _extract_span_total_tokens(span)

            # If token instrumentation isn't present, fall back to a rough estimate based on input/output size.
            # This is useful for correlating "bigger prompt/response" with "slower traces".
            tokens_estimated = False
            if total_tokens == 0:
                def _estimate_tokens_from_value(v) -> int:
                    if v is None:
                        return 0
                    if isinstance(v, dict):
                        v = v.get('value', v)
                    try:
                        text = str(v)
                    except Exception:
                        return 0
                    text = text.strip()
                    if not text:
                        return 0
                    # Heuristic: ~4 chars per token (varies by language/content).
                    return max(1, int(len(text) / 4))

                estimated = 0
                for span in trace_spans:
                    span_attrs = span.get('attributes', {})
                    if not isinstance(span_attrs, dict):
                        continue
                    estimated += _estimate_tokens_from_value(span_attrs.get('input'))
                    estimated += _estimate_tokens_from_value(span_attrs.get('output'))
                    # A few common alternates just in case:
                    estimated += _estimate_tokens_from_value(span_attrs.get('llm.input_messages'))
                    estimated += _estimate_tokens_from_value(span_attrs.get('llm.output_messages'))

                if estimated > 0:
                    total_tokens = estimated
                    tokens_estimated = True
            
            # Deduplicate zip codes before storing
            if zip_codes:
                seen_zips = set()
                deduped = []
                for z in zip_codes:
                    if z not in seen_zips:
                        deduped.append(z)
                        seen_zips.add(z)
                zip_codes = deduped
            
            # Get primary zip code (first one found)
            primary_zip = zip_codes[0] if zip_codes else ''
            
            trace_records.append({
                'trace_id': trace_id,
                'user_email': user_email,
                'user_name': user_email.split('@')[0] if user_email and '@' in user_email else 'unknown',
                'trace_type': trace_type,
                'trace_start': trace_start,
                'trace_end': trace_end,
                'trace_duration_s': trace_duration,
                'span_count': len(trace_spans),
                'llm_span_count': len(llm_spans),
                'total_tokens': total_tokens,
                'tokens_estimated': tokens_estimated,
                'query': query[:500] if query else '',  # Limit query length
                'category': category,
                'zip_code': primary_zip,
                'all_zip_codes': ','.join(zip_codes[:5]) if zip_codes else '',  # Store up to 5 zips
                'location_preference': location_preference,
                'status': root_span.get('status_code', 'UNKNOWN')
            })
        
        if not trace_records:
            return pd.DataFrame()
        
        df = pd.DataFrame(trace_records)
        
        # Convert timestamps
        if 'trace_start' in df.columns:
            df['trace_start'] = pd.to_datetime(df['trace_start'], errors='coerce')
        if 'trace_end' in df.columns:
            df['trace_end'] = pd.to_datetime(df['trace_end'], errors='coerce')
        
        return df

    def _parse_attribute_payload(self, attribute_value):
        """
        Normalize Phoenix attribute payloads (which may be nested dicts or JSON strings)
        into Python dictionaries for easier parsing.
        """
        if not attribute_value:
            return None
        
        if isinstance(attribute_value, dict):
            value = attribute_value.get('value', attribute_value)
        else:
            value = attribute_value
        
        if isinstance(value, dict):
            return value
        
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            try:
                return json.loads(text)
            except Exception:
                return None
        
        return None
    
    def _extract_context_from_payload(self, payload: Dict) -> Dict[str, List[str]]:
        """
        Walk potentially nested payloads to find query/category/location hints.
        """
        context = {
            'queries': [],
            'categories': [],
            'locations': []
        }
        
        def add_unique(target: List[str], value):
            if not value:
                return
            if isinstance(value, str):
                candidate = value.strip()
                if candidate and candidate not in target:
                    target.append(candidate)
            elif isinstance(value, list):
                for item in value:
                    add_unique(target, item)
        
        def visit(obj, depth=0):
            if depth > 4 or obj is None:
                return
            
            if isinstance(obj, dict):
                # Common keys for queries
                add_unique(context['queries'], obj.get('user_query'))
                add_unique(context['queries'], obj.get('query'))
                add_unique(context['queries'], obj.get('client_query'))
                add_unique(context['queries'], obj.get('prompt'))
                
                # Category selectors
                add_unique(context['categories'], obj.get('category'))
                add_unique(context['categories'], obj.get('categories'))
                add_unique(context['categories'], obj.get('selected_categories'))
                add_unique(context['categories'], obj.get('resource_categories'))
                add_unique(context['categories'], obj.get('focus_area'))
                add_unique(context['categories'], obj.get('resource_type'))
                
                # Location / zip hints
                add_unique(context['locations'], obj.get('location'))
                add_unique(context['locations'], obj.get('location_preference'))
                add_unique(context['locations'], obj.get('location_preferences'))
                add_unique(context['locations'], obj.get('zip_code'))
                add_unique(context['locations'], obj.get('zipcode'))
                add_unique(context['locations'], obj.get('zip'))
                
                # Follow nested structures likely to hold useful info
                for key in ['kwargs', 'data', 'logger', 'messages_list', 'filters', 'request', 'payload']:
                    if key in obj:
                        visit(obj[key], depth + 1)
            
            elif isinstance(obj, list):
                for item in obj:
                    visit(item, depth + 1)
        
        visit(payload)
        return context
    
    def _append_zip_from_text(self, text: str, zip_list: List[str]):
        """Extract ZIP codes from free text and append to a list without duplicates."""
        if not isinstance(text, str):
            return
        
        matches = re.findall(r'\b\d{5}\b', text)
        for match in matches:
            if match not in zip_list:
                zip_list.append(match)
    
    def _infer_category_from_resources(self, resources_text: str) -> str:
        """
        Infer the primary resource category from action plan resource descriptions.
        Action plans don't have explicit user queries, but we can deduce the category
        from the types of resources selected.
        """
        if not resources_text:
            return ''
        
        text_lower = resources_text.lower()
        
        # Category detection based on resource keywords (weighted by specificity)
        category_scores = {}
        
        category_keywords = {
            'Employment & Job Training': [
                'employment program', 'job training', 'ready to work', 'step program',
                'workforce development', 'job placement', 'career training', 'vocational',
                'job readiness', 'occupational training', 'internship', 'apprentice',
                'drivers ed', 'cdl', 'cna', 'certification program'
            ],
            'Housing & Homeless Support': [
                'housing', 'shelter', 'homeless', 'rental assistance', 'supportive housing',
                'transitional housing', 'affordable housing', 'rental', 'eviction', 'move-in'
            ],
            'Food Assistance': [
                'food bank', 'food pantry', 'meals', 'nutrition', 'snap', 'wic',
                'food assistance', 'feeding', 'groceries'
            ],
            'Financial Assistance': [
                'financial assistance', 'emergency funds', 'bill assistance', 'debt',
                'loan', 'financial help', 'grants', 'financial support'
            ],
            'Healthcare & Mental Health': [
                'health', 'medical', 'clinic', 'mental health', 'therapy', 'counseling',
                'healthcare', 'medication', 'prescription', 'dental', 'vision'
            ],
            'Education & GED': [
                'education', 'ged', 'high school', 'diploma', 'esl', 'tutoring',
                'college', 'scholarship', 'excel center', 'adult education'
            ],
            'Transportation': [
                'transportation', 'bus pass', 'transit', 'capital metro', 'ride',
                'vehicle', 'gas assistance'
            ],
            'Childcare & Family Support': [
                'childcare', 'child care', 'daycare', 'parenting', 'family support',
                'infant care', 'preschool'
            ],
            'Legal Services': [
                'legal', 'attorney', 'lawyer', 'legal aid', 'court', 'immigration',
                'legal services', 'legal assistance'
            ],
            'Substance Abuse Treatment': [
                'substance abuse', 'addiction', 'recovery', 'rehab', 'treatment',
                'sobriety', 'drug treatment', 'alcohol treatment'
            ],
            'Disability Services': [
                'disability', 'disabilities', 'disabled', 'adaptive', 'accessibility',
                'special needs', 'developmental disability'
            ],
            'Veterans Services': [
                'veteran', 'va benefits', 'military', 'service member'
            ]
        }
        
        # Count keyword matches for each category
        for category, keywords in category_keywords.items():
            score = 0
            for keyword in keywords:
                # Count occurrences (resources may mention the same keyword multiple times)
                count = text_lower.count(keyword)
                if count > 0:
                    # Weight longer/more specific keywords higher
                    weight = len(keyword.split())
                    score += count * weight
            
            if score > 0:
                category_scores[category] = score
        
        # Return category with highest score
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        
        return ''
    
    def _extract_location_names(self, text: str) -> List[str]:
        """
        Extract city/location names from text.
        Looks for common Central Texas cities and location patterns.
        """
        if not text:
            return []
        
        text_lower = text.lower()
        locations = []
        
        # Common Central Texas cities and areas
        known_locations = [
            'austin', 'round rock', 'georgetown', 'pflugerville', 'cedar park',
            'leander', 'hutto', 'manor', 'del valle', 'buda', 'kyle', 'san marcos',
            'bastrop', 'lockhart', 'marble falls', 'lago vista', 'jonestown',
            'dripping springs', 'bee cave', 'lakeway', 'west lake hills',
            'lancaster', 'virginia beach'  # Out of region mentions
        ]
        
        for loc in known_locations:
            if loc in text_lower:
                # Capitalize properly
                locations.append(loc.title())
        
        # Look for patterns like "in [City]", "near [City]", "at [City]", "[City], Texas", "[City] Texas"
        # Common patterns: "Kyle Texas", "city limits of Kyle", "within Kyle"
        city_patterns = [
            r'\b(?:in|near|at|within|around)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+Texas\b',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*(?:TX|Texas)\b',
            r'\bcity\s+limits\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
        ]
        
        for pattern in city_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match and match not in locations:
                    # Filter out common non-location words
                    if match.lower() not in ['texas', 'include', 'focus', 'resources', 'following', 'support']:
                        locations.append(match)
        
        return locations
    
    def _extract_trace_context(self, trace_spans: List[Dict]) -> Dict[str, List[str]]:
        """
        Combine context clues from every span in the trace to capture user query,
        selected categories, and preferred locations.
        """
        context = {
            'query': '',
            'categories': [],
            'location': '',
            'zip_codes': []
        }
        
        if not trace_spans:
            return context
        
        for span in trace_spans:
            attrs = span.get('attributes', {})
            if not isinstance(attrs, dict):
                continue
            
            # Parse inputs for rich context
            payload = self._parse_attribute_payload(attrs.get('input'))
            if payload:
                payload_context = self._extract_context_from_payload(payload)
                
                if payload_context['queries'] and not context['query']:
                    context['query'] = payload_context['queries'][0]
                
                for cat in payload_context['categories']:
                    if cat not in context['categories']:
                        context['categories'].append(cat)
                
                for loc in payload_context['locations']:
                    self._append_zip_from_text(loc, context['zip_codes'])
                if payload_context['locations'] and not context['location']:
                    context['location'] = payload_context['locations'][0]
                
                for q in payload_context['queries']:
                    self._append_zip_from_text(q, context['zip_codes'])
            
            # For action plans, extract category from resources
            if span.get('name') == 'Pipeline.run' and not context['categories']:
                if payload and isinstance(payload, dict):
                    data = payload.get('data', {})
                    if isinstance(data, dict):
                        prompt_builder = data.get('prompt_builder', {})
                        if isinstance(prompt_builder, dict):
                            resources_text = str(prompt_builder.get('resources', ''))
                            if resources_text:
                                # Infer category from resource names/descriptions
                                inferred_cat = self._infer_category_from_resources(resources_text)
                                if inferred_cat and inferred_cat not in context['categories']:
                                    context['categories'].append(inferred_cat)
            
            # Metadata may also include filters from the UI
            metadata = attrs.get('metadata', {})
            if isinstance(metadata, dict):
                if not context['location']:
                    for key in ['location', 'location_preference', 'zip_code', 'zipcode']:
                        if metadata.get(key):
                            context['location'] = str(metadata[key]).strip()
                            self._append_zip_from_text(context['location'], context['zip_codes'])
                            break
                meta_category = metadata.get('resource_category') or metadata.get('category')
                if meta_category and meta_category not in context['categories']:
                    context['categories'].append(str(meta_category).strip())
        
        # Derive hints directly from the combined query text when structured filters are missing
        if context['query']:
            # Extract explicit location mentions from UI-injected text
            # Patterns: "Focus on resources close to the following location: X"
            # or "within the city limits of X" or "near X"
            location_patterns = [
                r'(?:close to the following location|location|zip|area):\s*([^\n]+)',
                r'(?:within|in|near)\s+(?:the\s+)?(?:city\s+limits\s+of\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:\s+Texas)?)',
                r'Focus on resources close to[^:]*:\s*(\d{5})',
            ]
            
            for pattern in location_patterns:
                location_match = re.search(pattern, context['query'], re.IGNORECASE)
                if location_match:
                    loc = location_match.group(1).strip()
                    # Remove trailing text like "Include resources..."
                    loc = re.sub(r'\s+(Include|Focus).*$', '', loc, flags=re.IGNORECASE)
                    if loc and not context['location']:
                        context['location'] = loc
                        self._append_zip_from_text(loc, context['zip_codes'])
                        break
            
            # Extract city names from the query text if no explicit location found
            if not context['location']:
                location_names = self._extract_location_names(context['query'])
                if location_names:
                    context['location'] = location_names[0]  # Use first found
            
            # Parse explicit category mentions from UI-injected text
            # Patterns: "Include resources that support the following categories: X"
            # or "categories: X"
            categories_patterns = [
                r'(?:support the following categories?|categories?):\s*([^\n]+)',
                r'Include resources that support[^:]+:\s*([A-Z][^\n]+)',
            ]
            
            for pattern in categories_patterns:
                categories_match = re.search(pattern, context['query'], re.IGNORECASE)
                if categories_match:
                    raw_categories = categories_match.group(1)
                    # Split on common delimiters
                    candidates = re.split(r',|/|;|\s+and\s+', raw_categories)
                    for candidate in candidates:
                        candidate = candidate.strip()
                        # Remove trailing "Include" or "Focus" text
                        candidate = re.sub(r'\s+(Include|Focus|location).*$', '', candidate, flags=re.IGNORECASE)
                        if candidate and candidate not in context['categories']:
                            context['categories'].append(candidate)
        
        # Deduplicate zip codes while preserving order
        seen = set()
        unique_zips = []
        for z in context['zip_codes']:
            if z not in seen:
                unique_zips.append(z)
                seen.add(z)
        context['zip_codes'] = unique_zips
        
        return context
    
    def get_user_analytics(self) -> pd.DataFrame:
        """
        Get user-level analytics aggregated from traces
        Returns DataFrame with user metrics
        """
        if self.traces_df.empty:
            return pd.DataFrame()
        
        user_stats = self.traces_df.groupby('user_email').agg({
            'trace_id': 'count',
            'trace_type': lambda x: {
                'referrals': (x == 'referrals').sum(),
                'action_plans': (x == 'action_plans').sum(),
                'email_results': (x == 'email_results').sum(),
                'other': (x == 'other').sum()
            },
            'trace_start': ['min', 'max'],
            'trace_duration_s': 'mean',
            'total_tokens': 'sum'
        }).reset_index()
        
        user_stats.columns = ['user_email', 'total_traces', 'trace_type_breakdown', 'first_trace', 'last_trace', 'avg_duration_s', 'total_tokens']
        
        # Extract user names
        user_stats['user_name'] = user_stats['user_email'].apply(
            lambda x: x.split('@')[0] if x and '@' in x else x
        )
        
        # Expand trace type breakdown
        user_stats['referrals_count'] = user_stats['trace_type_breakdown'].apply(lambda x: x.get('referrals', 0) if isinstance(x, dict) else 0)
        user_stats['action_plans_count'] = user_stats['trace_type_breakdown'].apply(lambda x: x.get('action_plans', 0) if isinstance(x, dict) else 0)
        user_stats['email_results_count'] = user_stats['trace_type_breakdown'].apply(lambda x: x.get('email_results', 0) if isinstance(x, dict) else 0)
        user_stats['other_count'] = user_stats['trace_type_breakdown'].apply(lambda x: x.get('other', 0) if isinstance(x, dict) else 0)
        
        # Sort by total traces descending
        user_stats = user_stats.sort_values('total_traces', ascending=False)
        
        return user_stats[['user_email', 'user_name', 'total_traces', 'referrals_count', 'action_plans_count', 'email_results_count', 'other_count', 
                           'first_trace', 'last_trace', 'avg_duration_s', 'total_tokens']]
    
    def get_trace_time_series(self, freq: str = 'H') -> pd.DataFrame:
        """
        Get time series data based on traces (not spans)
        
        Args:
            freq: Frequency for grouping ('H' for hourly, 'D' for daily, etc.)
        """
        if self.traces_df.empty or 'trace_start' not in self.traces_df.columns:
            return pd.DataFrame()
        
        df_time = self.traces_df.set_index('trace_start')
        
        # Aggregate basic metrics
        time_series = df_time.groupby(pd.Grouper(freq=freq)).agg({
            'trace_id': 'count',
            'trace_duration_s': 'mean',
            'total_tokens': 'sum'
        }).reset_index()
        
        # Add trace type counts separately
        referrals_ts = df_time[df_time['trace_type'] == 'referrals'].groupby(pd.Grouper(freq=freq)).size()
        action_plans_ts = df_time[df_time['trace_type'] == 'action_plans'].groupby(pd.Grouper(freq=freq)).size()
        email_results_ts = df_time[df_time['trace_type'] == 'email_results'].groupby(pd.Grouper(freq=freq)).size()
        
        # Merge with main time series
        time_series = time_series.set_index('trace_start')
        time_series['referrals_count'] = referrals_ts.reindex(time_series.index, fill_value=0)
        time_series['action_plans_count'] = action_plans_ts.reindex(time_series.index, fill_value=0)
        time_series['email_results_count'] = email_results_ts.reindex(time_series.index, fill_value=0)
        time_series = time_series.reset_index()
        
        time_series.columns = ['timestamp', 'trace_count', 'avg_duration', 'total_tokens', 'referrals_count', 'action_plans_count', 'email_results_count']
        
        return time_series
    
    def get_user_trace_details(self, user_email: str) -> pd.DataFrame:
        """
        Get detailed trace information for a specific user
        """
        if self.traces_df.empty:
            return pd.DataFrame()
        
        user_traces = self.traces_df[self.traces_df['user_email'] == user_email].copy()
        return user_traces.sort_values('trace_start', ascending=False)
    
    def get_usage_breakdown_by_level(self) -> Dict:
        """
        Categorize users by usage level: high (4+), medium (2-3), low (1)
        """
        if self.traces_df.empty:
            return {'high': [], 'medium': [], 'low': []}
        
        user_counts = self.traces_df.groupby('user_email').size().to_dict()
        
        high_users = []
        medium_users = []
        low_users = []
        
        for email, count in user_counts.items():
            user_name = email.split('@')[0] if '@' in email else email
            user_data = {
                'email': email,
                'name': user_name,
                'count': count
            }
            
            if count >= 4:
                high_users.append(user_data)
            elif count >= 2:
                medium_users.append(user_data)
            else:
                low_users.append(user_data)
        
        # Sort by count descending
        high_users.sort(key=lambda x: x['count'], reverse=True)
        medium_users.sort(key=lambda x: x['count'], reverse=True)
        low_users.sort(key=lambda x: x['count'], reverse=True)
        
        return {
            'high': high_users,
            'medium': medium_users,
            'low': low_users
        }
    
    def get_resource_category_breakdown(self) -> Dict:
        """
        Analyze traces by resource category with counts and percentages.
        Uses the already-extracted category field from traces.
        """
        if self.traces_df.empty:
            return {}
        
        category_counts = defaultdict(int)
        category_traces = defaultdict(list)
        
        # Use the category field that was already extracted during trace creation
        for idx, row in self.traces_df.iterrows():
            category = str(row.get('category', '')).strip()
            
            # Mark empty categories as "Other"
            if not category:
                category = 'Other'
            
            category_counts[category] += 1
            category_traces[category].append({
                'user': row.get('user_name', 'unknown'),
                'query': row.get('query', '')[:100],
                'trace_type': row.get('trace_type', 'unknown')
            })
        
        # Calculate percentages
        total = sum(category_counts.values())
        category_breakdown = {}
        
        for category, count in category_counts.items():
            percentage = (count / total * 100) if total > 0 else 0
            category_breakdown[category] = {
                'count': count,
                'percentage': percentage,
                'examples': category_traces.get(category, [])[:3]  # Top 3 examples
            }
        
        # Sort by count
        category_breakdown = dict(sorted(category_breakdown.items(), 
                                        key=lambda x: x[1]['count'], 
                                        reverse=True))
        
        return category_breakdown
    
    def extract_zip_codes(self) -> Dict:
        """
        Extract and analyze zip codes from trace data
        """
        if self.traces_df.empty:
            return {'zip_codes': [], 'regions': {}}
        
        zip_codes = []
        
        # Extract zip codes from the zip_code and all_zip_codes columns
        if 'zip_code' in self.traces_df.columns:
            for idx, row in self.traces_df.iterrows():
                # Get primary zip code
                zip_code = str(row.get('zip_code', '')).strip()
                if zip_code and len(zip_code) == 5:
                    zip_codes.append(zip_code)
                
                # Get all zip codes
                all_zips = str(row.get('all_zip_codes', '')).strip()
                if all_zips:
                    for zc in all_zips.split(','):
                        zc = zc.strip()
                        if zc and len(zc) == 5 and zc not in zip_codes:
                            zip_codes.append(zc)
                
                location_pref = str(row.get('location_preference', '')).strip()
                if location_pref:
                    matches = re.findall(r'\b\d{5}\b', location_pref)
                    for match in matches:
                        if match not in zip_codes:
                            zip_codes.append(match)
        
        # If no zip codes in columns, try extracting from query
        if not zip_codes and 'query' in self.traces_df.columns:
            zip_pattern = r'\b\d{5}\b'
            for idx, row in self.traces_df.iterrows():
                query = str(row.get('query', ''))
                found_zips = re.findall(zip_pattern, query)
                zip_codes.extend(found_zips)
        
        if not zip_codes:
            return {
                'all_zips': [],
                'texas': [],
                'out_of_state': [],
                'total_unique': 0
            }
        
        # Central Texas ZIP code to city mapping
        zip_to_city = {
            # Austin area
            '78701': 'Austin (Downtown)', '78702': 'Austin (East)', '78703': 'Austin (West)', 
            '78704': 'Austin (South)', '78705': 'Austin (Central)', '78712': 'Austin (UT)', 
            '78721': 'Austin (East)', '78722': 'Austin (Central)', '78723': 'Austin (Northeast)',
            '78724': 'Austin (East)', '78725': 'Austin (Southeast)', '78726': 'Austin (West)',
            '78727': 'Austin (North)', '78728': 'Austin (North)', '78729': 'Austin (North)',
            '78730': 'Austin (West)', '78731': 'Austin (Northwest)', '78732': 'Austin (West)',
            '78733': 'Austin (West)', '78734': 'Austin (West)', '78735': 'Austin (Southwest)',
            '78736': 'Austin (Southwest)', '78737': 'Austin (South)', '78738': 'Austin (West)',
            '78739': 'Austin (South)', '78741': 'Austin (South)', '78742': 'Austin (Southeast)',
            '78744': 'Austin (South)', '78745': 'Austin (South)', '78746': 'Austin (West)',
            '78747': 'Austin (South)', '78748': 'Austin (South)', '78749': 'Austin (Southwest)',
            '78750': 'Austin (Northwest)', '78751': 'Austin (North)', '78752': 'Austin (North)',
            '78753': 'Austin (Northeast)', '78754': 'Austin (North)', '78756': 'Austin (Central)',
            '78757': 'Austin (North)', '78758': 'Austin (North)', '78759': 'Austin (North)',
            # Surrounding cities
            '78613': 'Cedar Park', '78641': 'Leander', '78664': 'Round Rock', 
            '78665': 'Round Rock', '78666': 'San Marcos', '78681': 'Round Rock',
            '78660': 'Pflugerville', '78691': 'Pflugerville',
            '78626': 'Georgetown', '78628': 'Georgetown', '78633': 'Georgetown',
            '78610': 'Buda', '78640': 'Kyle', '78644': 'Lockhart',
            '78617': 'Del Valle', '78653': 'Manor', '78654': 'Hutto',
            '78602': 'Bastrop', '78621': 'Elgin', '78645': 'Lago Vista',
            '78642': 'Leander', '78650': 'Marble Falls', '78656': 'Dripping Springs',
            # Out of region
            '77554': 'Galveston (Houston area)', '75835': 'Palestine, TX',
            '75765': 'Nacogdoches, TX', '18102': 'Allentown, PA',
            '23454': 'Virginia Beach, VA', '17602': 'Lancaster, PA',
            '78028': 'Kerrville, TX'
        }
        
        # Count occurrences
        zip_counts = Counter(zip_codes)
        
        # Categorize by region (basic Texas vs out-of-state) with city names
        texas_zips = []
        out_of_state = []
        
        for zip_code, count in zip_counts.items():
            city = zip_to_city.get(zip_code, 'Unknown')
            zip_entry = {'zip': zip_code, 'city': city, 'count': count}
            
            if zip_code.startswith('78') or zip_code.startswith('75'):
                texas_zips.append(zip_entry)
            else:
                out_of_state.append(zip_entry)
        
        return {
            'all_zips': [{'zip': z, 'city': zip_to_city.get(z, 'Unknown'), 'count': c} 
                        for z, c in zip_counts.most_common()],
            'texas': sorted(texas_zips, key=lambda x: x['count'], reverse=True),
            'out_of_state': sorted(out_of_state, key=lambda x: x['count'], reverse=True),
            'total_unique': len(zip_counts)
        }
    
    def get_cohort_analysis(self, cohort_emails: List[str], cohort_name: str = "Cohort") -> Dict:
        """
        Analyze usage for a specific cohort of users (e.g., G1 users)
        
        Args:
            cohort_emails: List of email addresses in the cohort
            cohort_name: Name of the cohort for display purposes
        """
        if self.traces_df.empty:
            return {
                'cohort_name': cohort_name,
                'active_users': [],
                'non_users': [{'email': e, 'name': e.split('@')[0] if '@' in e else e, 'trace_count': 0, 'status': 'not_used'} for e in cohort_emails],
                'total_cohort': len(cohort_emails),
                'active_count': 0,
                'inactive_count': len(cohort_emails),
                'adoption_rate': 0
            }
        
        cohort_users = []
        non_users = []
        
        # Get all users who have traces
        active_users_df = self.traces_df[['user_email']].drop_duplicates()
        
        # Build multiple lookup maps for flexible matching
        # 1. Full email (lowercase) -> original trace email
        full_email_map = {}
        # 2. Username only (before @, lowercase) -> original trace email  
        username_map = {}
        # 3. Username with common domain variations
        
        for _, row in active_users_df.iterrows():
            email = row['user_email']
            if email and isinstance(email, str) and not email.startswith('unknown_'):
                email_lower = email.lower().strip()
                full_email_map[email_lower] = email
                
                if '@' in email:
                    username = email.split('@')[0].lower().strip()
                    # Only use username map if we don't already have this username
                    # (prevents conflicts when same username exists with different domains)
                    if username not in username_map:
                        username_map[username] = email
        
        for cohort_email in cohort_emails:
            cohort_email_lower = cohort_email.lower().strip()
            matched_trace_email = None
            
            # Method 1: Exact email match (case-insensitive)
            if cohort_email_lower in full_email_map:
                matched_trace_email = full_email_map[cohort_email_lower]
            
            # Method 2: Match by username only (handles domain typos like gwct.org vs gwctx.org)
            if not matched_trace_email and '@' in cohort_email:
                cohort_username = cohort_email.split('@')[0].lower().strip()
                if cohort_username in username_map:
                    matched_trace_email = username_map[cohort_username]
            
            # Method 3: Check if trace email contains the cohort username with similar domain
            if not matched_trace_email and '@' in cohort_email:
                cohort_username = cohort_email.split('@')[0].lower().strip()
                cohort_domain = cohort_email.split('@')[1].lower().strip()
                for trace_email_lower, trace_email_orig in full_email_map.items():
                    if '@' in trace_email_lower:
                        trace_username = trace_email_lower.split('@')[0]
                        trace_domain = trace_email_lower.split('@')[1]
                        # Match if usernames are same and domains are similar (e.g., gwct vs gwctx)
                        if trace_username == cohort_username:
                            # Check for similar domains (one is substring of other, or levenshtein distance small)
                            if (cohort_domain in trace_domain or trace_domain in cohort_domain or
                                cohort_domain.replace('.org', '') in trace_domain or
                                trace_domain.replace('.org', '') in cohort_domain):
                                matched_trace_email = trace_email_orig
                                break
            
            if matched_trace_email:
                # Get traces for this user (case-insensitive match)
                user_traces = self.traces_df[
                    self.traces_df['user_email'].str.lower().str.strip() == matched_trace_email.lower().strip()
                ]
                cohort_users.append({
                    'email': cohort_email,
                    'trace_email': matched_trace_email,
                    'name': cohort_email.split('@')[0].replace('.', ' ').title() if '@' in cohort_email else cohort_email,
                    'trace_count': len(user_traces),
                    'first_trace': user_traces['trace_start'].min(),
                    'last_trace': user_traces['trace_start'].max(),
                    'status': 'active'
                })
            else:
                non_users.append({
                    'email': cohort_email,
                    'name': cohort_email.split('@')[0].replace('.', ' ').title() if '@' in cohort_email else cohort_email,
                    'trace_count': 0,
                    'status': 'not_used'
                })
        
        # Sort active users by trace count
        cohort_users.sort(key=lambda x: x['trace_count'], reverse=True)
        
        return {
            'cohort_name': cohort_name,
            'active_users': cohort_users,
            'non_users': non_users,
            'total_cohort': len(cohort_emails),
            'active_count': len(cohort_users),
            'inactive_count': len(non_users),
            'adoption_rate': (len(cohort_users) / len(cohort_emails) * 100) if cohort_emails else 0
        }
    
    def get_comprehensive_report(self, start_date=None, end_date=None, cohort_emails=None) -> Dict:
        """
        Generate a comprehensive usage report with all key metrics
        """
        if self.traces_df.empty:
            return {}
        
        # Filter by date range if provided
        filtered_df = self.traces_df.copy()
        if start_date:
            filtered_df = filtered_df[filtered_df['trace_start'] >= pd.to_datetime(start_date)]
        if end_date:
            filtered_df = filtered_df[filtered_df['trace_start'] <= pd.to_datetime(end_date)]
        
        # Temporarily update traces_df for report generation
        original_df = self.traces_df
        self.traces_df = filtered_df
        
        report = {
            'period': {
                'start': filtered_df['trace_start'].min() if len(filtered_df) > 0 else None,
                'end': filtered_df['trace_start'].max() if len(filtered_df) > 0 else None
            },
            'totals': {
                'unique_users': filtered_df['user_email'].nunique(),
                'total_traces': len(filtered_df),
                'referrals': len(filtered_df[filtered_df['trace_type'] == 'referrals']),
                'action_plans': len(filtered_df[filtered_df['trace_type'] == 'action_plans'])
            },
            'usage_breakdown': self.get_usage_breakdown_by_level(),
            'resource_categories': self.get_resource_category_breakdown(),
            'geographic': self.extract_zip_codes()
        }
        
        # Add cohort analysis if provided
        if cohort_emails:
            report['cohort_analysis'] = self.get_cohort_analysis(cohort_emails)
        
        # Restore original dataframe
        self.traces_df = original_df
        
        return report
    
    # ========== ADVANCED ANALYTICS FEATURES ==========
    
    def analyze_query_patterns(self) -> Dict:
        """
        Feature #1: Query Pattern Analysis & Search Intelligence
        Analyzes query patterns to understand what case managers need.
        """
        if self.traces_df.empty or 'query' not in self.traces_df.columns:
            return {}
        
        queries_df = self.traces_df[self.traces_df['query'].str.len() > 0].copy()
        
        if queries_df.empty:
            return {}
        
        # Common query clustering - extract key terms
        query_terms = defaultdict(int)
        for query in queries_df['query']:
            # Extract meaningful words (ignore common stop words)
            words = re.findall(r'\b[a-z]{4,}\b', query.lower())
            stop_words = {'that', 'this', 'with', 'from', 'have', 'need', 'want', 'help',
                         'looking', 'find', 'search', 'client', 'include', 'resources',
                         'support', 'following', 'close', 'near'}
            for word in words:
                if word not in stop_words:
                    query_terms[word] += 1
        
        # Query refinement detection - same user querying within short time
        refinements = []
        user_queries = queries_df.sort_values('trace_start').groupby('user_email')
        
        for user, user_traces in user_queries:
            prev_time = None
            prev_query = None
            for idx, row in user_traces.iterrows():
                if prev_time is not None:
                    time_diff = (row['trace_start'] - prev_time).total_seconds() / 60
                    if time_diff < 15:  # Within 15 minutes
                        refinements.append({
                            'user': user,
                            'query1': prev_query[:80],
                            'query2': row['query'][:80],
                            'time_gap_minutes': round(time_diff, 1),
                            'category': row.get('category', 'N/A')
                        })
                prev_time = row['trace_start']
                prev_query = row['query']
        
        # Unmet needs detection - queries without follow-up action plans
        referral_users = set(queries_df[queries_df['trace_type'] == 'referrals']['user_email'])
        action_plan_users = set(self.traces_df[self.traces_df['trace_type'] == 'action_plans']['user_email'])
        
        users_no_action = referral_users - action_plan_users
        no_action_queries = queries_df[queries_df['user_email'].isin(users_no_action)]
        
        # Natural language patterns - query length analysis
        queries_df['query_length'] = queries_df['query'].str.len()
        queries_df['word_count'] = queries_df['query'].str.split().str.len()
        
        return {
            'total_unique_queries': len(queries_df),
            'avg_query_length': queries_df['query_length'].mean(),
            'avg_word_count': queries_df['word_count'].mean(),
            'top_terms': dict(sorted(query_terms.items(), key=lambda x: x[1], reverse=True)[:20]),
            'refinements': refinements[:10],  # Top 10 refinement examples
            'refinement_rate': len(refinements) / len(queries_df) * 100 if len(queries_df) > 0 else 0,
            'queries_without_action': len(no_action_queries),
            'no_action_rate': len(no_action_queries) / len(queries_df) * 100 if len(queries_df) > 0 else 0,
            'no_action_examples': no_action_queries[['user_email', 'query', 'category']].head(5).to_dict('records')
        }
    
    def analyze_resource_effectiveness(self) -> Dict:
        """
        Feature #2: Resource Effectiveness Scoring
        Analyzes which resources are selected and which are gaps.
        """
        if self.traces_df.empty:
            return {}
        
        # Extract resources from action plans
        action_plans = self.traces_df[self.traces_df['trace_type'] == 'action_plans']
        
        if action_plans.empty:
            return {'message': 'No action plans found to analyze'}
        
        # Parse resources from traces - need to look at the raw span data
        _selected_resources = defaultdict(int)
        resources_by_category = defaultdict(lambda: defaultdict(int))
        
        # Analyze action plan content for resource mentions
        for idx, row in action_plans.iterrows():
            category = row.get('category', 'Other')
            # Count action plans per category as proxy for resource demand
            resources_by_category[category]['action_plans'] += 1
        
        # Referral to action plan conversion rate
        referrals = self.traces_df[self.traces_df['trace_type'] == 'referrals']
        
        # User conversion: users who searched vs. users who created action plans
        users_searched = set(referrals['user_email'].unique())
        users_acted = set(action_plans['user_email'].unique())
        users_both = users_searched & users_acted
        
        conversion_rate = len(users_both) / len(users_searched) * 100 if len(users_searched) > 0 else 0
        
        # Category-level effectiveness
        category_effectiveness = []
        for category in self.traces_df['category'].unique():
            if not category or category == 'Other':
                continue
            
            cat_referrals = len(referrals[referrals['category'] == category])
            cat_actions = len(action_plans[action_plans['category'] == category])
            cat_conversion = (cat_actions / cat_referrals * 100) if cat_referrals > 0 else 0
            
            category_effectiveness.append({
                'category': category,
                'referrals': cat_referrals,
                'action_plans': cat_actions,
                'conversion_rate': round(cat_conversion, 1)
            })
        
        category_effectiveness.sort(key=lambda x: x['conversion_rate'], reverse=True)
        
        return {
            'total_referrals': len(referrals),
            'total_action_plans': len(action_plans),
            'overall_conversion_rate': round(conversion_rate, 1),
            'users_searched': len(users_searched),
            'users_acted': len(users_acted),
            'users_both': len(users_both),
            'category_effectiveness': category_effectiveness,
            'top_categories_by_action': sorted(resources_by_category.items(), 
                                              key=lambda x: x[1]['action_plans'], 
                                              reverse=True)[:10]
        }
    
    def analyze_user_journeys(self) -> Dict:
        """
        Feature #3: User Journey & Workflow Analytics
        Analyzes how users interact with the tool over time.
        """
        if self.traces_df.empty:
            return {}
        
        # Session analysis - group traces by user and time
        sessions = []
        user_groups = self.traces_df.sort_values('trace_start').groupby('user_email')
        
        for user, user_traces in user_groups:
            session_traces = []
            session_start = None
            
            for idx, row in user_traces.iterrows():
                if session_start is None:
                    session_start = row['trace_start']
                    session_traces = [row]
                else:
                    time_diff = (row['trace_start'] - session_traces[-1]['trace_start']).total_seconds() / 60
                    
                    if time_diff > 30:  # New session if >30 min gap
                        # Save previous session
                        sessions.append({
                            'user': user,
                            'start': session_start,
                            'end': session_traces[-1]['trace_start'],
                            'duration_minutes': (session_traces[-1]['trace_start'] - session_start).total_seconds() / 60,
                            'trace_count': len(session_traces),
                            'types': [t['trace_type'] for t in session_traces],
                            'categories': list(set([t.get('category', '') for t in session_traces if t.get('category')]))
                        })
                        # Start new session
                        session_start = row['trace_start']
                        session_traces = [row]
                    else:
                        session_traces.append(row)
            
            # Save last session
            if session_traces:
                sessions.append({
                    'user': user,
                    'start': session_start,
                    'end': session_traces[-1]['trace_start'],
                    'duration_minutes': (session_traces[-1]['trace_start'] - session_start).total_seconds() / 60,
                    'trace_count': len(session_traces),
                    'types': [t['trace_type'] for t in session_traces],
                    'categories': list(set([t.get('category', '') for t in session_traces if t.get('category')]))
                })
        
        # Time-to-action metrics
        time_to_action = []
        for user, user_traces in user_groups:
            referrals = user_traces[user_traces['trace_type'] == 'referrals']
            action_plans = user_traces[user_traces['trace_type'] == 'action_plans']
            
            if not referrals.empty and not action_plans.empty:
                first_referral = referrals['trace_start'].min()
                first_action = action_plans['trace_start'].min()
                
                if first_action > first_referral:
                    time_diff = (first_action - first_referral).total_seconds() / 60
                    time_to_action.append({
                        'user': user,
                        'time_minutes': round(time_diff, 1),
                        'referral_count': len(referrals),
                        'action_count': len(action_plans)
                    })
        
        # Multi-category sessions
        multi_category = [s for s in sessions if len(s['categories']) > 1]
        
        # Drop-off analysis - users who searched but never created action plans
        users_dropped = set(self.traces_df[self.traces_df['trace_type'] == 'referrals']['user_email']) - \
                       set(self.traces_df[self.traces_df['trace_type'] == 'action_plans']['user_email'])
        
        dropped_traces = self.traces_df[self.traces_df['user_email'].isin(users_dropped)]
        
        return {
            'total_sessions': len(sessions),
            'avg_session_duration': np.mean([s['duration_minutes'] for s in sessions]) if sessions else 0,
            'avg_traces_per_session': np.mean([s['trace_count'] for s in sessions]) if sessions else 0,
            'multi_category_sessions': len(multi_category),
            'multi_category_rate': len(multi_category) / len(sessions) * 100 if sessions else 0,
            'avg_time_to_action': np.mean([t['time_minutes'] for t in time_to_action]) if time_to_action else 0,
            'median_time_to_action': np.median([t['time_minutes'] for t in time_to_action]) if time_to_action else 0,
            'users_with_action': len(time_to_action),
            'users_dropped': len(users_dropped),
            'drop_off_rate': len(users_dropped) / len(user_groups) * 100 if len(user_groups) > 0 else 0,
            'session_examples': sessions[:5],  # First 5 sessions as examples
            'time_to_action_examples': sorted(time_to_action, key=lambda x: x['time_minutes'])[:5],
            'dropped_user_categories': dropped_traces['category'].value_counts().to_dict()
        }
    
    def analyze_performance_quality(self) -> Dict:
        """
        Feature #4: Performance & Quality Metrics
        Analyzes LLM performance, error rates, and token usage.
        """
        if self.df.empty:
            return {}
        
        # Response time analysis by category
        response_times = {}
        if 'category' in self.traces_df.columns:
            for category in self.traces_df['category'].unique():
                if category and category != 'Other':
                    cat_traces = self.traces_df[self.traces_df['category'] == category]
                    response_times[category] = {
                        'avg_duration_s': cat_traces['trace_duration_s'].mean(),
                        'median_duration_s': cat_traces['trace_duration_s'].median(),
                        'p95_duration_s': cat_traces['trace_duration_s'].quantile(0.95),
                        'count': len(cat_traces)
                    }
        
        # Error rate analysis
        error_traces = self.traces_df[self.traces_df['status'] == 'ERROR'] if 'status' in self.traces_df.columns else pd.DataFrame()
        error_rate_by_category = {}
        
        for category in self.traces_df['category'].unique():
            if category:
                cat_total = len(self.traces_df[self.traces_df['category'] == category])
                cat_errors = len(error_traces[error_traces['category'] == category]) if not error_traces.empty else 0
                error_rate_by_category[category] = {
                    'total': cat_total,
                    'errors': cat_errors,
                    'error_rate': (cat_errors / cat_total * 100) if cat_total > 0 else 0
                }
        
        # Token usage analysis
        token_usage = {
            'total_tokens': self.traces_df['total_tokens'].sum() if 'total_tokens' in self.traces_df.columns else 0,
            'avg_tokens_per_trace': self.traces_df['total_tokens'].mean() if 'total_tokens' in self.traces_df.columns else 0,
            'max_tokens': self.traces_df['total_tokens'].max() if 'total_tokens' in self.traces_df.columns else 0
        }
        
        # Token usage by category
        token_by_category = {}
        if 'total_tokens' in self.traces_df.columns:
            for category in self.traces_df['category'].unique():
                if category:
                    cat_tokens = self.traces_df[self.traces_df['category'] == category]['total_tokens']
                    token_by_category[category] = {
                        'total': cat_tokens.sum(),
                        'avg': cat_tokens.mean(),
                        'count': len(cat_tokens)
                    }
        
        # LLM span performance
        llm_spans = self.df[self.df['span_kind'] == 'LLM'] if 'span_kind' in self.df.columns else pd.DataFrame()
        llm_performance = {}
        if not llm_spans.empty and 'latency_s' in llm_spans.columns:
            llm_performance = {
                'total_llm_calls': len(llm_spans),
                'avg_llm_latency_s': llm_spans['latency_s'].mean(),
                'median_llm_latency_s': llm_spans['latency_s'].median(),
                'p95_llm_latency_s': llm_spans['latency_s'].quantile(0.95),
                'max_llm_latency_s': llm_spans['latency_s'].max()
            }
        
        # Performance benchmarks (percentiles)
        benchmarks = {}
        if 'trace_duration_s' in self.traces_df.columns:
            durations = self.traces_df['trace_duration_s'].dropna()
            benchmarks = {
                'p50': durations.quantile(0.50),
                'p75': durations.quantile(0.75),
                'p90': durations.quantile(0.90),
                'p95': durations.quantile(0.95),
                'p99': durations.quantile(0.99)
            }
        
        # Slow trace analysis (>p95)
        slow_threshold = benchmarks.get('p95', 10)
        slow_traces = self.traces_df[self.traces_df['trace_duration_s'] > slow_threshold] if 'trace_duration_s' in self.traces_df.columns else pd.DataFrame()
        
        slow_trace_details = []
        for _, row in slow_traces.head(10).iterrows():
            slow_trace_details.append({
                'user': row.get('user_email', 'Unknown'),
                'category': row.get('category', 'N/A'),
                'duration_s': round(row.get('trace_duration_s', 0), 2),
                'query': row.get('query', '')[:60] + '...' if len(row.get('query', '')) > 60 else row.get('query', '')
            })
        
        return {
            'response_times_by_category': response_times,
            'error_rate_by_category': error_rate_by_category,
            'total_errors': len(error_traces),
            'overall_error_rate': len(error_traces) / len(self.traces_df) * 100 if len(self.traces_df) > 0 else 0,
            'token_usage': token_usage,
            'token_by_category': token_by_category,
            'llm_performance': llm_performance,
            'benchmarks': benchmarks,
            'slow_traces': slow_trace_details,
            'slow_threshold_s': slow_threshold
        }
    
    def analyze_geographic_gaps(self) -> Dict:
        """
        Feature #5: Geographic Service Gap Analysis
        Identifies service deserts and regional coverage issues.
        """
        if self.traces_df.empty:
            return {}
        
        # Central Texas region definition
        central_texas_zips = {
            '78701', '78702', '78703', '78704', '78705', '78712', '78721', '78722', '78723',
            '78724', '78725', '78726', '78727', '78728', '78729', '78730', '78731', '78732',
            '78733', '78734', '78735', '78736', '78737', '78738', '78739', '78741', '78742',
            '78744', '78745', '78746', '78747', '78748', '78749', '78750', '78751', '78752',
            '78753', '78754', '78756', '78757', '78758', '78759',  # Austin
            '78660',  # Pflugerville
            '78664', '78665', '78681',  # Round Rock
            '78613', '78641',  # Cedar Park / Leander
            '78626', '78627', '78628', '78633',  # Georgetown
            '78610',  # Buda
            '78640',  # Kyle
            '78666',  # San Marcos
            '76574',  # Taylor
            '78653',  # Manor
            '78669',  # Spicewood
            '78634',  # Hutto
        }
        
        # Zip code to city mapping
        zip_to_city = {
            '78701': 'Austin (Downtown)', '78702': 'Austin (East)', '78703': 'Austin (West)',
            '78704': 'Austin (South)', '78705': 'Austin (UT)', '78712': 'Austin (UT)',
            '78721': 'Austin (East)', '78722': 'Austin (Central)', '78723': 'Austin (Northeast)',
            '78724': 'Austin (Northeast)', '78725': 'Austin (Southeast)', '78726': 'Austin (Northwest)',
            '78727': 'Austin (North)', '78728': 'Austin (North)', '78729': 'Austin (Northwest)',
            '78730': 'Austin (West)', '78731': 'Austin (Northwest)', '78732': 'Austin (West)',
            '78733': 'Austin (West)', '78734': 'Austin (West)', '78735': 'Austin (Southwest)',
            '78736': 'Austin (Southwest)', '78737': 'Austin (South)', '78738': 'Austin (West)',
            '78739': 'Austin (South)', '78741': 'Austin (South)', '78742': 'Austin (Southeast)',
            '78744': 'Austin (South)', '78745': 'Austin (South)', '78746': 'Austin (West)',
            '78747': 'Austin (South)', '78748': 'Austin (South)', '78749': 'Austin (Southwest)',
            '78750': 'Austin (Northwest)', '78751': 'Austin (North)', '78752': 'Austin (North)',
            '78753': 'Austin (Northeast)', '78754': 'Austin (North)', '78756': 'Austin (Central)',
            '78757': 'Austin (North)', '78758': 'Austin (North)', '78759': 'Austin (North)',
            '78613': 'Cedar Park', '78641': 'Leander', '78664': 'Round Rock', 
            '78665': 'Round Rock', '78666': 'San Marcos', '78681': 'Round Rock',
            '78660': 'Pflugerville', '78691': 'Pflugerville',
            '78626': 'Georgetown', '78628': 'Georgetown', '78633': 'Georgetown',
            '78610': 'Buda', '78640': 'Kyle', '78644': 'Lockhart',
            '78617': 'Del Valle', '78653': 'Manor', '78654': 'Hutto', '78634': 'Hutto',
            '78602': 'Bastrop', '78621': 'Elgin', '78645': 'Lago Vista',
            '78642': 'Leander', '78650': 'Marble Falls', '78656': 'Dripping Springs',
            '78669': 'Spicewood', '76574': 'Taylor',
            '77554': 'Galveston', '75835': 'Palestine, TX', '75765': 'Nacogdoches, TX',
            '18102': 'Allentown, PA', '23454': 'Virginia Beach, VA', '17602': 'Lancaster, PA',
            '78028': 'Kerrville, TX'
        }
        
        # Collect all zip codes from traces
        all_zips = []
        zip_to_queries = defaultdict(list)
        zip_to_categories = defaultdict(list)
        
        for _, row in self.traces_df.iterrows():
            zips = row.get('all_zip_codes', [])
            if isinstance(zips, str):
                zips = [z.strip() for z in zips.split(',') if z.strip()]
            if zips:
                for z in zips:
                    all_zips.append(z)
                    zip_to_queries[z].append(row.get('query', '')[:50])
                    zip_to_categories[z].append(row.get('category', 'Other'))
        
        # Zip demand analysis
        zip_counts = defaultdict(int)
        for z in all_zips:
            zip_counts[z] += 1
        
        # Categorize zips
        in_region = {}
        out_of_region = {}
        
        for z, count in zip_counts.items():
            zip_data = {
                'count': count,
                'city': zip_to_city.get(z, 'Unknown'),
                'categories': list(set(zip_to_categories[z])),
                'sample_queries': zip_to_queries[z][:3]
            }
            if z in central_texas_zips:
                in_region[z] = zip_data
            else:
                out_of_region[z] = zip_data
        
        # High-demand areas (potential service gaps if resources are thin)
        high_demand_zips = {z: data for z, data in zip_counts.items() if data >= 3}
        
        # Category distribution by region
        category_by_region = {
            'central_texas': defaultdict(int),
            'out_of_region': defaultdict(int)
        }
        
        for z in all_zips:
            if z in central_texas_zips:
                category_by_region['central_texas'][zip_to_categories.get(z, ['Other'])[0] if z in zip_to_categories else 'Other'] += 1
            else:
                category_by_region['out_of_region'][zip_to_categories.get(z, ['Other'])[0] if z in zip_to_categories else 'Other'] += 1
        
        # "Service desert" detection - queries mentioning locations without zip codes
        location_mentions = defaultdict(int)
        for _, row in self.traces_df.iterrows():
            loc = row.get('location_preference', '')
            if loc and not row.get('zip_code'):
                location_mentions[loc] += 1
        
        # Distance clustering - identify if requests are spread out or concentrated
        unique_zips = len(set(all_zips))
        concentration_ratio = len(all_zips) / unique_zips if unique_zips > 0 else 0
        
        return {
            'total_zip_mentions': len(all_zips),
            'unique_zips': unique_zips,
            'in_region_zips': len(in_region),
            'out_of_region_zips': len(out_of_region),
            'in_region_details': dict(sorted(in_region.items(), key=lambda x: x[1]['count'], reverse=True)),
            'out_of_region_details': dict(sorted(out_of_region.items(), key=lambda x: x[1]['count'], reverse=True)),
            'high_demand_zips': high_demand_zips,
            'category_by_region': {k: dict(v) for k, v in category_by_region.items()},
            'location_without_zip': dict(location_mentions),
            'concentration_ratio': concentration_ratio,
            'coverage_summary': {
                'austin_metro': sum(1 for z in zip_counts.keys() if z.startswith('787')),
                'round_rock': sum(1 for z in zip_counts.keys() if z in ['78664', '78665', '78681']),
                'georgetown': sum(1 for z in zip_counts.keys() if z in ['78626', '78627', '78628', '78633']),
                'pflugerville': sum(1 for z in zip_counts.keys() if z == '78660'),
                'cedar_park_leander': sum(1 for z in zip_counts.keys() if z in ['78613', '78641']),
                'south_austin': sum(1 for z in zip_counts.keys() if z in ['78610', '78640', '78666'])
            }
        }
    
    def analyze_comparative_periods(self, period1_start: datetime = None, period1_end: datetime = None,
                                   period2_start: datetime = None, period2_end: datetime = None) -> Dict:
        """
        Feature #6: Comparative Period Analysis
        Compares metrics between two time periods.
        """
        if self.traces_df.empty or 'trace_start' not in self.traces_df.columns:
            return {}
        
        # Default: compare last 7 days vs previous 7 days
        if period2_end is None:
            period2_end = self.traces_df['trace_start'].max()
        if period2_start is None:
            period2_start = period2_end - pd.Timedelta(days=7)
        if period1_end is None:
            period1_end = period2_start
        if period1_start is None:
            period1_start = period1_end - pd.Timedelta(days=7)
        
        # Filter data for each period
        period1_df = self.traces_df[
            (self.traces_df['trace_start'] >= period1_start) & 
            (self.traces_df['trace_start'] < period1_end)
        ]
        period2_df = self.traces_df[
            (self.traces_df['trace_start'] >= period2_start) & 
            (self.traces_df['trace_start'] <= period2_end)
        ]
        
        def period_metrics(df):
            if df.empty:
                return {
                    'total_traces': 0,
                    'unique_users': 0,
                    'referrals': 0,
                    'action_plans': 0,
                    'avg_duration_s': 0,
                    'categories': {}
                }
            return {
                'total_traces': len(df),
                'unique_users': df['user_email'].nunique(),
                'referrals': len(df[df['trace_type'] == 'referrals']),
                'action_plans': len(df[df['trace_type'] == 'action_plans']),
                'avg_duration_s': df['trace_duration_s'].mean() if 'trace_duration_s' in df.columns else 0,
                'categories': df['category'].value_counts().to_dict()
            }
        
        p1_metrics = period_metrics(period1_df)
        p2_metrics = period_metrics(period2_df)
        
        # Calculate changes
        def calc_change(old, new):
            if old == 0:
                return 100 if new > 0 else 0
            return ((new - old) / old) * 100
        
        changes = {
            'traces_change': calc_change(p1_metrics['total_traces'], p2_metrics['total_traces']),
            'users_change': calc_change(p1_metrics['unique_users'], p2_metrics['unique_users']),
            'referrals_change': calc_change(p1_metrics['referrals'], p2_metrics['referrals']),
            'action_plans_change': calc_change(p1_metrics['action_plans'], p2_metrics['action_plans']),
            'duration_change': calc_change(p1_metrics['avg_duration_s'], p2_metrics['avg_duration_s'])
        }
        
        # Daily trends for each period
        def daily_breakdown(df):
            if df.empty:
                return []
            df_copy = df.copy()
            df_copy['date'] = df_copy['trace_start'].dt.date
            daily = df_copy.groupby('date').agg({
                'trace_id': 'count',
                'user_email': 'nunique'
            }).reset_index()
            daily.columns = ['date', 'traces', 'users']
            return daily.to_dict('records')
        
        # Category shifts
        p1_cats = set(p1_metrics['categories'].keys())
        p2_cats = set(p2_metrics['categories'].keys())
        
        new_categories = p2_cats - p1_cats
        dropped_categories = p1_cats - p2_cats
        
        category_changes = {}
        for cat in p1_cats | p2_cats:
            old = p1_metrics['categories'].get(cat, 0)
            new = p2_metrics['categories'].get(cat, 0)
            category_changes[cat] = {
                'period1': old,
                'period2': new,
                'change_pct': calc_change(old, new)
            }
        
        # Week-over-week by day of week
        def dow_breakdown(df):
            if df.empty:
                return {}
            df_copy = df.copy()
            df_copy['dow'] = df_copy['trace_start'].dt.day_name()
            return df_copy.groupby('dow').size().to_dict()
        
        return {
            'period1': {
                'start': period1_start.isoformat() if hasattr(period1_start, 'isoformat') else str(period1_start),
                'end': period1_end.isoformat() if hasattr(period1_end, 'isoformat') else str(period1_end),
                'metrics': p1_metrics,
                'daily': daily_breakdown(period1_df),
                'dow': dow_breakdown(period1_df)
            },
            'period2': {
                'start': period2_start.isoformat() if hasattr(period2_start, 'isoformat') else str(period2_start),
                'end': period2_end.isoformat() if hasattr(period2_end, 'isoformat') else str(period2_end),
                'metrics': p2_metrics,
                'daily': daily_breakdown(period2_df),
                'dow': dow_breakdown(period2_df)
            },
            'changes': changes,
            'category_changes': category_changes,
            'new_categories': list(new_categories),
            'dropped_categories': list(dropped_categories),
            'growth_trajectory': 'growing' if changes['traces_change'] > 10 else ('declining' if changes['traces_change'] < -10 else 'stable')
        }
    
    def analyze_realtime_alerts(self) -> Dict:
        """
        Feature #8: Real-time Alerting & Anomaly Detection
        Identifies unusual patterns and potential issues.
        """
        if self.traces_df.empty:
            return {'alerts': [], 'status': 'healthy'}
        
        alerts = []
        
        # 1. Error spike detection
        if 'status' in self.traces_df.columns:
            error_traces = self.traces_df[self.traces_df['status'] == 'ERROR']
            error_rate = len(error_traces) / len(self.traces_df) * 100
            
            if error_rate > 10:
                alerts.append({
                    'type': 'error_spike',
                    'severity': 'critical' if error_rate > 25 else 'warning',
                    'message': f'High error rate detected: {error_rate:.1f}%',
                    'value': error_rate,
                    'threshold': 10
                })
        
        # 2. Performance degradation (slow responses)
        if 'trace_duration_s' in self.traces_df.columns:
            avg_duration = self.traces_df['trace_duration_s'].mean()
            recent = self.traces_df.sort_values('trace_start').tail(20)
            recent_avg = recent['trace_duration_s'].mean()
            
            if recent_avg > avg_duration * 1.5:
                alerts.append({
                    'type': 'performance_degradation',
                    'severity': 'warning',
                    'message': f'Recent responses slower than average: {recent_avg:.2f}s vs {avg_duration:.2f}s',
                    'value': recent_avg,
                    'threshold': avg_duration * 1.5
                })
        
        # 3. Usage anomaly (sudden drop)
        if 'trace_start' in self.traces_df.columns:
            df_with_date = self.traces_df.copy()
            df_with_date['date'] = df_with_date['trace_start'].dt.date
            daily_counts = df_with_date.groupby('date').size()
            
            if len(daily_counts) >= 3:
                avg_daily = daily_counts.mean()
                last_day = daily_counts.iloc[-1] if len(daily_counts) > 0 else 0
                
                if last_day < avg_daily * 0.3 and avg_daily > 5:
                    alerts.append({
                        'type': 'usage_drop',
                        'severity': 'warning',
                        'message': f'Significant usage drop: {last_day} traces vs {avg_daily:.0f} avg',
                        'value': last_day,
                        'threshold': avg_daily * 0.3
                    })
        
        # 4. Token usage spike
        if 'total_tokens' in self.traces_df.columns:
            avg_tokens = self.traces_df['total_tokens'].mean()
            max_tokens = self.traces_df['total_tokens'].max()
            
            if max_tokens > avg_tokens * 5 and avg_tokens > 0:
                high_token_traces = self.traces_df[self.traces_df['total_tokens'] > avg_tokens * 3]
                alerts.append({
                    'type': 'token_spike',
                    'severity': 'info',
                    'message': f'{len(high_token_traces)} traces with unusually high token usage',
                    'value': max_tokens,
                    'threshold': avg_tokens * 5
                })
        
        # 5. Category concentration (one category dominating)
        if 'category' in self.traces_df.columns:
            cat_counts = self.traces_df['category'].value_counts()
            if len(cat_counts) > 0:
                top_cat_pct = cat_counts.iloc[0] / len(self.traces_df) * 100
                if top_cat_pct > 50:
                    alerts.append({
                        'type': 'category_concentration',
                        'severity': 'info',
                        'message': f'Category "{cat_counts.index[0]}" represents {top_cat_pct:.0f}% of all traces',
                        'value': top_cat_pct,
                        'threshold': 50
                    })
        
        # 6. User drop-off concern
        user_counts = self.traces_df.groupby('user_email').size()
        single_use_users = len(user_counts[user_counts == 1])
        total_users = len(user_counts)
        
        single_use_rate = single_use_users / total_users * 100 if total_users > 0 else 0
        if single_use_rate > 40:
            alerts.append({
                'type': 'user_retention',
                'severity': 'info',
                'message': f'{single_use_rate:.0f}% of users only used the tool once',
                'value': single_use_rate,
                'threshold': 40
            })
        
        # 7. "Other" category overload
        if 'category' in self.traces_df.columns:
            other_count = len(self.traces_df[self.traces_df['category'] == 'Other'])
            other_pct = other_count / len(self.traces_df) * 100
            
            if other_pct > 30:
                alerts.append({
                    'type': 'categorization_issue',
                    'severity': 'warning',
                    'message': f'{other_pct:.0f}% of traces categorized as "Other" - improve category detection',
                    'value': other_pct,
                    'threshold': 30
                })
        
        # 8. Geographic outliers
        out_of_region = 0
        total_with_zip = 0
        for _, row in self.traces_df.iterrows():
            zips = row.get('all_zip_codes', [])
            if zips:
                total_with_zip += 1
                if isinstance(zips, str):
                    zips = [z.strip() for z in zips.split(',')]
                for z in zips:
                    if not z.startswith('78') and not z.startswith('76'):
                        out_of_region += 1
                        break
        
        if total_with_zip > 0 and out_of_region / total_with_zip > 0.2:
            alerts.append({
                'type': 'geographic_outliers',
                'severity': 'info',
                'message': f'{out_of_region} requests from outside Central Texas region',
                'value': out_of_region,
                'threshold': total_with_zip * 0.2
            })
        
        # Determine overall health status
        critical_alerts = [a for a in alerts if a['severity'] == 'critical']
        warning_alerts = [a for a in alerts if a['severity'] == 'warning']
        
        if critical_alerts:
            status = 'critical'
        elif warning_alerts:
            status = 'warning'
        elif alerts:
            status = 'attention'
        else:
            status = 'healthy'
        
        # System health summary
        health_checks = {
            'error_rate': 'ok' if not any(a['type'] == 'error_spike' for a in alerts) else 'issue',
            'performance': 'ok' if not any(a['type'] == 'performance_degradation' for a in alerts) else 'issue',
            'usage': 'ok' if not any(a['type'] == 'usage_drop' for a in alerts) else 'issue',
            'categorization': 'ok' if not any(a['type'] == 'categorization_issue' for a in alerts) else 'issue',
            'retention': 'ok' if not any(a['type'] == 'user_retention' for a in alerts) else 'issue'
        }
        
        return {
            'alerts': sorted(alerts, key=lambda x: {'critical': 0, 'warning': 1, 'info': 2}[x['severity']]),
            'status': status,
            'health_checks': health_checks,
            'alert_counts': {
                'critical': len(critical_alerts),
                'warning': len(warning_alerts),
                'info': len([a for a in alerts if a['severity'] == 'info'])
            }
        }
    
    def analyze_query_intelligence(self) -> Dict:
        """
        Feature #9: AI-Powered Query Understanding
        Provides deep analysis of query patterns, intents, entities, and quality.
        """
        if self.traces_df.empty or 'query' not in self.traces_df.columns:
            return {}
        
        queries_df = self.traces_df[self.traces_df['query'].str.len() > 0].copy()
        
        if queries_df.empty:
            return {}
        
        # Entity patterns for extraction
        demographic_patterns = {
            'veteran': r'\b(veteran|vet|military|service\s*member|armed\s*forces|va\b)',
            'single_parent': r'\b(single\s*(mom|mother|dad|father|parent)|solo\s*parent)',
            'elderly': r'\b(elderly|senior|older\s*adult|65\+|aging|retired)',
            'disabled': r'\b(disab(led|ility)|handicap|special\s*needs|wheelchair|blind|deaf)',
            'homeless': r'\b(homeless|unhoused|housing\s*insecure|shelter|street)',
            'immigrant': r'\b(immigrant|refugee|asylum|undocumented|esl|non-english)',
            'youth': r'\b(youth|teen|adolescent|young\s*adult|minor|child)',
            'returning_citizen': r'\b(returning\s*citizen|ex-offender|felon|criminal\s*record|expung)',
            'pregnant': r'\b(pregnant|expecting|prenatal|maternity)',
            'domestic_violence': r'\b(domestic\s*violence|dv\s*survivor|abuse|battered)',
            'low_income': r'\b(low[\s-]*income|poverty|poor|struggling|financial\s*hardship)',
            'student': r'\b(student|college|university|school|education|tuition|loans)',
        }
        
        service_patterns = {
            'food': r'\b(food|meal|hunger|pantry|snap|wic|groceries|nutrition)',
            'housing': r'\b(hous(e|ing)|rent|apartment|shelter|eviction|mortgage|move-in)',
            'healthcare': r'\b(health|medical|doctor|clinic|hospital|medicaid|medicare|insurance)',
            'mental_health': r'\b(mental\s*health|counseling|therapy|depression|anxiety|psychiatric)',
            'employment': r'\b(job|employ|work|career|resume|interview|hiring|wages)',
            'training': r'\b(training|certification|cdl|cna|phlebotomy|skills|education|ged)',
            'transportation': r'\b(transport|bus|car|ride|commute|metro|vehicle)',
            'childcare': r'\b(child\s*care|daycare|babysit|preschool|after\s*school)',
            'utilities': r'\b(utilit|electric|water|gas|bill|energy|power)',
            'legal': r'\b(legal|lawyer|attorney|court|custody|immigration|expungement)',
            'substance_abuse': r'\b(substance|alcohol|drug|addiction|rehab|recovery|sober)',
            'financial': r'\b(financ|money|debt|credit|budget|savings|loan|assistance)',
        }
        
        urgency_patterns = {
            'critical': r'\b(emergency|urgent|crisis|immediate|asap|today|tonight|desperate)',
            'high': r'\b(soon|quickly|fast|hurry|need\s*now|this\s*week)',
            'moderate': r'\b(looking\s*for|searching|need|want|trying)',
        }
        
        # Analyze each query
        analyzed_queries = []
        intent_counts = defaultdict(int)
        entity_counts = {
            'demographics': defaultdict(int),
            'services': defaultdict(int),
            'locations': defaultdict(int)
        }
        urgency_distribution = defaultdict(int)
        complexity_scores = []
        quality_scores = []
        
        for idx, row in queries_df.iterrows():
            query = row['query'].lower()
            query_analysis = {
                'query': row['query'][:100],
                'user': row.get('user_email', 'Unknown'),
                'trace_type': row.get('trace_type', 'unknown'),
                'demographics': [],
                'services': [],
                'locations': [],
                'urgency': 'normal',
                'intent': 'unknown',
                'complexity': 0,
                'quality_score': 0,
                'suggestions': []
            }
            
            # Extract demographics
            for demo, pattern in demographic_patterns.items():
                if re.search(pattern, query, re.IGNORECASE):
                    query_analysis['demographics'].append(demo)
                    entity_counts['demographics'][demo] += 1
            
            # Extract services
            for service, pattern in service_patterns.items():
                if re.search(pattern, query, re.IGNORECASE):
                    query_analysis['services'].append(service)
                    entity_counts['services'][service] += 1
            
            # Extract locations
            locations_found = []
            # City names
            cities = re.findall(r'\b(austin|round\s*rock|georgetown|pflugerville|cedar\s*park|leander|buda|kyle|san\s*marcos|bastrop|taylor|hutto|manor)\b', query, re.IGNORECASE)
            locations_found.extend([c.title() for c in cities])
            # Zip codes
            zips = re.findall(r'\b(\d{5})\b', query)
            locations_found.extend(zips)
            query_analysis['locations'] = list(set(locations_found))
            for loc in locations_found:
                entity_counts['locations'][loc] += 1
            
            # Detect urgency
            if re.search(urgency_patterns['critical'], query, re.IGNORECASE):
                query_analysis['urgency'] = 'critical'
                urgency_distribution['critical'] += 1
            elif re.search(urgency_patterns['high'], query, re.IGNORECASE):
                query_analysis['urgency'] = 'high'
                urgency_distribution['high'] += 1
            elif re.search(urgency_patterns['moderate'], query, re.IGNORECASE):
                query_analysis['urgency'] = 'moderate'
                urgency_distribution['moderate'] += 1
            else:
                query_analysis['urgency'] = 'normal'
                urgency_distribution['normal'] += 1
            
            # Classify intent
            if row.get('trace_type') == 'action_plans':
                query_analysis['intent'] = 'create_action_plan'
            elif any(w in query for w in ['how', 'what is', 'explain', 'tell me about']):
                query_analysis['intent'] = 'information_seeking'
            elif any(w in query for w in ['find', 'search', 'looking for', 'need', 'where']):
                query_analysis['intent'] = 'resource_discovery'
            elif any(w in query for w in ['compare', 'difference', 'vs', 'better']):
                query_analysis['intent'] = 'comparison'
            elif any(w in query for w in ['help', 'assist', 'support']):
                query_analysis['intent'] = 'assistance_request'
            else:
                query_analysis['intent'] = 'general_inquiry'
            
            intent_counts[query_analysis['intent']] += 1
            
            # Calculate complexity score (0-10)
            complexity = 0
            complexity += min(len(query_analysis['demographics']) * 2, 4)  # Up to 4 points for demographics
            complexity += min(len(query_analysis['services']) * 1.5, 3)  # Up to 3 points for services
            complexity += min(len(query_analysis['locations']), 2)  # Up to 2 points for locations
            complexity += 1 if query_analysis['urgency'] in ['critical', 'high'] else 0  # 1 point for urgency
            query_analysis['complexity'] = min(round(complexity, 1), 10)
            complexity_scores.append(query_analysis['complexity'])
            
            # Calculate quality score (0-100)
            quality = 50  # Base score
            # Positive factors
            if query_analysis['services']:
                quality += 15  # Clear service need
            if query_analysis['locations']:
                quality += 15  # Location specified
            if query_analysis['demographics']:
                quality += 10  # Client context provided
            if len(row['query']) > 50:
                quality += 5  # Detailed query
            if len(row['query']) > 100:
                quality += 5  # Very detailed
            # Negative factors
            if len(row['query']) < 20:
                quality -= 20  # Too short
            if not query_analysis['services'] and not query_analysis['demographics']:
                quality -= 15  # No clear context
            
            query_analysis['quality_score'] = max(0, min(100, quality))
            quality_scores.append(query_analysis['quality_score'])
            
            # Generate suggestions
            if not query_analysis['locations']:
                query_analysis['suggestions'].append("Add location (city or zip code) for more relevant results")
            if not query_analysis['demographics'] and not query_analysis['services']:
                query_analysis['suggestions'].append("Specify client situation or service type needed")
            if len(row['query']) < 30:
                query_analysis['suggestions'].append("Provide more details about the client's needs")
            if query_analysis['complexity'] > 7:
                query_analysis['suggestions'].append("Consider breaking into multiple focused queries")
            
            analyzed_queries.append(query_analysis)
        
        # Find common query patterns/templates
        query_templates = defaultdict(list)
        for aq in analyzed_queries:
            if aq['services']:
                template_key = f"{'+'.join(sorted(aq['services'][:2]))}"
                if aq['demographics']:
                    template_key += f" for {'+'.join(sorted(aq['demographics'][:1]))}"
                query_templates[template_key].append(aq['query'])
        
        # Identify successful query patterns (queries that led to action plans)
        successful_patterns = []
        for aq in analyzed_queries:
            if aq['trace_type'] == 'action_plans' or (aq['quality_score'] >= 70 and aq['services']):
                successful_patterns.append({
                    'services': aq['services'],
                    'demographics': aq['demographics'],
                    'has_location': bool(aq['locations']),
                    'query_length': len(aq['query'])
                })
        
        # Identify problematic queries (low quality, no results pattern)
        problematic_queries = [aq for aq in analyzed_queries if aq['quality_score'] < 50]
        
        return {
            'total_queries_analyzed': len(analyzed_queries),
            'intent_distribution': dict(intent_counts),
            'entity_summary': {
                'top_demographics': dict(sorted(entity_counts['demographics'].items(), key=lambda x: x[1], reverse=True)[:10]),
                'top_services': dict(sorted(entity_counts['services'].items(), key=lambda x: x[1], reverse=True)[:10]),
                'top_locations': dict(sorted(entity_counts['locations'].items(), key=lambda x: x[1], reverse=True)[:10])
            },
            'urgency_distribution': dict(urgency_distribution),
            'complexity_stats': {
                'avg': np.mean(complexity_scores) if complexity_scores else 0,
                'median': np.median(complexity_scores) if complexity_scores else 0,
                'high_complexity_count': sum(1 for c in complexity_scores if c >= 7),
                'low_complexity_count': sum(1 for c in complexity_scores if c <= 3)
            },
            'quality_stats': {
                'avg': np.mean(quality_scores) if quality_scores else 0,
                'high_quality_count': sum(1 for q in quality_scores if q >= 70),
                'low_quality_count': sum(1 for q in quality_scores if q < 50),
                'needs_improvement_pct': sum(1 for q in quality_scores if q < 50) / len(quality_scores) * 100 if quality_scores else 0
            },
            'common_patterns': dict(sorted(query_templates.items(), key=lambda x: len(x[1]), reverse=True)[:10]),
            'sample_high_quality': [aq for aq in analyzed_queries if aq['quality_score'] >= 70][:5],
            'sample_needs_improvement': problematic_queries[:5],
            'all_analyzed': analyzed_queries[:50],  # First 50 for detailed view
            'insights': self._generate_query_insights(analyzed_queries, entity_counts, urgency_distribution)
        }
    
    def _generate_query_insights(self, analyzed_queries: List, entity_counts: Dict, urgency_dist: Dict) -> List[str]:
        """Generate actionable insights from query analysis."""
        insights = []
        
        # Demographic insights
        demos = entity_counts.get('demographics', {})
        if demos:
            top_demo = max(demos.items(), key=lambda x: x[1])
            insights.append(f"Most common client demographic: {top_demo[0].replace('_', ' ').title()} ({top_demo[1]} queries)")
        
        # Service demand insights
        services = entity_counts.get('services', {})
        if services:
            top_services = sorted(services.items(), key=lambda x: x[1], reverse=True)[:3]
            service_names = [s[0].replace('_', ' ').title() for s in top_services]
            insights.append(f"Top 3 services requested: {', '.join(service_names)}")
        
        # Urgency insights
        critical_pct = urgency_dist.get('critical', 0) / len(analyzed_queries) * 100 if analyzed_queries else 0
        if critical_pct > 10:
            insights.append(f"⚠️ {critical_pct:.0f}% of queries indicate critical urgency - consider priority handling")
        
        # Location insights
        _locations = entity_counts.get('locations', {})
        queries_with_location = sum(1 for aq in analyzed_queries if aq['locations'])
        location_rate = queries_with_location / len(analyzed_queries) * 100 if analyzed_queries else 0
        if location_rate < 50:
            insights.append(f"Only {location_rate:.0f}% of queries include location - encourage users to specify area")
        
        # Quality insights
        low_quality = sum(1 for aq in analyzed_queries if aq['quality_score'] < 50)
        if low_quality > len(analyzed_queries) * 0.3:
            insights.append(f"📝 {low_quality} queries ({low_quality/len(analyzed_queries)*100:.0f}%) need improvement - consider query templates")
        
        # Complexity insights
        high_complexity = sum(1 for aq in analyzed_queries if aq['complexity'] >= 7)
        if high_complexity > 5:
            insights.append(f"🔀 {high_complexity} complex multi-need queries detected - may benefit from case management approach")
        
        return insights
    
    def analyze_output_quality(self, return_full: bool = False) -> Dict:
        """
        Analyze the quality of AI responses/outputs for each trace.
        Scores responses on completeness, actionability, alignment, and structure.
        """
        output_analyses = self._build_output_analyses()
        if not output_analyses:
            return {}
        
        # Calculate aggregate statistics
        quality_scores = [a['quality_score'] for a in output_analyses]
        
        # Identify issues
        issues = {
            'no_resources': [a for a in output_analyses if a['resource_count'] == 0],
            'location_mismatch': [a for a in output_analyses if not a['location_aligned']],
            'category_mismatch': [a for a in output_analyses if not a['category_aligned']],
            'low_quality': [a for a in output_analyses if a['quality_score'] < 50],
            'generic_response': [a for a in output_analyses if a.get('is_generic', False)],
            'too_short': [a for a in output_analyses if a.get('too_short', False)]
        }
        
        # Generate insights
        insights = self._generate_output_insights(output_analyses, issues)
        
        return {
            'total_analyzed': len(output_analyses),
            'quality_stats': {
                'avg_score': np.mean(quality_scores) if quality_scores else 0,
                'median_score': np.median(quality_scores) if quality_scores else 0,
                'min_score': min(quality_scores) if quality_scores else 0,
                'max_score': max(quality_scores) if quality_scores else 0,
                'high_quality_count': sum(1 for q in quality_scores if q >= 70),
                'medium_quality_count': sum(1 for q in quality_scores if 50 <= q < 70),
                'low_quality_count': sum(1 for q in quality_scores if q < 50)
            },
            'alignment_stats': {
                'location_match_rate': sum(1 for a in output_analyses if a['location_aligned']) / len(output_analyses) * 100 if output_analyses else 0,
                'category_match_rate': sum(1 for a in output_analyses if a['category_aligned']) / len(output_analyses) * 100 if output_analyses else 0,
                'has_resources_rate': sum(1 for a in output_analyses if a['resource_count'] > 0) / len(output_analyses) * 100 if output_analyses else 0,
                'actionable_rate': sum(1 for a in output_analyses if a['has_actionable_info']) / len(output_analyses) * 100 if output_analyses else 0
            },
            'issue_counts': {k: len(v) for k, v in issues.items()},
            'issues': {k: v[:5] for k, v in issues.items()},  # Top 5 examples per issue
            'insights': insights,
            'all_analyses': (
                sorted(output_analyses, key=lambda x: x['quality_score'])
                if return_full
                else sorted(output_analyses, key=lambda x: x['quality_score'])[:50]
            ),
            'best_responses': sorted(output_analyses, key=lambda x: x['quality_score'], reverse=True)[:10]
        }

    def _build_output_analyses(self) -> List[Dict]:
        """Build per-trace output analysis records used for automated evals."""
        if self.df.empty or self.traces_df is None or self.traces_df.empty:
            return []

        output_analyses = []
        for trace_id in self.traces_df['trace_id'].unique():
            trace_spans = self.df[self.df['trace_id'] == trace_id]
            trace_rows = self.traces_df[self.traces_df['trace_id'] == trace_id]
            if trace_rows.empty:
                continue
            trace_row = trace_rows.iloc[0]
            
            # Extract output content and resources from spans
            output_text = ""
            resources_found = []
            
            for _, span in trace_spans.iterrows():
                # Try multiple locations for output data
                output_attr = span.get('output', '')
                
                # Parse output attribute
                if isinstance(output_attr, str) and output_attr:
                    output_text += output_attr
                    resources_found.extend(self._extract_resources_from_text_content(output_attr))
                
                # Check span attributes for nested output
                attrs = span.get('attributes', {})
                if isinstance(attrs, str):
                    try:
                        attrs = json.loads(attrs)
                    except Exception:
                        attrs = {}
                
                if isinstance(attrs, dict):
                    # Check output.value (common location)
                    output_data = attrs.get('output', {})
                    if isinstance(output_data, dict):
                        output_value = output_data.get('value', '')
                        if isinstance(output_value, str) and output_value:
                            output_text += output_value
                            resources_found.extend(self._extract_resources_from_text_content(output_value))
                    
                    # Check llm.replies for resource JSON
                    llm_data = attrs.get('llm', {})
                    if isinstance(llm_data, dict):
                        replies = llm_data.get('replies', [])
                        for reply in replies:
                            if isinstance(reply, str):
                                output_text += reply
                                resources_found.extend(self._extract_resources_from_text_content(reply))
                    
                    # Also check direct output.value at attribute level
                    for key in ['output.value', 'llm.output_messages']:
                        if key in attrs:
                            val = attrs[key]
                            if isinstance(val, str):
                                output_text += val
                                resources_found.extend(self._extract_resources_from_text_content(val))
                            elif isinstance(val, list):
                                for v in val:
                                    if isinstance(v, dict):
                                        content = str(v.get('message', {}).get('content', ''))
                                        output_text += content
                                        resources_found.extend(self._extract_resources_from_text_content(content))
            
            analysis = self._score_output_quality(
                output_text=output_text,
                resources=resources_found,
                query=trace_row.get('query', ''),
                query_category=trace_row.get('category', ''),
                query_location=trace_row.get('location_preference', ''),
                query_zip=trace_row.get('zip_code', ''),
                trace_type=trace_row.get('trace_type', '')
            )
            
            analysis.update(self._calculate_resource_detail_stats(resources_found))
            analysis['trace_id'] = trace_id
            analysis['user'] = trace_row.get('user_email', 'Unknown')
            analysis['query'] = trace_row.get('query', '')[:200]
            analysis['trace_type'] = trace_row.get('trace_type', '')
            analysis['timestamp'] = trace_row.get('trace_start', None)
            analysis['output_text'] = output_text[:5000]  # Store truncated for checks
            analysis['resources_found'] = resources_found  # Store for failure taxonomy
            
            output_analyses.append(analysis)
        
        return output_analyses

    def _extract_resources_from_text_content(self, text: str) -> List[Dict]:
        """
        Extract resources from text content, handling various formats:
        - JSON with {"resources": [...]}
        - JSON with {"resource_type": ...}
        - Embedded JSON in text
        """
        if not text or not isinstance(text, str):
            return []
        
        resources = []
        
        # Try to find and parse JSON blocks containing resources
        # Pattern 1: {"resources": [...]}
        json_patterns = [
            r'\{"resources"\s*:\s*\[',
            r'\{"resource_type"\s*:',
            r'\{"referrals"\s*:\s*\[',
            r'\{"results"\s*:\s*\[',
            r'\{"recommendations"\s*:\s*\[',
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, text)
            if match:
                start_idx = match.start()
                # Find the end of the JSON object by counting braces
                brace_count = 0
                end_idx = start_idx
                in_string = False
                escape_next = False
                
                for i, char in enumerate(text[start_idx:], start=start_idx):
                    if escape_next:
                        escape_next = False
                        continue
                    if char == '\\':
                        escape_next = True
                        continue
                    if char == '"' and not escape_next:
                        in_string = not in_string
                    if not in_string:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_idx = i + 1
                                break
                
                if end_idx > start_idx:
                    json_str = text[start_idx:end_idx]
                    # Clean up common escape issues
                    json_str = json_str.replace('\\n', ' ').replace('\\"', '"')
                    
                    try:
                        parsed = json.loads(json_str)
                        if isinstance(parsed, dict):
                            for key in ['resources', 'referrals', 'results', 'recommendations', 'data']:
                                if key in parsed and isinstance(parsed[key], list):
                                    for item in parsed[key]:
                                        if isinstance(item, dict):
                                            resources.append(item)
                    except json.JSONDecodeError:
                        pass
        
        # Also try parsing the whole text as JSON
        if text.strip().startswith('{') or text.strip().startswith('['):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    for key in ['resources', 'referrals', 'results', 'recommendations', 'data']:
                        if key in parsed and isinstance(parsed[key], list):
                            for item in parsed[key]:
                                if isinstance(item, dict):
                                    resources.append(item)
                elif isinstance(parsed, list):
                    for item in parsed:
                        if isinstance(item, dict) and ('name' in item or 'title' in item or 'organization' in item):
                            resources.append(item)
            except json.JSONDecodeError:
                pass
        
        return resources

    def _calculate_resource_detail_stats(self, resources: List[Dict]) -> Dict:
        """Compute resource detail completeness as a proxy for hallucination risk."""
        if not resources:
            return {
                'resource_detail_score': 0.0,
                'resources_missing_location': 0,
                'resources_missing_contact': 0,
                'resources_with_location': 0,
                'resources_with_contact': 0,
                'structured_resource_count': 0,
            }

        detail_scores = []
        missing_location = 0
        missing_contact = 0
        structured_count = 0

        for res in resources:
            if not isinstance(res, dict):
                continue
            structured_count += 1

            name = res.get('name') or res.get('title')
            has_name = bool(str(name).strip()) if name is not None else False

            has_location = any(
                bool(res.get(k))
                for k in ['address', 'city', 'zip', 'zip_code', 'state']
            )
            has_contact = any(
                bool(res.get(k))
                for k in ['phone', 'website', 'url', 'email']
            )

            if not has_location:
                missing_location += 1
            if not has_contact:
                missing_contact += 1

            detail_scores.append((has_name + has_location + has_contact) / 3)

        if structured_count == 0:
            return {
                'resource_detail_score': 0.0,
                'resources_missing_location': 0,
                'resources_missing_contact': 0,
                'resources_with_location': 0,
                'resources_with_contact': 0,
                'structured_resource_count': 0,
            }

        return {
            'resource_detail_score': float(np.mean(detail_scores) * 100),
            'resources_missing_location': missing_location,
            'resources_missing_contact': missing_contact,
            'resources_with_location': structured_count - missing_location,
            'resources_with_contact': structured_count - missing_contact,
            'structured_resource_count': structured_count,
        }

    def get_output_quality_evals(self) -> pd.DataFrame:
        """Return per-trace eval records for automated quality testing."""
        output_analyses = self._build_output_analyses()
        if not output_analyses:
            return pd.DataFrame()
        return pd.DataFrame(output_analyses)
    
    def _score_output_quality(self, output_text: str, resources: List, query: str, 
                              query_category: str, query_location: str, query_zip: str,
                              trace_type: str) -> Dict:
        """Score a single output for quality."""
        score = 50  # Base score
        factors = []
        
        output_lower = output_text.lower()
        _query_lower = query.lower()
        
        # 1. Response length analysis
        output_length = len(output_text)
        too_short = output_length < 100
        _too_long = output_length > 10000
        
        if too_short:
            score -= 20
            factors.append("Response too short")
        elif output_length > 500:
            score += 10
            factors.append("Detailed response")
        
        # 2. Resource presence
        resource_count = len(resources)
        if resource_count > 0:
            score += 15
            factors.append(f"Contains {resource_count} resources")
        elif trace_type == 'referrals':
            score -= 15
            factors.append("No resources in referral response")
        
        # 3. Check for specific/actionable information
        has_phone = bool(re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', output_text))
        has_address = bool(re.search(r'\b\d+\s+\w+\s+(st|street|ave|avenue|blvd|rd|road|dr|drive|ln|lane)\b', output_lower))
        has_website = bool(re.search(r'https?://|www\.|\.(org|com|gov|net)\b', output_lower))
        has_email = bool(re.search(r'\b[\w.-]+@[\w.-]+\.\w+\b', output_lower))
        
        actionable_count = sum([has_phone, has_address, has_website, has_email])
        has_actionable_info = actionable_count > 0
        
        if has_phone:
            score += 5
            factors.append("Has phone number")
        if has_address:
            score += 5
            factors.append("Has address")
        if has_website:
            score += 3
            factors.append("Has website")
        
        # 4. Location alignment
        location_aligned = True
        if query_location or query_zip:
            location_terms = []
            if query_location:
                location_terms.extend(query_location.lower().split())
            if query_zip:
                location_terms.append(query_zip)
            
            # Check if any location term appears in output
            location_found = any(term in output_lower for term in location_terms if len(term) > 2)
            location_aligned = location_found or not query_location  # Aligned if found OR no location requested
            
            if location_found:
                score += 10
                factors.append("Location matches query")
            elif query_location:
                score -= 10
                factors.append(f"Location mismatch (asked: {query_location})")
        
        # 5. Category alignment
        category_aligned = True
        if query_category and query_category.lower() != 'other':
            category_keywords = {
                'food': ['food', 'meal', 'pantry', 'hunger', 'nutrition', 'snap', 'wic'],
                'housing': ['housing', 'shelter', 'rent', 'apartment', 'homeless', 'eviction'],
                'healthcare': ['health', 'medical', 'clinic', 'doctor', 'hospital', 'medicaid'],
                'mental health': ['mental', 'counseling', 'therapy', 'psychiatric', 'behavioral'],
                'employment': ['job', 'employment', 'work', 'career', 'resume', 'hiring'],
                'training': ['training', 'certification', 'education', 'skills', 'cdl', 'cna'],
                'transportation': ['transport', 'bus', 'metro', 'ride', 'vehicle'],
                'childcare': ['childcare', 'daycare', 'child care', 'preschool'],
                'financial': ['financial', 'money', 'debt', 'budget', 'assistance', 'utility']
            }
            
            cat_lower = query_category.lower()
            keywords = category_keywords.get(cat_lower, [cat_lower])
            category_found = any(kw in output_lower for kw in keywords)
            category_aligned = category_found
            
            if category_found:
                score += 10
                factors.append("Category matches query")
            else:
                score -= 10
                factors.append(f"Category mismatch (asked: {query_category})")
        
        # 6. Detect generic/template responses
        generic_phrases = [
            "i'm sorry, i couldn't find",
            "no resources available",
            "i don't have information",
            "please try again",
            "unable to locate",
            "no results found"
        ]
        is_generic = any(phrase in output_lower for phrase in generic_phrases)
        
        if is_generic:
            score -= 20
            factors.append("Generic/no-results response")
        
        # 7. Structure quality (for action plans)
        if trace_type == 'action_plans':
            has_steps = bool(re.search(r'(step\s*\d|1\.|•|\-\s+\w)', output_lower))
            has_timeline = bool(re.search(r'(week|day|month|timeline|deadline|by\s+\w+day)', output_lower))
            
            if has_steps:
                score += 5
                factors.append("Has clear steps")
            if has_timeline:
                score += 5
                factors.append("Has timeline")
        
        # Clamp score
        score = max(0, min(100, score))
        
        return {
            'quality_score': score,
            'factors': factors,
            'resource_count': resource_count,
            'output_length': output_length,
            'too_short': too_short,
            'has_actionable_info': has_actionable_info,
            'has_phone': has_phone,
            'has_address': has_address,
            'has_website': has_website,
            'location_aligned': location_aligned,
            'category_aligned': category_aligned,
            'is_generic': is_generic
        }
    
    def _generate_output_insights(self, analyses: List, issues: Dict) -> List[str]:
        """Generate actionable insights from output analysis."""
        insights = []
        total = len(analyses)
        
        if total == 0:
            return insights
        
        # Quality distribution
        low_quality_pct = len(issues['low_quality']) / total * 100
        if low_quality_pct > 20:
            insights.append(f"⚠️ {low_quality_pct:.0f}% of responses are low quality - review AI prompts/configuration")
        
        # Location mismatch
        loc_mismatch_pct = len(issues['location_mismatch']) / total * 100
        if loc_mismatch_pct > 15:
            insights.append(f"📍 {loc_mismatch_pct:.0f}% of responses don't match requested location - check geographic filtering")
        
        # Category mismatch
        cat_mismatch_pct = len(issues['category_mismatch']) / total * 100
        if cat_mismatch_pct > 20:
            insights.append(f"🏷️ {cat_mismatch_pct:.0f}% of responses don't match the category requested - review category routing")
        
        # No resources
        no_resources_pct = len(issues['no_resources']) / total * 100
        if no_resources_pct > 30:
            insights.append(f"📋 {no_resources_pct:.0f}% of referral responses contain no resources - expand resource database")
        
        # Generic responses
        generic_pct = len(issues['generic_response']) / total * 100
        if generic_pct > 10:
            insights.append(f"🔄 {generic_pct:.0f}% are generic/no-result responses - improve fallback handling")
        
        # Actionability
        actionable_pct = sum(1 for a in analyses if a['has_actionable_info']) / total * 100
        if actionable_pct < 60:
            insights.append(f"📞 Only {actionable_pct:.0f}% include contact info (phone/address/website) - enhance resource data")
        else:
            insights.append(f"✅ {actionable_pct:.0f}% of responses include actionable contact information")
        
        return insights
    
    def analyze_resource_recommendations(self) -> Dict:
        """
        Analyze which resources are being recommended and their effectiveness.
        Tracks recommendation frequency, geographic distribution, and patterns.
        """
        if self.df.empty:
            return {}
        
        # Extract all recommended resources from spans
        all_resources = []
        resource_by_trace = defaultdict(list)
        
        for _, span in self.df.iterrows():
            trace_id = span.get('trace_id', '')
            
            # Try to extract resources from output
            output_attr = span.get('output', '')
            attrs = span.get('attributes', {})
            
            if isinstance(attrs, str):
                try:
                    attrs = json.loads(attrs)
                except Exception:
                    attrs = {}
            
            # Search for resources in various places
            resources_to_check = []
            
            # Check output attribute
            if isinstance(output_attr, str) and output_attr:
                try:
                    output_data = json.loads(output_attr) if output_attr.startswith('{') or output_attr.startswith('[') else {}
                    if isinstance(output_data, dict):
                        for key in ['resources', 'referrals', 'results', 'recommendations', 'data', 'items']:
                            if key in output_data and isinstance(output_data[key], list):
                                resources_to_check.extend(output_data[key])
                    elif isinstance(output_data, list):
                        resources_to_check.extend(output_data)
                except Exception:
                    pass
            
            # Check attributes for output.value containing resources
            if isinstance(attrs, dict):
                output_value = attrs.get('output.value', '')
                if isinstance(output_value, str):
                    try:
                        ov_data = json.loads(output_value) if output_value.startswith('{') or output_value.startswith('[') else {}
                        if isinstance(ov_data, dict):
                            for key in ['resources', 'referrals', 'results', 'recommendations', 'data']:
                                if key in ov_data and isinstance(ov_data[key], list):
                                    resources_to_check.extend(ov_data[key])
                        elif isinstance(ov_data, list):
                            resources_to_check.extend(ov_data)
                    except Exception:
                        pass
            
            # Process found resources
            for res in resources_to_check:
                if not isinstance(res, dict):
                    continue
                
                resource_info = {
                    'trace_id': trace_id,
                    'name': res.get('name', res.get('title', res.get('organization', 'Unknown'))),
                    'category': res.get('category', res.get('type', 'Unknown')),
                    'address': res.get('address', res.get('location', '')),
                    'city': res.get('city', ''),
                    'zip_code': res.get('zip', res.get('zip_code', res.get('postal_code', ''))),
                    'phone': res.get('phone', res.get('telephone', '')),
                    'website': res.get('website', res.get('url', '')),
                    'description': res.get('description', res.get('summary', ''))[:200] if res.get('description') or res.get('summary') else ''
                }
                
                # Try to extract zip from address if not present
                if not resource_info['zip_code'] and resource_info['address']:
                    zip_match = re.search(r'\b(\d{5})\b', str(resource_info['address']))
                    if zip_match:
                        resource_info['zip_code'] = zip_match.group(1)
                
                all_resources.append(resource_info)
                resource_by_trace[trace_id].append(resource_info)
        
        if not all_resources:
            # Fallback: try to extract resource names from output text
            return self._extract_resources_from_text()
        
        # Analyze resource patterns
        resource_counts = defaultdict(int)
        resource_details = {}
        category_distribution = defaultdict(int)
        zip_distribution = defaultdict(int)
        city_distribution = defaultdict(int)
        
        for res in all_resources:
            name = res['name']
            if name and name != 'Unknown':
                resource_counts[name] += 1
                if name not in resource_details:
                    resource_details[name] = res
                
                if res['category'] and res['category'] != 'Unknown':
                    category_distribution[res['category']] += 1
                
                if res['zip_code']:
                    zip_distribution[res['zip_code']] += 1
                
                if res['city']:
                    city_distribution[res['city']] += 1
        
        # Top resources
        top_resources = sorted(resource_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        
        # Resource diversity metrics
        unique_resources = len(resource_counts)
        total_recommendations = len(all_resources)
        
        # Calculate concentration (are we over-relying on a few resources?)
        top_5_count = sum(count for _, count in top_resources[:5])
        concentration_ratio = top_5_count / total_recommendations * 100 if total_recommendations > 0 else 0
        
        # Geographic analysis
        central_texas_zips = [z for z in zip_distribution.keys() if z.startswith('78') or z.startswith('76')]
        out_of_region_zips = [z for z in zip_distribution.keys() if z not in central_texas_zips]
        
        # Match rate with queries (how often does resource location match query location)
        location_match_count = 0
        total_with_location = 0
        
        for trace_id, resources in resource_by_trace.items():
            trace_row = self.traces_df[self.traces_df['trace_id'] == trace_id]
            if trace_row.empty:
                continue
            
            query_zip = trace_row.iloc[0].get('zip_code', '')
            query_location = str(trace_row.iloc[0].get('location_preference', '')).lower()
            
            if query_zip or query_location:
                total_with_location += 1
                
                # Check if any resource matches the location
                for res in resources:
                    res_zip = res.get('zip_code', '')
                    res_city = str(res.get('city', '')).lower()
                    res_address = str(res.get('address', '')).lower()
                    
                    if query_zip and res_zip and query_zip[:3] == res_zip[:3]:
                        location_match_count += 1
                        break
                    elif query_location and (query_location in res_city or query_location in res_address):
                        location_match_count += 1
                        break
        
        location_match_rate = location_match_count / total_with_location * 100 if total_with_location > 0 else 0
        
        # Generate insights
        insights = self._generate_resource_insights(
            unique_resources, total_recommendations, concentration_ratio,
            top_resources, location_match_rate, category_distribution
        )
        
        return {
            'total_recommendations': total_recommendations,
            'unique_resources': unique_resources,
            'recommendations_per_trace': total_recommendations / len(resource_by_trace) if resource_by_trace else 0,
            'top_resources': [
                {
                    'name': name,
                    'count': count,
                    'percentage': count / total_recommendations * 100,
                    'details': resource_details.get(name, {})
                }
                for name, count in top_resources
            ],
            'concentration_ratio': concentration_ratio,
            'diversity_score': min(100, unique_resources / total_recommendations * 100) if total_recommendations > 0 else 0,
            'category_distribution': dict(sorted(category_distribution.items(), key=lambda x: x[1], reverse=True)),
            'geographic_distribution': {
                'by_zip': dict(sorted(zip_distribution.items(), key=lambda x: x[1], reverse=True)[:15]),
                'by_city': dict(sorted(city_distribution.items(), key=lambda x: x[1], reverse=True)[:10]),
                'central_texas_count': sum(zip_distribution[z] for z in central_texas_zips),
                'out_of_region_count': sum(zip_distribution[z] for z in out_of_region_zips),
                'out_of_region_zips': out_of_region_zips
            },
            'location_match_rate': location_match_rate,
            'traces_with_resources': len(resource_by_trace),
            'traces_without_resources': len(self.traces_df) - len(resource_by_trace),
            'insights': insights,
            'sample_resources': all_resources[:30]  # First 30 for detailed view
        }
    
    def _extract_resources_from_text(self) -> Dict:
        """Fallback: Extract resource mentions from output text when structured data isn't available."""
        resource_mentions = defaultdict(int)
        
        # Common resource/organization patterns
        org_patterns = [
            r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,4})\s+(?:Center|Services|Program|Clinic|Shelter|Bank|Ministry|Foundation|Association|Organization)\b',
            r'\b(Capital\s+Area\s+Food\s+Bank|Caritas|Foundation\s+Communities|Goodwill|Salvation\s+Army|Catholic\s+Charities|United\s+Way)\b',
        ]
        
        for _, span in self.df.iterrows():
            output = str(span.get('output', ''))
            attrs = span.get('attributes', {})
            
            if isinstance(attrs, str):
                try:
                    attrs = json.loads(attrs)
                except Exception:
                    attrs = {}
            
            text_to_search = output
            if isinstance(attrs, dict):
                text_to_search += ' ' + str(attrs.get('output.value', ''))
            
            for pattern in org_patterns:
                matches = re.findall(pattern, text_to_search)
                for match in matches:
                    if len(match) > 5:  # Filter out short matches
                        resource_mentions[match] += 1
        
        if not resource_mentions:
            return {
                'total_recommendations': 0,
                'unique_resources': 0,
                'top_resources': [],
                'insights': ["No structured resource data found - consider enhancing output logging"],
                'note': "Resource analysis limited - structured resource data not available in trace logs"
            }
        
        total = sum(resource_mentions.values())
        return {
            'total_recommendations': total,
            'unique_resources': len(resource_mentions),
            'top_resources': [
                {'name': name, 'count': count, 'percentage': count / total * 100}
                for name, count in sorted(resource_mentions.items(), key=lambda x: x[1], reverse=True)[:20]
            ],
            'insights': [f"Found {len(resource_mentions)} unique resource mentions in output text"],
            'note': "Resource analysis based on text extraction - structured data not available"
        }
    
    def _generate_resource_insights(self, unique: int, total: int, concentration: float,
                                    top_resources: List, match_rate: float, categories: Dict) -> List[str]:
        """Generate insights about resource recommendations."""
        insights = []
        
        if total == 0:
            insights.append("No resource recommendations found in trace data")
            return insights
        
        # Diversity insights
        if concentration > 50:
            insights.append(f"⚠️ Top 5 resources account for {concentration:.0f}% of all recommendations - consider diversifying")
        elif concentration < 20:
            insights.append(f"✅ Good resource diversity - top 5 resources account for only {concentration:.0f}% of recommendations")
        
        # Most recommended
        if top_resources:
            top_name = top_resources[0][0]
            top_count = top_resources[0][1]
            insights.append(f"📊 Most recommended resource: {top_name} ({top_count} times, {top_count/total*100:.0f}%)")
        
        # Location matching
        if match_rate < 70:
            insights.append(f"📍 Only {match_rate:.0f}% of recommendations match query location - improve geographic targeting")
        else:
            insights.append(f"✅ {match_rate:.0f}% location match rate between queries and recommended resources")
        
        # Category coverage
        if categories:
            top_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
            cat_names = [c[0] for c in top_cats]
            insights.append(f"🏷️ Most recommended categories: {', '.join(cat_names)}")
        
        # Under-utilized detection
        if unique < 10:
            insights.append(f"📋 Only {unique} unique resources being recommended - expand resource database")
        
        return insights

    # =========================================================================
    # COMPREHENSIVE EVAL SYSTEM
    # =========================================================================

    def get_comprehensive_evals(
        self,
        resource_inventory: Optional[List[Dict]] = None,
        test_cases: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Run comprehensive automated evaluations on all traces.
        
        Args:
            resource_inventory: List of known resources for hallucination detection
            test_cases: List of query → expected_resources pairs for gold standard testing
        
        Returns:
            Comprehensive eval results with failure taxonomy, validation, coverage, etc.
        """
        # Build base output analyses
        output_analyses = self._build_output_analyses()
        if not output_analyses:
            return {'error': 'No output data available for evaluation'}

        # Index inventory for fast lookup
        inventory_index = self._build_inventory_index(resource_inventory)
        
        # Run all eval dimensions
        results = {
            'trace_count': len(output_analyses),
            'timestamp': datetime.now().isoformat(),
        }
        
        # 1. Structured failure taxonomy
        failure_taxonomy = self._run_failure_taxonomy(output_analyses, inventory_index)
        results['failure_taxonomy'] = failure_taxonomy
        
        # 2. Resource validation (hallucination detection)
        if inventory_index:
            validation = self._run_resource_validation(output_analyses, inventory_index)
            results['resource_validation'] = validation
        else:
            results['resource_validation'] = {'note': 'No inventory provided'}
        
        # 3. Coverage scoring
        if inventory_index:
            coverage = self._run_coverage_analysis(output_analyses, inventory_index)
            results['coverage_analysis'] = coverage
        else:
            results['coverage_analysis'] = {'note': 'No inventory provided'}
        
        # 4. Gold standard test case scoring
        if test_cases:
            test_results = self._run_test_case_evaluation(test_cases, inventory_index)
            results['test_case_results'] = test_results
        else:
            results['test_case_results'] = {'note': 'No test cases provided'}
        
        # 5. Executive summary
        results['executive_summary'] = self._build_executive_summary(
            output_analyses, failure_taxonomy, results.get('resource_validation', {})
        )
        
        # 6. Per-trace detailed evals
        results['trace_evals'] = output_analyses
        
        return results

    def _build_inventory_index(
        self, resource_inventory: Optional[List[Dict]]
    ) -> Dict[str, Dict]:
        """Build searchable index from resource inventory."""
        if not resource_inventory:
            return {}
        
        index = {}
        for res in resource_inventory:
            if not isinstance(res, dict):
                continue
            # Use name as primary key, normalized
            name = res.get('name') or res.get('title') or res.get('organization_name') or ''
            if not name:
                continue
            normalized = self._normalize_resource_name(name)
            index[normalized] = res
            
            # Also index by alternate names if present
            for alt_key in ['alternate_names', 'aliases', 'also_known_as']:
                alts = res.get(alt_key, [])
                if isinstance(alts, str):
                    alts = [alts]
                for alt in alts:
                    if alt:
                        index[self._normalize_resource_name(alt)] = res
        
        return index

    def _normalize_resource_name(self, name: str) -> str:
        """Normalize resource name for matching."""
        if not name:
            return ''
        # Lowercase, remove punctuation, collapse whitespace
        normalized = re.sub(r'[^\w\s]', '', name.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

    def _run_failure_taxonomy(
        self, output_analyses: List[Dict], inventory_index: Dict
    ) -> Dict:
        """
        Classify each trace into structured failure categories.
        
        Failure Types:
        - relevance: resource doesn't match query intent/category
        - coverage: missed key resources for this query
        - location: resource outside requested geography
        - hallucination: resource not in known inventory
        - actionability: missing phone/address/URL
        - freshness: outdated information (if detectable)
        - safety: inappropriate content
        - generic: template/no-results response
        """
        failures = {
            'relevance': [],
            'coverage': [],
            'location': [],
            'hallucination': [],
            'actionability': [],
            'freshness': [],
            'safety': [],
            'generic': [],
            'too_short': [],
            'no_resources': [],
        }
        
        failure_counts = {k: 0 for k in failures.keys()}
        traces_with_failures = 0
        
        for analysis in output_analyses:
            trace_failures = []
            
            # Relevance failure
            if not analysis.get('category_aligned', True):
                trace_failures.append('relevance')
                failures['relevance'].append({
                    'trace_id': analysis.get('trace_id'),
                    'query': analysis.get('query', ''),
                    'expected_category': analysis.get('query_category', ''),
                    'reason': 'Category mismatch between query and response',
                })
            
            # Location failure
            if not analysis.get('location_aligned', True):
                trace_failures.append('location')
                failures['location'].append({
                    'trace_id': analysis.get('trace_id'),
                    'query': analysis.get('query', ''),
                    'expected_location': analysis.get('query_location', ''),
                    'reason': 'Location mismatch between query and response',
                })
            
            # Hallucination (only if we have inventory)
            if inventory_index:
                resources = analysis.get('resources_found', [])
                for res in resources:
                    res_name = res.get('name') or res.get('title') or ''
                    if res_name:
                        normalized = self._normalize_resource_name(res_name)
                        if normalized and normalized not in inventory_index:
                            trace_failures.append('hallucination')
                            failures['hallucination'].append({
                                'trace_id': analysis.get('trace_id'),
                                'resource_name': res_name,
                                'reason': 'Resource not found in known inventory',
                            })
            
            # Actionability failure
            if analysis.get('resource_count', 0) > 0 and not analysis.get('has_actionable_info', True):
                trace_failures.append('actionability')
                failures['actionability'].append({
                    'trace_id': analysis.get('trace_id'),
                    'query': analysis.get('query', ''),
                    'reason': 'Response has resources but no contact details',
                })
            
            # Generic response
            if analysis.get('is_generic', False):
                trace_failures.append('generic')
                failures['generic'].append({
                    'trace_id': analysis.get('trace_id'),
                    'query': analysis.get('query', ''),
                    'reason': 'Generic/template response detected',
                })
            
            # Too short
            if analysis.get('too_short', False):
                trace_failures.append('too_short')
                failures['too_short'].append({
                    'trace_id': analysis.get('trace_id'),
                    'query': analysis.get('query', ''),
                    'output_length': analysis.get('output_length', 0),
                    'reason': 'Response too short',
                })
            
            # No resources (for referral type) - be smarter about this check
            # Only flag if: it's a referral, no structured resources found, 
            # AND the output doesn't look like it contains resource information
            if analysis.get('trace_type') == 'referrals' and analysis.get('resource_count', 0) == 0:
                output_text_check = analysis.get('output_text', '').lower()
                output_length = analysis.get('output_length', 0)
                
                # Check if output text mentions resource-like content even if we couldn't parse it
                resource_indicators = [
                    'address', 'phone', '512-', '737-', '(512)', '(737)',
                    'website', 'www.', 'http', '.org', '.com',
                    'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                    'hours:', 'open:', 'services:', 'provides:', 'offers:',
                    'food bank', 'food pantry', 'shelter', 'clinic', 'assistance',
                    'central texas', 'austin', 'travis county'
                ]
                has_resource_content = any(ind in output_text_check for ind in resource_indicators)
                
                # Only flag as "no resources" if output is short AND doesn't look like resource content
                if output_length < 200 or not has_resource_content:
                    trace_failures.append('no_resources')
                    failures['no_resources'].append({
                        'trace_id': analysis.get('trace_id'),
                        'query': analysis.get('query', ''),
                        'reason': 'Referral query returned no resources',
                    })
            
            # Safety check (basic keyword detection)
            output_text = analysis.get('output_text', '').lower()
            safety_keywords = ['kill', 'suicide', 'harm yourself', 'dangerous', 'illegal']
            if any(kw in output_text for kw in safety_keywords):
                trace_failures.append('safety')
                failures['safety'].append({
                    'trace_id': analysis.get('trace_id'),
                    'query': analysis.get('query', ''),
                    'reason': 'Potentially unsafe content detected',
                })
            
            # Update analysis with failures
            analysis['failure_types'] = list(set(trace_failures))
            analysis['has_failures'] = len(trace_failures) > 0
            
            if trace_failures:
                traces_with_failures += 1
                for f in set(trace_failures):
                    failure_counts[f] += 1
        
        return {
            'failure_counts': failure_counts,
            'traces_with_failures': traces_with_failures,
            'traces_without_failures': len(output_analyses) - traces_with_failures,
            'failure_rate': traces_with_failures / len(output_analyses) * 100 if output_analyses else 0,
            'failures_by_type': {k: v[:20] for k, v in failures.items()},  # Top 20 examples each
            'top_failure_types': sorted(
                [(k, v) for k, v in failure_counts.items() if v > 0],
                key=lambda x: x[1], reverse=True
            ),
        }

    def _run_resource_validation(
        self, output_analyses: List[Dict], inventory_index: Dict
    ) -> Dict:
        """Validate recommended resources against known inventory."""
        total_resources = 0
        matched_resources = 0
        unmatched_resources = []
        matched_list = []
        
        for analysis in output_analyses:
            resources = analysis.get('resources_found', [])
            for res in resources:
                res_name = res.get('name') or res.get('title') or ''
                if not res_name:
                    continue
                total_resources += 1
                normalized = self._normalize_resource_name(res_name)
                
                if normalized in inventory_index:
                    matched_resources += 1
                    matched_list.append({
                        'recommended': res_name,
                        'matched_to': inventory_index[normalized].get('name', res_name),
                        'trace_id': analysis.get('trace_id'),
                    })
                else:
                    unmatched_resources.append({
                        'name': res_name,
                        'trace_id': analysis.get('trace_id'),
                        'query': analysis.get('query', ''),
                    })
        
        match_rate = matched_resources / total_resources * 100 if total_resources > 0 else 0
        
        return {
            'total_resources_recommended': total_resources,
            'matched_to_inventory': matched_resources,
            'unmatched_count': len(unmatched_resources),
            'match_rate': match_rate,
            'hallucination_rate': 100 - match_rate,
            'unmatched_resources': unmatched_resources[:50],  # Top 50
            'matched_sample': matched_list[:20],
            'inventory_size': len(inventory_index),
            'health': 'good' if match_rate >= 90 else ('warning' if match_rate >= 70 else 'critical'),
        }

    def _run_coverage_analysis(
        self, output_analyses: List[Dict], inventory_index: Dict
    ) -> Dict:
        """
        Analyze coverage: are we recommending the right breadth of resources?
        """
        # Group inventory by category
        inventory_by_category = defaultdict(list)
        for name, res in inventory_index.items():
            cat = res.get('category') or res.get('service_category') or res.get('type') or 'other'
            if isinstance(cat, list):
                for c in cat:
                    inventory_by_category[c.lower()].append(name)
            else:
                inventory_by_category[cat.lower()].append(name)
        
        # Track which resources are being recommended
        recommended_names = set()
        recommendations_by_category = defaultdict(set)
        
        for analysis in output_analyses:
            resources = analysis.get('resources_found', [])
            query_category = (analysis.get('query_category') or '').lower()
            
            for res in resources:
                res_name = res.get('name') or res.get('title') or ''
                if res_name:
                    normalized = self._normalize_resource_name(res_name)
                    recommended_names.add(normalized)
                    if query_category:
                        recommendations_by_category[query_category].add(normalized)
        
        # Calculate coverage metrics
        total_in_inventory = len(inventory_index)
        total_recommended = len(recommended_names)
        overall_coverage = total_recommended / total_in_inventory * 100 if total_in_inventory > 0 else 0
        
        # Per-category coverage
        category_coverage = {}
        for cat, resources in inventory_by_category.items():
            cat_recommended = recommendations_by_category.get(cat, set())
            cat_in_inventory = set(resources)
            overlap = len(cat_recommended & cat_in_inventory)
            category_coverage[cat] = {
                'inventory_count': len(cat_in_inventory),
                'recommended_count': len(cat_recommended),
                'overlap': overlap,
                'coverage_pct': overlap / len(cat_in_inventory) * 100 if cat_in_inventory else 0,
            }
        
        # Find under-utilized resources
        never_recommended = [
            inventory_index[name].get('name', name)
            for name in inventory_index.keys()
            if name not in recommended_names
        ][:50]
        
        return {
            'total_in_inventory': total_in_inventory,
            'total_ever_recommended': total_recommended,
            'overall_coverage_pct': overall_coverage,
            'category_coverage': dict(sorted(
                category_coverage.items(),
                key=lambda x: x[1]['coverage_pct']
            )),
            'under_utilized_resources': never_recommended,
            'under_utilized_count': total_in_inventory - total_recommended,
        }

    def _run_test_case_evaluation(
        self, test_cases: List[Dict], inventory_index: Dict
    ) -> Dict:
        """
        Evaluate against gold standard test cases.
        
        Test case format:
        {
            'query': 'I need food assistance in Austin',
            'expected_resources': ['Central Texas Food Bank', 'Caritas of Austin'],
            'expected_category': 'food',
            'expected_location': 'Austin',
        }
        """
        results = []
        passed = 0
        failed = 0
        
        for tc in test_cases:
            query = tc.get('query', '')
            expected_resources = set(
                self._normalize_resource_name(r)
                for r in tc.get('expected_resources', [])
            )
            expected_category = (tc.get('expected_category') or '').lower()
            expected_location = (tc.get('expected_location') or '').lower()
            
            # Find matching trace(s) for this query
            matching_traces = [
                a for a in self._build_output_analyses()
                if query.lower() in (a.get('query') or '').lower()
            ]
            
            if not matching_traces:
                results.append({
                    'query': query,
                    'status': 'no_match',
                    'reason': 'No trace found matching this test query',
                })
                continue
            
            # Take most recent matching trace
            trace = matching_traces[0]
            actual_resources = set(
                self._normalize_resource_name(r.get('name') or r.get('title') or '')
                for r in trace.get('resources_found', [])
            )
            
            # Calculate metrics
            resource_recall = len(actual_resources & expected_resources) / len(expected_resources) * 100 if expected_resources else 100
            resource_precision = len(actual_resources & expected_resources) / len(actual_resources) * 100 if actual_resources else 0
            
            category_match = expected_category in (trace.get('query_category') or '').lower() if expected_category else True
            location_match = expected_location in (trace.get('output_text') or '').lower() if expected_location else True
            
            # Determine pass/fail
            is_pass = resource_recall >= 80 and category_match and location_match
            
            if is_pass:
                passed += 1
            else:
                failed += 1
            
            results.append({
                'query': query,
                'status': 'pass' if is_pass else 'fail',
                'resource_recall': resource_recall,
                'resource_precision': resource_precision,
                'expected_resources': list(expected_resources),
                'actual_resources': list(actual_resources),
                'missing_resources': list(expected_resources - actual_resources),
                'extra_resources': list(actual_resources - expected_resources),
                'category_match': category_match,
                'location_match': location_match,
            })
        
        return {
            'total_test_cases': len(test_cases),
            'passed': passed,
            'failed': failed,
            'pass_rate': passed / len(test_cases) * 100 if test_cases else 0,
            'results': results,
        }

    def _build_executive_summary(
        self,
        output_analyses: List[Dict],
        failure_taxonomy: Dict,
        resource_validation: Dict,
    ) -> Dict:
        """Build executive summary for leadership reporting."""
        total = len(output_analyses)
        if total == 0:
            return {'error': 'No data for executive summary'}
        
        # Overall quality score (weighted composite)
        quality_scores = [a.get('quality_score', 0) for a in output_analyses]
        avg_quality = np.mean(quality_scores) if quality_scores else 0
        
        # Pass rate (traces with no critical failures)
        critical_failures = {'hallucination', 'safety', 'no_resources'}
        traces_with_critical = sum(
            1 for a in output_analyses
            if any(f in a.get('failure_types', []) for f in critical_failures)
        )
        pass_rate = (total - traces_with_critical) / total * 100
        
        # Failure summary
        _failure_counts = failure_taxonomy.get('failure_counts', {})
        top_failures = failure_taxonomy.get('top_failure_types', [])[:3]
        
        # Resource health
        match_rate = resource_validation.get('match_rate', 0)
        hallucination_rate = resource_validation.get('hallucination_rate', 0)
        
        # Actionability
        actionable_rate = sum(
            1 for a in output_analyses if a.get('has_actionable_info', False)
        ) / total * 100 if total else 0
        
        # Compute overall health score (0-100)
        health_score = (
            avg_quality * 0.3 +
            pass_rate * 0.3 +
            match_rate * 0.2 +
            actionable_rate * 0.2
        )
        
        health_status = 'excellent' if health_score >= 85 else (
            'good' if health_score >= 70 else (
                'needs_attention' if health_score >= 50 else 'critical'
            )
        )
        
        return {
            'health_score': round(health_score, 1),
            'health_status': health_status,
            'total_traces_evaluated': total,
            'avg_quality_score': round(avg_quality, 1),
            'pass_rate': round(pass_rate, 1),
            'match_rate': round(match_rate, 1),
            'hallucination_rate': round(hallucination_rate, 1),
            'actionable_rate': round(actionable_rate, 1),
            'top_failure_types': top_failures,
            'traces_with_any_failure': failure_taxonomy.get('traces_with_failures', 0),
            'failure_rate': round(failure_taxonomy.get('failure_rate', 0), 1),
            'recommendations': self._generate_exec_recommendations(
                health_score, top_failures, match_rate, actionable_rate
            ),
        }

    def _generate_exec_recommendations(
        self,
        health_score: float,
        top_failures: List,
        match_rate: float,
        actionable_rate: float,
    ) -> List[str]:
        """Generate actionable recommendations for leadership."""
        recs = []
        
        if health_score < 70:
            recs.append("🚨 Overall quality needs immediate attention")
        
        for failure_type, count in top_failures:
            if failure_type == 'hallucination' and count > 0:
                recs.append(f"⚠️ {count} potential hallucinations detected - verify resource inventory")
            elif failure_type == 'location' and count > 5:
                recs.append(f"📍 {count} location mismatches - improve geographic targeting")
            elif failure_type == 'relevance' and count > 5:
                recs.append(f"🎯 {count} relevance issues - refine category matching")
            elif failure_type == 'no_resources' and count > 5:
                recs.append(f"📋 {count} queries returned no resources - expand database")
            elif failure_type == 'generic' and count > 5:
                recs.append(f"📝 {count} generic responses - improve prompt specificity")
        
        if match_rate < 80:
            recs.append(f"🔍 Only {match_rate:.0f}% of resources match inventory - investigate data gaps")
        
        if actionable_rate < 70:
            recs.append(f"📞 Only {actionable_rate:.0f}% include contact info - enhance resource data")
        
        if not recs:
            recs.append("✅ No critical issues detected - continue monitoring")
        
        return recs

    def run_consistency_analysis(
        self, test_queries: List[str], num_runs: int = 3
    ) -> Dict:
        """
        Analyze consistency: do similar queries produce similar results?
        Note: This requires access to the actual LLM to re-run queries.
        For now, we analyze variance in existing traces with similar queries.
        """
        # Group traces by similar queries
        query_groups = defaultdict(list)
        
        output_analyses = self._build_output_analyses()
        for analysis in output_analyses:
            query = analysis.get('query', '')
            if not query:
                continue
            # Simple grouping by first few words
            key = ' '.join(query.lower().split()[:5])
            query_groups[key].append(analysis)
        
        consistency_results = []
        
        for key, analyses in query_groups.items():
            if len(analyses) < 2:
                continue
            
            # Analyze variance in responses
            quality_scores = [a.get('quality_score', 0) for a in analyses]
            resource_counts = [a.get('resource_count', 0) for a in analyses]
            
            # Collect all resources across runs
            all_resources = []
            for a in analyses:
                resources = a.get('resources_found', [])
                names = [
                    self._normalize_resource_name(r.get('name') or r.get('title') or '')
                    for r in resources
                ]
                all_resources.append(set(names))
            
            # Calculate Jaccard similarity between resource sets
            if len(all_resources) >= 2:
                similarities = []
                for i in range(len(all_resources)):
                    for j in range(i + 1, len(all_resources)):
                        a, b = all_resources[i], all_resources[j]
                        if a or b:
                            jaccard = len(a & b) / len(a | b) if (a | b) else 1.0
                            similarities.append(jaccard)
                avg_similarity = np.mean(similarities) if similarities else 1.0
            else:
                avg_similarity = 1.0
            
            consistency_results.append({
                'query_group': key,
                'num_traces': len(analyses),
                'quality_variance': np.var(quality_scores) if len(quality_scores) > 1 else 0,
                'resource_count_variance': np.var(resource_counts) if len(resource_counts) > 1 else 0,
                'resource_similarity': avg_similarity,
                'is_consistent': avg_similarity >= 0.7 and np.var(quality_scores) < 100,
            })
        
        # Sort by inconsistency
        consistency_results.sort(key=lambda x: x['resource_similarity'])
        
        inconsistent_count = sum(1 for r in consistency_results if not r['is_consistent'])
        
        return {
            'groups_analyzed': len(consistency_results),
            'inconsistent_groups': inconsistent_count,
            'consistency_rate': (len(consistency_results) - inconsistent_count) / len(consistency_results) * 100 if consistency_results else 100,
            'most_inconsistent': consistency_results[:10],
            'most_consistent': consistency_results[-10:] if len(consistency_results) >= 10 else [],
        }
