"""
Plot generation from JSON configuration files.

This module provides a flexible plotting system that reads JSON config files
and generates matplotlib plots from filtered CSV data.

Usage:
    from src.plot_from_config import plot_from_config

    plot_from_config(
        csv_path="data/filtered_export.csv",
        config_path="configs/plots/dfu_sweep.json",
        output_path="outputs/my_plot.png"
    )

    # Or from command line:
    python src/plot_from_config.py --csv data.csv --config config.json --output plot.png
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import argparse
import sys

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class PlotConfigError(Exception):
    """Raised when there's an issue with the plot configuration."""
    pass


class PlotGenerator:
    """Generate plots from JSON configurations and CSV data."""

    # Color schemes
    COLOR_SCHEMES = {
        'default': None,  # Use matplotlib defaults
        'vibrant': ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf'],
        'pastel': ['#fbb4ae', '#b3cde3', '#ccebc5', '#decbe4', '#fed9a6', '#ffffcc', '#e5d8bd', '#fddaec'],
        'dark': ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e', '#e6ab02', '#a6761d', '#666666'],
        'earth': ['#8b4513', '#556b2f', '#2f4f4f', '#8b7355', '#cd853f', '#daa520', '#b8860b', '#6b8e23']
    }

    def __init__(self, config_path: str, csv_path: str):
        """
        Initialize plot generator.

        Args:
            config_path: Path to JSON configuration file
            csv_path: Path to CSV data file
        """
        self.config_path = Path(config_path)
        self.csv_path = Path(csv_path)
        self.config = self._load_config()
        self.df = self._load_data()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load and parse JSON configuration."""
        if not self.config_path.exists():
            raise PlotConfigError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = json.load(f)

        # Validate required top-level fields
        required_fields = ['name', 'description', 'axes', 'aggregation', 'style']
        missing = [f for f in required_fields if f not in config]
        if missing:
            raise PlotConfigError(f"Missing required fields: {', '.join(missing)}")

        return config

    def _load_data(self) -> pd.DataFrame:
        """Load CSV data."""
        if not self.csv_path.exists():
            raise PlotConfigError(f"CSV file not found: {self.csv_path}")

        df = pd.read_csv(self.csv_path)

        if df.empty:
            raise PlotConfigError("CSV file is empty")

        return df

    def _validate_config(self):
        """Validate configuration against data."""
        # Check required axes columns exist
        x_col = self.config['axes']['x']
        y_cols = self.config['axes']['y']
        if isinstance(y_cols, str):
            y_cols = [y_cols]

        missing_cols = []
        if x_col not in self.df.columns:
            missing_cols.append(x_col)
        for y_col in y_cols:
            if y_col not in self.df.columns:
                missing_cols.append(y_col)

        # Check optional error column
        y_error = self.config['axes'].get('y_error')
        if y_error and y_error not in self.df.columns:
            missing_cols.append(y_error)

        # Check grouping columns
        grouping = self.config.get('grouping', {})
        for key in ['group_by', 'facet_row', 'facet_col']:
            col = grouping.get(key)
            if col and col not in self.df.columns:
                missing_cols.append(col)

        if missing_cols:
            available = ', '.join(self.df.columns.tolist())
            raise PlotConfigError(
                f"Missing columns in CSV: {', '.join(set(missing_cols))}\\n"
                f"Available columns: {available}"
            )

    def _prepare_data(self) -> pd.DataFrame:
        """Prepare data according to aggregation settings."""
        df = self.df.copy()

        agg_config = self.config['aggregation']
        agg_method = agg_config['method']

        if agg_method == 'none':
            # No aggregation, return as-is
            return df

        # Aggregation needed
        group_cols = agg_config.get('group_cols', [])
        if not group_cols:
            raise PlotConfigError("aggregation.group_cols required when method is not 'none'")

        # Validate group columns exist
        missing = [col for col in group_cols if col not in df.columns]
        if missing:
            raise PlotConfigError(f"Group columns not found: {', '.join(missing)}")

        # Get y column(s)
        y_cols = self.config['axes']['y']
        if isinstance(y_cols, str):
            y_cols = [y_cols]

        # Aggregate
        if agg_method == 'mean':
            agg_df = df.groupby(group_cols)[y_cols].agg(['mean', 'std', 'sem', 'count']).reset_index()
        elif agg_method == 'median':
            agg_df = df.groupby(group_cols)[y_cols].agg(['median', 'std', 'count']).reset_index()
        else:
            raise PlotConfigError(f"Unknown aggregation method: {agg_method}")

        # Flatten multi-level columns
        agg_df.columns = ['_'.join(col).strip('_') if col[1] else col[0] for col in agg_df.columns.values]

        return agg_df

    def _apply_style(self, ax: plt.Axes):
        """Apply styling from config to axes."""
        style = self.config.get('style', {})

        # Grid
        if style.get('show_grid', True):
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        else:
            ax.grid(False)

        # Scales
        scales = self.config.get('scales', {})
        x_scale = scales.get('x_scale', 'linear')
        y_scale = scales.get('y_scale', 'linear')

        ax.set_xscale(x_scale)
        ax.set_yscale(y_scale)

        # Limits
        x_limits = scales.get('x_limits')
        y_limits = scales.get('y_limits')

        if x_limits:
            ax.set_xlim(x_limits)
        if y_limits:
            ax.set_ylim(y_limits)

        # Labels
        labels = self.config.get('labels', {})

        if 'title' in labels:
            ax.set_title(labels['title'], fontsize=14, fontweight='bold', pad=20)

        if 'x_label' in labels:
            ax.set_xlabel(labels['x_label'], fontsize=12, fontweight='bold')

        if 'y_label' in labels:
            ax.set_ylabel(labels['y_label'], fontsize=12, fontweight='bold')

        # Legend
        if style.get('show_legend', True):
            legend_pos = style.get('legend_position', 'best')
            legend_title = labels.get('legend_title')

            if legend_pos == 'outside':
                ax.legend(title=legend_title, bbox_to_anchor=(1.05, 1), loc='upper left',
                         frameon=True, fancybox=True, shadow=True)
            else:
                ax.legend(title=legend_title, loc=legend_pos,
                         frameon=True, fancybox=True, shadow=True)

    def _get_colors(self, n_colors: int) -> List[str]:
        """Get color palette from config."""
        style = self.config.get('style', {})
        scheme = style.get('color_scheme', 'default')

        if scheme == 'default' or scheme not in self.COLOR_SCHEMES:
            return None  # Let matplotlib choose

        colors = self.COLOR_SCHEMES[scheme]

        # Cycle colors if we need more than available
        if n_colors > len(colors):
            colors = colors * (n_colors // len(colors) + 1)

        return colors[:n_colors]

    def generate(self, output_path: Optional[str] = None, show: bool = False) -> Path:
        """
        Generate the plot.

        Args:
            output_path: Path to save plot (optional)
            show: Whether to display plot interactively (default: False)

        Returns:
            Path to saved plot file
        """
        # Prepare data
        df = self._prepare_data()

        # Create figure
        fig_config = self.config.get('figure', {})
        width = fig_config.get('width', 10)
        height = fig_config.get('height', 6)
        dpi = fig_config.get('dpi', 300)

        fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)

        # Extract plot parameters
        x_col = self.config['axes']['x']
        y_cols = self.config['axes']['y']
        if isinstance(y_cols, str):
            y_cols = [y_cols]

        # For now, support single y column (multi-y coming later)
        y_col = y_cols[0]

        # Check if data was aggregated
        agg_method = self.config['aggregation']['method']
        if agg_method != 'none':
            # Use aggregated column names
            y_col_plot = f"{y_col}_{agg_method}"
            if y_col_plot not in df.columns and f"{y_col}_mean" in df.columns:
                y_col_plot = f"{y_col}_mean"  # fallback to mean
        else:
            y_col_plot = y_col

        # Get grouping
        grouping = self.config.get('grouping', {})
        group_by = grouping.get('group_by')

        # Get style parameters
        style = self.config.get('style', {})
        plot_type = style.get('plot_type', 'line')
        marker_size = style.get('marker_size', 4)  # Smaller default
        line_width = style.get('line_width', 1.5)  # Thinner default
        alpha = style.get('alpha', 0.8)

        # Advanced options
        advanced = self.config.get('advanced', {})
        sort_x = advanced.get('sort_x', False)
        show_counts = advanced.get('show_counts', False)
        dodge_amount = advanced.get('dodge', 0)  # Amount to dodge overlapping points

        # Sort data if requested
        if sort_x:
            df = df.sort_values(x_col)

        # Get colors and groups
        if group_by:
            groups = df[group_by].unique()
            colors = self._get_colors(len(groups))
        else:
            groups = [None]
            colors = None

        # Calculate dodge offsets if enabled
        dodge_offsets = {}
        if dodge_amount > 0 and group_by:
            n_groups = len(groups)
            # Create symmetric offsets around center
            for idx in range(n_groups):
                offset = (idx - (n_groups - 1) / 2) * dodge_amount
                dodge_offsets[idx] = offset

        # Plot data
        for idx, group in enumerate(groups):
            if group is not None:
                group_df = df[df[group_by] == group].copy()
                label = str(group)

                # Add count to label if requested
                if show_counts and agg_method != 'none':
                    count_col = f"{y_col}_count"
                    if count_col in group_df.columns:
                        total_count = group_df[count_col].sum()
                        label = f"{label} (n={int(total_count)})"
            else:
                group_df = df.copy()
                label = y_col

            # Apply dodge offset if enabled
            x_data = group_df[x_col].values
            if dodge_amount > 0 and idx in dodge_offsets:
                x_data = x_data + dodge_offsets[idx]

            color = colors[idx] if colors else None

            # Determine plot style
            if plot_type == 'scatter':
                ax.scatter(x_data, group_df[y_col_plot].values,
                          label=label, s=marker_size**2, alpha=alpha, color=color)

            elif plot_type == 'line':
                ax.plot(x_data, group_df[y_col_plot].values,
                       label=label, linewidth=line_width, alpha=alpha, color=color)

            elif plot_type == 'line+markers':
                ax.plot(x_data, group_df[y_col_plot].values,
                       marker='o', markersize=marker_size, linewidth=line_width,
                       label=label, alpha=alpha, color=color, markeredgewidth=0.5,
                       markeredgecolor='white')

            elif plot_type == 'bar':
                if group_by:
                    # Grouped bar chart
                    x_positions = np.arange(len(group_df[x_col]))
                    width = 0.8 / len(groups)
                    offset = width * idx - (0.8 - width) / 2
                    ax.bar(x_positions + offset, group_df[y_col_plot], width=width,
                          label=label, alpha=alpha, color=color)
                    ax.set_xticks(x_positions)
                    ax.set_xticklabels(group_df[x_col])
                else:
                    ax.bar(group_df[x_col], group_df[y_col_plot],
                          label=label, alpha=alpha, color=color)

            else:
                raise PlotConfigError(f"Unsupported plot type: {plot_type}")

            # Add error bars if specified
            y_error = self.config['axes'].get('y_error')
            error_method = self.config['aggregation'].get('error_method')

            if y_error and agg_method == 'none':
                # Error column directly specified
                if y_error in group_df.columns:
                    ax.errorbar(x_data, group_df[y_col_plot].values,
                               yerr=group_df[y_error].values, fmt='none',
                               ecolor=color, alpha=alpha*0.5, capsize=2,
                               elinewidth=1, capthick=1)

            elif error_method and error_method != 'none' and agg_method != 'none':
                # Use aggregated error
                error_col = f"{y_col}_{error_method}"
                if error_col in group_df.columns:
                    ax.errorbar(x_data, group_df[y_col_plot].values,
                               yerr=group_df[error_col].values, fmt='none',
                               ecolor=color, alpha=alpha*0.5, capsize=2,
                               elinewidth=1, capthick=1)

        # Apply styling
        self._apply_style(ax)

        # Tight layout
        plt.tight_layout()

        # Save or show
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
            print(f"✓ Plot saved: {output_path}")

        if show:
            plt.show()
        else:
            plt.close(fig)

        return output_path if output_path else None


def plot_from_config(csv_path: str, config_path: str,
                     output_path: Optional[str] = None,
                     show: bool = False) -> Path:
    """
    Generate a plot from a JSON config and CSV data.

    Args:
        csv_path: Path to CSV data file
        config_path: Path to JSON configuration file
        output_path: Path to save plot (optional, auto-generated if None)
        show: Whether to display plot interactively (default: False)

    Returns:
        Path to saved plot file

    Example:
        plot_from_config(
            csv_path="data/filtered_export.csv",
            config_path="configs/plots/dfu_sweep.json",
            output_path="outputs/my_plot.png"
        )
    """
    generator = PlotGenerator(config_path=config_path, csv_path=csv_path)

    # Auto-generate output path if not provided
    if output_path is None and not show:
        config_name = Path(config_path).stem
        csv_name = Path(csv_path).stem
        output_path = f"outputs/plots/{config_name}_{csv_name}.png"

    return generator.generate(output_path=output_path, show=show)


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Generate plots from JSON configs and CSV data"
    )
    parser.add_argument('--csv', required=True, help='Path to CSV data file')
    parser.add_argument('--config', required=True, help='Path to JSON config file')
    parser.add_argument('--output', help='Path to save plot (optional)')
    parser.add_argument('--show', action='store_true', help='Display plot interactively')

    args = parser.parse_args()

    try:
        plot_from_config(
            csv_path=args.csv,
            config_path=args.config,
            output_path=args.output,
            show=args.show
        )
    except PlotConfigError as e:
        print(f"❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
