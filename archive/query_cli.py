"""
Natural Language Query CLI

Interactive command-line interface for querying the microfluidic device database
using natural language.

Usage:
    python query_cli.py                  # Interactive mode
    python query_cli.py "your query"     # One-shot mode
"""

import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
import pandas as pd

from src import DataAnalyst

console = Console()


def print_welcome():
    """Print welcome banner."""
    welcome = """
# Microfluidic Device Database - Natural Language Query Interface

Ask questions in plain English! Examples:
  • "Compare W13 and W14 devices"
  • "Show me all devices at 5 ml/hr flowrate"
  • "Track device W13_S1_R1 over time"
  • "Analyze pressure effects for W14"
  • "Generate a summary report"

Type 'help' for more examples, or 'exit' to quit.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    console.print(Markdown(welcome), style="bold cyan")


def format_dataframe(df: pd.DataFrame, max_rows: int = 10) -> Table:
    """Format a pandas DataFrame as a Rich table."""
    table = Table(show_header=True, header_style="bold magenta")

    # Add columns
    for col in df.columns:
        table.add_column(str(col))

    # Add rows (limit to max_rows)
    for idx, row in df.head(max_rows).iterrows():
        table.add_row(*[str(val) for val in row])

    if len(df) > max_rows:
        table.caption = f"Showing {max_rows} of {len(df)} rows"

    return table


def display_result(result: dict):
    """Display query result in a formatted way."""
    status = result.get('status', 'unknown')
    message = result.get('message', '')
    plot_path = result.get('plot_path')
    report_path = result.get('report_path')
    data = result.get('result')

    # Determine panel style based on status
    if status == 'success':
        panel_style = "green"
        title = "[Success]"
    elif status == 'clarification_needed':
        panel_style = "yellow"
        title = "[Clarification Needed]"
    elif status == 'error':
        panel_style = "red"
        title = "[Error]"
    else:
        panel_style = "blue"
        title = "[Info]"

    # Display main message
    console.print(Panel(message, title=title, border_style=panel_style))

    # Display DataFrame if present
    if data is not None and isinstance(data, pd.DataFrame) and len(data) > 0:
        console.print("\n[bold]Data Preview:[/bold]")
        table = format_dataframe(data)
        console.print(table)

    # Display plot path if present
    if plot_path:
        console.print(f"\n[bold green]Plot saved:[/bold green] {plot_path}")
        console.print(f"[dim]Open the file to view the visualization[/dim]")

    # Display report path if present
    if report_path:
        console.print(f"\n[bold green]Report saved:[/bold green] {report_path}")


def run_interactive_mode():
    """Run in interactive mode with continuous prompt."""
    console.clear()
    print_welcome()

    # Initialize analyst
    console.print("[dim]Loading database...[/dim]")
    analyst = DataAnalyst()
    console.print(f"[green]OK[/green] Loaded {len(analyst.df)} measurements\n")

    # Main query loop
    while True:
        try:
            # Get query from user
            query = console.input("[bold cyan]Query>[/bold cyan] ").strip()

            if not query:
                continue

            # Handle exit commands
            if query.lower() in ['exit', 'quit', 'q']:
                console.print("\n[bold]Goodbye![/bold]\n")
                break

            # Process query
            with console.status("[bold green]Processing query..."):
                result = analyst.process_natural_language_query(query)

            # Display result
            console.print()
            display_result(result)
            console.print()

        except KeyboardInterrupt:
            console.print("\n\n[bold]Interrupted. Goodbye![/bold]\n")
            break
        except Exception as e:
            console.print(f"\n[red]Error:[/red] {str(e)}\n", style="bold")


def run_oneshot_mode(query: str):
    """Run a single query and exit."""
    # Initialize analyst
    analyst = DataAnalyst()

    # Process query
    result = analyst.process_natural_language_query(query)

    # Display result
    display_result(result)

    # Return exit code based on status
    return 0 if result.get('status') == 'success' else 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Natural Language Query Interface for Microfluidic Device Database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python query_cli.py
      Start interactive mode

  python query_cli.py "Compare W13 and W14 devices"
      Run a single query and exit

  python query_cli.py "help"
      Show help and query examples
        """
    )

    parser.add_argument(
        'query',
        nargs='?',
        help='Query to execute (omit for interactive mode)'
    )

    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )

    args = parser.parse_args()

    # Disable color if requested
    if args.no_color:
        console._color_system = None

    # Run in appropriate mode
    if args.query:
        exit_code = run_oneshot_mode(args.query)
        sys.exit(exit_code)
    else:
        run_interactive_mode()


if __name__ == "__main__":
    main()
