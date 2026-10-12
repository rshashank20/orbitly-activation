#!/usr/bin/env python3
"""Orbitly — B2B SaaS activation & retention synthetic data generator.

Fictional company. Generates a 12-month, ~24K-user trial funnel with ~1.8M
product events, subscriptions, and 3 historical experiments.

Scenario mechanics (chosen so the synthetic data supports an end-to-end analysis):
  * observed activation (report_shared) around 19%; account trial-to-paid around 20%; 90d retention around 51%
  * data_source_connected fails/is abandoned by ~38% who reach it (cryptic OAuth errors)
  * paid_social is about 30% of account owners but has lower observed activation -> investigate channel quality; spend/CAC are not generated
  * report_shared is the product-defined activation event; its retention association is tested, not assumed
  * slower time-to-value predicts churn

Seeded data-quality problems (documented in DATA_DICTIONARY.md):
  * ~2% duplicate events from client retry logic
  * bot signups (is_bot_flag=1; filter via behavior)
  * pre-June-2025 timestamps stored in IST instead of UTC (instrumentation fix)
  * plan renamed mid-year: "Pro" -> "Growth" (same tier)
  * ad-blockers undercount report_shared for ~8% of activated users
  * invited teammates counted as raw signups

Usage:
    python3 data_generator.py [--db orbitly.db] [--dry-run]
"""
import argparse
import json
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

SEED = 20261012
START = datetime(2024, 7, 1)          # first signup cohort
END = datetime(2025, 6, 30)           # last signup cohort
TZ_FIX = datetime(2025, 6, 1)         # instrumentation fix: UTC from here on
RENAME_AT = datetime(2025, 1, 15)     # "Pro" -> "Growth"
N_USERS = 24000

CHANNELS = [  # (name, signup share, per-step multiplier)
    ("paid_social",    0.30, 0.72),
    ("organic_search", 0.22, 1.08),
    ("paid_search",    0.20, 0.95),
    ("referral",       0.12, 1.15),
    ("content",        0.10, 1.05),
    ("email",          0.06, 1.00),
]

STEP_P = {  # base per-step probabilities (before channel multiplier)
    "workspace": 0.80,
    "connect":   0.62,   # ~38% fail/abandon at the connection step
    "report":    0.72,
    "share":     0.60,
}

INDUSTRIES = ["ecommerce", "fintech", "healthtech", "edtech", "logistics", "hospitality"]
SIZE_BANDS = ["1-10", "11-50", "51-200", "201-1000"]
SOURCES = ["google_analytics", "meta_ads", "shopify", "hubspot", "stripe"]
CONNECT_ERRORS = ["oauth_denied", "oauth_denied", "token_expired", "unknown_error",
                  "unknown_error", "timeout", "invalid_credentials"]

SCHEMA = """
CREATE TABLE users(
    user_id TEXT PRIMARY KEY, account_id TEXT, signup_at TEXT,
    acquisition_channel TEXT, plan_trial TEXT, is_bot INTEGER, invited_by TEXT);
CREATE TABLE accounts(
    account_id TEXT PRIMARY KEY, company_size_band TEXT, industry TEXT,
    signup_cohort_month TEXT);
CREATE TABLE events(
    event_id INTEGER PRIMARY KEY, user_id TEXT, event_name TEXT,
    event_at TEXT, properties TEXT);
CREATE TABLE subscriptions(
    account_id TEXT PRIMARY KEY, converted_at TEXT, plan TEXT, mrr REAL,
    churned_at TEXT, retained_90d INTEGER);
CREATE TABLE experiments(
    experiment_id TEXT, account_id TEXT, variant TEXT, started_at TEXT);
CREATE TABLE funnel_defs(
    step TEXT, step_order INTEGER, defining_event TEXT);
CREATE INDEX idx_events_user ON events(user_id);
CREATE INDEX idx_events_name_time ON events(event_name, event_at);
CREATE INDEX idx_events_time ON events(event_at);
"""


