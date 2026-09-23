import random
import time
import logging
from typing import Dict, Any, Callable, List
from .browser import launch_edge_profile, wait_for_dashboard, extract_navigation_pages
from .slicer import SlicerEngine
from utils.config import PAGE_TIMEOUT, FILTER_TEST_COUNT

logger = logging.getLogger("automation.validator")


class DashboardValidator:
    def __init__(self, send_log: Callable):
        self.send_log = send_log

    async def _emit(self, event_type: str, message: str, payload: dict = None):
        """Routes a message to the Python logger and out over the WebSocket to the UI."""
        if event_type == "ERROR":
            logger.error(message)
        elif event_type == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)

        log_data = {"event": event_type, "message": message}
        if payload:
            log_data.update(payload)
        await self.send_log(log_data)

    async def _test_one_filter(self, engine: SlicerEngine, page, filter_name: str) -> Dict[str, Any]:
        """Applies one random option of one filter and times the visual refresh."""
        result = {
            "filter_name": filter_name,
            "selected_option": None,
            "refresh_seconds": None,
            "status": "SKIPPED",
        }

        options = await engine.get_filter_options(filter_name)
        valid_options = [opt for opt in options if opt.lower() != "select all"]

        if not valid_options:
            result["status"] = "NO_OPTIONS"
            return result

        chosen_option = random.choice(valid_options)
        result["selected_option"] = chosen_option

        t1 = time.time()
        applied = await engine.apply_filter(filter_name, chosen_option)

        if not applied:
            result["status"] = "CLICK_FAILED"
            return result

        # Real "data changed" timer: wait for Power BI's own spinners to clear.
        await wait_for_dashboard(page, extra_delay=1.0)
        result["refresh_seconds"] = round(time.time() - t1, 2)
        result["status"] = "OK"
        return result

    async def _measure_dashboard(self, url: str, name: str) -> Dict[str, Any]:
        """
        Launches Edge, loads the dashboard, times the initial load, discovers filters
        on the landing page, then randomly samples a handful of them (FILTER_TEST_COUNT)
        and times how long the visuals take to refresh after each one is applied.
        """
        await self._emit("INFO", f"⏳ Launching Edge browser session for {name}...")

        playwright_instance, context, page = await launch_edge_profile()

        metrics = {
            "dashboard": name,
            "load_time_seconds": 0,
            "filter_count": 0,
            "filters": [],
            "filter_tests": [],
            "avg_refresh_seconds": None,
        }

        try:
            # 1. Load the report and time it
            t0 = time.time()
            logger.info(f"Navigating to {name} URL: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)

            initial_delay = 6.0 if "BigQuery" in name else 4.0
            await wait_for_dashboard(page, extra_delay=initial_delay)

            metrics["load_time_seconds"] = round(time.time() - t0, 2)
            await self._emit(
                "PERFORMANCE",
                f"⚡ {name} report loaded in {metrics['load_time_seconds']}s",
                payload={"dashboard": name, "load_time_seconds": metrics["load_time_seconds"]},
            )

            await extract_navigation_pages(page)  # context only, not used further here

            # 2. Discover filters on the current page
            engine = SlicerEngine(page)
            metrics["filter_count"] = await engine.count_slicers()
            metrics["filters"] = await engine.extract_filters_from_dom()

            await self._emit(
                "INFO",
                f"🎛️ [{name}] Found {metrics['filter_count']} filter(s): {metrics['filters']}",
            )

            # 3. Randomly sample up to FILTER_TEST_COUNT filters and time each one
            if metrics["filters"]:
                sample_size = min(FILTER_TEST_COUNT, len(metrics["filters"]))
                sampled_filters: List[str] = random.sample(metrics["filters"], sample_size)

                await self._emit(
                    "INFO",
                    f"🧪 [{name}] Testing {sample_size} randomly sampled filter(s): {sampled_filters}",
                )

                refresh_times = []
                for f_name in sampled_filters:
                    test_result = await self._test_one_filter(engine, page, f_name)
                    metrics["filter_tests"].append(test_result)

                    if test_result["status"] == "OK":
                        refresh_times.append(test_result["refresh_seconds"])
                        await self._emit(
                            "INFO",
                            f"✅ [{name}] '{f_name} = {test_result['selected_option']}' "
                            f"refreshed in {test_result['refresh_seconds']}s",
                        )
                    else:
                        await self._emit(
                            "WARNING",
                            f"[{name}] Filter '{f_name}' test result: {test_result['status']}",
                        )

                if refresh_times:
                    metrics["avg_refresh_seconds"] = round(sum(refresh_times) / len(refresh_times), 2)
            else:
                await self._emit("WARNING", f"[{name}] No filters detected on this dashboard.")

            # 4. Send the full metrics packet for this dashboard to the UI
            await self._emit(
                "METRICS",
                f"📊 [{name}] Metrics collected.",
                payload=metrics,
            )

            return metrics

        except Exception as e:
            err_msg = f"❌ Error measuring {name}: {str(e)}"
            await self._emit("ERROR", err_msg)
            return metrics

        finally:
            logger.info(f"Terminating Edge context for {name}...")
            if context:
                await context.close()
            if playwright_instance:
                await playwright_instance.stop()

    async def run_comparison_suite(self, source_url: str, target_url: str) -> Dict[str, Any]:
        """Runs the same load + sampled-filter timing measurement against both dashboards."""
        logger.info("================ STARTING DASHBOARD METRICS RUN ================")

        source_metrics = await self._measure_dashboard(source_url, "Snowflake (Source)")
        target_metrics = await self._measure_dashboard(target_url, "BigQuery (Target)")

        await self._emit("COMPLETE", "✅ Metrics collection complete!")
        logger.info("================ DASHBOARD METRICS RUN COMPLETE ================")

        return {"source": source_metrics, "target": target_metrics}