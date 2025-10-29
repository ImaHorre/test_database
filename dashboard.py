"""
Interactive CLI Dashboard for Microfluidic Device Analysis

Built with Textual for beautiful terminal interface.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, Label, DataTable, Input, Select
from textual.binding import Binding
from textual import events
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
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
        yield Button("[Q] Ask a Question (Natural Language)", id="cmd_q", variant="warning")
        yield Label("")
        yield Button("[R] Refresh Database", id="cmd_refresh", variant="default")
        yield Button("[X] Exit", id="cmd_exit", variant="error")


class ResultDisplay(Static):
    """Widget for displaying analysis results."""

    def __init__(self):
        super().__init__()
        self.update("[dim]Results will appear here after running a command...[/dim]")

    def show_result(self, title: str, content: str, plot_path: str = None):
        """Display analysis result."""
        result_text = f"[bold green]{title}[/bold green]\n"
        result_text += "━" * 60 + "\n\n"
        result_text += content

        if plot_path and Path(plot_path).exists():
            result_text += f"\n\n[bold]Plot saved:[/bold] [cyan]{plot_path}[/cyan]"
            result_text += "\n[dim](Open the file to view the visualization)[/dim]"

        self.update(result_text)


class InputDialog(Container):
    """Dialog for collecting user input for analysis commands."""

    def __init__(self, command_id: str, analyst: DataAnalyst):
        super().__init__()
        self.command_id = command_id
        self.analyst = analyst

    def compose(self) -> ComposeResult:
        """Create input fields based on command."""

        if self.command_id == "cmd_q":
            yield Label("[bold]Natural Language Query[/bold]")
            yield Label("Ask a question in plain English:")
            yield Label("[dim]Examples: 'Compare W13 and W14', 'Track W13_S1_R1', 'Analyze flowrate effects for W13'[/dim]")
            yield Input(placeholder="Enter your question...", id="nl_query")

        elif self.command_id == "cmd_1":
            yield Label("[bold]Compare Devices at Same Parameters[/bold]")
            yield Label("Filter devices tested under same conditions:")
            yield Input(placeholder="Device Type (e.g., W13, W14, or leave empty)", id="device_type")
            yield Input(placeholder="Aqueous Flowrate (ml/hr, or leave empty)", id="flowrate")
            yield Input(placeholder="Oil Pressure (mbar, or leave empty)", id="pressure")

        elif self.command_id == "cmd_2":
            yield Label("[bold]Analyze Flow Parameter Effects[/bold]")
            yield Label("Analyze how parameters affect measurements:")
            yield Input(placeholder="Device Type (e.g., W13)", id="device_type")
            yield Input(placeholder="Parameter (aqueous_flowrate or oil_pressure)", id="parameter", value="aqueous_flowrate")
            yield Input(placeholder="Metric (droplet_size_mean or frequency_mean)", id="metric", value="droplet_size_mean")

        elif self.command_id == "cmd_3":
            yield Label("[bold]Track Device Over Time[/bold]")
            yield Label("Monitor individual device performance:")
            yield Input(placeholder="Device ID (e.g., W13_S1_R1)", id="device_id")

        elif self.command_id == "cmd_4":
            yield Label("[bold]Compare DFU Row Performance[/bold]")
            yield Label("Compare performance across DFU rows:")
            yield Input(placeholder="Device Type (e.g., W13, or leave empty for all)", id="device_type")
            yield Input(placeholder="Metric (droplet_size_mean or frequency_mean)", id="metric", value="droplet_size_mean")

        elif self.command_id == "cmd_5":
            yield Label("[bold]Compare Fluid Types[/bold]")
            yield Label("Compare different fluid combinations:")
            yield Input(placeholder="Device Type (e.g., W13, or leave empty for all)", id="device_type")

        yield Label("")
        yield Horizontal(
            Button("Run Analysis", id="run", variant="success"),
            Button("Cancel", id="cancel", variant="error"),
        )


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

    InputDialog {
        width: 100%;
        height: auto;
        border: solid $accent;
        background: $surface;
        padding: 1;
    }

    Input {
        width: 100%;
        margin: 0 1;
    }

    ResultDisplay {
        height: 1fr;
    }

    DatabaseStatus {
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("1", "command_1", "Compare Devices"),
        Binding("2", "command_2", "Parameter Effects"),
        Binding("3", "command_3", "Track Device"),
        Binding("4", "command_4", "DFU Comparison"),
        Binding("5", "command_5", "Fluid Comparison"),
        Binding("6", "command_6", "List Devices"),
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.analyst = DataAnalyst()
        self.current_dialog = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)

        with Horizontal(id="main-container"):
            with Vertical(id="left-panel"):
                yield DatabaseStatus(self.analyst)
                yield QuickCommandMenu()

            with ScrollableContainer(id="right-panel"):
                yield ResultDisplay()

        yield Footer()

    def on_mount(self) -> None:
        """Handle mount event."""
        self.title = "Microfluidic Device Analysis Dashboard"
        self.sub_title = f"{len(self.analyst.df)} measurements loaded"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        button_id = event.button.id

        if button_id == "cmd_exit":
            self.exit()

        elif button_id == "cmd_refresh":
            self.action_refresh()

        elif button_id == "cmd_6":
            self.action_command_6()

        elif button_id.startswith("cmd_"):
            self.show_input_dialog(button_id)

        elif button_id == "run":
            self.run_analysis()

        elif button_id == "cancel":
            self.hide_input_dialog()

    def show_input_dialog(self, command_id: str) -> None:
        """Show input dialog for a command."""
        if self.current_dialog:
            self.hide_input_dialog()

        dialog = InputDialog(command_id, self.analyst)
        right_panel = self.query_one("#right-panel")
        right_panel.mount(dialog)
        self.current_dialog = dialog

    def hide_input_dialog(self) -> None:
        """Hide and remove input dialog."""
        if self.current_dialog:
            self.current_dialog.remove()
            self.current_dialog = None

    def run_analysis(self) -> None:
        """Execute the analysis based on current dialog inputs."""
        if not self.current_dialog:
            return

        command_id = self.current_dialog.command_id
        result_display = self.query_one(ResultDisplay)

        try:
            if command_id == "cmd_q":
                self.run_natural_language_query()
            elif command_id == "cmd_1":
                self.run_compare_devices()
            elif command_id == "cmd_2":
                self.run_parameter_effects()
            elif command_id == "cmd_3":
                self.run_track_device()
            elif command_id == "cmd_4":
                self.run_dfu_comparison()
            elif command_id == "cmd_5":
                self.run_fluid_comparison()

        except Exception as e:
            result_display.show_result(
                "Error",
                f"[red]Analysis failed:[/red]\n{str(e)}\n\n[dim]Check your input parameters and try again.[/dim]"
            )

        finally:
            self.hide_input_dialog()

    def run_natural_language_query(self) -> None:
        """Run natural language query processing."""
        query_input = self.query_one("#nl_query", Input)
        query = query_input.value.strip()

        if not query:
            result_display = self.query_one(ResultDisplay)
            result_display.show_result(
                "Empty Query",
                "[yellow]Please enter a question.[/yellow]\n\n" +
                "Examples:\n" +
                "  • 'Compare W13 and W14 devices'\n" +
                "  • 'Show me devices at 5 ml/hr'\n" +
                "  • 'Track W13_S1_R1 over time'\n" +
                "  • 'Analyze pressure effects for W14'\n" +
                "  • 'Generate a summary report'"
            )
            return

        # Process the query
        result = self.analyst.process_natural_language_query(query)

        # Format the result for display
        title = f"Query: {query}"
        content = result.get('message', '')

        # Add data preview if available
        data = result.get('result')
        if data is not None and isinstance(data, pd.DataFrame) and len(data) > 0:
            content += f"\n\n[bold]Data preview:[/bold]\n"
            content += data.head(5).to_string()
            if len(data) > 5:
                content += f"\n\n[dim]... showing 5 of {len(data)} rows[/dim]"

        plot_path = result.get('plot_path')
        report_path = result.get('report_path')

        # Add report path if present
        if report_path:
            content += f"\n\n[bold]Report saved:[/bold] [cyan]{report_path}[/cyan]"

        result_display = self.query_one(ResultDisplay)
        result_display.show_result(title, content, plot_path)

    def run_compare_devices(self) -> None:
        """Run device comparison analysis."""
        device_type_input = self.query_one("#device_type", Input)
        flowrate_input = self.query_one("#flowrate", Input)
        pressure_input = self.query_one("#pressure", Input)

        device_type = device_type_input.value.strip() or None
        flowrate = int(flowrate_input.value) if flowrate_input.value.strip() else None
        pressure = int(pressure_input.value) if pressure_input.value.strip() else None

        output_path = f"outputs/dashboard_device_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        result = self.analyst.compare_devices_at_same_parameters(
            device_type=device_type,
            aqueous_flowrate=flowrate,
            oil_pressure=pressure,
            output_path=output_path
        )

        # Format result
        content = f"Found {len(result)} devices matching criteria:\n\n"
        content += result.to_string()

        result_display = self.query_one(ResultDisplay)
        result_display.show_result("Device Comparison Complete", content, output_path)

    def run_parameter_effects(self) -> None:
        """Run parameter effects analysis."""
        device_type = self.query_one("#device_type", Input).value.strip()
        parameter = self.query_one("#parameter", Input).value.strip()
        metric = self.query_one("#metric", Input).value.strip()

        output_path = f"outputs/dashboard_param_effects_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        result = self.analyst.analyze_flow_parameter_effects(
            device_type=device_type,
            parameter=parameter,
            metric=metric,
            output_path=output_path
        )

        content = f"Correlation: {result['correlation']}\n"
        content += f"Total measurements: {result['total_measurements']}\n\n"
        content += "Grouped Statistics:\n"
        content += result['grouped_stats'].to_string()

        result_display = self.query_one(ResultDisplay)
        result_display.show_result("Parameter Effects Analysis Complete", content, output_path)

    def run_track_device(self) -> None:
        """Run device tracking analysis."""
        device_id = self.query_one("#device_id", Input).value.strip()

        output_path = f"outputs/dashboard_tracking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        result = self.analyst.track_device_over_time(
            device_id=device_id,
            output_path=output_path
        )

        content = f"Tracked {len(result)} tests for device {device_id}\n\n"
        content += f"Date range: {result['testing_date'].min()} to {result['testing_date'].max()}\n\n"
        content += "Summary:\n"
        content += f"  Mean droplet size: {result['droplet_size_mean'].mean():.2f} µm\n"
        content += f"  Std deviation: {result['droplet_size_mean'].std():.2f} µm\n"
        content += f"  Min/Max: {result['droplet_size_mean'].min():.2f} - {result['droplet_size_mean'].max():.2f} µm\n"

        result_display = self.query_one(ResultDisplay)
        result_display.show_result("Device Tracking Complete", content, output_path)

    def run_dfu_comparison(self) -> None:
        """Run DFU row comparison analysis."""
        device_type_input = self.query_one("#device_type", Input)
        metric_input = self.query_one("#metric", Input)

        device_type = device_type_input.value.strip() or None
        metric = metric_input.value.strip()

        output_path = f"outputs/dashboard_dfu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        result = self.analyst.compare_dfu_row_performance(
            device_type=device_type,
            metric=metric,
            output_path=output_path
        )

        content = f"Compared {len(result)} DFU rows\n\n"
        content += result.to_string()

        result_display = self.query_one(ResultDisplay)
        result_display.show_result("DFU Row Comparison Complete", content, output_path)

    def run_fluid_comparison(self) -> None:
        """Run fluid type comparison analysis."""
        device_type_input = self.query_one("#device_type", Input)
        device_type = device_type_input.value.strip() or None

        output_path = f"outputs/dashboard_fluids_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        result = self.analyst.compare_fluid_types(
            device_type=device_type,
            output_path=output_path
        )

        content = f"Compared {len(result)} fluid combinations\n\n"
        content += result.to_string()

        result_display = self.query_one(ResultDisplay)
        result_display.show_result("Fluid Comparison Complete", content, output_path)

    def action_command_1(self) -> None:
        """Keyboard shortcut for command 1."""
        self.show_input_dialog("cmd_1")

    def action_command_2(self) -> None:
        """Keyboard shortcut for command 2."""
        self.show_input_dialog("cmd_2")

    def action_command_3(self) -> None:
        """Keyboard shortcut for command 3."""
        self.show_input_dialog("cmd_3")

    def action_command_4(self) -> None:
        """Keyboard shortcut for command 4."""
        self.show_input_dialog("cmd_4")

    def action_command_5(self) -> None:
        """Keyboard shortcut for command 5."""
        self.show_input_dialog("cmd_5")

    def action_command_6(self) -> None:
        """Show list of all available devices."""
        devices = self.analyst.df.groupby('device_id').agg({
            'device_type': 'first',
            'testing_date': ['min', 'max'],
            'droplet_size_mean': 'count'
        })

        content = "All devices in database:\n\n"
        for device_id in devices.index:
            device_type = devices.loc[device_id, ('device_type', 'first')]
            min_date = devices.loc[device_id, ('testing_date', 'min')]
            max_date = devices.loc[device_id, ('testing_date', 'max')]
            count = devices.loc[device_id, ('droplet_size_mean', 'count')]

            content += f"[bold]{device_id}[/bold] ({device_type})\n"
            content += f"  Tests: {count}\n"
            content += f"  Date range: {min_date} to {max_date}\n\n"

        result_display = self.query_one(ResultDisplay)
        result_display.show_result("Available Devices", content)

    def action_refresh(self) -> None:
        """Refresh database and status display."""
        self.analyst.refresh_data()
        status_widget = self.query_one(DatabaseStatus)
        status_widget.update_status()

        result_display = self.query_one(ResultDisplay)
        result_display.show_result(
            "Database Refreshed",
            f"Reloaded {len(self.analyst.df)} records from database.\n\n[green]Status updated successfully![/green]"
        )


def main():
    """Run the dashboard application."""
    app = MicrofluidicDashboard()
    app.run()


if __name__ == "__main__":
    main()
