"""CLI configuration commands."""

import typer
from rich.console import Console
from rich.table import Table

from greencloud.config_store import get_config, set_value

app = typer.Typer(no_args_is_help=True)
console = Console()

VALID_KEYS = ["api_url", "api_key", "carbon_url", "agent_url"]


@app.command("set")
def set_config(
    key: str = typer.Argument(..., help=f"Config key ({', '.join(VALID_KEYS)})"),
    value: str = typer.Argument(..., help="Config value"),
):
    """Set a configuration value."""
    if key not in VALID_KEYS:
        console.print(f"[red]Unknown key: {key}[/red]")
        console.print(f"Valid keys: {', '.join(VALID_KEYS)}")
        raise typer.Exit(1)

    set_value(key, value)
    display_value = "***" if "key" in key else value
    console.print(f"[green]Set {key} = {display_value}[/green]")


@app.command("show")
def show_config():
    """Show current CLI configuration."""
    config = get_config()

    if not config:
        console.print("[dim]No configuration set. Defaults will be used.[/dim]")
        console.print("\nDefaults:")
        console.print("  api_url: http://localhost:8000")
        console.print("  carbon_url: http://localhost:8002")
        console.print("  agent_url: http://localhost:8001")
        return

    table = Table(title="CLI Configuration")
    table.add_column("Key", style="bold")
    table.add_column("Value")

    for key, value in config.items():
        display_value = "***" if "key" in key else str(value)
        table.add_row(key, display_value)

    console.print(table)
