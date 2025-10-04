import asyncio
import typer
from rich.console import Console
from rich.table import Table
from app.scanner import ValueBetScanner

app = typer.Typer()
console = Console()


@app.command()
def scan():
    '''Scan for value bets once'''
    console.print("\n[bold blue]Starting value bet scan...[/bold blue]\n")
    scanner = ValueBetScanner()
    try:
        value_bets = asyncio.run(scanner.scan())
        if not value_bets:
            console.print("[yellow]No value bets found meeting criteria[/yellow]")
            return
        
        console.print(f"\n[bold green]Found {len(value_bets)} value bets![/bold green]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("League", style="cyan")
        table.add_column("Match", style="white")
        table.add_column("Time", style="yellow")
        table.add_column("Book", style="blue")
        table.add_column("Outcome", style="green")
        table.add_column("Odds", justify="right")
        table.add_column("Edge %", justify="right", style="green")
        table.add_column("EV", justify="right", style="green")
        table.add_column("Kelly $", justify="right", style="yellow")
        
        for bet in value_bets[:20]:
            match_str = f"{bet.home_team} vs {bet.away_team}"
            time_str = bet.start_time_local.strftime("%m/%d %H:%M")
            table.add_row(
                bet.league, match_str, time_str, bet.bookmaker, bet.outcome.value,
                f"{bet.price_decimal:.2f}", f"{bet.edge_pct:.1f}%",
                f"{bet.ev:.3f}", f"${bet.kelly_stake:.0f}"
            )
        
        console.print(table)
        scanner.export_to_csv(value_bets)
    finally:
        asyncio.run(scanner.close())


@app.command()
def demo():
    '''Run demo with synthetic data'''
    console.print("\n[bold blue]Running demo...[/bold blue]\n")
    console.print("[yellow]For full demo, run: python demo.py[/yellow]")


if __name__ == "__main__":
    app()
