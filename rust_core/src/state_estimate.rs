//! State estimation output

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

/// Estimated satellite state (including hidden states)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StateEstimate {
    pub timestamp: DateTime<Utc>,
    
    /// Estimated battery charge (Ah)
    pub battery_charge: f64,
    
    /// Estimated battery voltage (V)
    pub battery_voltage: f64,
    
    /// Estimated solar input power (W)
    pub solar_input: f64,
    
    /// Estimated battery efficiency [0-1]
    pub battery_efficiency: f64,
    
    /// Estimated battery temperature (°C)
    pub battery_temp: f64,
    
    /// Confidence in estimate [0-1]
    pub confidence: f64,
    
    /// Covariance trace (uncertainty measure)
    pub covariance_trace: f64,
}

impl StateEstimate {
    /// Serialize to JSON
    pub fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap_or_default()
    }

    /// Check if confidence is sufficient
    pub fn is_reliable(&self) -> bool {
        self.confidence > 0.7 && self.covariance_trace < 100.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_state_estimate_json() {
        let est = StateEstimate {
            timestamp: Utc::now(),
            battery_charge: 95.0,
            battery_voltage: 28.0,
            solar_input: 400.0,
            battery_efficiency: 0.90,
            battery_temp: 35.0,
            confidence: 0.95,
            covariance_trace: 5.0,
        };
        
        let json = est.to_json();
        assert!(json.contains("battery_charge"));
    }
}
