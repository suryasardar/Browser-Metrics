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
    Waits for visual containers to attach, waits for Power BI loading spinners 
    to disappear, and adds a stabilization buffer.
    """
    logger.info("Waiting for Power BI visual containers to attach to DOM...")
    
    # 1. Wait for containers to attach
    await page.wait_for_selector(
        "visual-container, .visualContainer", 
        state="attached", 
        timeout=PAGE_TIMEOUT
    )
    
    # 2. Wait for loading spinners/overlays to detach (disappear)
    try:
        logger.info("Waiting for Power BI data loading spinners to clear...")
        await page.wait_for_selector(
            ".loading-spinner, .visual-loading, .gxp-visual-container-spinner", 
            state="detached", 
            timeout=10000
        )
    except Exception:
        # Spinners cleared or were not present
        pass

    # 3. Dedicated stabilization pause for visual data rendering
    logger.info(f"Stabilizing visual calculations ({extra_delay}s buffer)...")
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