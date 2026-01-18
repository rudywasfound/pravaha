"""
Visualization module for satellite telemetry comparison.

Plots nominal vs degraded scenarios side-by-side.
Highlights degradation periods.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Tuple
from simulator.power import PowerTelemetry


class TelemetryPlotter:
    """Visualize power subsystem telemetry."""

    def __init__(self, figsize: Tuple[int, int] = (14, 10)):
        self.figsize = figsize

    def plot_comparison(
        self,
        nominal: PowerTelemetry,
        degraded: PowerTelemetry,
        degradation_hours: Optional[Tuple[float, float]] = None,
        save_path: Optional[str] = None,
    ):
        """
        Plot nominal vs degraded telemetry side-by-side.

        Args:
            nominal: PowerTelemetry from healthy scenario
            degraded: PowerTelemetry from faulty scenario
            degradation_hours: (start_hour, end_hour) to highlight degraded regions
            save_path: Path to save figure (None = display only)
        """
        fig, axes = plt.subplots(2, 2, figsize=self.figsize)
        fig.suptitle("Power Subsystem: Nominal vs Degraded", fontsize=14, fontweight="bold")

        # Convert time to hours for readability
        time_hours = nominal.time / 3600

        # Plot 1: Solar Input
        ax = axes[0, 0]
        ax.plot(time_hours, nominal.solar_input, label="Nominal", linewidth=1.5)
        ax.plot(time_hours, degraded.solar_input, label="Degraded", linewidth=1.5, alpha=0.7)
        self._highlight_degradation(ax, degradation_hours)
        ax.set_ylabel("Solar Input (W)")
        ax.set_title("Solar Power Input")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Plot 2: Battery Voltage
        ax = axes[0, 1]
        ax.plot(time_hours, nominal.battery_voltage, label="Nominal", linewidth=1.5)
        ax.plot(time_hours, degraded.battery_voltage, label="Degraded", linewidth=1.5, alpha=0.7)
        self._highlight_degradation(ax, degradation_hours)
        ax.set_ylabel("Battery Voltage (V)")
        ax.set_title("Battery Voltage")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Plot 3: Battery Charge
        ax = axes[1, 0]
        ax.plot(time_hours, nominal.battery_charge, label="Nominal", linewidth=1.5)
        ax.plot(time_hours, degraded.battery_charge, label="Degraded", linewidth=1.5, alpha=0.7)
        self._highlight_degradation(ax, degradation_hours)
        ax.set_xlabel("Time (hours)")
        ax.set_ylabel("Battery Charge (%)")
        ax.set_title("Battery Charge State")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Plot 4: Bus Voltage
        ax = axes[1, 1]
        ax.plot(time_hours, nominal.bus_voltage, label="Nominal", linewidth=1.5)
        ax.plot(time_hours, degraded.bus_voltage, label="Degraded", linewidth=1.5, alpha=0.7)
        self._highlight_degradation(ax, degradation_hours)
        ax.set_xlabel("Time (hours)")
        ax.set_ylabel("Bus Voltage (V)")
        ax.set_title("Regulated Bus Voltage")
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            print(f"Figure saved: {save_path}")
        else:
            plt.show()

    def plot_residuals(
        self,
        nominal: PowerTelemetry,
        degraded: PowerTelemetry,
        save_path: Optional[str] = None,
    ):
        """
        Plot deviation (residuals) of degraded from nominal.

        Args:
            nominal: PowerTelemetry from healthy scenario
            degraded: PowerTelemetry from faulty scenario
            save_path: Path to save figure
        """
        fig, axes = plt.subplots(1, 4, figsize=self.figsize)
        fig.suptitle("Degradation Deviations from Nominal", fontsize=14, fontweight="bold")

        time_hours = nominal.time / 3600

        metrics = [
            ("solar_input", "Solar Input (W)"),
            ("battery_voltage", "Battery Voltage (V)"),
            ("battery_charge", "Battery Charge (%)"),
            ("bus_voltage", "Bus Voltage (V)"),
        ]

        for idx, (attr, label) in enumerate(metrics):
            ax = axes[idx]
            nominal_val = getattr(nominal, attr)
            degraded_val = getattr(degraded, attr)
            residual = degraded_val - nominal_val

            ax.fill_between(time_hours, 0, residual, alpha=0.5, color="red")
            ax.plot(time_hours, residual, color="darkred", linewidth=1)
            ax.axhline(0, color="black", linestyle="--", alpha=0.5)
            ax.set_xlabel("Time (hours)")
            ax.set_ylabel("Δ " + label)
            ax.set_title(label)
            ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
            print(f"Residuals plot saved: {save_path}")
        else:
            plt.show()

    @staticmethod
    def _highlight_degradation(ax, degradation_hours: Optional[Tuple[float, float]]):
        """Add shaded region to highlight degradation period."""
        if degradation_hours:
            start_h, end_h = degradation_hours
            ax.axvspan(start_h, end_h, alpha=0.1, color="red", label="Degraded period")


if __name__ == "__main__":
    from simulator.power import PowerSimulator

    # Generate test data
    sim = PowerSimulator(duration_hours=24)
    nominal = sim.run_nominal()
    degraded = sim.run_degraded(
        solar_degradation_hour=6.0,
        battery_degradation_hour=8.0,
    )

    # Plot
    plotter = TelemetryPlotter()
    plotter.plot_comparison(
        nominal, degraded, degradation_hours=(6, 24), save_path="/tmp/comparison.png"
    )
    plotter.plot_residuals(nominal, degraded, save_path="/tmp/residuals.png")
