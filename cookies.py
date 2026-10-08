from playwright.async_api import BrowserContext
from models import Cookie

async def capture_cookies(context: BrowserContext) -> list[Cookie]:
    """Extracts and validates all cookies from the context."""
    raw_cookies = await context.cookies()
    
    # Strict validation through Pydantic
    valid_cookies = []
    for c in raw_cookies:
        valid_cookies.append(Cookie(
            name=c.get('name', ''),
            value=c.get('value', ''),
            domain=c.get('domain', ''),
            path=c.get('path', ''),
            expires=float(c.get('expires', -1)),
            httpOnly=c.get('httpOnly', False),
            secure=c.get('secure', False),
            sameSite=c.get('sameSite', 'None')
        ))
    return valid_cookies