def pick_channel(rng):
    x = rng.random()
    cum = 0.0
    for name, share, mult in CHANNELS:
        cum += share
        if x <= cum:
            return name, mult
    return CHANNELS[-1][0], CHANNELS[-1][2]


def gen_accounts_users(rng):
    """Return (accounts, users). Each account has one owner and optional later teammates."""
    accounts, users = [], []
    uid = 0
    n_accounts = 0
    while uid < N_USERS:
        n_accounts += 1
        account_id = f"A{n_accounts:05d}"
        r = rng.random()
        size = 1 if r < 0.72 else (2 if r < 0.92 else rng.randint(3, 5))
        size = min(size, N_USERS - uid)
        industry = rng.choice(INDUSTRIES)
        band = rng.choices(SIZE_BANDS, weights=[0.35, 0.35, 0.22, 0.08])[0]

        owner_day = rng.randint(0, (END - START).days)
        owner_signup = START + timedelta(days=owner_day,
                                         hours=rng.randint(0, 23),
                                         minutes=rng.randint(0, 59))
        members = []
        member_times = []
        for member_idx in range(size):
            uid += 1
            user_id = f"U{uid:05d}"
            if member_idx == 0:
                signup_at = owner_signup
                invited_by = None
            else:
                # Teammates arrive after the owner/previous team member, not before them.
                remaining_seconds = int(((END + timedelta(days=1) - timedelta(seconds=1)) - member_times[-1]).total_seconds())
                max_delay = min(30 * 86400, max(0, remaining_seconds))
                min_delay = min(86400, max_delay)
                delay_seconds = rng.randint(min_delay, max_delay) if max_delay > 0 else 0
                signup_at = member_times[-1] + timedelta(seconds=delay_seconds)
                if rng.random() < 0.35:
                    invited_by = rng.choice(members)
                elif rng.random() < 0.04:
                    invited_by = "external"
                else:
                    invited_by = None
            channel, mult = pick_channel(rng)
            is_bot = 1 if rng.random() < 0.03 else 0
            members.append(user_id)
            member_times.append(signup_at)
            users.append({
                "user_id": user_id, "account_id": account_id, "signup_at": signup_at,
                "channel": channel, "mult": mult, "is_bot": is_bot,
                "invited_by": invited_by,
                "plan_trial": rng.choices(["trial_14d", "trial_30d"], weights=[0.9, 0.1])[0],
            })
        accounts.append({"account_id": account_id, "band": band,
                         "industry": industry, "cohort": owner_signup.strftime("%Y-%m")})
    return accounts, users


def normalize_account_conversion_outcomes(users):
    """Keep paid conversion and 90-day retention at the account-owner grain.

    Subscriptions are one row per account, so invited teammates should not each
    create a separate paid-conversion event for the same company account.
    """
    by_acc = {}
    for u in users:
        by_acc.setdefault(u["account_id"], []).append(u)
    for members in by_acc.values():
        members.sort(key=lambda u: (u["signup_at"], u["user_id"]))
        owner = members[0]
        for member in members[1:]:
            member["conv"] = False
            member["converted_at"] = None
            member["ret"] = None

def clamp(p):
    return max(0.02, min(0.97, p))


