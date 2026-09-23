import logging
from playwright.async_api import Page

logger = logging.getLogger("automation.slicer")

POPUP_SELECTOR = ".slicer-dropdown-popup:visible, .slicer-dropdown-popup.focused"


class SlicerEngine:
    def __init__(self, page: Page):
        self.page = page

    async def _close_any_open_popups(self):
        """Ensures any currently open dropdown popup is actually closed (not just Escape-and-hope)."""
        try:
            popup = self.page.locator(".slicer-dropdown-popup:visible")
            if await popup.count() > 0:
                await self.page.keyboard.press("Escape")
                try:
                    await popup.first.wait_for(state="hidden", timeout=2000)
                except Exception:
                    pass
        except Exception:
            pass

    async def _open_dropdown(self, filter_name: str):
        """
        Locates the slicer's visual container, clicks its dropdown trigger, and waits
        for the popup AND at least one item row to actually render before returning it.
        This replaces fixed sleeps, which is what was causing CLICK_FAILED / NO_OPTIONS
        on slower-loading slicers (e.g. relative-date filters, or a slower data source).
        Returns the popup locator, or None if it never opened/populated.
        """
        slicer_visual = self.page.locator(
            f"visual-container:has(.slicer-header-text:text-is('{filter_name}'))"
        ).first
        if await slicer_visual.count() == 0:
            slicer_visual = self.page.locator(
                f"visual-container:has(.slicer-header-text:has-text('{filter_name}'))"
            ).first

        if await slicer_visual.count() == 0:
            logger.warning(f"Slicer visual '{filter_name}' not found in DOM.")
            return None

        dropdown_btn = slicer_visual.locator(
            ".slicer-dropdown-menu, .slicer-rest-item, [role='combobox']"
        ).first
        if await dropdown_btn.count() == 0:
            logger.warning(f"No dropdown trigger found for '{filter_name}'.")
            return None

        await dropdown_btn.click(force=True)

        popup = self.page.locator(POPUP_SELECTOR).first
        try:
            await popup.wait_for(state="visible", timeout=4000)
        except Exception:
            logger.warning(f"Popup never became visible for '{filter_name}'.")
            return None

        # Wait for the item list itself to populate (this is the part that was racing).
        try:
            await popup.locator(".slicerItemContainer").first.wait_for(state="visible", timeout=5000)
        except Exception:
            # Popup opened but items never rendered in time — caller decides what to do.
            logger.warning(f"Popup opened for '{filter_name}' but no items rendered within timeout.")

        return popup

    async def count_slicers(self) -> int:
        """Counts filter header titles in DOM."""
        try:
            count = await self.page.locator(".slicer-header-text").count()
            return count
        except Exception as e:
            logger.error(f"Error counting slicer elements: {e}")
            return 0

    async def extract_filters_from_dom(self) -> list[str]:
        """Extracts visible filter title strings using .slicer-header-text."""
        filter_names = []
        try:
            headers = self.page.locator(".slicer-header-text")
            count = await headers.count()
            for i in range(count):
                txt = await headers.nth(i).text_content()
                clean = txt.strip() if txt else ""
                if clean and clean not in filter_names:
                    filter_names.append(clean)
            return filter_names
        except Exception as e:
            logger.error(f"Error extracting DOM filter titles: {e}")
            return filter_names

    async def get_filter_options(self, filter_name: str) -> list[str]:
        """Ensures clean state, opens specific dropdown, waits for it to populate, and reads items."""
        logger.info(f"Reading options for filter: '{filter_name}'")
        options = []
        try:
            await self._close_any_open_popups()

            popup = await self._open_dropdown(filter_name)
            if popup is None:
                return options

            items = popup.locator(".slicerItemContainer .slicerText")
            count = await items.count()

            for i in range(min(count, 15)):
                txt = await items.nth(i).text_content()
                clean = txt.strip() if txt else ""
                if clean and clean not in options:
                    options.append(clean)

            await self._close_any_open_popups()

            logger.info(f"✅ Discovered options for '{filter_name}': {options}")
            return options

        except Exception as e:
            logger.error(f"Error reading options for '{filter_name}': {e}")
            await self._close_any_open_popups()
            return options

    async def apply_filter(self, filter_name: str, option_value: str) -> bool:
        """
        Selects option in the dropdown popup. Waits for the popup/items to actually
        render (not a fixed sleep), and retries opening the dropdown once if the
        target row isn't found the first time — the popup can genuinely still be
        populating (slow slicer, slow data source) even after it's visible.
        Does not sleep for DAX recalculation here — the caller times that separately.
        Returns True if the option was found and clicked.
        """
        logger.info(f"Applying filter: [{filter_name} = '{option_value}']")

        for attempt in range(2):
            try:
                await self._close_any_open_popups()

                popup = await self._open_dropdown(filter_name)
                if popup is None:
                    if attempt == 0:
                        continue  # retry once
                    return False

                target_row = popup.locator(
                    f".slicerItemContainer:has(.slicerText:text-is('{option_value}'))"
                ).first
                if await target_row.count() == 0:
                    target_row = popup.locator(
                        f".slicerItemContainer:has(.slicerText:has-text('{option_value}'))"
                    ).first

                if await target_row.count() == 0:
                    logger.warning(
                        f"Attempt {attempt + 1}: option '{option_value}' not found in '{filter_name}' popup."
                    )
                    await self._close_any_open_popups()
                    if attempt == 0:
                        continue  # retry once — popup may still have been populating
                    return False

                await target_row.scroll_into_view_if_needed()

                text_el = target_row.locator(".slicerText").first
                if await text_el.count() > 0:
                    await text_el.click(force=True)
                else:
                    await target_row.click(force=True)

                logger.info(f"✅ Successfully selected option '{option_value}' under '{filter_name}'.")

                await self.page.keyboard.press("Escape")
                await self.page.wait_for_timeout(300)
                return True

            except Exception as e:
                logger.error(f"Error applying filter '{filter_name}' = '{option_value}': {e}")
                await self._close_any_open_popups()
                if attempt == 0:
                    continue
                return False

        return False