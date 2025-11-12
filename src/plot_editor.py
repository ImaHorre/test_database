"""
Plot Editor for Live Plot Preview and Interactive Editing

Provides a sophisticated interface for editing matplotlib plots in real-time
through terminal commands. Supports adding metadata, changing colors, toggling
elements, and more.
"""

import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PlotEditor:
    """
    Interactive plot editor for live plot manipulation.

    Manages plot state, handles editing commands, and provides
    terminal-based plot modification interface.
    """

    def __init__(self, fig, ax, plot_data: Dict[str, Any], metadata: Dict[str, Any]):
        """
        Initialize Plot Editor.

        Args:
            fig: Matplotlib figure object
            ax: Matplotlib axes object
            plot_data: Dictionary containing original plot data
            metadata: Dictionary containing plot metadata (filters, devices, etc.)
        """
        self.fig = fig
        self.ax = ax
        self.plot_data = plot_data
        self.metadata = metadata

        # Track modifications
        self.modifications = {
            'show_legend': True,
            'show_grid': True,
            'color_scheme': 'default',
            'theme': 'light',
            'show_error_bars': True,
            'show_test_date': False,
            'show_bond_date': False,
            'custom_title': None,
        }

        # Color schemes
        self.color_schemes = {
            'default': None,  # Use matplotlib defaults
            'vibrant': ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33'],
            'pastel': ['#fbb4ae', '#b3cde3', '#ccebc5', '#decbe4', '#fed9a6', '#ffffcc'],
            'dark': ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e', '#e6ab02'],
            'earth': ['#8b4513', '#556b2f', '#2f4f4f', '#8b7355', '#a0522d', '#cd853f'],
        }

        # Keep original data for reverting
        self.original_lines = None
        self._save_original_lines()

        logger.info("PlotEditor initialized")

    def _save_original_lines(self):
        """Save original line objects for potential restoration."""
        self.original_lines = []
        for line in self.ax.get_lines():
            # Store line properties
            self.original_lines.append({
                'data': (line.get_xdata().copy(), line.get_ydata().copy()),
                'color': line.get_color(),
                'marker': line.get_marker(),
                'linestyle': line.get_linestyle(),
                'linewidth': line.get_linewidth(),
                'label': line.get_label(),
                'alpha': line.get_alpha(),
            })

    def process_command(self, command: str) -> Dict[str, Any]:
        """
        Process an editing command.

        Args:
            command: Command string from user

        Returns:
            Dictionary with status, message, and action taken
        """
        command = command.strip().lower()

        # Help command
        if command == 'help':
            return self._show_help()

        # Save command
        elif command == 'save':
            return self._save_plot()

        # Discard command
        elif command == 'discard':
            return self._discard_plot()

        # Legend commands
        elif command == 'remove legend':
            return self._toggle_legend(False)
        elif command == 'show legend':
            return self._toggle_legend(True)

        # Grid commands
        elif command == 'add grid':
            return self._toggle_grid(True)
        elif command == 'remove grid':
            return self._toggle_grid(False)

        # Color scheme commands
        elif command == 'change colors' or command == 'change color':
            return self._cycle_color_scheme()

        # Theme commands
        elif command.startswith('change theme'):
            theme = command.replace('change theme', '').strip()
            return self._change_theme(theme)

        # Error bar commands
        elif command == 'add error bars':
            return self._toggle_error_bars(True)
        elif command == 'remove error bars':
            return self._toggle_error_bars(False)

        # Metadata commands
        elif command == 'add test date':
            return self._add_test_date_info()
        elif command == 'add bond date':
            return self._add_bond_date_info()

        # Title commands
        elif command.startswith('change title'):
            new_title = command.replace('change title', '').strip()
            return self._change_title(new_title)

        # Size commands
        elif command.startswith('resize'):
            size = command.replace('resize', '').strip()
            return self._resize_figure(size)

        # Unknown command
        else:
            return {
                'status': 'error',
                'message': f"Unknown command: '{command}'. Type 'help' to see available commands.",
                'action': 'none'
            }

    def _show_help(self) -> Dict[str, Any]:
        """Show help text with available commands."""
        help_text = """
========================================
PLOT EDITING COMMANDS
========================================

LEGEND & DISPLAY:
  show legend       - Display plot legend
  remove legend     - Hide plot legend
  add grid          - Show grid lines
  remove grid       - Hide grid lines

VISUAL STYLING:
  change colors     - Cycle through color schemes
  change theme [light/dark] - Change plot theme
  resize [small/medium/large] - Change figure size

DATA DISPLAY:
  add error bars    - Show error bars on data points
  remove error bars - Hide error bars
  add test date     - Add testing date info to legend
  add bond date     - Add bonding date info to legend

CUSTOMIZATION:
  change title [new title] - Set custom plot title

ACTIONS:
  save             - Save plot to file and exit
  discard          - Close plot without saving
  help             - Show this help message

========================================
"""
        return {
            'status': 'success',
            'message': help_text,
            'action': 'help'
        }

    def _toggle_legend(self, show: bool) -> Dict[str, Any]:
        """Toggle legend visibility."""
        self.modifications['show_legend'] = show

        if show:
            self.ax.legend(loc='best', framealpha=0.9, fontsize=9)
            message = "Legend displayed"
        else:
            legend = self.ax.get_legend()
            if legend:
                legend.remove()
            message = "Legend hidden"

        self._refresh_plot()

        return {
            'status': 'success',
            'message': message,
            'action': 'legend_toggle'
        }

    def _toggle_grid(self, show: bool) -> Dict[str, Any]:
        """Toggle grid visibility."""
        self.modifications['show_grid'] = show
        self.ax.grid(show, alpha=0.3, linestyle='--')
        self._refresh_plot()

        message = "Grid displayed" if show else "Grid hidden"

        return {
            'status': 'success',
            'message': message,
            'action': 'grid_toggle'
        }

    def _cycle_color_scheme(self) -> Dict[str, Any]:
        """Cycle through available color schemes."""
        schemes = list(self.color_schemes.keys())
        current_idx = schemes.index(self.modifications['color_scheme'])
        next_idx = (current_idx + 1) % len(schemes)
        new_scheme = schemes[next_idx]

        self.modifications['color_scheme'] = new_scheme

        # Apply new colors to lines
        if new_scheme != 'default':
            colors = self.color_schemes[new_scheme]
            lines = [line for line in self.ax.get_lines() if not line.get_label().startswith('_')]

            for i, line in enumerate(lines):
                color = colors[i % len(colors)]
                line.set_color(color)
        else:
            # Restore original colors
            lines = [line for line in self.ax.get_lines() if not line.get_label().startswith('_')]
            for i, line in enumerate(lines):
                if i < len(self.original_lines):
                    line.set_color(self.original_lines[i]['color'])

        self._refresh_plot()

        return {
            'status': 'success',
            'message': f"Color scheme changed to: {new_scheme}",
            'action': 'color_change'
        }

    def _change_theme(self, theme: str) -> Dict[str, Any]:
        """Change plot theme (light/dark)."""
        if theme not in ['light', 'dark']:
            return {
                'status': 'error',
                'message': "Theme must be 'light' or 'dark'",
                'action': 'none'
            }

        self.modifications['theme'] = theme

        if theme == 'dark':
            self.fig.patch.set_facecolor('#2e2e2e')
            self.ax.set_facecolor('#1e1e1e')
            self.ax.spines['bottom'].set_color('white')
            self.ax.spines['left'].set_color('white')
            self.ax.tick_params(colors='white')
            self.ax.xaxis.label.set_color('white')
            self.ax.yaxis.label.set_color('white')
            self.ax.title.set_color('white')
        else:
            self.fig.patch.set_facecolor('white')
            self.ax.set_facecolor('white')
            self.ax.spines['bottom'].set_color('black')
            self.ax.spines['left'].set_color('black')
            self.ax.tick_params(colors='black')
            self.ax.xaxis.label.set_color('black')
            self.ax.yaxis.label.set_color('black')
            self.ax.title.set_color('black')

        self._refresh_plot()

        return {
            'status': 'success',
            'message': f"Theme changed to: {theme}",
            'action': 'theme_change'
        }

    def _toggle_error_bars(self, show: bool) -> Dict[str, Any]:
        """Toggle error bar visibility."""
        self.modifications['show_error_bars'] = show

        # Find and modify error bar containers
        for container in self.ax.containers:
            if hasattr(container, 'has_xerr') or hasattr(container, 'has_yerr'):
                for line in container.get_children():
                    if hasattr(line, 'set_visible'):
                        line.set_visible(show)

        # Also handle individual error bar lines
        for line in self.ax.get_lines():
            label = line.get_label()
            if label.startswith('_') and ('errorbar' in label.lower() or 'err' in label.lower()):
                line.set_visible(show)

        self._refresh_plot()

        message = "Error bars displayed" if show else "Error bars hidden"

        return {
            'status': 'success',
            'message': message,
            'action': 'errorbar_toggle'
        }

    def _add_test_date_info(self) -> Dict[str, Any]:
        """Add testing date information to legend or title."""
        self.modifications['show_test_date'] = True

        # Get test dates from metadata
        if 'devices_with_dates' in self.plot_data:
            # Update legend labels to include test dates
            lines = [line for line in self.ax.get_lines() if not line.get_label().startswith('_')]
            devices_dates = self.plot_data['devices_with_dates']

            for i, line in enumerate(lines):
                current_label = line.get_label()
                device_id = current_label.split(' ')[0]  # Get device ID from label

                if device_id in devices_dates:
                    test_date = devices_dates[device_id]
                    # Add date to label if not already present
                    if test_date not in current_label:
                        new_label = f"{current_label} [Test: {test_date}]"
                        line.set_label(new_label)

            # Refresh legend
            if self.modifications['show_legend']:
                self.ax.legend(loc='best', framealpha=0.9, fontsize=8)

            self._refresh_plot()

            return {
                'status': 'success',
                'message': "Testing date information added to legend",
                'action': 'test_date_added'
            }
        else:
            return {
                'status': 'error',
                'message': "No testing date information available",
                'action': 'none'
            }

    def _add_bond_date_info(self) -> Dict[str, Any]:
        """Add bonding date information to legend or title."""
        self.modifications['show_bond_date'] = True

        # Get bond dates from metadata
        if 'devices_with_bond_dates' in self.plot_data:
            # Update legend labels to include bond dates
            lines = [line for line in self.ax.get_lines() if not line.get_label().startswith('_')]
            devices_dates = self.plot_data['devices_with_bond_dates']

            for i, line in enumerate(lines):
                current_label = line.get_label()
                device_id = current_label.split(' ')[0]  # Get device ID from label

                if device_id in devices_dates:
                    bond_date = devices_dates[device_id]
                    # Add date to label if not already present
                    if bond_date not in current_label:
                        new_label = f"{current_label} [Bond: {bond_date}]"
                        line.set_label(new_label)

            # Refresh legend
            if self.modifications['show_legend']:
                self.ax.legend(loc='best', framealpha=0.9, fontsize=8)

            self._refresh_plot()

            return {
                'status': 'success',
                'message': "Bonding date information added to legend",
                'action': 'bond_date_added'
            }
        else:
            return {
                'status': 'error',
                'message': "No bonding date information available",
                'action': 'none'
            }

    def _change_title(self, new_title: str) -> Dict[str, Any]:
        """Change plot title."""
        if not new_title:
            return {
                'status': 'error',
                'message': "Please provide a title. Usage: change title [your new title]",
                'action': 'none'
            }

        self.modifications['custom_title'] = new_title
        self.ax.set_title(new_title, fontsize=14, fontweight='bold')
        self._refresh_plot()

        return {
            'status': 'success',
            'message': f"Title changed to: {new_title}",
            'action': 'title_change'
        }

    def _resize_figure(self, size: str) -> Dict[str, Any]:
        """Resize the figure."""
        sizes = {
            'small': (10, 6),
            'medium': (14, 8),
            'large': (18, 10),
        }

        if size not in sizes:
            return {
                'status': 'error',
                'message': "Size must be 'small', 'medium', or 'large'",
                'action': 'none'
            }

        self.fig.set_size_inches(sizes[size])
        self.fig.tight_layout()
        self._refresh_plot()

        return {
            'status': 'success',
            'message': f"Figure resized to: {size}",
            'action': 'resize'
        }

    def _save_plot(self) -> Dict[str, Any]:
        """Save the plot to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path('outputs/analyst/plots')
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"edited_plot_{timestamp}.png"

        try:
            self.fig.savefig(output_path, bbox_inches='tight', dpi=300)

            # Close the plot window
            plt.close(self.fig)

            logger.info(f"Plot saved: {output_path}")

            return {
                'status': 'success',
                'message': f"Plot saved to: {output_path}",
                'action': 'save',
                'file_path': str(output_path)
            }
        except Exception as e:
            logger.error(f"Failed to save plot: {e}")
            return {
                'status': 'error',
                'message': f"Failed to save plot: {str(e)}",
                'action': 'none'
            }

    def _discard_plot(self) -> Dict[str, Any]:
        """Discard the plot without saving."""
        plt.close(self.fig)

        return {
            'status': 'success',
            'message': "Plot discarded without saving",
            'action': 'discard'
        }

    def _refresh_plot(self):
        """Refresh the plot display."""
        try:
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
        except Exception as e:
            logger.warning(f"Could not refresh plot: {e}")

    def is_plot_open(self) -> bool:
        """Check if the plot window is still open."""
        try:
            return plt.fignum_exists(self.fig.number)
        except:
            return False


def create_live_plot_editor(fig, ax, plot_data: Dict[str, Any], metadata: Dict[str, Any]) -> PlotEditor:
    """
    Create a live plot editor instance.

    Args:
        fig: Matplotlib figure
        ax: Matplotlib axes
        plot_data: Dictionary with plot data (for metadata additions)
        metadata: Dictionary with plot metadata

    Returns:
        PlotEditor instance
    """
    return PlotEditor(fig, ax, plot_data, metadata)
