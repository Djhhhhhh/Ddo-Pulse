"""Ddo-Pulse CLI entry point."""

from __future__ import annotations

import csv
import json
import os
import signal
from pathlib import Path
from typing import Any, Optional

import typer

from ddo_pulse_core.config_yaml import (
    export_config,
    get_default_profile_template,
    load_config,
    write_default_config,
)
from ddo_pulse_cli.items_display import print_analyzed_detail, print_analyzed_list
from ddo_pulse_core.digest.builder import digest_date_today
from ddo_pulse_core.digest.runner import build_and_push_digest
from ddo_pulse_core.notifier.feishu import FEISHU_SETTING_KEY
from ddo_pulse_core.pipeline import run_once
from ddo_pulse_core.web_config import (
    load_web_config,
    sync_vite_env_file,
    write_default_web_config,
)
from ddo_pulse_db.paths import (
    ensure_data_dir,
    get_config_path,
    get_data_dir,
    get_db_path,
    get_web_config_path,
)
from ddo_pulse_db.repository import Database


def _dev_state_path() -> Path:
    return get_data_dir() / "dev_state.json"


def _terminate_pid_tree(pid: int) -> None:
    """Best-effort stop a process (and on Windows, its child tree)."""
    import subprocess
    import sys

    if pid <= 0:
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            check=False,
        )
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


app = typer.Typer(
    name="ddo-pulse",
    help="Ddo-Pulse: blog aggregation with LLM curation",
    no_args_is_help=True,
)
source_app = typer.Typer(help="Manage subscription sources")
config_app = typer.Typer(help="Manage configuration")
profile_app = typer.Typer(help="Manage LLM profiles (OpenRouter)")
items_app = typer.Typer(help="Browse analyzed articles")
digest_app = typer.Typer(help="Daily digest and Feishu push")
seed_app = typer.Typer(help="Seed library management (CSV → sources)")
app.add_typer(source_app, name="source")
app.add_typer(config_app, name="config")
app.add_typer(profile_app, name="profile")
app.add_typer(items_app, name="items")
app.add_typer(digest_app, name="digest")
app.add_typer(seed_app, name="seed")


def _get_db() -> Database:
    db_path = get_db_path()
    if not db_path.exists():
        typer.echo("Database not found. Run: ddo-pulse init", err=True)
        raise typer.Exit(1)
    return Database()


def _resolve_pipeline_job_id(db: Database, job: int) -> int | None:
    if job > 0:
        return job
    return db.get_first_pipeline_job_id()


@app.command()
def init(
    force: bool = typer.Option(False, "--force", help="Re-initialize schema if DB exists"),
) -> None:
    """Create ~/.ddo_pulse, config.yaml, and SQLite schema."""
    data_dir = ensure_data_dir()
    config_path = get_config_path()
    if not config_path.exists() or force:
        write_default_config(config_path)
        typer.echo(f"Config: {config_path}")
    else:
        typer.echo(f"Config exists: {config_path}")

    db = Database()
    if get_db_path().exists() and not force:
        typer.echo(f"Database exists: {get_db_path()} (use --force to re-init schema)")
    else:
        db.init_schema()
        typer.echo(f"Database initialized: {get_db_path()}")

    db = Database()
    if not db.list_llm_profiles():
        cfg = load_config(config_path) if config_path.exists() else {}
        llm = cfg.get("llm") or {}
        profiles = llm.get("profiles") or []
        default_name = llm.get("default_profile")
        if profiles:
            n = db.import_llm_profiles_from_yaml(profiles, default_name=default_name)
            typer.echo(f"Seeded {n} LLM profile(s) from config")
        else:
            pid = db.ensure_default_profile_from_dict(get_default_profile_template())
            typer.echo(f"Seeded default LLM profile id={pid}")
    if config_path.exists():
        db.sync_settings_from_yaml(load_config(config_path))

    web_path = get_web_config_path()
    if not web_path.exists() or force:
        write_default_web_config(web_path, force=force)
        typer.echo(f"Web config: {web_path}")
    else:
        typer.echo(f"Web config exists: {web_path}")
    sync_vite_env_file(load_web_config())

    db.close()
    typer.echo(f"Data directory: {data_dir}")


