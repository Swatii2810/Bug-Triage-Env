"""
30 realistic GitHub-style bug reports.
10 bugs (P1/P2/P3), 10 feature requests, 10 questions.
5 are duplicates of earlier issues.
"""

ISSUES = [
    # ── BUGS ──────────────────────────────────────────────────────────────────
    {
        "issue_id": "ISSUE-001",
        "title": "App crashes on login with Google OAuth",
        "description": (
            "When users attempt to sign in using Google OAuth on the mobile app, "
            "the application crashes immediately after the OAuth redirect. "
            "This affects 100% of Google login attempts in production. "
            "Error in logs: NullPointerException at AuthCallbackHandler.java:42. "
            "Regression introduced in v2.3.1."
        ),
        "reporter": "alice_dev",
        "created_at": "2024-01-15T09:23:00Z",
        "ground_truth": {
            "issue_type": "bug",
            "severity": "P1",
            "component": "mobile",
            "assigned_team": "mobile",
            "repro_steps_keywords": ["google", "oauth", "login", "crash", "mobile"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-002",
        "title": "Database connection pool exhausted under load",
        "description": (
            "Under sustained load (>500 concurrent users), the PostgreSQL connection pool "
            "becomes exhausted and new requests fail with 'too many connections'. "
            "The pool is configured for 100 connections but we're seeing 200+ open connections. "
            "Affects checkout flow and causes revenue loss. Happens every Friday evening."
        ),
        "reporter": "bob_sre",
        "created_at": "2024-01-16T14:05:00Z",
        "ground_truth": {
            "issue_type": "bug",
            "severity": "P1",
            "component": "database",
            "assigned_team": "platform",
            "repro_steps_keywords": ["load", "concurrent", "connection", "pool", "postgres"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-003",
        "title": "User profile images not loading in Safari",
        "description": (
            "Profile images fail to render in Safari 16+ on macOS. "
            "The img tags return 200 but display as broken images. "
            "Chrome and Firefox work fine. Console shows: "
            "'Blocked loading mixed active content'. Images are served over HTTP "
            "while the page is HTTPS."
        ),
        "reporter": "carol_qa",
        "created_at": "2024-01-17T11:30:00Z",
        "ground_truth": {
            "issue_type": "bug",
            "severity": "P3",
            "component": "frontend",
            "assigned_team": "core",
            "repro_steps_keywords": ["safari", "profile", "image", "broken", "https"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-004",
        "title": "Payment webhook silently drops events when payload > 64KB",
        "description": (
            "Stripe webhook events larger than 64KB are silently dropped by our ingestion service. "
            "This causes missed payment confirmations and orders stuck in 'pending' state. "
            "Discovered after a batch of subscription renewals failed to process. "
            "The nginx body size limit is set to 64KB."
        ),
        "reporter": "dave_backend",
        "created_at": "2024-01-18T08:45:00Z",
        "ground_truth": {
            "issue_type": "bug",
            "severity": "P2",
            "component": "backend",
            "assigned_team": "core",
            "repro_steps_keywords": ["webhook", "stripe", "payload", "64kb", "nginx", "payment"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-005",
        "title": "Kubernetes pods OOMKilled during nightly batch job",
        "description": (
            "Every night at 02:00 UTC the data-pipeline pods are OOMKilled. "
            "Memory usage spikes from 512MB to 4GB within 10 minutes of job start. "
            "The batch job processes ~2M records. Memory limit is 2GB. "
            "Started after upgrading pandas from 1.5 to 2.0."
        ),
        "reporter": "eve_devops",
        "created_at": "2024-01-19T03:12:00Z",
        "ground_truth": {
            "issue_type": "bug",
            "severity": "P2",
            "component": "infra",
            "assigned_team": "devops",
            "repro_steps_keywords": ["kubernetes", "oom", "memory", "batch", "pandas", "pod"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-006",
        "title": "Search autocomplete shows stale results after cache flush",
        "description": (
            "After flushing the Redis cache, the search autocomplete continues to show "
            "outdated suggestions for up to 30 minutes. The TTL is set to 5 minutes "
            "but the old data persists. Affects the main search bar on web and mobile."
        ),
        "reporter": "frank_fe",
        "created_at": "2024-01-20T16:00:00Z",
        "ground_truth": {
            "issue_type": "bug",
            "severity": "P3",
            "component": "backend",
            "assigned_team": "platform",
            "repro_steps_keywords": ["search", "autocomplete", "cache", "redis", "stale"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-007",
        "title": "Dark mode toggle resets on page refresh",
        "description": (
            "The dark mode preference is not persisted across page refreshes. "
            "Users toggle dark mode, refresh the page, and it reverts to light mode. "
            "The preference should be saved to localStorage but the key is missing after reload."
        ),
        "reporter": "grace_ux",
        "created_at": "2024-01-21T10:15:00Z",
        "ground_truth": {
            "issue_type": "bug",
            "severity": "P3",
            "component": "frontend",
            "assigned_team": "core",
            "repro_steps_keywords": ["dark mode", "toggle", "refresh", "localstorage", "persist"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-008",
        "title": "SQL injection vulnerability in user search endpoint",
        "description": (
            "The /api/users/search endpoint does not sanitize the 'q' query parameter. "
            "Passing `' OR '1'='1` returns all users. This is a critical security vulnerability "
            "exposing PII. Discovered during internal pen test on 2024-01-22."
        ),
        "reporter": "henry_security",
        "created_at": "2024-01-22T09:00:00Z",
        "ground_truth": {
            "issue_type": "bug",
            "severity": "P1",
            "component": "backend",
            "assigned_team": "core",
            "repro_steps_keywords": ["sql", "injection", "search", "sanitize", "security", "api"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-009",
        "title": "iOS app freezes when switching between tabs rapidly",
        "description": (
            "On iOS 17, rapidly switching between the Home, Explore, and Profile tabs "
            "causes the app to freeze for 3-5 seconds. CPU spikes to 100% during the freeze. "
            "Reproducible on iPhone 12 and newer. Not observed on Android."
        ),
        "reporter": "iris_mobile",
        "created_at": "2024-01-23T14:30:00Z",
        "ground_truth": {
            "issue_type": "bug",
            "severity": "P2",
            "component": "mobile",
            "assigned_team": "mobile",
            "repro_steps_keywords": ["ios", "tab", "freeze", "cpu", "iphone", "swift"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-010",
        "title": "Email notifications sent twice for the same event",
        "description": (
            "Users are receiving duplicate email notifications for order confirmations. "
            "The issue appears to be a race condition in the notification worker — "
            "two workers pick up the same job from the queue simultaneously. "
            "Affects ~5% of orders. Started after scaling workers from 2 to 8."
        ),
        "reporter": "jack_backend",
        "created_at": "2024-01-24T11:00:00Z",
        "ground_truth": {
            "issue_type": "bug",
            "severity": "P2",
            "component": "backend",
            "assigned_team": "platform",
            "repro_steps_keywords": ["email", "duplicate", "notification", "race condition", "worker", "queue"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },

    # ── FEATURE REQUESTS ──────────────────────────────────────────────────────
    {
        "issue_id": "ISSUE-011",
        "title": "Add two-factor authentication via TOTP",
        "description": (
            "We need to support TOTP-based 2FA (Google Authenticator, Authy) for user accounts. "
            "Currently only SMS 2FA is available. TOTP is more secure and doesn't require a phone number. "
            "Should support QR code enrollment and backup codes."
        ),
        "reporter": "kate_pm",
        "created_at": "2024-01-25T09:00:00Z",
        "ground_truth": {
            "issue_type": "feature",
            "severity": "P2",
            "component": "backend",
            "assigned_team": "core",
            "repro_steps_keywords": ["2fa", "totp", "authenticator", "qr", "security"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-012",
        "title": "Export dashboard data to CSV and Excel",
        "description": (
            "Users want to export their analytics dashboard data to CSV and Excel formats. "
            "Currently only PDF export is supported. This is a frequently requested feature "
            "from enterprise customers who need to process data in spreadsheets."
        ),
        "reporter": "liam_sales",
        "created_at": "2024-01-26T10:30:00Z",
        "ground_truth": {
            "issue_type": "feature",
            "severity": "P2",
            "component": "frontend",
            "assigned_team": "core",
            "repro_steps_keywords": ["export", "csv", "excel", "dashboard", "download"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-013",
        "title": "Add Slack integration for alert notifications",
        "description": (
            "Teams want to receive system alerts and monitoring notifications directly in Slack. "
            "Should support configurable channels per alert type, message formatting with severity colors, "
            "and the ability to acknowledge alerts from within Slack."
        ),
        "reporter": "mia_devops",
        "created_at": "2024-01-27T13:00:00Z",
        "ground_truth": {
            "issue_type": "feature",
            "severity": "P3",
            "component": "infra",
            "assigned_team": "devops",
            "repro_steps_keywords": ["slack", "integration", "alert", "notification", "webhook"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-014",
        "title": "Implement GraphQL API for mobile clients",
        "description": (
            "Mobile clients currently use REST APIs which result in over-fetching. "
            "A GraphQL API would allow clients to request exactly the data they need, "
            "reducing payload sizes by an estimated 60%. Should support subscriptions for real-time updates."
        ),
        "reporter": "noah_mobile",
        "created_at": "2024-01-28T09:45:00Z",
        "ground_truth": {
            "issue_type": "feature",
            "severity": "P2",
            "component": "backend",
            "assigned_team": "platform",
            "repro_steps_keywords": ["graphql", "api", "mobile", "subscription", "rest"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-015",
        "title": "Add offline mode support to mobile app",
        "description": (
            "Users in areas with poor connectivity need to use core features offline. "
            "The app should cache recent data locally and sync when connectivity is restored. "
            "Priority features for offline: reading content, drafting posts, viewing profile."
        ),
        "reporter": "olivia_pm",
        "created_at": "2024-01-29T11:00:00Z",
        "ground_truth": {
            "issue_type": "feature",
            "severity": "P3",
            "component": "mobile",
            "assigned_team": "mobile",
            "repro_steps_keywords": ["offline", "cache", "sync", "mobile", "connectivity"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-016",
        "title": "Implement database query result caching layer",
        "description": (
            "Frequently executed read queries are hitting the database on every request. "
            "We need a caching layer (Redis) in front of the database for read-heavy endpoints. "
            "Expected to reduce DB load by 70% and improve p99 latency from 800ms to 50ms."
        ),
        "reporter": "peter_dba",
        "created_at": "2024-01-30T14:00:00Z",
        "ground_truth": {
            "issue_type": "feature",
            "severity": "P2",
            "component": "database",
            "assigned_team": "platform",
            "repro_steps_keywords": ["cache", "redis", "database", "query", "performance"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-017",
        "title": "Add keyboard shortcuts for power users",
        "description": (
            "Power users have requested keyboard shortcuts for common actions: "
            "creating new items (Ctrl+N), search (Ctrl+K), save (Ctrl+S), and navigation. "
            "Should include a shortcut reference modal (Ctrl+?)."
        ),
        "reporter": "quinn_ux",
        "created_at": "2024-01-31T10:00:00Z",
        "ground_truth": {
            "issue_type": "feature",
            "severity": "P3",
            "component": "frontend",
            "assigned_team": "core",
            "repro_steps_keywords": ["keyboard", "shortcut", "hotkey", "navigation", "accessibility"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-018",
        "title": "Multi-region deployment support",
        "description": (
            "Enterprise customers in EU and APAC require data residency compliance. "
            "We need to support deploying the stack to multiple AWS regions with data isolation. "
            "Should include region-aware routing and cross-region replication for non-PII data."
        ),
        "reporter": "rachel_infra",
        "created_at": "2024-02-01T09:00:00Z",
        "ground_truth": {
            "issue_type": "feature",
            "severity": "P2",
            "component": "infra",
            "assigned_team": "devops",
            "repro_steps_keywords": ["multi-region", "aws", "deployment", "data residency", "gdpr"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-019",
        "title": "Add biometric authentication to mobile app",
        "description": (
            "Users want to use Face ID and fingerprint to log in to the mobile app "
            "instead of entering their password every time. Should fall back to PIN if biometrics fail. "
            "Required for enterprise MDM compliance."
        ),
        "reporter": "sam_mobile",
        "created_at": "2024-02-02T11:30:00Z",
        "ground_truth": {
            "issue_type": "feature",
            "severity": "P2",
            "component": "mobile",
            "assigned_team": "mobile",
            "repro_steps_keywords": ["biometric", "face id", "fingerprint", "authentication", "mobile"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-020",
        "title": "Implement audit log for admin actions",
        "description": (
            "We need a comprehensive audit trail for all admin actions: user management, "
            "config changes, data exports. Logs should be immutable, searchable, and exportable. "
            "Required for SOC2 compliance audit in Q2."
        ),
        "reporter": "tina_compliance",
        "created_at": "2024-02-03T09:00:00Z",
        "ground_truth": {
            "issue_type": "feature",
            "severity": "P1",
            "component": "backend",
            "assigned_team": "core",
            "repro_steps_keywords": ["audit", "log", "admin", "compliance", "soc2", "immutable"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },

    # ── QUESTIONS / SUPPORT ───────────────────────────────────────────────────
    {
        "issue_id": "ISSUE-021",
        "title": "How do I reset my API rate limit?",
        "description": (
            "I've hit the API rate limit (429 Too Many Requests) and I'm not sure how to reset it "
            "or request a higher limit. My use case requires ~10,000 requests/hour but the default "
            "limit appears to be 1,000/hour. Is there a way to increase this?"
        ),
        "reporter": "user_dev_1",
        "created_at": "2024-02-04T10:00:00Z",
        "ground_truth": {
            "issue_type": "question",
            "severity": "P4",
            "component": "backend",
            "assigned_team": "platform",
            "repro_steps_keywords": ["rate limit", "429", "api", "quota", "increase"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-022",
        "title": "What is the recommended way to handle pagination in the REST API?",
        "description": (
            "I'm building a client that needs to fetch all records from /api/items. "
            "The docs mention cursor-based and offset pagination but don't explain when to use each. "
            "What's the recommended approach for large datasets (>100k records)?"
        ),
        "reporter": "user_dev_2",
        "created_at": "2024-02-05T14:00:00Z",
        "ground_truth": {
            "issue_type": "question",
            "severity": "P4",
            "component": "backend",
            "assigned_team": "platform",
            "repro_steps_keywords": ["pagination", "cursor", "offset", "api", "rest"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-023",
        "title": "How to configure custom domain for self-hosted deployment?",
        "description": (
            "I'm self-hosting the application and want to configure a custom domain with SSL. "
            "I've set up nginx as a reverse proxy but the WebSocket connections keep dropping. "
            "What's the correct nginx configuration for WebSocket proxying?"
        ),
        "reporter": "user_ops_1",
        "created_at": "2024-02-06T09:30:00Z",
        "ground_truth": {
            "issue_type": "question",
            "severity": "P4",
            "component": "infra",
            "assigned_team": "devops",
            "repro_steps_keywords": ["nginx", "websocket", "ssl", "domain", "proxy", "self-hosted"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-024",
        "title": "Does the mobile SDK support React Native?",
        "description": (
            "We're building a React Native app and want to use the mobile SDK. "
            "The docs only mention native iOS (Swift) and Android (Kotlin) SDKs. "
            "Is there a React Native wrapper available or planned?"
        ),
        "reporter": "user_dev_3",
        "created_at": "2024-02-07T11:00:00Z",
        "ground_truth": {
            "issue_type": "question",
            "severity": "P4",
            "component": "mobile",
            "assigned_team": "mobile",
            "repro_steps_keywords": ["react native", "sdk", "mobile", "javascript", "wrapper"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-025",
        "title": "How to migrate data from v1 to v2 schema?",
        "description": (
            "We're upgrading from v1 to v2 and the migration guide mentions running a migration script "
            "but doesn't provide the script. The v2 schema has breaking changes to the users and orders tables. "
            "Is there an official migration tool or do we need to write custom SQL?"
        ),
        "reporter": "user_dba_1",
        "created_at": "2024-02-08T13:00:00Z",
        "ground_truth": {
            "issue_type": "question",
            "severity": "P3",
            "component": "database",
            "assigned_team": "platform",
            "repro_steps_keywords": ["migration", "schema", "v1", "v2", "sql", "upgrade"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-026",
        "title": "What are the system requirements for running in production?",
        "description": (
            "We're planning our infrastructure for a production deployment expecting 10,000 DAU. "
            "What are the minimum recommended CPU, RAM, and storage requirements? "
            "Should we use managed Kubernetes or bare metal?"
        ),
        "reporter": "user_ops_2",
        "created_at": "2024-02-09T10:00:00Z",
        "ground_truth": {
            "issue_type": "question",
            "severity": "P4",
            "component": "infra",
            "assigned_team": "devops",
            "repro_steps_keywords": ["production", "requirements", "cpu", "ram", "kubernetes", "infrastructure"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-027",
        "title": "How to implement SSO with Okta?",
        "description": (
            "Our enterprise requires SSO via Okta SAML 2.0. The docs mention OIDC support "
            "but we need SAML. Is SAML supported? If so, what are the SP metadata URL and "
            "required attribute mappings?"
        ),
        "reporter": "user_enterprise_1",
        "created_at": "2024-02-10T09:00:00Z",
        "ground_truth": {
            "issue_type": "question",
            "severity": "P3",
            "component": "backend",
            "assigned_team": "core",
            "repro_steps_keywords": ["sso", "okta", "saml", "oidc", "enterprise", "authentication"],
            "is_duplicate": False,
            "duplicate_of": "",
        },
    },
    {
        "issue_id": "ISSUE-028",
        "title": "App crashes on login — same as ISSUE-001",
        "description": (
            "Getting the same crash as reported in ISSUE-001. Google OAuth login crashes the app "
            "immediately after the redirect. Seeing NullPointerException in the logs. "
            "This is still happening on v2.3.2."
        ),
        "reporter": "user_mobile_2",
        "created_at": "2024-02-11T10:00:00Z",
        "ground_truth": {
            "issue_type": "bug",
            "severity": "P1",
            "component": "mobile",
            "assigned_team": "mobile",
            "repro_steps_keywords": ["google", "oauth", "crash", "login", "nullpointerexception"],
            "is_duplicate": True,
            "duplicate_of": "ISSUE-001",
        },
    },
    {
        "issue_id": "ISSUE-029",
        "title": "Dark mode preference lost after refresh — duplicate",
        "description": (
            "Every time I refresh the page my dark mode setting is gone. "
            "I have to toggle it back every single session. This is very annoying. "
            "Please fix this — it was reported before as ISSUE-007."
        ),
        "reporter": "user_fe_1",
        "created_at": "2024-02-12T15:00:00Z",
        "ground_truth": {
            "issue_type": "bug",
            "severity": "P3",
            "component": "frontend",
            "assigned_team": "core",
            "repro_steps_keywords": ["dark mode", "refresh", "localstorage", "preference", "persist"],
            "is_duplicate": True,
            "duplicate_of": "ISSUE-007",
        },
    },
    {
        "issue_id": "ISSUE-030",
        "title": "Duplicate email notifications for orders",
        "description": (
            "I'm receiving two confirmation emails every time I place an order. "
            "This started about a week ago. My inbox is flooded. "
            "Seems related to ISSUE-010 about the notification worker race condition."
        ),
        "reporter": "user_customer_1",
        "created_at": "2024-02-13T09:00:00Z",
        "ground_truth": {
            "issue_type": "bug",
            "severity": "P2",
            "component": "backend",
            "assigned_team": "platform",
            "repro_steps_keywords": ["email", "duplicate", "notification", "order", "confirmation"],
            "is_duplicate": True,
            "duplicate_of": "ISSUE-010",
        },
    },
]

# Task-specific issue subsets
TASK1_ISSUES = ISSUES[:10]   # Easy: just classify type
TASK2_ISSUES = ISSUES[10:20] # Medium: severity + component

# Adversarial Task 3 set — 8 hand-crafted issues with misleading titles and subtle duplicates
TASK3_ISSUES = [
    {
        "issue_id": "T3-001",
        "title": "App freezes when opening notification tray on iOS 17",
        "description": (
            "After v4.2.1 the app freezes 5-10 seconds whenever the user pulls "
            "down the iOS notification tray while in the foreground. Steps: "
            "1) Open app. 2) Pull down from top to show notifications. 3) Observe freeze. "
            "Affects iPhone 12+ running iOS 17.x."
        ),
        "reporter": "kate@example.com",
        "created_at": "2024-03-11T08:00:00Z",
        "ground_truth": {
            "issue_type": "bug", "severity": "P2", "component": "mobile",
            "assigned_team": "mobile",
            "repro_steps_keywords": ["open", "notification", "freeze", "ios", "foreground"],
            "is_duplicate": False, "duplicate_of": "",
        },
    },
    {
        "issue_id": "T3-002",
        "title": "Enhancement: improve data export reliability",
        "description": (
            "Since the v4.3.0 deploy, the CSV export feature silently produces "
            "empty files for any dataset over 10,000 rows. Users discover the "
            "loss only after downloading. The previous version worked correctly. "
            "This is causing data loss for finance team exports."
        ),
        "reporter": "liam@example.com",
        "created_at": "2024-03-12T09:30:00Z",
        "ground_truth": {
            "issue_type": "bug", "severity": "P1", "component": "backend",
            "assigned_team": "core",
            "repro_steps_keywords": ["export", "csv", "empty", "download", "rows"],
            "is_duplicate": False, "duplicate_of": "",
        },
    },
    {
        "issue_id": "T3-003",
        "title": "Profile page UI tweak needed",
        "description": (
            "The profile page layout looks slightly off — the avatar is a few pixels "
            "out of alignment on some screen sizes. Cosmetic only, no functional impact. "
            "While investigating the CSS, I noticed something more serious: the profile "
            "API endpoint /api/users/profile is returning another user's PII (email, "
            "phone number, address) to the requesting user under concurrent load. "
            "This is a data isolation failure exposing sensitive user data."
        ),
        "reporter": "mia@example.com",
        "created_at": "2024-03-13T20:15:00Z",
        "ground_truth": {
            "issue_type": "bug", "severity": "P1", "component": "backend",
            "assigned_team": "core",
            "repro_steps_keywords": ["profile", "api", "pii", "concurrent", "data"],
            "is_duplicate": False, "duplicate_of": "",
        },
    },
    {
        "issue_id": "T3-004",
        "title": "Dashboard shows stale data after editing a record",
        "description": (
            "After editing any record in the admin panel, the dashboard table "
            "still shows the old value. A full page refresh shows the correct "
            "data. Initially suspected a React state bug, but the /api/records "
            "endpoint returns the stale value without refresh — the backend "
            "response is served from a cache that is not invalidated on write."
        ),
        "reporter": "noah@example.com",
        "created_at": "2024-03-14T14:00:00Z",
        "ground_truth": {
            "issue_type": "bug", "severity": "P2", "component": "backend",
            "assigned_team": "platform",
            "repro_steps_keywords": ["stale", "cache", "edit", "dashboard", "invalidate"],
            "is_duplicate": False, "duplicate_of": "",
        },
    },
    {
        "issue_id": "T3-005",
        "title": "Push notifications not delivered on Android after Firebase upgrade",
        "description": (
            "Users report missing push notifications on Android 12+. Started "
            "after Firebase SDK updated from v30 to v32. iOS unaffected. "
            "FCM send logs show messages dispatched but devices never display them."
        ),
        "reporter": "olivia@example.com",
        "created_at": "2024-03-15T09:00:00Z",
        "ground_truth": {
            "issue_type": "bug", "severity": "P2", "component": "mobile",
            "assigned_team": "mobile",
            "repro_steps_keywords": ["push", "notification", "android", "firebase", "fcm"],
            "is_duplicate": False, "duplicate_of": "",
        },
    },
    {
        "issue_id": "T3-006",
        "title": "App hangs briefly when notification arrives on Android",
        "description": (
            "When a push notification arrives while the app is open on Android 13, "
            "the UI freezes for 2-3 seconds. This is different from the iOS "
            "notification tray issue. Root cause appears to be the notification "
            "handler blocking the main thread on the Android SDK side."
        ),
        "reporter": "peter@example.com",
        "created_at": "2024-03-16T10:00:00Z",
        "ground_truth": {
            "issue_type": "bug", "severity": "P3", "component": "mobile",
            "assigned_team": "mobile",
            "repro_steps_keywords": ["android", "notification", "freeze", "handler", "thread"],
            "is_duplicate": False, "duplicate_of": "",
        },
    },
    {
        "issue_id": "T3-007",
        "title": "Android users stopped receiving alerts after last SDK release",
        "description": (
            "Our Android customers are not getting any in-app alerts since the "
            "infrastructure team pushed the Firebase dependency update last sprint. "
            "Checked the messaging dashboard — the platform confirms delivery but "
            "nothing shows on the handsets. iPhone users are fine."
        ),
        "reporter": "quinn@example.com",
        "created_at": "2024-03-17T11:00:00Z",
        "ground_truth": {
            "issue_type": "bug", "severity": "P2", "component": "mobile",
            "assigned_team": "mobile",
            "repro_steps_keywords": ["android", "firebase", "alert", "delivery", "sdk"],
            "is_duplicate": True, "duplicate_of": "T3-005",
        },
    },
    {
        "issue_id": "T3-008",
        "title": "Database connection pool exhausted under peak load",
        "description": (
            "During peak hours (18:00-20:00 UTC) the app throws 'too many connections'. "
            "pg_stat_activity shows 500/500 connections. Pool not releasing connections "
            "after requests — suspected ORM session teardown leak. Causes 503 for ~15% of users."
        ),
        "reporter": "rachel@example.com",
        "created_at": "2024-03-18T20:00:00Z",
        "ground_truth": {
            "issue_type": "bug", "severity": "P1", "component": "database",
            "assigned_team": "platform",
            "repro_steps_keywords": ["connection", "pool", "leak", "peak", "503"],
            "is_duplicate": False, "duplicate_of": "",
        },
    },
]

# Full issues alias used for duplicate context lookup
ISSUES = TASK3_ISSUES
