import asyncio
from typing import Dict, List
from playwright.async_api import Page

class SlicerEngine:
    def __init__(self, page: Page):
        self.page = page

    async def get_filter_options(self, filter_name: str) -> List[str]:
        """Extracts options from a dropdown slicer."""
        options = []
        try:
            container = self.page.locator("visual-container").filter(has_text=filter_name).first
            dropdown_btn = container.locator("[role='combobox'], .slicer-dropdown-menu").first
            await dropdown_btn.click(timeout=5000)
            await self.page.wait_for_timeout(800)

            option_elements = self.page.locator("[role='option'], .row")
            count = await option_elements.count()

            for i in range(count):
                text = await option_elements.nth(i).inner_text()
                clean_text = text.strip().split("\n")[0]
                if clean_text and clean_text.lower() != "select all":
                    options.append(clean_text)

            await self.page.keyboard.press("Escape")
        except Exception:
            await self.page.keyboard.press("Escape")

        return options

    async def clear_filter(self, filter_name: str):
        try:
            container = self.page.locator("visual-container").filter(has_text=filter_name).first
            clear_btn = container.locator(".clear-selections, [title='Clear selections']")
            if await clear_btn.is_visible():
                await clear_btn.click()
                await self.page.wait_for_timeout(1000)
        except Exception:
            pass

    async def apply_filter(self, filter_name: str, option_value: str) -> bool:
        try:
            await self.clear_filter(filter_name)
            container = self.page.locator("visual-container").filter(has_text=filter_name).first
            dropdown_btn = container.locator("[role='combobox'], .slicer-dropdown-menu").first
            await dropdown_btn.click(timeout=5000)
            await self.page.wait_for_timeout(800)

            target_option = self.page.locator("[role='option'], .row").filter(has_text=option_value).first
            await target_option.click(timeout=4000)

            await self.page.keyboard.press("Escape")
            await self.page.wait_for_timeout(2000) # Wait for DAX recalculation
            return True
        except Exception:
            await self.page.keyboard.press("Escape")
            return False

    async def extract_kpi_cards(self) -> Dict[str, str]:
        kpi_data = {}
        try:
            cards = self.page.locator("visual-container:has(.card), visual-container:has(svg.card)")
            count = await cards.count()
            for i in range(count):
                text_content = await cards.nth(i).inner_text()
                lines = [line.strip() for line in text_content.split("\n") if line.strip()]
                if len(lines) >= 2:
                    val, label = lines[0], lines[1]
                    if any(char.isdigit() for char in val):
                        kpi_data[label] = val
                    else:
                        kpi_data[val] = label
        except Exception:
            pass
        return kpi_data