@source_app.command("add")
def source_add(
    name: str = typer.Argument(..., help="Display name"),
    type: str = typer.Argument(
        ..., help="rss | json_feed | html_list | browser_session"
    ),
    url: str = typer.Argument(..., help="Feed or list page URL"),
    config_json: Optional[str] = typer.Option(
        None, "--config-json", help="Adapter JSON string"
    ),
) -> None:
    """Add a subscription source."""
    cfg = config_json or "{}"
    allowed = ("rss", "json_feed", "html_list", "browser_session")
    if type not in allowed:
        typer.echo(f"Supported types: {', '.join(allowed)}", err=True)
        raise typer.Exit(1)
    if type in ("html_list", "browser_session") and cfg == "{}":
        typer.echo(
            "html_list / browser_session require --config-json with selectors. "
            'Example: {"selectors":{"item":"article","title":"h2 a","link":"h2 a@href"}}',
            err=True,
        )
        raise typer.Exit(1)
    try:
        json.loads(cfg)
    except json.JSONDecodeError as e:
        typer.echo(f"Invalid --config-json: {e}", err=True)
        raise typer.Exit(1)

    db = _get_db()
    job_id = db.get_first_pipeline_job_id()
    if job_id is None:
        typer.echo(
            "还没有定时任务。请先在 Web「配置」中新建任务，或使用 API POST /pipeline-jobs。",
            err=True,
        )
        raise typer.Exit(1)
    sid = db.add_source(
        job_id=job_id, name=name, type_=type, url=url, config_json=cfg
    )
    db.close()
    typer.echo(f"Added source id={sid} name={name!r} type={type} url={url}")


@source_app.command("list")
def source_list() -> None:
    """List all sources."""
    db = _get_db()
    rows = db.list_sources()
    db.close()
    if not rows:
        typer.echo("No sources.")
        return
    typer.echo(f"{'ID':<4} {'EN':<3} {'TYPE':<12} {'NAME':<20} URL")
    for r in rows:
        en = "Y" if r["enabled"] else "N"
        typer.echo(
            f"{r['id']:<4} {en:<3} {r['type']:<12} {r['name'][:20]:<20} {r['url']}"
        )


@source_app.command("rm")
def source_rm(source_id: int = typer.Argument(..., help="Source ID")) -> None:
    """Remove a source."""
    db = _get_db()
    ok = db.delete_source(source_id)
    db.close()
    if not ok:
        typer.echo(f"Source {source_id} not found.", err=True)
        raise typer.Exit(1)
    typer.echo(f"Removed source {source_id}")


@source_app.command("enable")
def source_enable(source_id: int = typer.Argument(...)) -> None:
    db = _get_db()
    ok = db.set_source_enabled(source_id, True)
    db.close()
    if not ok:
        typer.echo(f"Source {source_id} not found.", err=True)
        raise typer.Exit(1)
    typer.echo(f"Enabled source {source_id}")


@source_app.command("disable")
def source_disable(source_id: int = typer.Argument(...)) -> None:
    db = _get_db()
    ok = db.set_source_enabled(source_id, False)
    db.close()
    if not ok:
        typer.echo(f"Source {source_id} not found.", err=True)
        raise typer.Exit(1)
    typer.echo(f"Disabled source {source_id}")


@config_app.command("show")
def config_show() -> None:
    """Show data paths and summary (no secrets)."""
    typer.echo(f"Data dir:   {get_data_dir()}")
    typer.echo(f"Config:     {get_config_path()}")
    typer.echo(f"Database:   {get_db_path()}")
    if get_db_path().exists():
        db = _get_db()
        n = len(db.list_sources())
        items = db.count_raw_items()
        analyzed = db.count_analyzed_items()
        profiles = len(db.list_llm_profiles())
        default = db.get_default_llm_profile()
        db.close()
        typer.echo(f"Sources:    {n}")
        typer.echo(f"Raw items:  {items}")
        typer.echo(f"Analyzed:   {analyzed}")
        typer.echo(f"Profiles:   {profiles}")
        if default:
            key = default["api_key"] or ""
            masked = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else ("(set)" if key else "(empty)")
            typer.echo(
                f"Default LLM: {default['name']!r} model={default['model']} api_key={masked}"
            )
        webhook = db.get_app_setting(FEISHU_SETTING_KEY) or ""
        wh = "(set)" if webhook.strip() else "(empty)"
        typer.echo(f"Feishu:     webhook_url={wh}")
    typer.echo(f"Web config: {get_web_config_path()}")


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="e.g. feishu.webhook_url"),
    value: str = typer.Argument(..., help="Setting value"),
) -> None:
    """Set an app_settings key (stored in SQLite)."""
    db = _get_db()
    db.set_app_setting(key, value)
    db.close()
    typer.echo(f"Set {key}")


