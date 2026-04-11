"""Procedural bug report generator. Fully deterministic given a seed."""
import random

BUG_TEMPLATES = [
    {
        "title_tmpl": "{component_cap} crashes when {action} on {platform}",
        "desc_tmpl": (
            "After {version}, the app crashes when users {action}. "
            "Stack trace: NullPointerException at {component}Manager.{method}(line {line}). "
            "Reproducible on {platform} 100% of the time."
        ),
        "severity": "P2", "component": "mobile",
        "repro_keywords": ["crash", "nullpointer", "reproducible"],
    },
    {
        "title_tmpl": "{component_cap} returns 500 for {input_type} input",
        "desc_tmpl": (
            "The /api/{component}/search endpoint returns HTTP 500 when the "
            "request contains {input_type} characters. Server log shows a SQL "
            "syntax error — input is not sanitised before interpolation. "
            "Potential injection vector. Affects version {version}."
        ),
        "severity": "P1", "component": "backend",
        "repro_keywords": ["500", "sql", "injection", "sanitised"],
    },
    {
        "title_tmpl": "Nightly {job} job failing silently since {date}",
        "desc_tmpl": (
            "The scheduled {job} job has not completed for {days} days. "
            "Cron exits with code 0 but writes 0 bytes. No alert was triggered. "
            "We have no off-site copy for the last {days} days."
        ),
        "severity": "P1", "component": "infra",
        "repro_keywords": ["cron", "silent", "backup", "alert"],
    },
    {
        "title_tmpl": "Slow query on {table} — {latency}s p99 latency",
        "desc_tmpl": (
            "The /api/{table}/list endpoint has p99 latency of {latency}s. "
            "EXPLAIN ANALYZE shows a sequential scan. No index on {column}. "
            "No user-facing errors, but sluggish UX under load."
        ),
        "severity": "P2", "component": "database",
        "repro_keywords": ["slow", "query", "latency", "index", "sequential"],
    },
    {
        "title_tmpl": "Dashboard {chart} labels overlap on {resolution} screens",
        "desc_tmpl": (
            "On {resolution} resolution the Y-axis labels on the {chart} chart "
            "overlap, making them unreadable. Higher resolutions are fine. "
            "Cosmetic only — data is accessible via tooltips."
        ),
        "severity": "P3", "component": "frontend",
        "repro_keywords": ["overlap", "label", "resolution", "chart"],
    },
]

FEATURE_TEMPLATES = [
    {
        "title_tmpl": "Add {feature} support for {persona} users",
        "desc_tmpl": (
            "Enterprise customers have requested {feature}. This would {benefit}. "
            "Expected: the app should support {feature} accessible from {location}."
        ),
        "severity": "P3", "component": "backend",
        "repro_keywords": [],
    },
    {
        "title_tmpl": "Allow bulk {action} via CSV import",
        "desc_tmpl": (
            "Currently admins must {action} one at a time through the UI. "
            "For enterprise on-boarding we need to import thousands of records "
            "from an HR export. Please add a CSV-upload flow with column mapping "
            "and a dry-run validation step."
        ),
        "severity": "P3", "component": "frontend",
        "repro_keywords": [],
    },
    {
        "title_tmpl": "Add multi-factor authentication (MFA) to {flow}",
        "desc_tmpl": (
            "Security audit recommends MFA on {flow}. We need TOTP (Google "
            "Authenticator) and SMS OTP as fallback. Admins should enforce MFA org-wide."
        ),
        "severity": "P2", "component": "backend",
        "repro_keywords": [],
    },
]

QUESTION_TEMPLATES = [
    {
        "title_tmpl": "How do I {user_action} in {product}?",
        "desc_tmpl": (
            "Hi, I've been looking through the docs but can't find how to "
            "{user_action}. Is this feature available? If so, where is it? Thanks."
        ),
        "severity": "P4", "component": "frontend",
        "repro_keywords": [],
    },
    {
        "title_tmpl": "What is the rate limit for the {endpoint} endpoint?",
        "desc_tmpl": (
            "We're building an integration and need to know the rate limits "
            "for {endpoint}. The docs mention limits exist but don't specify "
            "the numbers. Can you clarify?"
        ),
        "severity": "P4", "component": "backend",
        "repro_keywords": [],
    },
]

