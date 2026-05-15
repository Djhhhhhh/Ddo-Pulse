"""Ddo-Pulse CLI entry point."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from ddo_pulse_core.config_yaml import export_config, load_config, write_default_config
from ddo_pulse_core.pipeline import run_once
from ddo_pulse_db.paths import ensure_data_dir, get_config_path, get_data_dir, get_db_path
from ddo_pulse_db.repository import Database

app = typer.Typer(
    name="ddo-pulse",
    help="Ddo-Pulse: blog aggregation with LLM curation",
    no_args_is_help=True,
)
source_app = typer.Typer(help="Manage subscription sources")
config_app = typer.Typer(help="Manage configuration")
app.add_typer(source_app, name="source")
app.add_typer(config_app, name="config")


def _get_db() -> Database:
    db_path = get_db_path()
    if not db_path.exists():
        typer.echo("Database not found. Run: ddo-pulse init", err=True)
        raise typer.Exit(1)
    return Database()


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
    db.close()
    typer.echo(f"Data directory: {data_dir}")


@source_app.command("add")
def source_add(
    name: str = typer.Argument(..., help="Display name"),
    type: str = typer.Argument(..., help="rss | json_feed"),
    url: str = typer.Argument(..., help="Feed URL"),
    config_json: Optional[str] = typer.Option(
        None, "--config-json", help="Adapter JSON string"
    ),
) -> None:
    """Add a subscription source."""
    if type not in ("rss", "json_feed"):
        typer.echo("M1 supports types: rss, json_feed", err=True)
        raise typer.Exit(1)
    cfg = config_json or "{}"
    try:
        json.loads(cfg)
    except json.JSONDecodeError as e:
        typer.echo(f"Invalid --config-json: {e}", err=True)
        raise typer.Exit(1)

    db = _get_db()
    sid = db.add_source(name=name, type_=type, url=url, config_json=cfg)
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
        db.close()
        typer.echo(f"Sources:    {n}")
        typer.echo(f"Raw items:  {items}")


@config_app.command("import")
def config_import(
    path: Optional[Path] = typer.Option(
        None, "--path", help="YAML path (default ~/.ddo_pulse/config.yaml)"
    ),
) -> None:
    """Import sources from config.yaml into SQLite."""
    yaml_path = path or get_config_path()
    data = load_config(yaml_path)
    sources = data.get("sources") or []
    if not sources:
        typer.echo("No sources in config file.")
        return
    db = _get_db()
    count = db.import_sources_from_yaml(sources)
    db.close()
    typer.echo(f"Imported {count} source(s) from {yaml_path}")


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
                "fetch_cron": r["fetch_cron"],
            }
        )
    db.close()
    out = export_config(path or get_config_path(), sources=sources)
    typer.echo(f"Exported to {out}")


@app.command("run-once")
def run_once_cmd() -> None:
    """Run fetch pipeline once (no LLM, no Feishu)."""
    if not get_db_path().exists():
        typer.echo("Run ddo-pulse init first.", err=True)
        raise typer.Exit(1)
    stats = run_once()
    typer.echo(
        f"Done: sources={stats['sources']} entries={stats['fetched_entries']} "
        f"new={stats['new_items']} errors={stats['errors']}"
    )
    if stats["errors"] > 0:
        raise typer.Exit(1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
