"""
Interactive CLI Dashboard for Microfluidic Device Analysis

Built with Textual for beautiful terminal interface.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, Label, DataTable, Input, Select, RichLog
from textual.binding import Binding
from textual import events
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from datetime import datetime
import pandas as pd
from pathlib import Path

from src import DataAnalyst


class DatabaseStatus(Static):
    """Widget showing current database status."""

    def __init__(self, analyst: DataAnalyst):
        super().__init__()
        self.analyst = analyst

    def on_mount(self) -> None:
        """Update the widget when mounted."""
        self.update_status()

    def update_status(self) -> None:
        """Refresh database status display."""
        df = self.analyst.df

        # Calculate statistics
        total_records = len(df)
        device_types = df['device_type'].value_counts().to_dict()
        unique_devices = df['device_id'].nunique()

        # Handle date range with mixed types
        date_col = pd.to_datetime(df['testing_date'], errors='coerce')
        date_col_clean = date_col.dropna()
        if len(date_col_clean) > 0:
            date_range = f"{date_col_clean.min().strftime('%Y-%m-%d')} to {date_col_clean.max().strftime('%Y-%m-%d')}"
        else:
            date_range = "N/A"

        # Count measurement types
        csv_files = len(df[df['file_type'] == 'csv'])
        txt_files = len(df[df['file_type'] == 'txt'])

        # Build status display
        status_text = f"""[bold cyan]DATABASE STATUS[/bold cyan]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[bold]Total Records:[/bold] {total_records}
[bold]Unique Devices:[/bold] {unique_devices}

[bold]Device Types:[/bold]"""

        for dtype, count in device_types.items():
            status_text += f"\n  • {dtype}: {count} measurements"

        status_text += f"""

[bold]Measurement Files:[/bold]
  • CSV (droplet data): {csv_files}
  • TXT (frequency data): {txt_files}

[bold]Date Range:[/bold] {date_range}