def simulate_funnel(rng, users, exp_boost):
    """Assign funnel outcomes. exp_boost: {user_id: connect-prob lift}."""
    for u in users:
        if u["is_bot"]:
            u.update(ws=0, conn=0, rep=0, shr=0, week2=0, conv=0,
                     ret=None, ttv_h=None, adblock=0)
            continue
        m = u["mult"]
        boost = exp_boost.get(u["user_id"], 0.0)
        ws = rng.random() < clamp(STEP_P["workspace"] * m)
        conn = ws and rng.random() < clamp(STEP_P["connect"] * m + boost)
        rep = conn and rng.random() < clamp(STEP_P["report"] * m)
        shr = rep and rng.random() < clamp(STEP_P["share"] * m)
        # time-to-value (hours, signup -> report_shared)
        ttv = None
        if shr:
            # The product's trial lasts 14 days; activation should occur within that window.
            ttv = max(0.5, min(312, rng.lognormvariate(3.4, 1.1)))
        week2 = shr and rng.random() < 0.65
        p_conv = 0.75 if shr else 0.06
        if u["invited_by"]:
            p_conv *= 0.6
        conv = rng.random() < p_conv
        converted_at = None
        if conv:
            converted_at = u["signup_at"] + timedelta(days=rng.randint(3, 14))
            if shr and ttv is not None:
                # Keep the account's payment after the value event but inside the 14-day trial.
                converted_at = max(converted_at, u["signup_at"] + timedelta(hours=min(330, ttv + 6)))
        # 90d retention (only meaningful if converted & mature; NULL if unobservable)
        ret = None
        if conv:
            p_ret = 0.36
            if shr:
                p_ret += 0.16
                p_ret += 0.08 if (ttv or 999) < 48 else (-0.10 if ttv > 96 else 0)
            if u["channel"] == "referral":
                p_ret += 0.06
            if u["channel"] == "paid_social":
                p_ret -= 0.05
            ret = 1 if rng.random() < clamp(p_ret) else 0
        # ad-blocker: 8% of activated users lose their report_shared event
        adblock = 1 if (shr and rng.random() < 0.08) else 0
        u.update(ws=ws, conn=conn, rep=rep, shr=shr, week2=week2, conv=conv,
                 converted_at=converted_at, ret=ret, ttv_h=ttv, adblock=adblock)


def dry_run_report(users):
    gen = [u for u in users if not u["is_bot"]]
    n = len(gen)
    shr = sum(u["shr"] for u in gen)
    conv = sum(u["conv"] for u in gen)
    rets = [u["ret"] for u in gen if u["conv"] and u["ret"] is not None]
    print(f"users={len(users)} genuine={n} bots={sum(u['is_bot'] for u in users)}")
    print(f"activation={shr/n:.1%}  trial_to_paid={conv/n:.1%}  "
          f"ret90_mature={sum(rets)/len(rets):.1%} (n={len(rets)})")
    for name, _, _ in CHANNELS:
        g = [u for u in gen if u["channel"] == name]
        a = sum(u["shr"] for u in g) / len(g)
        print(f"  {name:15s} share={len(g)/n:.1%} activation={a:.1%}")
    # aha-moment check: retention gap for report_shared doers vs non-doers
    doers = [u for u in gen if u["shr"] and u["conv"] and u["ret"] is not None]
    nondo = [u for u in gen if not u["shr"] and u["conv"] and u["ret"] is not None]
    if doers and nondo:
        print(f"aha check: ret|shared={sum(u['ret'] for u in doers)/len(doers):.1%} "
              f"vs ret|not_shared={sum(u['ret'] for u in nondo)/len(nondo):.1%}")

