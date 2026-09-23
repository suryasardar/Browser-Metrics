import os
import asyncio
import logging
from pathlib import Path
from playwright.async_api import async_playwright, Page
from utils.config import PAGE_TIMEOUT, RENDER_WAIT

# Configure Logger
logger = logging.getLogger("automation.browser")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

EDGE_USER_DATA = Path(os.path.expanduser("~")) / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data"

def find_edge_profiles():
    """Scans for profile subfolders (Default, Profile 1, Profile 2, etc.)."""
    if not EDGE_USER_DATA.exists():
        logger.error(f"Edge User Data directory not found at {EDGE_USER_DATA}")
        raise FileNotFoundError(f"Edge User Data directory not found at {EDGE_USER_DATA}")

    profiles = []
    for folder in EDGE_USER_DATA.iterdir():
        if folder.is_dir() and (folder.name == "Default" or folder.name.startswith("Profile")):
            profiles.append(folder)

    sorted_profiles = sorted(profiles, key=lambda p: p.name != "Default")
    logger.info(f"Discovered {len(sorted_profiles)} Edge profile folder(s): {[p.name for p in sorted_profiles]}")
    return sorted_profiles

async def launch_edge_profile():
    """Tries launching available Edge profile subfolders until one succeeds."""
    profiles = find_edge_profiles()

    logger.info("Executing background process cleanup for msedge.exe...")
    os.system("taskkill /f /im msedge.exe >nul 2>&1")
    await asyncio.sleep(1.5)

    for profile_path in profiles:
        try:
            logger.info(f"Attempting browser launch with profile directory: {profile_path}")
            playwright = await async_playwright().start()

            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=str(profile_path),
                channel="msedge",
                headless=False,
                slow_mo=300,
                no_viewport=True,
                args=["--start-maximized"]
            )

            page = context.pages[0] if context.pages else await context.new_page()
            await page.bring_to_front()

            logger.info(f"✅ Edge successfully initialized using profile subfolder: '{profile_path.name}'")
            return playwright, context, page

        except Exception as e:
            logger.warning(f"Profile '{profile_path.name}' locked or unavailable: {e}")
            try:
                if 'context' in locals() and context: await context.close()
                if 'playwright' in locals() and playwright: await playwright.stop()
            except Exception:
                pass

    logger.critical("Failed to launch Microsoft Edge with any detected profile subfolders.")
    raise RuntimeError("Could not launch Microsoft Edge with any available profile.")

async def wait_for_dashboard(page: Page, extra_delay: float = 3.0):
    """
    Waits for visual containers to attach, then polls until the dashboard reaches
    a genuinely stable, non-loading state instead of guessing with a fixed sleep.

    Adapted from a teammate's signature-based stability check: on each 500ms tick,
    take a fingerprint of every visual's text content, and only declare the
    dashboard ready once that fingerprint stops changing AND no loading
    spinners/placeholders are present, for 3 consecutive samples in a row.
    This is what actually fixed the CLICK_FAILED / NO_OPTIONS races you were
    seeing — a fixed delay can't adapt to a slower backend (e.g. BigQuery),
    this polling loop can.
    """
    logger.info("Waiting for Power BI visual containers to attach to DOM...")

    # 1. Wait for containers to attach
    await page.wait_for_selector(
        "visual-container, .visualContainer",
        state="attached",
        timeout=PAGE_TIMEOUT
    )

    # 2. Poll for a quiet, non-loading, text-stable state
    logger.info("Polling for a stable, fully-rendered dashboard state...")
    stable_samples = 0
    previous_signature = None
    max_ticks = max(6, RENDER_WAIT // 500)

    for _ in range(max_ticks):
        try:
            signature = await page.evaluate(
                """() => [...document.querySelectorAll('visual-container, .visualContainer')]
                    .map(node => (node.innerText || '').trim())
                    .filter(Boolean)
                    .join('\\n')
                    .slice(0, 50000)"""
            )
        except Exception:
            signature = None

        loading_count = await page.locator(
            ".loading-spinner, .visual-loading, .gxp-visual-container-spinner, "
            "[aria-label*='loading' i], [aria-busy='true']"
        ).count()

        try:
            has_loading_placeholder = await page.evaluate(
                """() => [...document.querySelectorAll('visual-container, .visualContainer')].some(node =>
                    /\\bvisuals?\\s+are\\s+loading\\b/i.test((node.innerText || '').trim()))"""
            )
        except Exception:
            has_loading_placeholder = False

        if signature is not None and signature == previous_signature and loading_count == 0 and not has_loading_placeholder:
            stable_samples += 1
            if stable_samples >= 3:
                logger.info("✅ Dashboard reached a stable, fully-rendered state.")
                break
        else:
            stable_samples = 0

        previous_signature = signature
        await page.wait_for_timeout(500)
    else:
        logger.warning("Dashboard did not confirm a fully stable state within the polling window; continuing anyway.")

    # 3. Small extra buffer for any trailing DAX recalculation, kept configurable per caller
    if extra_delay > 0:
        logger.info(f"Stabilization buffer ({extra_delay}s)...")
        await page.wait_for_timeout(int(extra_delay * 1000))

async def extract_navigation_pages(page: Page) -> list[str]:
    """Extracts page tab names safely using .itemName and text_content()."""
    pages = []
    try:
        # Primary: Target .itemName directly inside the navigation panel
        tabs = page.locator(".itemName, .page-navigation .itemName")
        count = await tabs.count()

        # Fallback: Use standard tab roles if .itemName is not present
        if count == 0:
            tabs = page.locator(".page-navigation [role='tab'], .page-navigation [role='treeitem']")
            count = await tabs.count()

        for i in range(count):
            try:
                name = await tabs.nth(i).text_content()
                clean_name = name.strip() if name else ""
                if clean_name and clean_name not in pages:
                    pages.append(clean_name)
            except Exception:
                continue

        logger.info(f"Extracted page names: {pages}")
    except Exception as e:
        logger.error(f"Failed to extract navigation pages: {e}")
    return pages

async def switch_to_page(page: Page, page_name: str):
    """Switches to a specific report page tab using .itemName."""
    try:
        logger.info(f"Switching report tab to: '{page_name}'")

        # Target .itemName directly matching the target page name
        tab = page.locator(f".itemName:has-text('{page_name}')").first

        # Fallback to standard ARIA roles if .itemName is not found
        if await tab.count() == 0:
            tab = page.locator(f".page-navigation [role='tab']:has-text('{page_name}'), [role='treeitem']:has-text('{page_name}')").first

        await tab.click()
        logger.info(f"✅ Successfully clicked tab: '{page_name}'. Waiting for dashboard stabilization...")
        await wait_for_dashboard(page)
    except Exception as e:
        logger.error(f"Failed to switch to page '{page_name}': {e}")