@config_app.command("import")
def config_import(
    path: Optional[Path] = typer.Option(
        None, "--path", help="YAML path (default ~/.ddo_pulse/config.yaml)"
    ),
    profiles_only: bool = typer.Option(
        False, "--profiles-only", help="Only import LLM profiles"
    ),
    sources_only: bool = typer.Option(
        False, "--sources-only", help="Only import subscription sources"
    ),
) -> None:
    """Import sources and LLM profiles from config.yaml into SQLite."""
    yaml_path = path or get_config_path()
    data = load_config(yaml_path)
    db = _get_db()
    imported_sources = 0
    imported_profiles = 0

    if not profiles_only:
        sources = data.get("sources") or []
        if sources:
            imported_sources = db.import_sources_from_yaml(sources)

    if not sources_only:
        db.sync_settings_from_yaml(data)
        llm = data.get("llm") or {}
        profiles = llm.get("profiles") or []
        if profiles:
            imported_profiles = db.import_llm_profiles_from_yaml(
                profiles, default_name=llm.get("default_profile")
            )

    db.close()
    if not profiles_only and not sources_only:
        typer.echo(
            f"Imported {imported_sources} source(s), {imported_profiles} profile(s) from {yaml_path}"
        )
    elif profiles_only:
        typer.echo(f"Imported {imported_profiles} profile(s) from {yaml_path}")
    else:
        typer.echo(f"Imported {imported_sources} source(s) from {yaml_path}")


@config_app.command("export")
def config_export(
    path: Optional[Path] = typer.Option(None, "--path", help="Output YAML path"),
) -> None:
    """Export sources from DB to config.yaml."""
    db = _get_db()
    rows = db.list_sources()
    sources = []
    for r in rows:
        sources.append(
            {
                "name": r["name"],
                "type": r["type"],
                "url": r["url"],
                "enabled": bool(r["enabled"]),
                "config_json": r["config_json"],
            }
        )
    db.close()
    out = export_config(path or get_config_path(), sources=sources)
    typer.echo(f"Exported to {out}")


# ---------------------------------------------------------------------------
# Seed library import
# ---------------------------------------------------------------------------

_CSV_COLUMN_MAP = {
    "源名称": "name",
    "源类型": "category",
    "rss_url": "rss_url",
    "官网链接": "homepage",
    "简介": "description",
    "接入优先级": "priority",
    "推荐的LLM分析profile": "profile",
    "是否需要网页正文提取": "need_extract",
}


@seed_app.command("import")
def seed_import(
    path: Path = typer.Option(
        Path("docs/ddo_pulse_rss_seed_library.csv"),
        "--path",
        "-p",
        help="CSV file path",
    ),
    job: int = typer.Option(
        0, "--job", help="Pipeline job id (default: first job)"
    ),
    clear: bool = typer.Option(
        False,
        "--clear",
        help="Delete all existing sources before import (full replace)",
    ),
) -> None:
    """Import sources from seed library CSV. Full replace with --clear."""
    if not path.exists():
        typer.echo(f"CSV not found: {path}", err=True)
        raise typer.Exit(1)

    db = _get_db()
    job_id = _resolve_pipeline_job_id(db, job)
    if job_id is None:
        typer.echo(
            "还没有定时任务。请先在 Web「配置」中新建任务，或使用 API POST /pipeline-jobs。",
            err=True,
        )
        raise typer.Exit(1)

    if clear:
        deleted = db.delete_all_sources()
        typer.echo(f"Cleared {deleted} existing source(s)")

    # Parse CSV
    rows: list[dict[str, str]] = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rss_url = (row.get("rss_url") or "").strip()
            if not rss_url:
                continue  # Skip rows without RSS URL
            rows.append(row)

    if not rows:
        typer.echo("No valid rows (all rss_url empty).", err=True)
        db.close()
        raise typer.Exit(1)

    created = 0
    updated = 0
    for row in rows:
        name = (row.get("源名称") or "").strip()
        rss_url = (row.get("rss_url") or "").strip()
        need_extract = (row.get("是否需要网页正文提取") or "").strip()

        # Build config_json with metadata from CSV
        cfg: dict[str, Any] = {}
        if row.get("官网链接"):
            cfg["homepage"] = row["官网链接"].strip()
        if row.get("简介"):
            cfg["description"] = row["简介"].strip()
        if row.get("接入优先级"):
            cfg["priority"] = row["接入优先级"].strip()
        if row.get("推荐的LLM分析profile"):
            cfg["profile"] = row["推荐的LLM分析profile"].strip()
        if need_extract:
            cfg["need_extract"] = need_extract == "是"

        source_type = "rss"
        sid, is_new = db.upsert_source_by_url(
            name=name,
            type_=source_type,
            url=rss_url,
            config_json=json.dumps(cfg, ensure_ascii=False),
            enabled=True,
        )
        # Associate with the pipeline job
        if job_id is not None:
            existing_js = db.get_job_source(job_id, sid)
            if not existing_js:
                db.add_job_source(job_id=job_id, source_id=sid)
        if is_new:
            created += 1
        else:
            updated += 1

    db.close()
    typer.echo(
        f"Seed import done: {created} new, {updated} updated, "
        f"{len(rows)} total from {path.name}"
    )


