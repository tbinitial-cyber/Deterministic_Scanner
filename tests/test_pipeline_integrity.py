import unittest
import json
import os
import subprocess
import hashlib



def compute_sha256(filepath):
    sha256_hash = hashlib.sha256()
    if not os.path.exists(filepath): return None
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

class TestPipelineIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import shutil
        if os.path.exists("test_output"):
            shutil.rmtree("test_output")
        shutil.copytree("fixtures/synthetic", "test_output")

    @classmethod
    def tearDownClass(cls):
        import shutil
        if os.path.exists("test_output"):
            shutil.rmtree("test_output")

    def test_hash_integrity(self):
        man_path = os.path.join("test_output", "final", "audit_manifest.json")
        self.assertTrue(os.path.exists(man_path))
        with open(man_path) as f:
            manifest = json.load(f)
            
        # Check final output hashes
        for fname, exp_hash in manifest['output_hashes'].items():
            fpath = os.path.join("test_output", "final", fname)
            self.assertTrue(os.path.exists(fpath))
            self.assertEqual(compute_sha256(fpath), exp_hash)
            
    def test_dependency_integrity_failure(self):
        # Move step 5 manifest temporarily
        doc_manifest = os.path.join("test_output", "documents", "document_manifest.json")
        doc_manifest_bak = os.path.join("test_output", "documents", "document_manifest.json.bak")
        os.rename(doc_manifest, doc_manifest_bak)
        try:
            # Running from step 6 should fail because step 5 is missing
            res = subprocess.run(["python", "audit.py", "https://miro.com", "--from-step", "6", "--output", "test_output"], capture_output=True, text=True)
            self.assertIn("FAILED", res.stdout)
            self.assertIn("Manifest missing", res.stdout)
        finally:
            os.rename(doc_manifest_bak, doc_manifest)

    def test_no_legal_leakage_in_ropa(self):
        ropa_file = os.path.join("test_output", "ropa", "processing_activities.json")
        with open(ropa_file) as f:
            ropa = json.load(f)
        for pa in ropa:
            str_repr = json.dumps(pa).lower()
            self.assertNotIn("violation", str_repr)
            self.assertNotIn("illegal", str_repr)
            
    def test_step9_boundary(self):
        legal_file = os.path.join("test_output", "legal", "control_assessments.json")
        with open(legal_file) as f:
            legal = json.load(f)
        self.assertGreater(len(legal), 0)
        for l in legal:
            self.assertIn("legal_relevance", l)
            self.assertIn("current_enforceability", l)
            self.assertIn("readiness_assessment", l)
            self.assertIn("current_legal_violation", l)
            
    def test_step10_boundary(self):
        dpia_file = os.path.join("test_output", "dpia", "dpi_assessments.json")
        with open(dpia_file) as f:
            dpia = json.load(f)
        self.assertGreater(len(dpia), 0)
        for d in dpia:
            self.assertIn("residual_risks", d)
            self.assertIn("existing_controls", d)
            self.assertIn("statutory_dpia_status", d)

if __name__ == "__main__":
    unittest.main()
