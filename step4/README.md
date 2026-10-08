# Step 4: Cloud & Database Discovery Interface (Reserved)

## Status: DEFERRED
Implementation of this module is deferred until the controlled Azure/database environment is available.

## Objective
This layer is responsible for discovering and extracting the "backend reality." It connects to the SaaS backend/cloud environment to collect:
- Database schema
- Data assets and derived fields
- Access controls (RBAC/IAM)
- Encryption-at-rest configurations
- Retention policies
- Storage geographic locations
- General cloud environment configuration

## Integration Contract
When implemented, this module will consume read-only credentials to the cloud environment and produce structured factual outputs (e.g., `backend_assets.json`, `schema.json`) that parallel the frontend factual outputs generated in Steps 1-3.
