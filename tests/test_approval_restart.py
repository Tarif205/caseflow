import json
import os
import subprocess
import sys

import pytest

from support_copilot.config import PROJECT_ROOT


@pytest.mark.integration
def test_separate_processes_pause_approve_resume_without_model_replay(db):
    # db fixture has already validated the loopback test database setting.
    result = subprocess.run(
        [sys.executable, "scripts/check_approval_restart.py"],
        cwd=PROJECT_ROOT,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        timeout=100,
    )
    assert result.returncode == 0, "Restart test failed; raw child stderr withheld"
    report = json.loads(result.stdout)
    assert report["durable_pause"] and report["unapproved_execution_blocked"]
    assert report["process_exit_between_start_and_resume"]
    assert report["resume_without_model_replay"]
    assert report["refund_rows_after_repeated_resume"] == 1