def to_stored(ts):
    """Pre-June-2025 timestamps were stored in IST (the instrumentation bug)."""
    if ts < TZ_FIX:
        ts = ts + timedelta(hours=5, minutes=30)
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def gen_events(rng, users):
    """Create product events with plausible stage order and a few seeded retry duplicates."""
    out = []
    noise_pages = ["pricing", "docs", "templates", "settings", "billing", "integrations", "help"]
    for u in users:
        t0 = u["signup_at"]
        ev = [("signup", t0, json.dumps({"channel": u["channel"], "plan": u["plan_trial"]}))]
        if u["is_bot"]:
            nb = rng.randint(300, 600)
            for _ in range(nb):
                ts = t0 + timedelta(seconds=rng.randint(0, 1800))
                ev.append((rng.choice(["page_view", "session_start", "click", "form_submit"]),
                           ts, json.dumps({"page": rng.choice(noise_pages)})))
            out.extend((u["user_id"], name, ts, props) for name, ts, props in ev)
            continue

        if u["invited_by"]:
            ev.append(("invite_accepted", t0 + timedelta(hours=rng.randint(1, 72)),
                       json.dumps({"invited_by": u["invited_by"]})))

        # If the account owner reaches the aha event, place all prerequisite events before it.
        if u["shr"]:
            ttv_h = u["ttv_h"] or 24.0
            workspace_at = t0 + timedelta(hours=max(0.05, ttv_h * 0.12))
            connected_at = t0 + timedelta(hours=max(ttv_h * 0.38, ttv_h * 0.12 + 0.04))
            report_at = t0 + timedelta(hours=max(ttv_h * 0.78, ttv_h * 0.38 + 0.04))
            share_at = t0 + timedelta(hours=ttv_h)
        else:
            workspace_at = t0 + timedelta(hours=rng.randint(1, 24)) if u["ws"] else None
            connected_at = (workspace_at + timedelta(minutes=rng.randint(10, 240))) if (u["ws"] and u["conn"]) else None
            report_at = (connected_at + timedelta(hours=rng.randint(1, 48))) if (u["conn"] and u["rep"]) else None
            share_at = None

        if u["ws"]:
            ev.append(("workspace_created", workspace_at, json.dumps({"seats": rng.randint(1, 8)})))
            if u["conn"]:
                attempt_at = connected_at - timedelta(minutes=2)
                ev.append(("data_source_connect_attempted", attempt_at,
                           json.dumps({"source": rng.choice(SOURCES), "attempt": 1})))
                ev.append(("data_source_connected", connected_at,
                           json.dumps({"source": rng.choice(SOURCES)})))
            else:
                attempts = 1
                while attempts < 3 and rng.random() < 0.5:
                    attempts += 1
                for attempt in range(1, attempts + 1):
                    attempted_at = workspace_at + timedelta(minutes=5 + 20 * (attempt - 1))
                    ev.append(("data_source_connect_attempted", attempted_at,
                               json.dumps({"source": rng.choice(SOURCES), "attempt": attempt})))
                    ev.append(("data_source_connect_failed", attempted_at + timedelta(minutes=2),
                               json.dumps({"error": rng.choice(CONNECT_ERRORS)})))

        if u["rep"]:
            if report_at is None:
                report_at = (workspace_at or t0) + timedelta(hours=rng.randint(2, 48))
            if rng.random() < 0.40:
                ev.append(("template_used", report_at - timedelta(minutes=5),
                           json.dumps({"template": "marketing_overview"})))
            ev.append(("report_created", report_at + timedelta(minutes=1),
                       json.dumps({"widgets": rng.randint(2, 9)})))
            for _ in range(rng.randint(1, 4)):
                ev.append(("report_viewed", report_at + timedelta(hours=rng.randint(1, 96)), "{}"))

        if u["shr"] and not u["adblock"]:
            # The user really shared the report, but the client event is missing for a seeded ad-blocker slice.
            ev.append(("report_shared", share_at, json.dumps({"via": "link"})))

        if u["week2"]:
            ev.append(("week2_active", t0 + timedelta(days=rng.randint(8, 14)), "{}"))
        if u["conv"]:
            ev.append(("trial_converted", u["converted_at"],
                       json.dumps({"plan": "pro"})))

        # Session/page events are background usage; their timestamps are not process-stage events.
        depth = u["shr"] + u["rep"] + u["conn"] + u["ws"]
        n_sessions = max(1, int(rng.expovariate(1 / (4 + depth * 6))))
        for _ in range(n_sessions):
            ts = t0 + timedelta(days=rng.randint(0, 100), hours=rng.randint(0, 23))
            if ts > END + timedelta(days=150):
                continue
            ev.append(("session_start", ts, "{}"))
            for _ in range(rng.randint(1, 4)):
                ev.append(("page_view", ts + timedelta(minutes=rng.randint(1, 40)),
                           json.dumps({"page": rng.choice(noise_pages)})))
        out.extend((u["user_id"], name, ts, props) for name, ts, props in ev)

    # Add retry duplicates seconds later, retaining the same user, event and payload.
    duplicates = []
    for row in out:
        if rng.random() < 0.02:
            uid, name, ts, props = row
            duplicates.append((uid, name, ts + timedelta(seconds=rng.randint(1, 5)), props))
    out.extend(duplicates)
    rng.shuffle(out)
    return [(uid, name, to_stored(ts), props) for uid, name, ts, props in out]

