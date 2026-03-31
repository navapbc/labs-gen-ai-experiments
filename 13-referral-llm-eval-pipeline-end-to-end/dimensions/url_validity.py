from __future__ import annotations

"""Check URLs in resources via HEAD requests."""
from dimensions.base import EvalDimension, DimensionResult


class UrlValidityDimension(EvalDimension):
    name = 'url_validity'

    def evaluate(self, resources: list[dict], context: dict) -> DimensionResult:
        flags = []
        skip_validation = self.config.get('skip_validation', False)
        timeout = self.config.get('timeout', 10)
        url_results = []

        for res in resources:
            if not isinstance(res, dict):
                continue
            website = res.get('website', '') or res.get('url', '')
            name = res.get('name', '')

            if not website:
                url_results.append({'resource': name, 'url': '', 'status': 'MISSING'})
                continue

            if skip_validation:
                url_results.append({'resource': name, 'url': website, 'status': 'UNCHECKED'})
                continue

            status = self._check_url(website, timeout)
            url_results.append({'resource': name, 'url': website, 'status': status})

        broken = [u for u in url_results if u['status'] in ('BROKEN_404', 'SERVER_ERROR')]
        missing = [u for u in url_results if u['status'] == 'MISSING']
        homepage_redirects = [u for u in url_results if u['status'] == 'HOMEPAGE_REDIRECT']

        if broken:
            flags.append('BROKEN_URL')
        if missing and len(missing) > len(resources) * 0.5:
            flags.append('MANY_MISSING_URLS')
        if homepage_redirects:
            flags.append('HOMEPAGE_ONLY')

        return DimensionResult(flags=flags, details={'url_results': url_results})

    def _check_url(self, url: str, timeout: int) -> str:
        import httpx
        try:
            resp = httpx.head(url, follow_redirects=True, timeout=float(timeout), verify=False)
            if resp.status_code == 200:
                final_url = str(resp.url)
                original_path = url.rstrip('/').split('/')
                final_path = final_url.rstrip('/').split('/')
                if len(original_path) > 3 and len(final_path) <= 3:
                    return 'HOMEPAGE_REDIRECT'
                return 'VALID'
            elif resp.status_code == 404:
                return 'BROKEN_404'
            elif resp.status_code == 403:
                return 'FORBIDDEN'
            elif resp.status_code >= 500:
                return 'SERVER_ERROR'
            else:
                return f'HTTP_{resp.status_code}'
        except httpx.TimeoutException:
            return 'TIMEOUT'
        except Exception as e:
            return f'ERROR_{type(e).__name__}'
