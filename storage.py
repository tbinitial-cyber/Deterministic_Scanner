from playwright.async_api import Page
from models import StorageItem

async def capture_storage(page: Page) -> list[StorageItem]:
    """Extracts local and session storage from the current page."""
    
    # We must swallow errors if storage access is denied (e.g. strict origin policies)
    try:
        ls_entries = await page.evaluate("() => Object.entries(localStorage)")
    except Exception:
        ls_entries = []
        
    try:
        ss_entries = await page.evaluate("() => Object.entries(sessionStorage)")
    except Exception:
        ss_entries = []
        
    items = []
    
    for k, v in ls_entries:
        items.append(StorageItem(storage_type="localStorage", key=k, value=str(v)))
        
    for k, v in ss_entries:
        items.append(StorageItem(storage_type="sessionStorage", key=k, value=str(v)))
        
    return items