def gen_subscriptions(rng, users):
    """One row per account. retained_90d NULL when not yet observable."""
    by_acc = {}
    for u in users:
        by_acc.setdefault(u["account_id"], []).append(u)
    rows = []
    for acc, members in by_acc.items():
        conv_u = [u for u in members if u["conv"]]
        if not conv_u:
            rows.append((acc, None, None, None, None, None))
            continue
        u0 = min(conv_u, key=lambda u: u["signup_at"])
        # Reuse the same timestamp as the trial_converted event.
        converted_at = u0["converted_at"]
        plan = "Pro" if converted_at < RENAME_AT else "Growth"
        mrr = rng.choice([49, 99, 249, 499])
        # retained_90d observable only for mature cohorts
        ret, churned = None, None
        if converted_at <= datetime(2025, 3, 31):
            ret = u0["ret"]
            if ret == 0:
                churned = (converted_at + timedelta(days=rng.randint(30, 89))).strftime("%Y-%m-%d")
        rows.append((acc, converted_at.strftime("%Y-%m-%d %H:%M:%S"), plan,
                     mrr, churned, ret))
    return rows


def gen_experiments(rng, users):
    """3 historical experiments on mature-cohort accounts; EXP-OAUTH/B has a true lift."""
    by_acc = {}
    for u in users:
        by_acc.setdefault(u["account_id"], []).append(u)
    mature = [a for a, ms in by_acc.items()
              if min(u["signup_at"] for u in ms) < datetime(2024, 12, 1)
              and not any(u["is_bot"] for u in ms)]
    rng.shuffle(mature)
    defs = [("EXP-OAUTH", 0.04), ("EXP-CHECKLIST", 0.0), ("EXP-TEMPLATES", 0.0)]
    rows, boost = [], {}
    for exp_id, lift in defs:
        for acc in mature[:2000]:
            variant = "B" if rng.random() < 0.5 else "A"
            ms = by_acc[acc]
            started = min(u["signup_at"] for u in ms)  # assignment occurs at trial start
            rows.append((exp_id, acc, variant, started.strftime("%Y-%m-%d %H:%M:%S")))
            if variant == "B" and lift:
                for u in ms:
                    boost[u["user_id"]] = lift
        mature = mature[2000:]
    return rows, boost


FUNNEL_DEFS = [
    ("signup", 1, "signup"),
    ("workspace_created", 2, "workspace_created"),
    ("data_source_connected", 3, "data_source_connected"),
    ("first_report_built", 4, "report_created"),
    ("report_shared", 5, "report_shared"),
    ("second_week_active", 6, "week2_active"),
    ("trial_converted", 7, "trial_converted"),
    ("retained_90d", 8, "DERIVED"),
]