@seed_app.command("list")
def seed_list(
    path: Path = typer.Option(
        Path("docs/ddo_pulse_rss_seed_library.csv"),
        "--path",
        "-p",
        help="CSV file path",
    ),
) -> None:
    """Show seed library contents (CSV preview)."""
    if not path.exists():
        typer.echo(f"CSV not found: {path}", err=True)
        raise typer.Exit(1)

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        total = 0
        with_rss = 0
        for row in reader:
            total += 1
            rss = (row.get("rss_url") or "").strip()
            if rss:
                with_rss += 1

    typer.echo(f"Seed library: {path}")
    typer.echo(f"  Total rows:  {total}")
    typer.echo(f"  With RSS:    {with_rss}")
    typer.echo(f"  Without RSS: {total - with_rss}")


@profile_app.command("add")
def profile_add(
    name: str = typer.Argument(..., help="Profile name"),
    model: str = typer.Option("openai/gpt-4o-mini", "--model", "-m"),
    api_key: str = typer.Option("", "--api-key", help="OpenRouter API key"),
    score_threshold: int = typer.Option(7, "--score-threshold"),
    default: bool = typer.Option(False, "--default", help="Set as default profile"),
) -> None:
    """Add an LLM profile."""
    db = _get_db()
    pid = db.add_llm_profile(
        name=name,
        model=model,
        api_key=api_key,
        score_threshold=score_threshold,
        is_default=default or not db.list_llm_profiles(),
    )
    db.close()
    typer.echo(f"Added profile id={pid} name={name!r} model={model}")


@profile_app.command("list")
def profile_list() -> None:
    """List LLM profiles (api_key masked)."""
    db = _get_db()
    rows = db.list_llm_profiles()
    db.close()
    if not rows:
        typer.echo("No LLM profiles. Run: ddo-pulse profile add ...")
        return
    typer.echo(f"{'ID':<4} {'DEF':<4} {'NAME':<16} {'MODEL':<28} API_KEY")
    for r in rows:
        key = r["api_key"] or ""
        masked = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else ("(set)" if key else "(empty)")
        def_mark = "Y" if r["is_default"] else "N"
        typer.echo(f"{r['id']:<4} {def_mark:<4} {r['name'][:16]:<16} {r['model'][:28]:<28} {masked}")


@profile_app.command("set-default")
def profile_set_default(profile_id: int = typer.Argument(..., help="Profile ID")) -> None:
    """Set the default LLM profile."""
    db = _get_db()
    ok = db.set_default_llm_profile(profile_id)
    db.close()
    if not ok:
        typer.echo(f"Profile {profile_id} not found.", err=True)
        raise typer.Exit(1)
    typer.echo(f"Default profile set to id={profile_id}")


@items_app.command("list")
def items_list(
    limit: int = typer.Option(20, "--limit", "-n", min=1),
    min_score: Optional[int] = typer.Option(
        None, "--min-score", help="Only items with score >= N"
    ),
    quality_only: bool = typer.Option(
        False, "--quality-only", help="Only is_quality=true"
    ),
    json_out: bool = typer.Option(False, "--json", help="JSON array output"),
) -> None:
    """List analyzed articles (newest first)."""
    db = _get_db()
    rows = db.list_analyzed_items(
        limit=limit, min_score=min_score, quality_only=quality_only
    )
    db.close()
    print_analyzed_list(rows, as_json=json_out)


