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

async def wait_for_dashboard(page: Page):
    """Waits for Power BI visual elements to attach to the DOM and stabilize."""
    logger.info("Waiting for Power BI visual containers to attach to DOM...")
    await page.wait_for_selector(
        "visual-container, .visualContainer", 
        state="attached", 
        timeout=PAGE_TIMEOUT
    )
    logger.info("Visual containers attached. Stabilizing visual calculations...")
    await page.wait_for_timeout(RENDER_WAIT)

async def extract_navigation_pages(page: Page) -> list[str]:
    """Extracts report page tab names from the left or bottom navigation panel."""
    pages = []
    try:
        tabs = page.locator(".page-navigation [role='tab'], [role='treeitem']")
        count = await tabs.count()
        logger.info(f"Detected {count} page navigation element(s) in DOM.")
        for i in range(count):
            name = await tabs.nth(i).inner_text()
            if name.strip():
                pages.append(name.strip())
        logger.info(f"Extracted page names: {pages}")
    except Exception as e:
        logger.error(f"Failed to extract navigation pages: {e}")
    return pages

async def switch_to_page(page: Page, page_name: str):
    """Navigates to a specific page tab in the report."""
    try:
        logger.info(f"Switching report tab to: '{page_name}'")
        tab = page.locator(f".page-navigation [role='tab']:has-text('{page_name}'), [role='treeitem']:has-text('{page_name}')").first
        await tab.click()
        await wait_for_dashboard(page)
    except Exception as e:
        logger.error(f"Failed to switch to page '{page_name}': {e}")