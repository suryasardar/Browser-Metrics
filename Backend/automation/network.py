"""
network.py

Captures browser network activity for a single dashboard run:
requests, responses, failed requests (4xx/5xx), console messages, and JS errors.

Adapted from a teammate's version, which used module-level globals — that would
leak data between the Source and Target runs since validator.py runs them
sequentially in the same process. This version is instance-scoped instead:
create one NetworkMonitor per dashboard run, register it on that run's page,
and read its summary() before moving to the next dashboard.
"""

import logging

logger = logging.getLogger("automation.network")


class NetworkMonitor:
    def __init__(self):
        self.requests = []
        self.responses = []
        self.failed_requests = []
        self.console_logs = []
        self.page_errors = []

    def register(self, page):
        """Attaches listeners for this run's page. Call once per dashboard run."""

        def handle_request(request):
            try:
                self.requests.append({
                    "method": request.method,
                    "url": request.url,
                    "resource_type": request.resource_type,
                })
            except Exception:
                logger.exception("Error handling request event")

        def handle_response(response):
            try:
                data = {
                    "url": response.url,
                    "status": response.status,
                    "status_text": response.status_text,
                    "ok": response.ok,
                }
                self.responses.append(data)
                if response.status >= 400:
                    self.failed_requests.append(data)
            except Exception:
                logger.exception("Error handling response event")

        def handle_console(message):
            try:
                self.console_logs.append({
                    "type": message.type,
                    "text": message.text,
                })
            except Exception:
                logger.exception("Error handling console event")

        def handle_page_error(error):
            try:
                self.page_errors.append(str(error))
            except Exception:
                logger.exception("Error handling page error event")

        try:
            page.on("request", handle_request)
            page.on("response", handle_response)
            page.on("console", handle_console)
            page.on("pageerror", handle_page_error)
        except Exception:
            logger.exception("Error registering network listeners")

    def summary(self) -> dict:
        """Lightweight counts, safe to attach to a METRICS payload."""
        return {
            "total_requests": len(self.requests),
            "total_responses": len(self.responses),
            "failed_requests": len(self.failed_requests),
            "console_messages": len(self.console_logs),
            "page_errors": len(self.page_errors),
        }

    def failure_details(self, max_items: int = 20) -> dict:
        """Fuller detail for surfacing *why* a filter/load might have failed."""
        return {
            "failed_requests": [
                {"url": r["url"], "status": r["status"]} for r in self.failed_requests[:max_items]
            ],
            "page_errors": list(self.page_errors[:max_items]),
        }