_COMPONENTS   = ["frontend", "backend", "infra", "database", "mobile"]
_PLATFORMS    = ["Android 13", "iOS 17", "Windows 11", "Ubuntu 22.04", "macOS Sonoma"]
_ACTIONS      = ["logging out", "uploading a file", "opening a modal", "submitting a form", "refreshing the page"]
_METHODS      = ["destroy", "handle", "process", "init", "teardown"]
_INPUT_TYPES  = ["special", "unicode", "emoji", "null-byte", "control"]
_JOBS         = ["backup", "sync", "report", "cleanup", "index"]
_TABLES       = ["users", "orders", "products", "sessions", "events"]
_CHARTS       = ["analytics", "revenue", "usage", "retention", "conversion"]
_RESOLUTIONS  = ["1366x768", "1280x720", "1024x768", "1440x900"]
_FEATURES     = ["dark mode", "SSO", "audit logging", "webhook support", "2FA"]
_PERSONAS     = ["enterprise", "mobile", "admin", "developer", "power"]
_BENEFITS     = ["reduce eye strain", "improve security", "meet compliance", "speed up workflows"]
_LOCATIONS    = ["Settings > Account", "the sidebar", "the profile menu", "the dashboard"]
_FLOWS        = ["the admin login", "the checkout flow", "the API", "password reset"]
_ENDPOINTS    = ["/api/users", "/api/search", "/api/export", "/api/webhooks"]
_PRODUCTS     = ["the dashboard", "the mobile app", "the API", "the admin panel"]
_USER_ACTIONS = ["export data to CSV", "set up webhooks", "configure SSO", "manage team roles"]


def _pick(rng: random.Random, lst: list) -> str:
    return rng.choice(lst)


def _version(rng: random.Random) -> str:
    return f"v{rng.randint(2,5)}.{rng.randint(0,9)}.{rng.randint(0,9)}"


def _date(rng: random.Random) -> str:
    m = rng.randint(1, 12)
    d = rng.randint(1, 28)
    return f"2024-{m:02d}-{d:02d}"


def _reporter(rng: random.Random) -> str:
    first = _pick(rng, ["alice", "bob", "carol", "dave", "eve", "frank",
                         "grace", "henry", "iris", "jack", "kate", "liam"])
    domain = _pick(rng, ["example.com", "corp.io", "startup.dev", "enterprise.org"])
    return f"{first}@{domain}"


def generate_issue(task_id: int, seed: int, index: int = 0) -> dict:
    """Generate a single issue deterministically from (task_id, seed, index)."""
    rng = random.Random(seed * 100 + index)
    issue_id = f"GEN-{seed:04d}-{index:02d}"

    ctx = {
        "component": "backend", "component_cap": "Backend",
        "action": _pick(rng, _ACTIONS), "platform": _pick(rng, _PLATFORMS),
        "version": _version(rng), "method": _pick(rng, _METHODS),
        "line": rng.randint(50, 300), "input_type": _pick(rng, _INPUT_TYPES),
        "job": _pick(rng, _JOBS), "days": rng.randint(2, 7),
        "date": _date(rng), "table": _pick(rng, _TABLES),
        "latency": rng.randint(4, 15), "column": "email",
        "chart": _pick(rng, _CHARTS), "resolution": _pick(rng, _RESOLUTIONS),
        "feature": _pick(rng, _FEATURES), "persona": _pick(rng, _PERSONAS),
        "benefit": _pick(rng, _BENEFITS), "location": _pick(rng, _LOCATIONS),
        "flow": _pick(rng, _FLOWS), "endpoint": _pick(rng, _ENDPOINTS),
        "product": _pick(rng, _PRODUCTS), "user_action": _pick(rng, _USER_ACTIONS),
    }

    if task_id == 1:
        type_idx = index % 3
        if type_idx == 0:
            tpl = _pick(rng, BUG_TEMPLATES)
            issue_type = "bug"
        elif type_idx == 1:
            tpl = _pick(rng, FEATURE_TEMPLATES)
            issue_type = "feature"
        else:
            tpl = _pick(rng, QUESTION_TEMPLATES)
            issue_type = "question"
        comp = tpl["component"]
        ctx["component"] = comp
        ctx["component_cap"] = comp.capitalize()
        try:
            title = tpl["title_tmpl"].format(**ctx)
            desc  = tpl["desc_tmpl"].format(**ctx)
        except KeyError:
            title = f"Issue with {comp}"
            desc  = "See description."
        return {
            "issue_id": issue_id, "title": title, "description": desc,
            "reporter": _reporter(rng),
            "created_at": f"{_date(rng)}T{rng.randint(8,18):02d}:{rng.randint(0,59):02d}:00Z",
            "ground_truth": {"issue_type": issue_type},
        }

    elif task_id == 2:
        tpl = _pick(rng, BUG_TEMPLATES)
        comp = tpl["component"]
        sev  = tpl["severity"]
        ctx["component"] = comp
        ctx["component_cap"] = comp.capitalize()
        try:
            title = tpl["title_tmpl"].format(**ctx)
            desc  = tpl["desc_tmpl"].format(**ctx)
        except KeyError:
            title = f"Bug in {comp}"
            desc  = "Needs investigation."
        return {
            "issue_id": issue_id, "title": title, "description": desc,
            "reporter": _reporter(rng),
            "created_at": f"{_date(rng)}T{rng.randint(8,18):02d}:00:00Z",
            "ground_truth": {"severity": sev, "component": comp},
        }

    else:  # task 3 — use static adversarial set
        from data.issues import TASK3_ISSUES
        return TASK3_ISSUES[index % len(TASK3_ISSUES)]


def generate_episode(task_id: int, seed: int, num_issues: int) -> list:
    """Generate a full episode of num_issues issues."""
    return [generate_issue(task_id, seed, i) for i in range(num_issues)]
