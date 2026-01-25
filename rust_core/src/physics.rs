//! Physics models for satellite power and thermal systems

use serde::{Deserialize, Serialize};

/// Power system physics model
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PowerModel {
    /// Battery capacity (Ah)
    pub battery_capacity: f64,
    
    /// Max discharge rate (A)
    pub max_discharge_current: f64,
    
    /// Max charge rate (A)
    pub max_charge_current: f64,
    
    /// Battery internal resistance (Ω)
    pub battery_resistance: f64,
    
    /// Solar panel area (m²)
    pub solar_panel_area: f64,
    
    /// Solar efficiency coefficient
    pub solar_efficiency: f64,
}

impl Default for PowerModel {
    fn default() -> Self {
        Self {
            battery_capacity: 100.0,      // 100 Ah
            max_discharge_current: 50.0,  // 50 A
            max_charge_current: 40.0,     // 40 A
            battery_resistance: 0.1,      // 0.1 Ω
            solar_panel_area: 2.5,        // 2.5 m²
            solar_efficiency: 0.25,       // 25% efficient
        }
    }
}

impl PowerModel {
    /// Calculate battery voltage from state of charge
    pub fn voltage_from_soc(&self, soc: f64) -> f64 {
        // V = V_nominal * (0.8 + 0.2 * SOC)
        28.0 * (0.8 + 0.2 * soc)
    }

    /// Calculate charge rate from solar input
    pub fn charge_rate(&self, solar_watts: f64, current_soc: f64) -> f64 {
        let available_current = self.max_charge_current * (1.0 - current_soc.min(1.0));
        (solar_watts / 28.0).min(available_current)
    }

    /// Calculate discharge rate from load
    pub fn discharge_rate(&self, load_watts: f64) -> f64 {
        (load_watts / 28.0).min(self.max_discharge_current)
    }

    /// Calculate rate of change of state of charge
    /// dSOC/dt = (charge_current - discharge_current) / capacity
    pub fn soc_derivative(
        &self,
        solar_input: f64,
        load_power: f64,
        current_soc: f64,
    ) -> f64 {
        let charge_current = self.charge_rate(solar_input, current_soc);
        let discharge_current = self.discharge_rate(load_power);
        (charge_current - discharge_current) / self.battery_capacity / 3600.0
    }
}

/// Thermal system physics model
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThermalModel {
    /// Solar panel absorptivity
    pub panel_absorptivity: f64,
    
    /// Panel radiator area (m²)
    pub panel_radiator_area: f64,
    
    /// Battery thermal time constant (seconds)
    pub battery_time_constant: f64,
    
    /// Ambient space temperature (K)
    pub space_temperature: f64,
    
    /// Stefan-Boltzmann constant
    pub stefan_boltzmann: f64,
}

impl Default for ThermalModel {
    fn default() -> Self {
        Self {
            panel_absorptivity: 0.9,
            panel_radiator_area: 2.5,
            battery_time_constant: 1800.0,  // 30 minutes
            space_temperature: 4.0,          // ~4K (cosmic background)
            stefan_boltzmann: 5.67e-8,       // W/(m²·K⁴)
        }
    }
}

impl ThermalModel {
    /// Calculate heat dissipation from radiator
    /// Q_rad = σ * A * ε * (T^4 - T_space^4)
    pub fn radiative_heat_loss(&self, temperature_k: f64) -> f64 {
        let t4 = temperature_k.powi(4);
        let t_space4 = self.space_temperature.powi(4);
        self.stefan_boltzmann * self.panel_radiator_area * 0.9 * (t4 - t_space4)
    }

    /// Temperature rate of change
    /// dT/dt = (Q_input - Q_loss) / (m * c)
    pub fn temperature_derivative(
        &self,
        current_temp_k: f64,
        heat_input_w: f64,
    ) -> f64 {
        let heat_loss = self.radiative_heat_loss(current_temp_k);
        let net_heat = heat_input_w - heat_loss;
        net_heat / self.battery_time_constant  // Simplified
    }
}

/// Complete satellite physics model
pub struct PhysicsModel {
    pub power: PowerModel,
    pub thermal: ThermalModel,
}

impl Default for PhysicsModel {
    fn default() -> Self {
        Self {
            power: PowerModel::default(),
            thermal: ThermalModel::default(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_power_model() {
        let model = PowerModel::default();
        let voltage = model.voltage_from_soc(0.95);
        assert!(voltage > 27.0 && voltage < 29.0);
    }

    #[test]
    fn test_thermal_model() {
        let model = ThermalModel::default();
        // Temperature in Kelvin (room temp)
        let heat_loss = model.radiative_heat_loss(300.0);
        assert!(heat_loss > 0.0);
    }
}