DICT_TEMPLATE = """# Orbitly — Data Dictionary

Synthetic data for the Activation & Retention Analytics case study.
All timestamps: UTC, **except** events before 2025-06-01 which were stored in
IST wall-time by a pre-fix instrumentation bug (add -5:30 to compare across eras).

## Tables (rows as generated: {stamp})

| Table | Rows | Grain |
|---|---|---|
| users | {n_users} | one row per trial user |
| accounts | {n_accounts} | one row per company account |
| events | {n_events} | one row per product event |
| subscriptions | {n_subs} | one row per account |
| experiments | {n_exp} | one row per account × experiment |
| funnel_defs | 8 | the KPI contract: step -> defining event |

### users
user_id, account_id, signup_at, acquisition_channel, plan_trial, is_bot (1=bot),
invited_by (user_id of inviter, or 'external', or NULL)

### accounts
account_id, company_size_band, industry, signup_cohort_month

### events
event_id, user_id, event_name, event_at, properties (JSON string)
Key events: signup, invite_accepted, workspace_created, data_source_connect_attempted,
data_source_connect_failed (properties.error), data_source_connected, template_used,
report_created, report_viewed, report_shared, week2_active, trial_converted,
session_start, page_view.

### subscriptions
account_id, converted_at, plan (**"Pro" before 2025-01-15, "Growth" after — same tier**),
mrr, churned_at, retained_90d (1/0 for converted accounts with observable follow-up; NULL for non-converters or cohorts without 90-day follow-up)

### experiments
experiment_id (EXP-OAUTH, EXP-CHECKLIST, EXP-TEMPLATES), account_id,
variant (A/B), started_at

### funnel_defs
step, step_order, defining_event. `retained_90d` is DERIVED (from subscriptions),
not an event — join carefully.

## Known data-quality issues (seeded deliberately)
1. ~2% duplicate events from client retry logic (same user/event/properties, seconds apart).
2. Bot signups: is_bot=1; also detectable by behavior (hundreds of events in minutes).
3. Mixed timezones: pre-2025-06-01 event_at is IST wall-time; post-fix is UTC.
4. Plan rename: "Pro" -> "Growth" on 2025-01-15 breaks naive plan filters.
5. Ad-blocker bias: ~8% of true activated users are missing their report_shared event. The later account outcome can still exist, so observed activation is an undercount.
6. Invited teammates appear as signups in raw counts; separate via invited_by.

## Scenario assumptions (not facts)
Funnel probabilities, channel mix/quality, the OAuth-error story, and experiment
effects are authored scenario parameters so the analysis has something real to
find. Treat all findings as findings *about this synthetic company*.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="orbitly.db")
    ap.add_argument("--dry-run", action="store_true",
                    help="simulate funnel only, print anchors, no DB")
    args = ap.parse_args()
    rng = random.Random(SEED)
    base = Path(__file__).resolve().parent

    accounts, users = gen_accounts_users(rng)
    # experiments first: EXP-OAUTH/B gives a true connect-prob lift
    exp_rows, boost = gen_experiments(rng, users)
    simulate_funnel(rng, users, boost)
    normalize_account_conversion_outcomes(users)

    if args.dry_run:
        dry_run_report(users)
        return

    print("generating events (this takes a minute)...")
    events = gen_events(rng, users)
    subs = gen_subscriptions(rng, users)

    db_path = base / args.db
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)
    con.executemany(
        "INSERT INTO users VALUES (?,?,?,?,?,?,?)",
        [(u["user_id"], u["account_id"], u["signup_at"].strftime("%Y-%m-%d %H:%M:%S"),
          u["channel"], u["plan_trial"], u["is_bot"], u["invited_by"]) for u in users])
    con.executemany(
        "INSERT INTO accounts VALUES (?,?,?,?)",
        [(a["account_id"], a["band"], a["industry"], a["cohort"]) for a in accounts])
    con.executemany(
        "INSERT INTO events (user_id, event_name, event_at, properties) VALUES (?,?,?,?)",
        events)
    con.executemany("INSERT INTO subscriptions VALUES (?,?,?,?,?,?)", subs)
    con.executemany("INSERT INTO experiments VALUES (?,?,?,?)", exp_rows)
    con.executemany("INSERT INTO funnel_defs VALUES (?,?,?)", FUNNEL_DEFS)
    con.commit()
    n_ev = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    con.close()

    (base / "DATA_DICTIONARY.md").write_text(DICT_TEMPLATE.format(
        stamp=datetime.now().strftime("%Y-%m-%d"), n_users=len(users),
        n_accounts=len(accounts), n_events=f"{n_ev:,}", n_subs=len(subs),
        n_exp=len(exp_rows)))
    print(f"wrote {db_path}  users={len(users):,} accounts={len(accounts):,} "
          f"events={n_ev:,} subscriptions={len(subs):,} experiments={len(exp_rows):,}")


if __name__ == "__main__":
    main()
