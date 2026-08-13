import asyncio
import time
import random
from typing import Dict, Any, Callable
from .browser import launch_edge_profile, wait_for_dashboard, extract_navigation_pages, switch_to_page
from .slicer import SlicerEngine
from services.ai import extract_filters
from utils.config import SCREENSHOT_DIR, PAGE_TIMEOUT

class DashboardValidator:
    def __init__(self, send_log: Callable):
        self.send_log = send_log

    async def _scrape_dashboard(self, url: str, name: str) -> Dict[str, Any]:
        """Opens the browser, scrapes a single dashboard, and closes the browser."""
        await self.send_log({"event": "INFO", "message": f"⏳ Starting browser for {name}..."})
        
        print(f"DEBUG: Preparing to load {name} -> '{url}'")
        
        playwright_instance, context, page = await launch_edge_profile()
        
        data = {
            "load_time": 0,
            "pages": [],
            "kpis": {}
        }
        
        try:
            print("DEBUG: Playwright gave us a tab. Injecting URL now...")
            t0 = time.time()
            
            # The exact moment of truth
            await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
            
            print("DEBUG: URL successfully loaded in the browser!")
            await wait_for_dashboard(page)
            data["load_time"] = round(time.time() - t0, 2)
            
            print(f"DEBUG: Extracting navigation pages for {name}...")
            # 2. Get Navigation Pages
            data["pages"] = await extract_navigation_pages(page)
            
            print(f"DEBUG: Extracting KPIs for {name}...")
            # 3. Extract KPIs from the default loaded page
            engine = SlicerEngine(page)
            data["kpis"] = await engine.extract_kpi_cards()

            return data
            
        except Exception as e:
            error_msg = f"❌ Error scraping {name}: {str(e)}"
            print(f"DEBUG: {error_msg}")
            await self.send_log({"event": "ERROR", "message": error_msg})
            return data
            
        finally:
            print(f"DEBUG: Cleaning up and closing browser for {name}...")
            if context: await context.close()
            if playwright_instance: await playwright_instance.stop()

    async def run_comparison_suite(self, source_url: str, target_url: str) -> Dict[str, Any]:
        print("\n--- STARTING AUTOMATED QA SUITE ---")
        
        # 1. Scrape Source (Snowflake)
        source_data = await self._scrape_dashboard(source_url, "Snowflake (Source)")
        
        # 2. Scrape Target (BigQuery)
        target_data = await self._scrape_dashboard(target_url, "BigQuery (Target)")
        
        # 3. Compare Load Times
        await self.send_log({
            "event": "PERFORMANCE",
            "message": f"✅ Load Time: Snowflake ({source_data['load_time']}s) | BigQuery ({target_data['load_time']}s)",
            "snowflake_time": source_data['load_time'],
            "bigquery_time": target_data['load_time']
        })

        # 4. Compare Pages (Schema Check)
        if len(source_data["pages"]) != len(target_data["pages"]):
            await self.send_log({"event": "WARNING", "message": f"⚠️ Page mismatch! Snowflake: {len(source_data['pages'])}, BigQuery: {len(target_data['pages'])}"})

        # 5. Compare KPIs
        print("DEBUG: Comparing KPI values...")
        failures = []
        passed = 0
        all_keys = set(source_data["kpis"].keys()) | set(target_data["kpis"].keys())
        
        for key in all_keys:
            v_src = source_data["kpis"].get(key, "N/A")
            v_tgt = target_data["kpis"].get(key, "N/A")
            
            if v_src == v_tgt and v_src != "N/A":
                passed += 1
            else:
                try:
                    n_src = float(''.join(c for c in str(v_src) if c.isdigit() or c == '.' or c == '-'))
                    n_tgt = float(''.join(c for c in str(v_tgt) if c.isdigit() or c == '.' or c == '-'))
                    diff = round(n_tgt - n_src, 2)
                    pct = round((diff / n_src) * 100, 2) if n_src != 0 else 0
                except:
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
            "page": "Default Overview",
            "filters_applied": {"State": "Default Load"},
            "summary": {
                "status": status,
                "total_metrics_checked": len(all_keys),
                "passed_count": passed,
                "failed_count": len(failures)
            },
            "failures": failures
        }
        
        await self.send_log(payload)
        await self.send_log({"event": "COMPLETE", "message": "✅ Validation finished!"})
        print("--- QA SUITE COMPLETED ---")
        
        return {"results": [payload]}