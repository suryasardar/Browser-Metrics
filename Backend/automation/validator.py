import asyncio
import time
import logging
from typing import Dict, Any, Callable
from .browser import launch_edge_profile, wait_for_dashboard, extract_navigation_pages, switch_to_page
from .slicer import SlicerEngine
from utils.config import PAGE_TIMEOUT

# Configure Logger
logger = logging.getLogger("automation.validator")


class DashboardValidator:
    def __init__(self, send_log: Callable):
        self.send_log = send_log

    async def _emit_log(self, event_type: str, message: str, payload: dict = None):
        """Unified logging helper to route messages to Python logger and React WebSocket UI."""
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

    async def _scrape_dashboard_full(self, url: str, name: str) -> Dict[str, Any]:
        """
        Launches Edge profile, navigates report tabs with extended wait buffers,
        counts DOM filters, and scrapes KPI metrics under default and filtered states.
        """
        await self._emit_log("INFO", f"⏳ Launching Edge browser session for {name}...")

        playwright_instance, context, page = await launch_edge_profile()

        data = {
            "load_time": 0,
            "pages": [],
            "page_details": {}
        }

        try:
            # 1. Initial Dashboard Load & Stabilization Buffer
            t0 = time.time()
            logger.info(f"Navigating to {name} URL: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)

            # BUMPED UP: Initial load stabilization delay (BigQuery: 6.0s | Snowflake: 4.0s)
            initial_delay = 6.0 if "BigQuery" in name else 4.0
            await wait_for_dashboard(page, extra_delay=initial_delay)

            data["load_time"] = round(time.time() - t0, 2)
            await self._emit_log("INFO", f"⚡ {name} report loaded and stabilized in {data['load_time']}s")

            # 2. Extract Report Navigation Pages using .itemName
            pages = await extract_navigation_pages(page)
            if not pages:
                pages = ["Default Overview"]
            data["pages"] = pages

            await self._emit_log("INFO", f"📄 [{name}] Found {len(pages)} report page tab(s): {', '.join(pages)}")

            engine = SlicerEngine(page)

            # 3. Process Each Page Tab
            for page_index, page_name in enumerate(pages):
                if page_index > 0:
                    await self._emit_log("INFO", f"🔄 [{name}] Switching tab to: '{page_name}'")
                    await switch_to_page(page, page_name)
                    
                    # BUMPED UP: 5.0-second delay after switching page tab to clear all spinners
                    await wait_for_dashboard(page, extra_delay=5.0)

                # Count Slicer Visuals in DOM (.slicer-header-text)
                filter_count = await engine.count_slicers()
                await self._emit_log("INFO", f"🎛️ [{name}] Tab '{page_name}': Identified {filter_count} filter visual(s) in DOM.")

                page_data = {
                    "filter_count": filter_count,
                    "permutations": {}
                }

                # Scrape Initial Default KPI Values
                default_kpis = await engine.extract_kpi_cards()
                page_data["permutations"]["Default Load"] = default_kpis

                # DOM Filter Discovery & Permutation Execution
                try:
                    detected_filters = await engine.extract_filters_from_dom()
                    
                    if detected_filters:
                        await self._emit_log("INFO", f"🔍 [{name}] Active slicer headers on '{page_name}': {detected_filters}")

                        # Limit permutation checks to top 2 filters for optimized runtime
                        for f_name in detected_filters[:2]:
                            options = await engine.get_filter_options(f_name)
                            valid_options = [opt for opt in options if opt.lower() != "select all"]
                            
                            if valid_options:
                                for opt in valid_options[:2]:
                                    perm_label = f"{f_name} = '{opt}'"
                                    await self._emit_log("INFO", f"🧪 [{name}] Testing filter state: {perm_label}")

                                    await engine.apply_filter(f_name, opt)
                                    
                                    # BUMPED UP: 4.5-second buffer after applying filter for DAX query recalculation
                                    logger.info("Waiting 4.5s for Power BI visuals to recalculate after filter application...")
                                    await page.wait_for_timeout(4500)

                                    perm_kpis = await engine.extract_kpi_cards()
                                    page_data["permutations"][perm_label] = perm_kpis

                except Exception as filter_err:
                    logger.warning(f"Filter interaction notice on '{page_name}': {filter_err}")

                data["page_details"][page_name] = page_data

            return data

        except Exception as e:
            err_msg = f"❌ Error scraping {name}: {str(e)}"
            await self._emit_log("ERROR", err_msg)
            return data

        finally:
            logger.info(f"Terminating Edge context for {name}...")
            if context:
                await context.close()
            if playwright_instance:
                await playwright_instance.stop()

    async def run_comparison_suite(self, source_url: str, target_url: str) -> Dict[str, Any]:
        """Executes full automated reconciliation between Source and Target."""
        logger.info("================ STARTING AUTOMATED RECONCILIATION SUITE ================")

        source_data = await self._scrape_dashboard_full(source_url, "Snowflake (Source)")
        target_data = await self._scrape_dashboard_full(target_url, "BigQuery (Target)")

        await self._emit_log(
            "PERFORMANCE",
            f"✅ Load Performance: Snowflake ({source_data['load_time']}s) | BigQuery ({target_data['load_time']}s)",
            payload={
                "snowflake_time": source_data['load_time'],
                "bigquery_time": target_data['load_time']
            }
        )

        src_pages = source_data.get("pages", [])
        tgt_pages = target_data.get("pages", [])
        shared_pages = list(set(src_pages) & set(tgt_pages))

        if len(src_pages) != len(tgt_pages):
            await self._emit_log(
                "WARNING",
                f"⚠️ Page Tab Count Mismatch! Snowflake has {len(src_pages)} tab(s) while BigQuery has {len(tgt_pages)} tab(s)."
            )

        all_results = []

        for page_name in (shared_pages if shared_pages else src_pages):
            src_page_info = source_data.get("page_details", {}).get(page_name, {})
            tgt_page_info = target_data.get("page_details", {}).get(page_name, {})

            src_f_count = src_page_info.get("filter_count", 0)
            tgt_f_count = tgt_page_info.get("filter_count", 0)

            if src_f_count != tgt_f_count:
                await self._emit_log(
                    "WARNING",
                    f"⚠️ Visual Filter Count Mismatch on '{page_name}'! Snowflake DOM: {src_f_count} | BigQuery DOM: {tgt_f_count}."
                )

            src_perms = src_page_info.get("permutations", {})
            tgt_perms = tgt_page_info.get("permutations", {})
            shared_perms = set(src_perms.keys()) | set(tgt_perms.keys())

            for state_label in shared_perms:
                kpis_src = src_perms.get(state_label, {})
                kpis_tgt = tgt_perms.get(state_label, {})

                failures = []
                passed = 0
                all_kpi_keys = set(kpis_src.keys()) | set(kpis_tgt.keys())

                for key in all_kpi_keys:
                    v_src = kpis_src.get(key, "N/A")
                    v_tgt = kpis_tgt.get(key, "N/A")

                    if str(v_src).strip() == str(v_tgt).strip() and v_src != "N/A":
                        passed += 1
                    else:
                        try:
                            clean_src = ''.join(c for c in str(v_src) if c.isdigit() or c == '.' or c == '-')
                            clean_tgt = ''.join(c for c in str(v_tgt) if c.isdigit() or c == '.' or c == '-')

                            n_src = float(clean_src)
                            n_tgt = float(clean_tgt)

                            diff = round(n_tgt - n_src, 2)
                            pct = round((diff / n_src) * 100, 2) if n_src != 0 else 0
                        except Exception:
                            diff = "N/A"
                            pct = "N/A"

                        failures.append({
                            "kpi_name": key,
                            "snowflake_value": v_src,
                            "bigquery_value": v_tgt,
                            "difference_delta": diff,
                            "variance_percentage": f"{pct}%" if pct != "N/A" else "N/A"
                        })

                status = "FAIL" if failures else "PASS"
                payload = {
                    "event": "FILTER_PERMUTATION_RESULT",
                    "page": page_name,
                    "filters_applied": {"State": state_label},
                    "summary": {
                        "status": status,
                        "total_metrics_checked": len(all_kpi_keys),
                        "passed_count": passed,
                        "failed_count": len(failures)
                    },
                    "failures": failures
                }

                await self.send_log(payload)
                all_results.append(payload)

        await self._emit_log("COMPLETE", "✅ Automated Reconciliation Complete!")
        logger.info("================ RECONCILIATION SUITE COMPLETE ================")

        return {"results": all_results}