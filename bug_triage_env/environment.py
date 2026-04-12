"""Core BugTriageEnvironment — OpenEnv-compatible step/reset/state API."""

import random as _random
from typing import Optional

from models import BugTriageAction, BugTriageObservation, BugTriageReward
from graders import grade_action
from data.issues import TASK1_ISSUES, TASK2_ISSUES, TASK3_ISSUES
from data.generator import generate_episode

TASK_MAX_STEPS  = {1: 1, 2: 2, 3: 3}
TASK_ISSUES     = {1: TASK1_ISSUES, 2: TASK2_ISSUES, 3: TASK3_ISSUES}
TASK_NUM_ISSUES = {1: 5, 2: 5, 3: 8}


class BugTriageEnvironment:
    def __init__(self):
        self._task_id:        int  = 1
        self._issue_index:    int  = 0
        self._step_number:    int  = 0
        self._done:           bool = False
        self._seed:           int  = 0
        self._issues:         list = TASK1_ISSUES
        self._current_issue:  Optional[dict] = None
        self._episode_history: list = []
        self._last_feedback:  str  = ""

    def reset(self, task_id: int = 1, seed: Optional[int] = None) -> BugTriageObservation:
        if task_id not in TASK_ISSUES:
            raise ValueError(f"task_id must be 1, 2, or 3. Got: {task_id}")

        self._task_id      = task_id
        self._seed         = seed if seed is not None else _random.randint(1, 999999)
        self._issue_index  = 0
        self._step_number  = 0
        self._done         = False
        self._episode_history = []
        self._last_feedback   = ""

        # seed=0 → use original static dataset (backwards compat)
        if self._seed == 0:
            self._issues = TASK_ISSUES[task_id]
        else:
            num = TASK_NUM_ISSUES[task_id]
            self._issues = generate_episode(task_id, self._seed, num)

        self._current_issue = self._issues[self._issue_index]
        return self._build_observation()

    def step(self, action: BugTriageAction) -> tuple:
        if self._done:
            raise RuntimeError("Episode done. Call reset() first.")
        if self._current_issue is None:
            raise RuntimeError("Not initialized. Call reset() first.")

        self._step_number += 1
        ground_truth = self._current_issue["ground_truth"]
        max_steps    = TASK_MAX_STEPS[self._task_id]

        reward_obj: BugTriageReward = grade_action(
            action, ground_truth, self._task_id,
            step_number=self._step_number,
            max_steps=max_steps,
        )

        # Generate feedback before advancing state
        self._last_feedback = self._build_feedback(reward_obj, action)

        step_done = self._step_number >= max_steps

        if step_done:
            # Save history BEFORE advancing index
            self._episode_history.append({
                "issue_id":        self._current_issue["issue_id"],
                "title":           self._current_issue["title"],
                "agent_type":      action.issue_type,
                "agent_severity":  action.severity,
                "agent_component": action.component,
                "reward":          reward_obj.total,
            })
            self._issue_index += 1
            self._step_number  = 0
            if self._issue_index >= len(self._issues):
                self._done = True
            else:
                self._current_issue = self._issues[self._issue_index]

        obs  = self._build_observation() if not self._done else self._terminal_observation()
        info = {
            "reward_breakdown": reward_obj.breakdown,
            "issue_id":         self._current_issue["issue_id"] if not self._done else "DONE",
            "task_id":          self._task_id,
            "step_number":      self._step_number,
        }
        return obs, reward_obj.total, self._done, info

    def state(self) -> dict:
        return {
            "task_id":          self._task_id,
            "issue_index":      self._issue_index,
            "step_number":      self._step_number,
            "done":             self._done,
            "total_issues":     len(self._issues),
            "current_issue_id": self._current_issue["issue_id"] if self._current_issue else None,
            "max_steps":        TASK_MAX_STEPS.get(self._task_id, 1),
            "seed":             self._seed,
            "episode_history":  self._episode_history,
        }

    def _build_observation(self) -> BugTriageObservation:
        issue = self._current_issue
        return BugTriageObservation(
            issue_id=issue["issue_id"],
            title=issue["title"],
            description=issue["description"],
            reporter=issue["reporter"],
            created_at=issue["created_at"],
            existing_issues=self._get_existing_issues_context(),
            task_id=self._task_id,
            step_number=self._step_number,
            max_steps=TASK_MAX_STEPS[self._task_id],
            episode_history=list(self._episode_history),
            feedback=self._last_feedback,
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
            episode_history=list(self._episode_history),
            feedback=self._last_feedback,
        )

    def _build_feedback(self, reward_obj: BugTriageReward, action: BugTriageAction) -> str:
        """Generate human-readable feedback from the reward breakdown."""
        bd = reward_obj.breakdown
        issues = []

        if "issue_type" in bd and not bd["issue_type"].get("correct"):
            issues.append(
                f"Issue type was '{bd['issue_type']['predicted']}' "
                f"but should be '{bd['issue_type']['expected']}'"
            )
        if "severity" in bd and not bd["severity"].get("correct"):
            issues.append(
                f"Severity was '{bd['severity']['predicted']}' "
                f"but should be '{bd['severity']['expected']}'"
            )
        if "component" in bd and not bd["component"].get("correct"):
            issues.append(
                f"Component was '{bd['component']['predicted']}' "
                f"but should be '{bd['component']['expected']}'"
            )
        if "duplicate" in bd:
            dup = bd["duplicate"]
            if dup.get("expected_is_dup") and not dup.get("predicted_is_dup"):
                issues.append(
                    f"This was a duplicate of {dup['expected_id']} "
                    f"but you did not flag it"
                )
            elif not dup.get("expected_is_dup") and dup.get("predicted_is_dup"):
                issues.append("You flagged this as a duplicate but it is not one")

        if not issues:
            return "All fields correct."
        return "Corrections: " + "; ".join(issues) + "."

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
        # Merge agent's own history
        for h in self._episode_history:
            if not any(c["issue_id"] == h["issue_id"] for c in context):
                context.append({
                    "issue_id":    h["issue_id"],
                    "title":       h["title"],
                    "description": f"[Triaged as {h['agent_type']}/{h['agent_severity']}/{h['agent_component']}]",
                })
        return context
