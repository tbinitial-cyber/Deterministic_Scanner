# Deterministic Privacy-GRC Engine

A strictly deterministic, non-AI engine for auditing websites against the **DPDPA 2023** and **DPDP Rules 2025**.

## Architecture & Design Principles

1. **Raw-Facts-First**: Observations are made purely through headless browser telemetry (CDP) and DOM inspection.
2. **Deterministic Evaluation**: No LLMs or AI inference are used anywhere in the decision-making pipeline. Decisions are made using explicitly encoded legal mappings and Pydantic schemas.
3. **Traceable Evidence**: Every finding, risk, or compliance gap must point back to a specific piece of technical or documentary evidence.
4. **Separation of Concerns**: Technical observation (Steps 1-3) is completely separated from legal interpretation (Steps 8-10).

## Pipeline Steps

* **Step 1: Raw Telemetry Capture**: Captures headless browser network and storage data.
* **Step 2: Consent Behaviour**: Audits cookie/tracker dropping before and after consent interactions.
* **Step 3: Data Flow Intelligence**: Maps hosts, trackers, and vendors.
* **Step 4: Cloud/DB Discovery**: *(RESERVED)* For future backend/cloud data mapping.
* **Step 5: Document Parsing**: Extracts facts from Privacy Policies and DPAs.
* **Step 6: Reconciliation**: Compares observed technical entities against documented entities.
* **Step 7: Lineage**: Reconstructs the data lineage graph.
* **Step 8: Governance Register**: Builds the processing activity register.
* **Step 9: Legal Obligation Mapping**: Maps processing activities to the DPDPA 2023 legal knowledge base.
* **Step 10: DPIA Engine**: Evaluates privacy risk and generates remediation plans.
* **Step 11: End-to-End Orchestrator**: Runs the complete pipeline sequentially (`audit.py`).

## Usage

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run the end-to-end audit
python audit.py https://example.com
```

### Running Tests

The test suite uses synthetic, sanitized fixtures located in `fixtures/synthetic` to ensure pipeline integrity without needing to run a live scan.

```bash
python -m unittest tests/test_pipeline_integrity.py
```

## Legal Disclaimer

This tool is a **risk-assessment and DPIA-support engine**. It is NOT an automated legal judge. Outputs provide control-assessment states such as `gap`, `aligned`, or `requires_human_review`, but should not be interpreted as definitive legal advice. Output must not be used to automatically declare an entity as acting "illegally" or "unlawfully".
