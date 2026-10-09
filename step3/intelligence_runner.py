import sys
import os
import argparse

# Add parent to path for utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import save_json

from step3.analyzer import IntelligenceAnalyzer

def run_intelligence(target_url: str):
    print(f"=== Starting Step 3 Intelligence Enrichment for {target_url} ===")
    analyzer = IntelligenceAnalyzer(target_url)
    
    print("Enriching hosts and building Data Flow Graph...")
    enriched_hosts, graph = analyzer.analyze_hosts()
    
    print("Enriching cookies...")
    enriched_cookies = analyzer.analyze_cookies()
    
    # Save outputs
    out_dir = "output/data_flow"
    os.makedirs(out_dir, exist_ok=True)
    
    save_json(enriched_hosts, os.path.join(out_dir, "hosts.json"))
    save_json(enriched_cookies, os.path.join(out_dir, "cookies_enriched.json"))
    save_json(graph, os.path.join(out_dir, "data_flow_graph.json"))
    
    # Also separate vendors and trackers for convenience
    vendors = sorted(list({h.vendor for h in enriched_hosts if not h.is_first_party and h.vendor != "Unknown"}))
    trackers = [h for h in enriched_hosts if h.category in ["Advertising", "Behavioural analytics", "Analytics"]]
    
    save_json(vendors, os.path.join(out_dir, "vendors.json"))
    save_json(trackers, os.path.join(out_dir, "trackers.json"))
    
    print(f"\nIntelligence Enrichment Complete!")
    print(f"Discovered {len(enriched_hosts)} hosts ({len([h for h in enriched_hosts if h.is_first_party])} first-party, {len([h for h in enriched_hosts if not h.is_first_party])} third-party).")
    print(f"Identified {len(vendors)} known vendors.")
    print(f"Classified {len(trackers)} tracking domains.")
    print(f"Outputs located in: {out_dir}/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deterministic Step 3 Intelligence")
    parser.add_argument("url", nargs="?", default="https://miro.com", help="Target URL")
    args = parser.parse_args()
    
    run_intelligence(args.url)