@items_app.command("show")
def items_show(
    analyzed_id: int = typer.Argument(..., help="analyzed_items.id"),
    json_out: bool = typer.Option(False, "--json", help="JSON object output"),
) -> None:
    """Show full analysis for one article."""
    db = _get_db()
    row = db.get_analyzed_item(analyzed_id)
    db.close()
    if row is None:
        typer.echo(f"Analyzed item {analyzed_id} not found.", err=True)
        raise typer.Exit(1)
    print_analyzed_detail(row, as_json=json_out)


@digest_app.command("show")
def digest_show(
    date: Optional[str] = typer.Option(
        None, "--date", help="YYYY-MM-DD (default: today UTC)"
    ),
    job: int = typer.Option(
        0, "--job", help="Pipeline job id (default: first job)"
    ),
) -> None:
    """Print digest markdown for a date."""
    db = _get_db()
    digest_date = date or digest_date_today()
    jid = _resolve_pipeline_job_id(db, job)
    if jid is None:
        typer.echo("No pipeline job. Create one first (Web UI or POST /pipeline-jobs).", err=True)
        db.close()
        raise typer.Exit(1)
    row = db.get_digest_by_date_and_job(digest_date, jid)
    db.close()
    if row is None:
        typer.echo(f"No digest for {digest_date}. Run: ddo-pulse digest build")
        raise typer.Exit(1)
    typer.echo(row["markdown_body"])


@digest_app.command("build")
def digest_build(
    date: Optional[str] = typer.Option(None, "--date"),
    top_n: int = typer.Option(8, "--top-n", min=1),
    job: int = typer.Option(
        0, "--job", help="Pipeline job id (default: first job)"
    ),
) -> None:
    """Build/update digest without pushing to Feishu."""
    db = _get_db()
    jid = _resolve_pipeline_job_id(db, job)
    if jid is None:
        typer.echo("No pipeline job. Create one first.", err=True)
        db.close()
        raise typer.Exit(1)
    jrow = db.get_pipeline_job(jid)
    if jrow is None:
        typer.echo(f"Pipeline job {jid} not found.", err=True)
        db.close()
        raise typer.Exit(1)
    job_sources = db.list_job_sources(jid)
    source_ids = [int(js["source_id"]) for js in job_sources]
    stats = build_and_push_digest(
        db,
        job_id=jid,
        date=date,
        top_n=top_n,
        score_threshold=int(jrow["score_threshold"]),
        source_ids=source_ids or None,
        push=False,
        force_push=False,
    )
    db.close()
    typer.echo(
        f"Digest {stats['digest_date']}: id={stats['digest_id']} items={stats['digest_items']}"
    )


@digest_app.command("push")
def digest_push(
    date: Optional[str] = typer.Option(None, "--date"),
    force: bool = typer.Option(False, "--force", help="Push even if already sent"),
    top_n: int = typer.Option(8, "--top-n", min=1),
    job: int = typer.Option(
        0, "--job", help="Pipeline job id (default: first job)"
    ),
) -> None:
    """Build digest and push to Feishu."""
    db = _get_db()
    jid = _resolve_pipeline_job_id(db, job)
    if jid is None:
        typer.echo("No pipeline job. Create one first.", err=True)
        db.close()
        raise typer.Exit(1)
    jrow = db.get_pipeline_job(jid)
    if jrow is None:
        typer.echo(f"Pipeline job {jid} not found.", err=True)
        db.close()
        raise typer.Exit(1)
    job_sources = db.list_job_sources(jid)
    source_ids = [int(js["source_id"]) for js in job_sources]
    stats = build_and_push_digest(
        db,
        job_id=jid,
        date=date,
        top_n=top_n,
        score_threshold=int(jrow["score_threshold"]),
        source_ids=source_ids or None,
        push=True,
        force_push=force,
        feishu_webhook_url=str(jrow["feishu_webhook_url"] or "").strip(),
    )
    db.close()
    _echo_digest_push_stats(stats)
    if stats.get("push_error"):
        raise typer.Exit(1)


