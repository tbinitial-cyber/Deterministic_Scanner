from playwright.async_api import Page

class ConsentDetector:
    def __init__(self):
        # Configurable, deterministic selectors
        self.accept_selectors = [
            'button:has-text("Accept All")',
            'button:has-text("Allow All")',
            '#onetrust-accept-btn-handler',
            '.accept-all'
        ]
        self.reject_selectors = [
            'button:has-text("Reject All")',
            'button:has-text("Decline All")',
            '#onetrust-reject-all-handler',
            '.reject-all'
        ]
    
    async def find_and_click_accept(self, page: Page) -> bool:
        for sel in self.accept_selectors:
            btn = page.locator(sel).first
            try:
                if await btn.is_visible(timeout=2000):
                    await btn.click()
                    print(f"Clicked Accept button using selector: {sel}")
                    return True
            except:
                continue
        print("Failed to find Accept button.")
        return False
        
    async def find_and_click_reject(self, page: Page) -> bool:
        for sel in self.reject_selectors:
            btn = page.locator(sel).first
            try:
                if await btn.is_visible(timeout=2000):
                    await btn.click()
                    print(f"Clicked Reject button using selector: {sel}")
                    return True
            except:
                continue
        print("Failed to find Reject button.")
        return False
