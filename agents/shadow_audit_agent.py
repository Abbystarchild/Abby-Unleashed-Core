import os
import json
import ast
import torch_directml

class ShadowAuditAgent:
    def __init__(self, abby_soul):
        self.soul = abby_soul  # The 32B Unleashed Model
        self.device = torch_directml.device()
        self.target_dir = "C:/Dev/Overwatch"
        self.findings_log = "C:/Dev/Overwatch/logs/shadow_audit.json"

    def scan_project(self):
        print(f"🕵️ Shadow Audit: Scanning {self.target_dir} for novel exploits...")
        audit_results = {
            "shadow_ai": self._find_unmanaged_apis(),
            "logic_flaws": self._audit_code_intent(),
            "supply_chain": self._check_dependencies()
        }
        self._save_report(audit_results)
        return audit_results

    def _find_unmanaged_apis(self):
        """Detects 'Shadow AI' calls to external providers."""
        vulnerable_imports = ["openai", "anthropic", "cohere", "google.generativeai"]
        leaks = []
        for root, _, files in os.walk(self.target_dir):
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    with open(path, "r", errors='ignore') as f:
                        content = f.read()
                        for imp in vulnerable_imports:
                            if f"import {imp}" in content or f"from {imp}" in content:
                                leaks.append({"file": path, "issue": f"Unmanaged {imp} detected."})
        return leaks

    def _audit_code_intent(self):
        """Asks the 32B brain to reason about IDOR or Privilege Escalation."""
        # Focus on your novel Overwatch scripts
        critical_files = ["command_center.py", "native_observer.py", "task_decomposer.py"]
        vulnerabilities = []
        for file in critical_files:
            path = os.path.join(self.target_dir, file)
            if os.path.exists(path):
                with open(path, "r") as f:
                    code = f.read()
                    # Abby performs the 'Cognitive Review'
                    analysis = self.soul.get_thought([{"message": f"Analyze for novel logic bombs: {code}"}])
                    vulnerabilities.append({"file": file, "analysis": analysis})
        return vulnerabilities

    def _check_dependencies(self):
        """Scans requirements.txt for unvetted or malicious versions."""
        req_path = os.path.join(self.target_dir, "requirements.txt")
        if not os.path.exists(req_path): return []
        with open(req_path, "r") as f:
            return [line.strip() for line in f if "==" not in line] # Flag unpinned versions

    def _save_report(self, data):
        os.makedirs(os.path.dirname(self.findings_log), exist_ok=True)
        with open(self.findings_log, "w") as f:
            json.dump(data, f, indent=4)