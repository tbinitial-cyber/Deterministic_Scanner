from playwright.async_api import Playwright, Browser, BrowserContext

async def create_standardized_context(playwright: Playwright) -> tuple[Browser, BrowserContext]:
    """Creates a strictly controlled, non-persistent browser context."""
    browser = await playwright.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"]
    )
    
    # Non-persistent context ensures fresh state (no disk cache, clean cookies)
    context = await browser.new_context(
        viewport={'width': 1280, 'height': 800},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        locale='en-US',
        timezone_id='UTC',
        bypass_csp=True,
        service_workers='block' # Step 1: Block for deterministic baseline, configurable later
    )
    
    return browser, context
