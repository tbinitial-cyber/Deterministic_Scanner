import asyncio
import argparse
import os
import sys
from datetime import datetime, timezone
from typing import Callable, Awaitable, Optional
from playwright.async_api import async_playwright, Page

from browser import create_standardized_context
from cdp_network import CDPCapture
from cookies import capture_cookies
from storage import capture_storage
from utils import save_json, compute_sha256
from models import ScanManifest

async def run_scan(target_url: str, window_ms: int, output_dir: str = "output", action_callback: Optional[Callable[[Page], Awaitable[None]]] = None):
    os.makedirs(output_dir, exist_ok=True)

    
    print(f"Starting deterministic scan for: {target_url} (Window: {window_ms}ms)")
    
    async with async_playwright() as p:
        browser, context = await create_standardized_context(p)
        page = await context.new_page()
        
        # Attach CDP capturing
        cdp = CDPCapture()
        await cdp.attach(page)

        # Deterministic state machine (Navigation -> Readiness -> Fixed Window -> Capture)
        print(f"Navigating (wait_until='load')...")
        try:
            await page.goto(target_url, wait_until="load", timeout=60000)
        except Exception as e:
            print(f"Navigation exception (proceeding to capture): {e}")
            
        if action_callback:
            print("Executing targeted consent action...")
            try:
                await action_callback(page)
            except Exception as e:
                print(f"Action callback failed: {e}")
                
        print(f"Waiting for fixed observation window ({window_ms}ms)...")
        await asyncio.sleep(window_ms / 1000.0)
        
        print("Extracting state (Cookies & Storage)...")
        cookies = await capture_cookies(context)
        storage = await capture_storage(page)
        
        await browser.close()
        
        print("Validating and dumping artifacts...")
        save_json(cdp.requests, f"{output_dir}/network_requests.json")
        save_json(cdp.responses, f"{output_dir}/network_responses.json")
        save_json(cdp.loading_finished, f"{output_dir}/loading_finished.json")
        save_json(cdp.loading_failed, f"{output_dir}/loading_failed.json")
        save_json(cookies, f"{output_dir}/cookies.json")
        save_json(storage, f"{output_dir}/storage.json")
        
        # Manifest Generation for cryptographic provenance
        print("Generating cryptographic manifest...")
        files_to_hash = [
            "network_requests.json", 
            "network_responses.json", 
            "loading_finished.json",
            "loading_failed.json",
            "cookies.json", 
            "storage.json"
        ]
        hashed_files = {}
        for fn in files_to_hash:
            filepath = os.path.join(output_dir, fn)
            if os.path.exists(filepath):
                hashed_files[fn] = compute_sha256(filepath)
                
        manifest = ScanManifest(
            target_url=target_url,
            captured_at=datetime.now(timezone.utc).isoformat(),
            files=hashed_files
        )
        save_json(manifest, f"{output_dir}/scan_manifest.json")
        
        print("Scan complete.")
        print(f"Manifest Hash: {compute_sha256(os.path.join(output_dir, 'scan_manifest.json'))[:16]}...")
        print(f"Results saved in ./{output_dir}/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deterministic Browser Scanner")
    parser.add_argument("url", nargs="?", default="https://miro.com", help="Target URL to scan")
    parser.add_argument("--window", type=int, default=5000, help="Observation window in ms (default: 5000)")
    args = parser.parse_args()
    
    asyncio.run(run_scan(args.url, args.window))
