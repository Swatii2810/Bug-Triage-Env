"""Core BugTriageEnvironment — OpenEnv-compatible step/reset/state API."""

from typing import Optional

from models import BugTriageAction, BugTriageObservation, BugTriageReward
from graders import grade_action
from data.issues import TASK1_ISSUES, TASK2_ISSUES, TASK3_ISSUES

TASK_MAX_STEPS = {1: 1, 2: 2, 3: 3}
TASK_ISSUES    = {1: TASK1_ISSUES, 2: TASK2_ISSUES, 3: TASK3_ISSUES}


class BugTriageEnvironment:
    def __init__(self):
        self._task_id: int = 1
        self._issue_index: int = 0
        self._step_number: int = 0
        self._done: bool = False
        self._issues: list = TASK1_ISSUES
        self._current_issue: Optional[dict] = None

    def reset(self, task_id: int = 1) -> BugTriageObservation:
        if task_id not in TASK_ISSUES:
            raise ValueError(f"task_id must be 1, 2, or 3. Got: {task_id}")

        self._task_id = task_id
        self._issues = TASK_ISSUES[task_id]
        self._issue_index = 0
        self._step_number = 0
        self._done = False
        self._current_issue = self._issues[self._issue_index]

        return self._build_observation()

    def step(self, action: BugTriageAction) -> tuple[BugTriageObservation, float, bool, dict]:
        if self._done:
            raise RuntimeError("Episode done. Call reset() first.")
        if self._current_issue is None:
            raise RuntimeError("Not initialized. Call reset() first.")

        self._step_number += 1
        ground_truth = self._current_issue["ground_truth"]
        reward_obj: BugTriageReward = grade_action(action, ground_truth, self._task_id)

        max_steps = TASK_MAX_STEPS[self._task_id]
        step_done = self._step_number >= max_steps

        if step_done:
            self._issue_index += 1
            self._step_number = 0
            if self._issue_index >= len(self._issues):
                self._done = True
            else:
                self._current_issue = self._issues[self._issue_index]

        obs  = self._build_observation() if not self._done else self._terminal_observation()
        info = {
            "reward_breakdown": reward_obj.breakdown,
            "issue_id":   self._current_issue["issue_id"] if not self._done else "DONE",
            "task_id":    self._task_id,
            "step_number": self._step_number,
        }
        return obs, reward_obj.total, self._done, info

    def state(self) -> dict:
        return {
            "task_id": self._task_id,
            "issue_index": self._issue_index,
            "step_number": self._step_number,
            "done": self._done,
            "total_issues": len(self._issues),
            "current_issue_id": self._current_issue["issue_id"] if self._current_issue else None,
            "max_steps": TASK_MAX_STEPS.get(self._task_id, 1),
        }

    def _build_observation(self) -> BugTriageObservation:
        issue = self._current_issue
        existing = self._get_existing_issues_context()
        return BugTriageObservation(
            issue_id=issue["issue_id"],
            title=issue["title"],
            description=issue["description"],
            reporter=issue["reporter"],
            created_at=issue["created_at"],
            existing_issues=existing,
            task_id=self._task_id,
            step_number=self._step_number,
            max_steps=TASK_MAX_STEPS[self._task_id],
        )

    def _terminal_observation(self) -> BugTriageObservation:
        return BugTriageObservation(
            issue_id="DONE",
            title="Episode complete",
            description="All issues in this task have been processed.",
            reporter="system",
            created_at="",
            existing_issues=[],
            task_id=self._task_id,
            step_number=0,
            max_steps=TASK_MAX_STEPS[self._task_id],
        )

    def _get_existing_issues_context(self) -> list:
        # Only Task 3 needs prior issues for duplicate detection
        if self._task_id != 3:
            return []
        from data.issues import ISSUES
        current_id = self._current_issue["issue_id"]
        context = []
        for iss in ISSUES:
            if iss["issue_id"] == current_id:
                break
            context.append({
                "issue_id":    iss["issue_id"],
                "title":       iss["title"],
                "description": iss["description"][:200],
            })
        return context
