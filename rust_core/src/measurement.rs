//! Satellite telemetry measurement types

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use crate::error::{Error, Result};

/// A single telemetry measurement from satellite
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Measurement {
    pub timestamp: DateTime<Utc>,
    
    /// Battery voltage (Volts) [20-35V]
    pub battery_voltage: f64,
    
    /// Battery charge (Ah) [40-105Ah]
    pub battery_charge: f64,
    
    /// Battery temperature (Celsius) [0-80°C]
    pub battery_temp: f64,
    
    /// Bus voltage (Volts) [25-32V]
    pub bus_voltage: f64,
    
    /// Bus current (Amps) [0-50A]
    pub bus_current: f64,
    
    /// Solar input power (Watts) [0-500W]
    pub solar_input: f64,
    
    /// Solar panel temperature (Celsius) [20-100°C]
    pub solar_panel_temp: f64,
    
    /// Payload temperature (Celsius) [0-80°C]
    pub payload_temp: f64,
    
    /// Measurement quality score [0-1]
    #[serde(default = "default_quality")]
    pub quality: f64,
}

fn default_quality() -> f64 {
    1.0
}

impl Measurement {
    /// Create new measurement
    pub fn new(timestamp: DateTime<Utc>) -> Self {
        Self {
            timestamp,
            battery_voltage: 28.0,
            battery_charge: 95.0,
            battery_temp: 35.0,
            bus_voltage: 29.0,
            bus_current: 15.0,
            solar_input: 400.0,
            solar_panel_temp: 45.0,
            payload_temp: 38.0,
            quality: 1.0,
        }
    }

    /// Parse from JSON
    pub fn from_json(json: &str) -> Result<Self> {
        serde_json::from_str(json)
            .map_err(|e| Error::JsonError(e))
    }

    /// Serialize to JSON
    pub fn to_json(&self) -> Result<String> {
        serde_json::to_string(self)
            .map_err(|e| Error::JsonError(e))
    }
}

/// Validates measurement values are in acceptable ranges
pub struct MeasurementValidator {
    battery_voltage_range: (f64, f64),
    battery_charge_range: (f64, f64),
    battery_temp_range: (f64, f64),
    bus_voltage_range: (f64, f64),
    bus_current_range: (f64, f64),
    solar_input_range: (f64, f64),
    solar_panel_temp_range: (f64, f64),
    payload_temp_range: (f64, f64),
}

impl Default for MeasurementValidator {
    fn default() -> Self {
        Self {
            battery_voltage_range: (20.0, 35.0),
            battery_charge_range: (40.0, 105.0),
            battery_temp_range: (0.0, 80.0),
            bus_voltage_range: (25.0, 32.0),
            bus_current_range: (0.0, 50.0),
            solar_input_range: (0.0, 500.0),
            solar_panel_temp_range: (20.0, 100.0),
            payload_temp_range: (0.0, 80.0),
        }
    }
}

impl MeasurementValidator {
    pub fn validate(&self, m: &Measurement) -> Result<()> {
        self.check_range("battery_voltage", m.battery_voltage, self.battery_voltage_range)?;
        self.check_range("battery_charge", m.battery_charge, self.battery_charge_range)?;
        self.check_range("battery_temp", m.battery_temp, self.battery_temp_range)?;
        self.check_range("bus_voltage", m.bus_voltage, self.bus_voltage_range)?;
        self.check_range("bus_current", m.bus_current, self.bus_current_range)?;
        self.check_range("solar_input", m.solar_input, self.solar_input_range)?;
        self.check_range("solar_panel_temp", m.solar_panel_temp, self.solar_panel_temp_range)?;
        self.check_range("payload_temp", m.payload_temp, self.payload_temp_range)?;

        if m.quality < 0.0 || m.quality > 1.0 {
            return Err(Error::OutOfRange("quality".to_string(), 0.0, 1.0));
        }

        Ok(())
    }

    fn check_range(&self, name: &str, value: f64, (min, max): (f64, f64)) -> Result<()> {
        if value < min || value > max {
            Err(Error::OutOfRange(name.to_string(), min, max))
        } else {
            Ok(())
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_measurement_creation() {
        let m = Measurement::new(Utc::now());
        assert_eq!(m.battery_voltage, 28.0);
        assert_eq!(m.quality, 1.0);
    }

    #[test]
    fn test_measurement_validation() {
        let m = Measurement::new(Utc::now());
        let validator = MeasurementValidator::default();
        assert!(validator.validate(&m).is_ok());
    }

    #[test]
    fn test_measurement_json() {
        let m = Measurement::new(Utc::now());
        let json = m.to_json().unwrap();
        let m2 = Measurement::from_json(&json).unwrap();
        assert_eq!(m.battery_voltage, m2.battery_voltage);
    }
}
