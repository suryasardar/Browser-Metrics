import os
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright, Page
from utils.config import PAGE_TIMEOUT, RENDER_WAIT

# Path to the parent User Data directory on Windows
EDGE_USER_DATA = Path(os.path.expanduser("~")) / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data"

def find_edge_profiles():
    """Scans for actual profile subfolders (Default, Profile 1, Profile 2, etc.)"""
    if not EDGE_USER_DATA.exists():
        raise FileNotFoundError(f"Edge User Data directory not found at {EDGE_USER_DATA}")

    profiles = []
    for folder in EDGE_USER_DATA.iterdir():
        if folder.is_dir() and (folder.name == "Default" or folder.name.startswith("Profile")):
            profiles.append(folder)
            
    # Try 'Default' profile first, then remaining profiles
    return sorted(profiles, key=lambda p: p.name != "Default")

async def launch_edge_profile():
    """Tries launching available Edge profile subfolders until one succeeds."""
    profiles = find_edge_profiles()
    print(f"DEBUG: Found {len(profiles)} Edge profiles: {[p.name for p in profiles]}")

    # Force cleanup background processes first
    os.system("taskkill /f /im msedge.exe >nul 2>&1")
    await asyncio.sleep(1.5)

    for profile_path in profiles:
        try:
            print(f"DEBUG: Attempting to launch with profile: {profile_path}")
            playwright = await async_playwright().start()
            
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=str(profile_path),  # Must point to specific subfolder (e.g., .../User Data/Default)
                channel="msedge",
                headless=False,
                slow_mo=300,
                no_viewport=True,
                args=["--start-maximized"]
            )
            
            page = context.pages[0] if context.pages else await context.new_page()
            await page.bring_to_front()
            
            print(f"✅ Successfully launched profile: {profile_path.name}")
            return playwright, context, page

        except Exception as e:
            print(f"⚠️ Profile '{profile_path.name}' failed or locked: {e}")
            try:
                if 'context' in locals() and context:
                    await context.close()
                if 'playwright' in locals() and playwright:
                    await playwright.stop()
            except Exception:
                pass

    raise RuntimeError("Could not launch Microsoft Edge with any available profile.")

async def wait_for_dashboard(page: Page):
    """Waits for Power BI visuals to attach to the DOM and allow layout to render."""
    print("DEBUG: Waiting for Power BI visuals to load into DOM...")
    
    # Use state="attached" so hidden or off-screen visual containers don't trigger timeouts
    await page.wait_for_selector(
        "visual-container, .visualContainer", 
        state="attached", 
        timeout=PAGE_TIMEOUT
    )
    
    print("DEBUG: Visual containers attached! Allowing numbers to calculate...")
    # Give Power BI visuals time to finish calculations and rendering animations
    await page.wait_for_timeout(RENDER_WAIT)

async def extract_navigation_pages(page: Page) -> list[str]:
    """Extracts the names of the pages from the left navigation pane."""
    pages = []
    try:
        tabs = page.locator(".page-navigation [role='tab'], [role='treeitem']")
        count = await tabs.count()
        for i in range(count):
            name = await tabs.nth(i).inner_text()
            if name.strip():
                pages.append(name.strip())
    except Exception as e:
        print(f"Failed to extract pages: {e}")
    return pages

async def switch_to_page(page: Page, page_name: str):
    """Clicks a page tab in the Power BI navigation menu."""
    try:
        tab = page.locator(f".page-navigation [role='tab']:has-text('{page_name}'), [role='treeitem']:has-text('{page_name}')").first
        await tab.click()
        await wait_for_dashboard(page)
    except Exception as e:
        print(f"Failed to switch to {page_name}: {e}")