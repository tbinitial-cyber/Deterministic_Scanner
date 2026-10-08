import asyncio
import os
import sys
import argparse

# Add parent dir to path to import scan logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scan import run_scan
from utils import save_json

from step2.state_manager import StateManager
from step2.consent_detector import ConsentDetector
from step2.differential import DifferentialAnalyzer
from step2.findings import generate_findings

async def run_audit(url: str, window_ms: int = 5000):
    manager = StateManager()
    manager.setup()
    detector = ConsentDetector()
    
    print(f"=== Starting Step 2 Consent Audit for {url} ===")
    
    # 1. Pre-consent
    print("\n[State 1/3] Running PRE_CONSENT...")
    await run_scan(url, window_ms, output_dir=manager.pre_consent_dir)
    
    # 2. Accept All
    print("\n[State 2/3] Running ACCEPT_ALL...")
    async def accept_action(page):
        await detector.find_and_click_accept(page)
    await run_scan(url, window_ms, output_dir=manager.accept_dir, action_callback=accept_action)
    
    # 3. Reject All
    print("\n[State 3/3] Running REJECT_ALL...")
    async def reject_action(page):
        await detector.find_and_click_reject(page)
    await run_scan(url, window_ms, output_dir=manager.reject_dir, action_callback=reject_action)

    print("\n=== All states captured. Running Differential Analysis ===")
    analyzer = DifferentialAnalyzer(manager)
    diff_hosts = analyzer.analyze_hosts()
    
    # Save the raw comparison
    save_json(diff_hosts, os.path.join(manager.base_dir, "consent_comparison.json"))
    
    # Generate and save factual findings
    findings = generate_findings(diff_hosts)
    save_json(findings, os.path.join(manager.base_dir, "behaviour_findings.json"))
    
    print(f"Audit complete. Findings generated: {len(findings)} host patterns classified.")
    print(f"Outputs located in: {manager.base_dir}/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deterministic Step 2 Audit")
    parser.add_argument("url", nargs="?", default="https://miro.com", help="Target URL")
    parser.add_argument("--window", type=int, default=5000, help="Observation window in ms")
    args = parser.parse_args()
    
    asyncio.run(run_audit(args.url, args.window))
