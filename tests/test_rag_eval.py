"""Tests for the lightweight RAG evaluation runner."""

import json
import os
import subprocess
import sys
from pathlib import Path


class TestEvalRunner:
    """Verify the eval script runs end-to-end with expected outcomes."""

    def _eval_result(self) -> subprocess.CompletedProcess:
        root = Path(__file__).resolve().parent.parent
        env = {**os.environ, "PYTHONPATH": str(root)}
        return subprocess.run(
            [sys.executable, "evals/run_rag_eval.py"],
            capture_output=True,
            text=True,
            cwd=root,
            env=env,
        )

    def test_eval_script_exists(self) -> None:
        script = Path("evals/run_rag_eval.py")
        assert script.exists()

    def test_eval_cases_file_exists(self) -> None:
        cases = Path("evals/rag_cases.json")
        assert cases.exists()
        data = json.loads(cases.read_text())
        assert len(data) >= 4

    def test_eval_runs_and_passes(self) -> None:
        result = self._eval_result()
        assert result.returncode == 0, (
            f"eval failed (exit {result.returncode}):\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_eval_output_contains_all_case_ids(self) -> None:
        cases = json.loads(Path("evals/rag_cases.json").read_text())
        case_ids = {c["id"] for c in cases}
        result = self._eval_result()
        for cid in case_ids:
            assert cid in result.stdout, f"Case {cid} not found in eval output"