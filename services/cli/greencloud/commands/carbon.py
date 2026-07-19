"""Carbon intensity and emissions commands."""

import typer
from rich.console import Console
from rich.table import Table

from greencloud.api_client import api_get, _get_carbon_url

app = typer.Typer(invoke_without_command=True)
console = Console()


@app.callback()
def show_carbon():
    """Show current carbon intensity and status."""
    result = api_get("/carbon/status", base=_get_carbon_url())
    if not result:
        console.print("[red]Could not reach Carbon Engine.[/red]")
        return

    status = result.get("status", "unknown")
    intensity = result.get("carbon_intensity_gco2_kwh", 0)
    description = result.get("description", "")

    color = {"low": "green", "medium": "yellow", "high": "red"}.get(status, "white")

    console.print(f"\n[bold]Grid Carbon Status:[/bold] [{color}]{status.upper()}[/{color}]")
    console.print(f"  Intensity: {intensity:.0f} gCO\u2082/kWh")
    console.print(f"  {description}")


@app.command("emissions")
def show_emissions():
    """Show cumulative emissions data."""
    result = api_get("/energy/emissions", base=_get_carbon_url())
    if not result:
        console.print("[red]Could not reach Carbon Engine.[/red]")
        return

    console.print("\n[bold]Emissions[/bold]")
    console.print(f"  Today: {result.get('today_gco2', 0):.2f} gCO\u2082")
    console.print(f"  Total: {result.get('total_gco2', 0):.2f} gCO\u2082")
    console.print(f"  Energy today: {result.get('today_kwh', 0):.4f} kWh")
    console.print(f"  Measurements: {result.get('measurement_count', 0)}")


@app.command("power")
def show_power():
    """Show current power draw."""
    result = api_get("/energy/power", base=_get_carbon_url())
    if not result:
        console.print("[red]Could not reach Carbon Engine.[/red]")
        return

    console.print(f"\n[bold]Power Draw:[/bold] {result.get('total_watts', 0):.1f}W")
    for node in result.get("nodes", []):
        console.print(f"  {node['node']}: {node['watts']:.1f}W (CPU: {node['cpu_percent']}%, {node['source']})")