[dim]Last updated: {datetime.now().strftime('%H:%M:%S')}[/dim]"""

        self.update(status_text)


class CommandTerminal(Container):
    """Terminal-style command interface."""

    def __init__(self, analyst: DataAnalyst):
        super().__init__()
        self.analyst = analyst
        self.command_history = []
        self.history_index = -1

    def compose(self) -> ComposeResult:
        """Create terminal widgets."""
        yield Label("[bold cyan]COMMAND TERMINAL[/bold cyan]")
        yield Label("Type natural language queries or 'help' for examples")
        yield Label("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        yield RichLog(id="terminal_output", wrap=True, highlight=True)
        yield Input(placeholder="Enter command... (e.g., 'compare W13 and W14 devices')", id="terminal_input")

    def on_mount(self) -> None:
        """Initialize terminal on mount."""
        output = self.query_one("#terminal_output", RichLog)
        output.write("[dim]Terminal ready. Type a query or 'help' for examples.[/dim]")
        output.write("")

    def execute_command(self, command: str) -> None:
        """Execute a natural language command."""
        if not command.strip():
            return

        # Add to history
        self.command_history.append(command)
        self.history_index = -1

        output = self.query_one("#terminal_output", RichLog)

        # Show command
        output.write(f"[bold cyan]Query>[/bold cyan] {command}")
        output.write("")

        # Process the query
        result = self.analyst.process_natural_language_query(command)

        # Display result
        status = result.get('status', 'unknown')
        message = result.get('message', '')

        if status == 'success':
            output.write("[bold green][Success][/bold green]")
        elif status == 'clarification_needed':
            output.write("[bold yellow][Clarification Needed][/bold yellow]")
        elif status == 'error':
            output.write("[bold red][Error][/bold red]")

        output.write(message)

        # Show data preview if available
        data = result.get('result')
        if data is not None and isinstance(data, pd.DataFrame) and len(data) > 0:
            output.write("")
            output.write("[bold]Data preview (first 5 rows):[/bold]")
            preview_text = data.head(5).to_string()
            output.write(preview_text)
            if len(data) > 5:
                output.write(f"[dim]... {len(data)} total rows[/dim]")

        # Show plot path if available
        plot_path = result.get('plot_path')
        if plot_path:
            output.write("")
            output.write(f"[bold green]Plot saved:[/bold green] {plot_path}")
            output.write("[dim]Open the file to view the visualization[/dim]")

        # Show report path if available
        report_path = result.get('report_path')
        if report_path:
            output.write("")
            output.write(f"[bold green]Report saved:[/bold green] {report_path}")

        output.write("")
        output.write("━" * 60)
        output.write("")

        # Clear input
        input_widget = self.query_one("#terminal_input", Input)
        input_widget.value = ""


class QuickCommandMenu(Static):
    """Widget showing quick command options."""

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Label("[bold yellow]QUICK COMMANDS[/bold yellow]")
        yield Label("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        yield Button("[1] Compare Devices at Same Parameters", id="cmd_1", variant="primary")
        yield Button("[2] Analyze Flow Parameter Effects", id="cmd_2", variant="primary")
        yield Button("[3] Track Device Over Time", id="cmd_3", variant="primary")
        yield Button("[4] Compare DFU Row Performance", id="cmd_4", variant="primary")
        yield Button("[5] Compare Fluid Types", id="cmd_5", variant="primary")
        yield Button("[6] View All Available Devices", id="cmd_6", variant="success")
        yield Label("")
        yield Button("[R] Refresh Database", id="cmd_refresh", variant="default")
        yield Button("[X] Exit", id="cmd_exit", variant="error")

class MicrofluidicDashboard(App):
    """Main dashboard application."""

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        height: 100%;
    }

    #left-panel {
        width: 45;
        height: 100%;
        border: solid $primary;
        padding: 1;
    }

    #right-panel {
        width: 1fr;
        height: 100%;
        border: solid $primary;
        padding: 1;
    }

    Button {
        width: 100%;
        margin: 0 1;
    }

    CommandTerminal {
        height: 100%;
    }

    #terminal_output {
        height: 1fr;
        border: solid $accent;
        margin-bottom: 1;
    }

    #terminal_input {
        width: 100%;
        dock: bottom;
    }

    DatabaseStatus {
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
        Binding("escape", "focus_terminal", "Focus Terminal"),
    ]

    def __init__(self):
        super().__init__()
        self.analyst = DataAnalyst()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)

        with Horizontal(id="main-container"):
            with Vertical(id="left-panel"):
                yield DatabaseStatus(self.analyst)
                yield QuickCommandMenu()

            with Container(id="right-panel"):
                yield CommandTerminal(self.analyst)

        yield Footer()

    def on_mount(self) -> None:
        """Handle mount event."""
        self.title = "Microfluidic Device Analysis Dashboard"
        self.sub_title = f"{len(self.analyst.df)} measurements loaded"

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command input submission."""
        if event.input.id == "terminal_input":
            command = event.value.strip()
            if command:
                terminal = self.query_one(CommandTerminal)
                terminal.execute_command(command)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        button_id = event.button.id
        terminal = self.query_one(CommandTerminal)

        if button_id == "cmd_exit":
            self.exit()

        elif button_id == "cmd_refresh":
            self.action_refresh()

        elif button_id == "cmd_1":
            # Pre-fill the input for user to customize
            input_widget = self.query_one("#terminal_input", Input)
            input_widget.value = "compare devices at "
            input_widget.focus()

        elif button_id == "cmd_2":
            input_widget = self.query_one("#terminal_input", Input)
            input_widget.value = "analyze flowrate effects for W13"
            input_widget.focus()

        elif button_id == "cmd_3":
            input_widget = self.query_one("#terminal_input", Input)
            input_widget.value = "track W13_S1_R1 over time"
            input_widget.focus()

        elif button_id == "cmd_4":
            terminal.execute_command("compare DFU row performance")

        elif button_id == "cmd_5":
            terminal.execute_command("compare fluid types")

        elif button_id == "cmd_6":
            terminal.execute_command("list all devices")

    def action_refresh(self) -> None:
        """Refresh database and status display."""
        self.analyst.refresh_data()
        status_widget = self.query_one(DatabaseStatus)
        status_widget.update_status()

        terminal = self.query_one(CommandTerminal)
        output = terminal.query_one("#terminal_output", RichLog)
        output.write(f"[bold green][Database Refreshed][/bold green]")
        output.write(f"Reloaded {len(self.analyst.df)} records from database.")
        output.write(f"[green]Status updated successfully![/green]")
        output.write("")

    def action_focus_terminal(self) -> None:
        """Focus the terminal input."""
        input_widget = self.query_one("#terminal_input", Input)
        input_widget.focus()


def main():
    """Run the dashboard application."""
    app = MicrofluidicDashboard()
    app.run()


if __name__ == "__main__":
    main()
