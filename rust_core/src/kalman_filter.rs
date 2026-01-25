/// Kalman Filter for satellite power system state estimation during telemetry dropout.
///
/// When the satellite loses connection for 5+ seconds, observable measurements stop flowing.
/// The Kalman Filter maintains estimates of hidden states (battery charge, voltage, solar input)
/// by:
/// 1. PREDICT: Using physics-based dynamics model to evolve state forward
/// 2. UPDATE: When telemetry resumes, correcting estimates with real measurements
///
/// State vector: [battery_charge, battery_voltage, solar_input, battery_efficiency]

use nalgebra::{Matrix4, Vector4};

/// State estimate with uncertainty covariance
#[derive(Clone, Debug)]
pub struct KalmanState {
    pub charge: f64,        // Battery charge (%)
    pub voltage: f64,       // Battery voltage (V)
    pub solar: f64,         // Solar input (W)
    pub efficiency: f64,    // Battery efficiency (0-1)
    pub timestamp: u32,     // Sample index when this state was estimated
}

/// Kalman Filter for power subsystem state estimation
pub struct PowerSystemKalmanFilter {
    // State vector
    x: Vector4<f64>,  // [charge, voltage, solar, efficiency]
    
    // Covariance matrix (4x4)
    p: Matrix4<f64>,
    
    // System dynamics (state transition matrix)
    f: Matrix4<f64>,
    
    // Process noise covariance
    q: Matrix4<f64>,
    
    // Measurement matrix
    h: Matrix4<f64>,
    
    // Measurement noise covariance
    r: Matrix4<f64>,
    
    // System parameters
    nominal_voltage: f64,
    nominal_capacity: f64,
    dt: f64,  // Time step in seconds
}

impl PowerSystemKalmanFilter {
    /// Initialize Kalman Filter with power system parameters
    pub fn new(nominal_voltage: f64, nominal_capacity: f64, dt: f64) -> Self {
        // Initial state (healthy satellite)
        let x = Vector4::new(80.0, nominal_voltage, 400.0, 1.0);
        
        // State transition matrix: mostly identity (slow dynamics)
        let mut f = Matrix4::identity();
        f[(0, 0)] = 0.99;  // Slight charge decay
        
        // Process noise (uncertainty in physics model)
        let q = Matrix4::from_diagonal(&Vector4::new(0.5, 0.3, 20.0, 0.02));
        
        // Measurement matrix (we measure all 4 states)
        let h = Matrix4::identity();
        
        // Measurement noise (sensor uncertainty)
        let r = Matrix4::from_diagonal(&Vector4::new(0.1, 0.2, 15.0, 0.01));
        
        // Initial covariance (high uncertainty)
        let p = Matrix4::from_diagonal(&Vector4::new(10.0, 2.0, 50.0, 0.1));
        
        Self {
            x,
            p,
            f,
            q,
            h,
            r,
            nominal_voltage,
            nominal_capacity,
            dt,
        }
    }
    
    /// Predict state forward one time step using physics-based model
    pub fn predict(&mut self, load_power: f64) -> KalmanState {
        let charge = self.x[0];
        let _voltage = self.x[1];
        let solar = self.x[2];
        let efficiency = self.x[3];
        
        // Power balance: dQ = (P_in - P_out) * dt / (capacity_Wh) * 100
        let power_in = solar * efficiency;
        let power_out = load_power;
        let dcharge = (power_in - power_out) * self.dt / (self.nominal_capacity * 3600.0) * 100.0;
        
        // Update charge, clipped to valid range
        let new_charge = (charge + dcharge).clamp(20.0, 100.0);
        
        // Voltage follows charge (linear SOC model)
        let soc_factor = 0.8 + 0.2 * (new_charge / 100.0);
        let new_voltage = self.nominal_voltage * soc_factor;
        
        // Solar input decays slightly (eclipse or natural variation)
        let new_solar = (solar * 0.98).clamp(0.0, 600.0);
        
        // Efficiency roughly constant with small drift
        let new_efficiency = (efficiency + 0.0).clamp(0.5, 1.0);
        
        // Update state
        self.x = Vector4::new(new_charge, new_voltage, new_solar, new_efficiency);
        
        // Covariance prediction: P = F*P*F^T + Q
        self.p = &self.f * &self.p * self.f.transpose() + &self.q;
        
        KalmanState {
            charge: new_charge,
            voltage: new_voltage,
            solar: new_solar,
            efficiency: new_efficiency,
            timestamp: 0,
        }
    }
    