def _echo_digest_push_stats(stats: dict) -> None:
    typer.echo(
        f"Digest {stats['digest_date']}: id={stats['digest_id']} items={stats['digest_items']}"
    )
    if stats.get("pushed"):
        typer.echo("Feishu: pushed ok")
    elif stats.get("push_skipped"):
        reason = stats.get("push_skip_reason") or "unknown"
        typer.echo(f"Feishu: skipped ({reason})")
    elif stats.get("push_error"):
        typer.echo(f"Feishu: failed — {stats['push_error']}", err=True)


@app.command("run-once")
def run_once_cmd(
    skip_analyze: bool = typer.Option(
        False, "--skip-analyze", help="Fetch only, skip LLM analysis"
    ),
    analyze_limit: int = typer.Option(
        50,
        "--analyze-limit",
        "-n",
        min=0,
        help="Max unanalyzed articles to LLM-analyze this run (0 = all pending)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="After analyze, print details of items analyzed this run",
    ),
    skip_digest: bool = typer.Option(
        False, "--skip-digest", help="Skip digest build and Feishu push"
    ),
    skip_push: bool = typer.Option(
        False, "--skip-push", help="Build digest but do not push to Feishu"
    ),
    force_push: bool = typer.Option(
        False, "--force-push", help="Push to Feishu even if already sent today"
    ),
) -> None:
    """Run fetch + analyze + digest + optional Feishu push."""
    if not get_db_path().exists():
        typer.echo("Run ddo-pulse init first.", err=True)
        raise typer.Exit(1)
    stats = run_once(
        analyze=not skip_analyze,
        analyze_limit=analyze_limit,
        push=not skip_push,
        force_push=force_push,
        skip_digest=skip_digest,
    )
    typer.echo(
        f"Fetch: sources={stats['sources']} entries={stats['fetched_entries']} "
        f"new={stats['new_items']} errors={stats['errors']}"
    )
    if not skip_analyze:
        reason = stats.get("analyze_skip_reason")
        reason_txt = f" reason={reason}" if reason else ""
        cap_txt = "all" if analyze_limit == 0 else str(analyze_limit)
        typer.echo(
            f"Analyze: limit={cap_txt} pending={stats['analyze_pending']} "
            f"done={stats['analyzed']} skipped={stats['analyze_skipped']} "
            f"errors={stats['analyze_errors']}{reason_txt}"
        )
        if verbose and int(stats.get("analyzed") or 0) > 0:
            db = _get_db()
            rows = db.list_analyzed_items(limit=int(stats["analyzed"]))
            db.close()
            typer.echo("")
            typer.echo("--- 本轮分析结果 ---")
            for row in rows:
                print_analyzed_detail(row)
                typer.echo("")
    if not skip_digest:
        typer.echo(
            f"Digest: items={stats.get('digest_items', 0)} id={stats.get('digest_id')}"
        )
        if not skip_push:
            if stats.get("pushed"):
                typer.echo("Feishu: pushed ok")
            elif stats.get("push_skipped"):
                reason = stats.get("push_skip_reason") or "unknown"
                typer.echo(f"Feishu: skipped ({reason})")
            elif stats.get("push_error"):
                typer.echo(f"Feishu: failed — {stats['push_error']}", err=True)
    err_count = int(stats["errors"])
    if err_count > 0:
        raise typer.Exit(1)


web_app = typer.Typer(help="Web frontend configuration")
app.add_typer(web_app, name="web")


@web_app.command("sync")
def web_sync() -> None:
    """Sync ~/.ddo_pulse/web.yaml -> frontend/.ddo-pulse.env.json for Vite."""
    if not get_web_config_path().exists():
        write_default_web_config()
        typer.echo(f"Created {get_web_config_path()}")
    out = sync_vite_env_file(load_web_config())
    typer.echo(f"Synced Vite env: {out}")


