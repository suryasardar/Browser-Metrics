import logging
import asyncio
from playwright.async_api import Page

logger = logging.getLogger("automation.slicer")

class SlicerEngine:
    def __init__(self, page: Page):
        self.page = page

    async def count_slicers(self) -> int:
        """Counts all active slicer/filter elements in the Power BI DOM."""
        try:
            selector = "pbi-slicer, .slicer-container, .slicer, visual-container:has(.slicer-dropdown-menu), visual-container:has(.slicer-rest-item)"
            count = await self.page.locator(selector).count()
            logger.info(f"DOM Slicer Scan: Found {count} filter element(s).")
            return count
        except Exception as e:
            logger.error(f"Error counting slicer elements: {e}")
            return 0

    async def extract_kpi_cards(self) -> dict:
        """Extracts KPI card values and labels from visual containers."""
        logger.info("Extracting KPI metrics from report visuals...")
        kpis = {}
        try:
            visuals = self.page.locator("visual-container")
            count = await visuals.count()
            logger.info(f"Scanning {count} visual container(s) for KPI values...")
            
            for i in range(count):
                visual = visuals.nth(i)
                text = await visual.inner_text()
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                
                # If visual contains a metric label and value
                if len(lines) >= 2:
                    label = lines[0]
                    value = lines[1]
                    # Exclude long text paragraphs or slicer header clutter
                    if len(label) < 40 and len(value) < 25:
                        kpis[label] = value

            logger.info(f"Extracted {len(kpis)} KPI metric(s): {kpis}")
            return kpis
        except Exception as e:
            logger.error(f"Error extracting KPI cards: {e}")
            return kpis

    async def get_filter_options(self, filter_name: str) -> list[str]:
        """Finds options available inside a specific slicer visual."""
        logger.info(f"Fetching available filter options for slicer: '{filter_name}'")
        options = []
        try:
            # Locate slicer visual matching the header title
            slicer_visual = self.page.locator(f"visual-container:has-text('{filter_name}')").first
            if await slicer_visual.count() == 0:
                logger.warning(f"Slicer visual '{filter_name}' not found in DOM.")
                return options

            # Expand dropdown if it's a dropdown slicer
            dropdown_btn = slicer_visual.locator(".slicer-dropdown-menu, [role='button']").first
            if await dropdown_btn.count() > 0 and await dropdown_btn.is_visible():
                await dropdown_btn.click()
                await self.page.wait_for_timeout(500)

            # Read items from popup list or checkbox container
            items = self.page.locator(".slicerItemContainer, .slicerText, [role='option']")
            item_count = await items.count()
            
            for i in range(min(item_count, 10)):  # Read top 10 options
                opt_text = await items.nth(i).inner_text()
                if opt_text.strip() and opt_text.strip() not in options:
                    options.append(opt_text.strip())

            logger.info(f"Discovered options for '{filter_name}': {options}")
            return options
        except Exception as e:
            logger.error(f"Failed to fetch filter options for '{filter_name}': {e}")
            return options

    async def apply_filter(self, filter_name: str, option_value: str):
        """Selects a specific filter option in a slicer."""
        logger.info(f"Applying filter permutation: [{filter_name} = '{option_value}']")
        try:
            slicer_visual = self.page.locator(f"visual-container:has-text('{filter_name}')").first
            
            # Click option matching value
            target_item = slicer_visual.locator(f".slicerItemContainer:has-text('{option_value}'), [role='option']:has-text('{option_value}')").first
            if await target_item.count() > 0:
                await target_item.click()
                logger.info(f"Successfully selected filter option '{option_value}'.")
            else:
                logger.warning(f"Option value '{option_value}' not found in slicer '{filter_name}'.")
                
            await self.page.wait_for_timeout(1500)  # Wait for visuals to update
        except Exception as e:
            logger.error(f"Error applying filter '{filter_name}' = '{option_value}': {e}")