    /// Update state estimate with new measurement(s)
    pub fn update(
        &mut self,
        z_charge: Option<f64>,
        z_voltage: Option<f64>,
        z_solar: Option<f64>,
        z_efficiency: Option<f64>,
    ) -> KalmanState {
        // Build measurement vector (use predicted if not provided)
        let z = Vector4::new(
            z_charge.unwrap_or(self.x[0]),
            z_voltage.unwrap_or(self.x[1]),
            z_solar.unwrap_or(self.x[2]),
            z_efficiency.unwrap_or(self.x[3]),
        );
        
        // Innovation (measurement residual): y = z - H*x
        let y = &z - &self.h * &self.x;
        
        // Innovation covariance: S = H*P*H^T + R
        let s = &self.h * &self.p * self.h.transpose() + &self.r;
        
        // Kalman gain: K = P*H^T*S^-1
        let s_inv = s.try_inverse()
            .expect("Failed to invert innovation covariance");
        let k = &self.p * self.h.transpose() * s_inv;
        
        // State update: x = x + K*y
        self.x = &self.x + &k * &y;
        
        // Clip to valid ranges
        self.x[0] = self.x[0].clamp(20.0, 100.0);    // Charge: 20-100%
        self.x[1] = self.x[1].clamp(20.0, 32.0);     // Voltage: 20-32V
        self.x[2] = self.x[2].clamp(0.0, 600.0);     // Solar: 0-600W
        self.x[3] = self.x[3].clamp(0.5, 1.0);       // Efficiency: 50-100%
        
        // Covariance update: P = (I - K*H)*P
        let i = Matrix4::<f64>::identity();
        self.p = (&i - &k * &self.h) * &self.p;
        
        KalmanState {
            charge: self.x[0],
            voltage: self.x[1],
            solar: self.x[2],
            efficiency: self.x[3],
            timestamp: 0,
        }
    }
    
    /// Get current state uncertainty (trace of covariance)
    pub fn uncertainty(&self) -> f64 {
        self.p.trace()
    }
    
    /// Get current state vector
    pub fn get_state(&self) -> [f64; 4] {
        [self.x[0], self.x[1], self.x[2], self.x[3]]
    }
}

/// Detects telemetry dropouts and fills gaps using Kalman prediction
pub struct TelemetryDropoutHandler {
    kf: PowerSystemKalmanFilter,
    dropout_threshold_samples: u32,
    last_valid_sample: u32,
    in_dropout: bool,
    dropout_start: u32,
}

impl TelemetryDropoutHandler {
    /// Initialize dropout handler
    pub fn new(kf: PowerSystemKalmanFilter, dropout_threshold_samples: u32) -> Self {
        Self {
            kf,
            dropout_threshold_samples,
            last_valid_sample: 0,
            in_dropout: false,
            dropout_start: 0,
        }
    }
    
    /// Check if we've entered a dropout based on sample gap
    pub fn check_dropout(&mut self, current_sample: u32) -> bool {
        let gap = current_sample.saturating_sub(self.last_valid_sample);
        
        if gap > self.dropout_threshold_samples {
            self.in_dropout = true;
            self.dropout_start = self.last_valid_sample;
            true
        } else {
            false
        }
    }
    
    /// Record sample index when telemetry resumed
    pub fn update_last_valid(&mut self, sample: u32) {
        self.last_valid_sample = sample;
        self.in_dropout = false;
    }
    
    /// Fill missing samples during dropout using Kalman predictions
    pub fn fill_dropout_gap(
        &mut self,
        gap_start: u32,
        gap_end: u32,
        load_power: f64,
    ) -> Vec<(u32, KalmanState)> {
        let mut filled_samples = Vec::new();
        
        for sample_idx in gap_start..=gap_end {
            let state = self.kf.predict(load_power);
            filled_samples.push((sample_idx, state));
        }
        
        filled_samples
    }
    
    /// Estimate confidence degradation during dropout
    /// Returns confidence factor in [0, 1]
    pub fn estimate_confidence_degradation(&self, gap_duration_samples: u32) -> f64 {
        // Exponential decay: each 10-sample gap reduces confidence by ~10%
        let prediction_decay = (-0.1 * gap_duration_samples as f64).exp();
        
        // Covariance-based uncertainty
        let uncertainty = self.kf.uncertainty();
        let covariance_factor = 1.0 / (1.0 + uncertainty / 100.0);
        
        prediction_decay * covariance_factor
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_kalman_predict() {
        let mut kf = PowerSystemKalmanFilter::new(28.0, 50.0, 10.0);
        let state = kf.predict(300.0);
        
        assert!(state.charge > 0.0);
        assert!(state.voltage > 0.0);
        assert!(state.solar > 0.0);
    }
    
    #[test]
    fn test_kalman_update() {
        let mut kf = PowerSystemKalmanFilter::new(28.0, 50.0, 10.0);
        kf.predict(300.0);
        let state = kf.update(Some(75.0), Some(26.8), Some(350.0), None);
        
        assert!((state.charge - 75.0).abs() < 5.0);
        assert!((state.voltage - 26.8).abs() < 1.0);
    }
    
    #[test]
    fn test_dropout_detection() {
        let kf = PowerSystemKalmanFilter::new(28.0, 50.0, 10.0);
        let mut handler = TelemetryDropoutHandler::new(kf, 5);
        
        handler.update_last_valid(10);
        assert!(!handler.check_dropout(11));
        assert!(handler.check_dropout(20));
    }
}
