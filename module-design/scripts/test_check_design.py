"""Behavior checks for ownership mistakes and pre-implementation review."""
import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from check_design import ContractError, analyze, unique_object


def design():
    return {
        "version": 1,
        "modules": {
            "orders": {
                "path": "orders", "purpose": "确认订单", "entrypoint": True,
                "owns": ["accepted-order"], "decides": ["confirm-order"],
                "depends_on": [{"module": "stock", "contract": "预留与释放库存"}],
            },
            "stock": {
                "path": "stock", "purpose": "管理可售库存",
                "owns": ["available-stock"], "decides": ["reserve-stock"],
                "independent_reason": "负责盘点和并发预留", "depends_on": [],
            },
        },
        "resources": {
            "discount": {"path": "orders/discount.py", "owner": "orders", "consumers": ["orders"]},
        },
    }


class DesignChecks(unittest.TestCase):
    def codes(self, data, level=None):
        return {f.code for f in analyze(data) if level is None or f.level == level}

    def test_planned_paths_do_not_require_directories(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertFalse(self.codes(design(), "error"))
            findings = analyze(design(), Path(folder))
            self.assertEqual(sum(f.code == "MISSING_PATH" for f in findings), 3)

    def test_single_consumer_external_then_internal(self):
        data = design()
        data["resources"]["discount"]["path"] = "shared/discount.py"
        self.assertIn("SINGLE_CONSUMER_EXTERNAL", self.codes(data))
        data["resources"]["discount"]["path"] = "orders/discount.py"
        self.assertFalse(self.codes(data, "error"))

    def test_path_prefix_is_not_module_containment(self):
        data = design()
        data["resources"]["discount"]["path"] = "orders-legacy/discount.py"
        self.assertIn("SINGLE_CONSUMER_EXTERNAL", self.codes(data))

    def test_marking_single_consumer_shared_does_not_bypass_rule(self):
        data = design()
        data["resources"]["discount"].update(owner=None, shared_reason="将来复用", maintainer="团队")
        self.assertIn("SINGLE_CONSUMER_EXTERNAL", self.codes(data))

    def test_single_consumer_business_module_requires_review_not_forced_merge(self):
        findings = [f for f in analyze(design()) if f.target == "stock"]
        self.assertEqual([(f.level, f.code) for f in findings], [("warning", "SINGLE_CONSUMER_MODULE")])

    def test_multiple_consumers_need_evidence_and_still_need_review(self):
        data = design()
        data["resources"]["hash"] = {"path": "shared/hash.py", "owner": None, "consumers": ["orders", "stock"]}
        self.assertIn("UNJUSTIFIED_SHARED", self.codes(data, "error"))
        data["resources"]["hash"].update(shared_reason="相同的无状态编码", maintainer="工具维护者")
        self.assertNotIn("UNJUSTIFIED_SHARED", self.codes(data))
        self.assertIn("SHARED_REVIEW", self.codes(data, "warning"))

    def test_public_contract_stays_with_provider(self):
        data = design()
        data["resources"]["stock-contract"] = {
            "path": "stock/contract.py", "owner": "stock", "consumers": ["stock", "orders"],
        }
        self.assertFalse(self.codes(data, "error"))
        data["modules"]["orders"]["depends_on"] = []
        self.assertIn("UNDECLARED_CONSUMPTION", self.codes(data, "error"))

    def test_duplicate_authority_and_cycles_are_errors(self):
        data = design()
        data["modules"]["stock"]["owns"].append("accepted-order")
        data["modules"]["stock"]["depends_on"].append({"module": "orders", "contract": "读取内部状态"})
        self.assertTrue({"DUPLICATE_AUTHORITY", "DEPENDENCY_CYCLE"} <= self.codes(data, "error"))

    def test_empty_contract_and_self_dependency(self):
        data = design()
        data["modules"]["orders"]["depends_on"] = [{"module": "orders", "contract": " "}]
        self.assertTrue({"MISSING_CONTRACT", "SELF_DEPENDENCY"} <= self.codes(data, "error"))

    def test_unused_design_is_a_question_not_an_invented_dependency(self):
        data = design()
        data["modules"]["orders"]["depends_on"] = []
        data["resources"]["discount"]["consumers"] = []
        self.assertTrue({"NO_CONSUMER", "UNUSED_RESOURCE"} <= self.codes(data, "warning"))

    def test_invalid_declarations_are_rejected(self):
        mutations = [
            lambda d: d["modules"]["stock"].update(path="../stock"),
            lambda d: d["modules"]["stock"].update(path="orders"),
            lambda d: d["modules"]["stock"].update(entrypoint="true"),
            lambda d: d["modules"]["stock"].update(depend_on=[]),
            lambda d: d["modules"]["orders"]["depends_on"][0].update(module="missing"),
            lambda d: d["resources"]["discount"].update(consumers=["orders", "docs"]),
            lambda d: d["resources"]["discount"].update(consumers=["orders", "orders"]),
            lambda d: d["resources"].update(duplicate=deepcopy(d["resources"]["discount"])),
        ]
        for mutation in mutations:
            data = design()
            mutation(data)
            with self.subTest(data=data), self.assertRaises(ContractError):
                analyze(data)
        with self.assertRaises(ContractError):
            json.loads('{"modules": {}, "modules": {}}', object_pairs_hook=unique_object)

    def test_check_paths_respects_symlink_boundary(self):
        with tempfile.TemporaryDirectory() as folder, tempfile.TemporaryDirectory() as external:
            root = Path(folder)
            (root / "orders").symlink_to(external, target_is_directory=True)
            self.assertIn("PATH_ESCAPE", {f.code for f in analyze(design(), root)})

    def test_cli_exit_status_report_and_no_write_mode(self):
        script = Path(__file__).with_name("check_design.py")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            declaration = root / "design.json"
            data = design()

            def run(*args):
                return subprocess.run([sys.executable, str(script), "--root", str(root), "--design", "design.json", *args],
                                      capture_output=True, text=True)

            declaration.write_text(json.dumps(data))
            self.assertEqual(run("--check-only").returncode, 0)
            self.assertFalse((root / ".reports").exists())
            data["resources"]["discount"]["path"] = "shared/discount.py"
            declaration.write_text(json.dumps(data))
            self.assertEqual(run().returncode, 1)
            self.assertIn("SINGLE_CONSUMER_EXTERNAL", (root / ".reports/module-design.md").read_text())
            original = declaration.read_text()
            self.assertEqual(run("--output", "design.json").returncode, 2)
            self.assertEqual(declaration.read_text(), original)
            declaration.write_text("{")
            self.assertEqual(run("--check-only").returncode, 2)


if __name__ == "__main__":
    unittest.main()
