import sys
import os
import argparse
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import save_json, compute_sha256
from step5.schemas import PolicyFact, DPAFact, SubprocessorFact, DocumentManifest, ExtractedFact
from step5.discovery import DocumentDiscoverer
from step5.extractor import DeterministicExtractor

def run_document_pipeline(target_url: str):
    print(f"=== Starting Step 5 Deterministic Document Pipeline for {target_url} ===")
    
    out_dir = "output/documents"
    source_dir = os.path.join(out_dir, "source_documents")
    
    # 1. Discover and Download
    discoverer = DocumentDiscoverer(target_url, source_dir)
    downloaded_files = discoverer.discover_and_download()
    
    if not downloaded_files:
        print("No documents found automatically. You may need to provide direct URLs.")
    
    # 2. Extract Facts
    policy_facts = PolicyFact()
    dpa_facts = DPAFact()
    subprocessors = []
    
    # Parse Privacy Policy
    if 'Privacy_Policy' in downloaded_files:
        ext = DeterministicExtractor(downloaded_files['Privacy_Policy'])
        policy_facts.data_categories.append(ext.extract_fact(r"(?i)(what|information|data)\s*(we\s*)?collect", "data_categories"))
        policy_facts.purposes.append(ext.extract_fact(r"(?i)how\s*we\s*use|purpose", "purposes"))
        policy_facts.third_parties.append(ext.extract_fact(r"(?i)third\s*part(y|ies)|share|sharing", "third_parties"))
        policy_facts.retention_statements.append(ext.extract_fact(r"(?i)retention|how\s*long", "retention_statements"))
        policy_facts.international_transfers.append(ext.extract_fact(r"(?i)international|transfer", "international_transfers"))
        policy_facts.rights_information.append(ext.extract_fact(r"(?i)your\s*rights", "rights_information"))
        policy_facts.cookie_disclosures.append(ext.extract_fact(r"(?i)cookie", "cookie_disclosures"))

    # Parse DPA
    if 'DPA' in downloaded_files:
        ext = DeterministicExtractor(downloaded_files['DPA'])
        dpa_facts.subprocessors.append(ext.extract_fact(r"(?i)sub(-?)processor", "subprocessors"))
        dpa_facts.security_measures.append(ext.extract_fact(r"(?i)security", "security_measures"))
        dpa_facts.international_transfers.append(ext.extract_fact(r"(?i)transfer", "international_transfers"))
        
    # Generate Manifest
    processed_hashes = {}
    for doc_type, filepath in downloaded_files.items():
        processed_hashes[filepath.split('/')[-1].split('\\')[-1]] = compute_sha256(filepath)
        
    manifest = DocumentManifest(
        target_url=target_url,
        documents_processed=processed_hashes,
        extraction_timestamp=datetime.now(timezone.utc).isoformat(),
        extraction_engine="Deterministic Regex Extractor v1.0"
    )
    
    print("Validating extracted schemas and dumping to JSON...")
    save_json(policy_facts, os.path.join(out_dir, "policy_facts.json"))
    save_json(dpa_facts, os.path.join(out_dir, "dpa_facts.json"))
    save_json(subprocessors, os.path.join(out_dir, "subprocessors.json"))
    save_json(manifest, os.path.join(out_dir, "document_manifest.json"))
    
    print("Step 5 Pipeline Complete.")
    print(f"Outputs located in: {out_dir}/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deterministic Step 5 Document Intelligence")
    parser.add_argument("url", nargs="?", default="https://miro.com", help="Target URL to crawl for policies")
    args = parser.parse_args()
    
    run_document_pipeline(args.url)