@app.command("dev")
def dev_cmd(
    install: bool = typer.Option(
        False, "--install", help="Run npm install in frontend if needed"
    ),
) -> None:
    """Start API + Vite dev server (reads ~/.ddo_pulse/web.yaml)."""
    import subprocess
    import sys
    import time

    from ddo_pulse_core.web_config import get_vite_env_path

    if not get_db_path().exists():
        typer.echo("Run ddo-pulse init first.", err=True)
        raise typer.Exit(1)

    web_sync()
    cfg = load_web_config()
    api_cfg = cfg.get("api") or {}
    dev_cfg = cfg.get("dev_server") or {}
    api_host = str(api_cfg.get("host", "127.0.0.1"))
    api_port = int(api_cfg.get("port", 8765))
    vite_port = int(dev_cfg.get("port", 5173))

    frontend_dir = get_vite_env_path().parent
    if install or not (frontend_dir / "node_modules").exists():
        typer.echo("Running npm install...")
        subprocess.run(
            ["npm", "install"],
            cwd=str(frontend_dir),
            check=True,
            shell=sys.platform == "win32",
        )

    repo_root = frontend_dir.parents[3]
    state_path = _dev_state_path()
    try:
        state_path.unlink()
    except OSError:
        pass

    typer.echo(f"Starting API http://{api_host}:{api_port}")
    api_proc = subprocess.Popen(
        ["ddo-pulse", "api"],
        cwd=str(repo_root),
        shell=sys.platform == "win32",
    )
    time.sleep(1.5)
    typer.echo(f"Starting Web http://127.0.0.1:{vite_port}")
    vite_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(frontend_dir),
        shell=sys.platform == "win32",
    )
    ensure_data_dir()
    payload: dict[str, Any] = {
        "api_pid": api_proc.pid,
        "vite_pid": vite_proc.pid,
        "api_port": api_port,
        "vite_port": vite_port,
    }
    try:
        state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        typer.echo(f"Warning: could not write {state_path}: {exc}", err=True)

    try:
        vite_proc.wait()
    except KeyboardInterrupt:
        typer.echo("Stopping...")
    finally:
        try:
            state_path.unlink()
        except OSError:
            pass
        if api_proc.poll() is None:
            _terminate_pid_tree(api_proc.pid)
        else:
            api_proc.wait(timeout=0.5)
        if vite_proc.poll() is None:
            _terminate_pid_tree(vite_proc.pid)
        else:
            vite_proc.wait(timeout=0.5)


@app.command("stop")
def stop_cmd() -> None:
    """Stop API + Vite started by `ddo-pulse dev` (uses ~/.ddo_pulse/dev_state.json)."""
    path = _dev_state_path()
    if not path.exists():
        typer.echo(
            "No dev session file. Start with `ddo-pulse dev`, or processes were already stopped.",
            err=True,
        )
        raise typer.Exit(1)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        typer.echo(f"Invalid dev state file: {exc}", err=True)
        path.unlink(missing_ok=True)
        raise typer.Exit(1) from exc
    vite_pid = int(data.get("vite_pid") or 0)
    api_pid = int(data.get("api_pid") or 0)
    if not api_pid and not vite_pid:
        path.unlink(missing_ok=True)
        typer.echo("Dev state file had no PIDs.", err=True)
        raise typer.Exit(1)
    typer.echo("Stopping dev servers…")
    if vite_pid:
        _terminate_pid_tree(vite_pid)
    if api_pid:
        _terminate_pid_tree(api_pid)
    try:
        path.unlink()
    except OSError:
        pass
    typer.echo("Stopped.")


@app.command("api")
def api_cmd(
    host: Optional[str] = typer.Option(None, "--host", help="Override web.yaml api.host"),
    port: Optional[int] = typer.Option(None, "--port", help="Override web.yaml api.port"),
) -> None:
    """Start FastAPI server (REST + optional static frontend dist)."""
    if not get_db_path().exists():
        typer.echo("Run ddo-pulse init first.", err=True)
        raise typer.Exit(1)
    try:
        import uvicorn
    except ImportError as exc:
        typer.echo("Install API deps: pip install -e .", err=True)
        raise typer.Exit(1) from exc
    cfg = load_web_config()
    api_cfg = cfg.get("api") or {}
    bind_host = host or str(api_cfg.get("host", "127.0.0.1"))
    bind_port = port if port is not None else int(api_cfg.get("port", 8765))
    typer.echo(f"API http://{bind_host}:{bind_port}  docs: /docs")
    uvicorn.run("ddo_pulse_api.main:app", host=bind_host, port=bind_port, reload=False)


@app.command("mcp")
def mcp_cmd() -> None:
    """Start MCP server on stdio (for Cursor / Claude Desktop)."""
    try:
        from ddo_pulse_mcp.server import main as mcp_main
    except ImportError as exc:
        typer.echo(
            "MCP support not installed. Run: pip install 'ddo-pulse[mcp]'",
            err=True,
        )
        raise typer.Exit(1) from exc
    mcp_main()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
