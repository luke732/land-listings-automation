"""
Browser Automation Posters for Land.com and LandFlip.com
Uses Playwright (headless Chromium) to log in and submit listings.

NOTE: Browser automation is inherently fragile - if Land.com or LandFlip update
their UI, selectors may need updating. The code uses multiple fallback selectors
and logs exactly where it succeeds or fails to make debugging easy.
"""
import asyncio
import logging
from config import (
    LAND_COM_USERNAME, LAND_COM_PASSWORD,
    LANDFLIP_USERNAME, LANDFLIP_PASSWORD,
)

logger = logging.getLogger(__name__)


# ── Shared helpers ────────────────────────────────────────────────────────────

async def _safe_fill(page, selectors: list, value: str):
    """Try each CSS selector in order until one works."""
    if not value:
        return
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.count() > 0:
                await loc.fill(str(value))
                return
        except Exception:
            continue
    logger.debug(f"Could not fill any of {selectors}")


async def _safe_click(page, selectors: list):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.count() > 0:
                await loc.click()
                return True
        except Exception:
            continue
    return False


def _build_title(prop: dict) -> str:
    return (
        prop.get('title')
        or f"{prop.get('acreage', '')} Acres \u2013 {prop.get('county', '')}, {prop.get('state', '')}"
    )


# ── Land.com ──────────────────────────────────────────────────────────────────

class LandComPoster:
    LOGIN_URL       = "https://network.land.com/login/"
    ADD_LISTING_URL = "https://network.land.com/listings/add/"

    async def post_listing(self, property_data: dict, image_paths: list = None) -> str:
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=['--no-sandbox'])
            context = await browser.new_context(viewport={'width': 1280, 'height': 900})
            page = await context.new_page()
            try:
                await self._login(page)
                await page.goto(self.ADD_LISTING_URL, wait_until='networkidle')
                await self._fill_form(page, property_data, image_paths or [])
                await self._submit(page)
                url = page.url
                logger.info(f"Land.com listing submitted. Page: {url}")
                return url
            finally:
                await browser.close()

    async def _login(self, page):
        await page.goto(self.LOGIN_URL, wait_until='networkidle')
        await _safe_fill(page, [
            'input[name="username"]', 'input[name="email"]',
            'input[id="username"]',   'input[type="email"]',
        ], LAND_COM_USERNAME)
        await _safe_fill(page, [
            'input[name="password"]', 'input[id="password"]',
            'input[type="password"]',
        ], LAND_COM_PASSWORD)
        await _safe_click(page, ['button[type="submit"]', 'input[type="submit"]', 'button:has-text("Log In")'])
        await page.wait_for_load_state('networkidle')
        logger.info("Logged into Land.com")

    async def _fill_form(self, page, prop: dict, image_paths: list):
        title = _build_title(prop)
        price = str(int(prop['price'])) if prop.get('price') else ''
        acres = str(prop.get('acreage', ''))

        await _safe_fill(page, ['input[name="title"]', '#title', 'input[placeholder*="title" i]'], title)
        await _safe_fill(page, ['input[name="price"]', '#price', 'input[placeholder*="price" i]'], price)
        await _safe_fill(page, ['input[name="acres"]', 'input[name="acreage"]', '#acres'], acres)
        await _safe_fill(page, ['input[name="address"]', '#address'], prop.get('address', ''))
        await _safe_fill(page, ['input[name="county"]', '#county', 'input[name="city"]'], prop.get('county', ''))
        await _safe_fill(page, ['input[name="state"]', '#state'], prop.get('state', ''))
        await _safe_fill(page, ['input[name="parcel"]', 'input[name="apn"]', '#parcel'], prop.get('parcel_apn', ''))
        await _safe_fill(page, ['textarea[name="description"]', '#description', 'div[contenteditable]'], prop.get('description', ''))

        # Upload photos
        for img_path in image_paths[:20]:
            try:
                fi = page.locator('input[type="file"]').first
                if await fi.count() > 0:
                    await fi.set_input_files(img_path)
                    await asyncio.sleep(1.5)
            except Exception as exc:
                logger.warning(f"Photo upload skipped ({img_path}): {exc}")

    async def _submit(self, page):
        clicked = await _safe_click(page, [
            'button[type="submit"]', 'input[type="submit"]',
            'button:has-text("Submit")', 'button:has-text("Save")',
            'button:has-text("Publish")',
        ])
        if clicked:
            await page.wait_for_load_state('networkidle')


# ── LandFlip.com ──────────────────────────────────────────────────────────────

class LandFlipPoster:
    LOGIN_URL    = "https://www.landflip.com/login"
    ADD_LIST_URL = "https://www.landflip.com/my-account/listings/add"

    async def post_listing(self, property_data: dict, image_paths: list = None) -> str:
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=['--no-sandbox'])
            context = await browser.new_context(viewport={'width': 1280, 'height': 900})
            page = await context.new_page()
            try:
                await self._login(page)
                await page.goto(self.ADD_LIST_URL, wait_until='networkidle')
                await self._fill_form(page, property_data, image_paths or [])
                await self._submit(page)
                url = page.url
                logger.info(f"LandFlip listing submitted. Page: {url}")
                return url
            finally:
                await browser.close()

    async def _login(self, page):
        await page.goto(self.LOGIN_URL, wait_until='networkidle')
        await _safe_fill(page, [
            'input[name="username"]', 'input[name="email"]', 'input[type="email"]',
        ], LANDFLIP_USERNAME)
        await _safe_fill(page, [
            'input[name="password"]', 'input[type="password"]',
        ], LANDFLIP_PASSWORD)
        await _safe_click(page, [
            'button[type="submit"]', 'input[type="submit"]',
            'button:has-text("Log In")', 'button:has-text("Sign In")',
        ])
        await page.wait_for_load_state('networkidle')
        logger.info("Logged into LandFlip.com")

    async def _fill_form(self, page, prop: dict, image_paths: list):
        title = _build_title(prop)
        price = str(int(prop['price'])) if prop.get('price') else ''
        acres = str(prop.get('acreage', ''))

        await _safe_fill(page, ['input[name="title"]', '#listing-title', 'input[placeholder*="title" i]'], title)
        await _safe_fill(page, ['input[name="price"]', '#price', 'input[placeholder*="price" i]'], price)
        await _safe_fill(page, ['input[name="acres"]', 'input[name="acreage"]', '#acres'], acres)
        await _safe_fill(page, ['input[name="address"]', '#address'], prop.get('address', ''))
        await _safe_fill(page, ['input[name="county"]', '#county'], prop.get('county', ''))
        await _safe_fill(page, ['input[name="state"]', '#state'], prop.get('state', ''))
        await _safe_fill(page, ['textarea[name="description"]', '#description'], prop.get('description', ''))

        if image_paths:
            try:
                fi = page.locator('input[type="file"]').first
                if await fi.count() > 0:
                    await fi.set_input_files(image_paths[:10])
                    await asyncio.sleep(2)
            except Exception as exc:
                logger.warning(f"Photo upload skipped: {exc}")

    async def _submit(self, page):
        clicked = await _safe_click(page, [
            'button[type="submit"]', 'input[type="submit"]',
            'button:has-text("Submit")', 'button:has-text("Save Listing")',
            'button:has-text("Post Listing")',
        ])
        if clicked:
            await page.wait_for_load_state('networkidle')


# ── Convenience wrapper ───────────────────────────────────────────────────────

def run_async(coro):
    """Run an async coroutine safely from a sync thread."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)
