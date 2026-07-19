"""Status and health commands."""

import typer
from rich.console import Console
from rich.table import Table

from greencloud.api_client import api_get, _get_base_url, _get_agent_url, _get_carbon_url

app = typer.Typer(invoke_without_command=True)
console = Console()


@app.callback()
def show_status():
    """Show overview of all GreenCloud services."""
    console.print("[bold]GreenCloud Status[/bold]\n")

    table = Table()
    table.add_column("Service", style="bold")
    table.add_column("URL")
    table.add_column("Status")

    services = [
        ("GreenCloud API", _get_base_url(), "/health"),
        ("Agent", _get_agent_url(), "/health"),
        ("Carbon Engine", _get_carbon_url(), "/health"),
    ]

    for name, base_url, health_path in services:
        try:
            result = api_get(health_path, base=base_url)
            status = result.get("status", "unknown") if result else "unreachable"
            color = "green" if status == "healthy" else "red"
            table.add_row(name, base_url, f"[{color}]{status}[/{color}]")
        except SystemExit:
            table.add_row(name, base_url, "[red]unreachable[/red]")
        except Exception:
            table.add_row(name, base_url, "[red]error[/red]")

    console.print(table)


@app.command("health")
def health_check():
    """Detailed health check of all components."""
    show_status()

    # System stats from agent
    console.print("\n[bold]System Resources[/bold]")
    try:
        stats = api_get("/agent/stats", base=_get_agent_url())
        if stats:
            cpu = stats.get("cpu_percent")
            mem = stats.get("memory")
            disk = stats.get("disk")

            if cpu is not None:
                console.print(f"  CPU: {cpu}%")
            if mem:
                console.print(f"  Memory: {mem['percent']}% ({_fmt_bytes(mem['used_bytes'])} / {_fmt_bytes(mem['total_bytes'])})")
            if disk:
                console.print(f"  Disk: {disk['percent']}% ({_fmt_bytes(disk['used_bytes'])} / {_fmt_bytes(disk['total_bytes'])})")
    except (SystemExit, Exception):
        console.print("  [dim]Could not reach agent for system stats[/dim]")


def _fmt_bytes(b: int) -> str:
    """Format bytes to human-readable."""
    for unit in ["B", "KB", "MB", "GB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"
