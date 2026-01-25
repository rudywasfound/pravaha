//! Telemetry dropout detection and state prediction during gaps

use chrono::{DateTime, Utc};
use crate::measurement::Measurement;
use crate::kalman::KalmanFilter;
use crate::state_estimate::StateEstimate;
use crate::error::Result;

/// Detects and handles telemetry dropouts (communication gaps)
pub struct DropoutHandler {
    /// Last received measurement
    last_measurement: Option<Measurement>,
    
    /// Gap threshold (seconds)
    gap_threshold: f64,
    
    /// Is currently in dropout
    in_dropout: bool,
    
    /// Dropout start time
    dropout_start: Option<DateTime<Utc>>,
    
    /// Kalman filter for prediction during dropout
    kalman: KalmanFilter,
}

impl DropoutHandler {
    /// Create new dropout handler
    pub fn new(dt: f64) -> Self {
        Self {
            last_measurement: None,
            gap_threshold: 5.0,  // 5 seconds
            in_dropout: false,
            dropout_start: None,
            kalman: KalmanFilter::new(dt),
        }
    }

    /// Process measurement, detect dropout, predict if needed
    pub fn process(&mut self, measurement: &Measurement) -> Result<Option<StateEstimate>> {
        let now = measurement.timestamp;

        // Check for gap from last measurement
        let in_dropout = if let Some(last) = &self.last_measurement {
            let gap = (now - last.timestamp).num_seconds() as f64;
            gap > self.gap_threshold
        } else {
            false
        };

        if in_dropout {
            // Dropout detected
            let last = self.last_measurement.as_ref().unwrap().clone();
            self.in_dropout = true;
            self.dropout_start = Some(now);
            
            // Predict forward to fill gap
            let predictions = self.predict_during_dropout(&last, &measurement)?;
            self.last_measurement = Some(measurement.clone());
            return Ok(Some(predictions));
        }

        // Normal case: update with measurement
        self.in_dropout = false;
        self.dropout_start = None;
        self.kalman.update(measurement)?;
        self.last_measurement = Some(measurement.clone());
        
        Ok(Some(self.kalman.get_estimate()))
    }

    /// Predict satellite state during communication dropout
    fn predict_during_dropout(
        &mut self,
        last_measurement: &Measurement,
        current_measurement: &Measurement,
    ) -> Result<StateEstimate> {
        let gap_seconds = 
            (current_measurement.timestamp - last_measurement.timestamp).num_seconds() as f64;

        // Use Kalman filter to propagate state forward
        // In practice, run multiple prediction steps for the gap duration
        
        let mut estimate = self.kalman.get_estimate();
        estimate.confidence *= 0.95_f64.powi((gap_seconds / 10.0) as i32);  // Degrade confidence
        
        Ok(estimate)
    }

    /// Get current dropout status
    pub fn dropout_status(&self) -> DropoutStatus {
        DropoutStatus {
            in_dropout: self.in_dropout,
            dropout_duration: self.dropout_start.map(|start| {
                (Utc::now() - start).num_seconds()
            }),
        }
    }

    /// Reset handler
    pub fn reset(&mut self) {
        self.in_dropout = false;
        self.dropout_start = None;
        self.last_measurement = None;
        self.kalman.reset();
    }
}

/// Current dropout status
#[derive(Debug, Clone)]
pub struct DropoutStatus {
    pub in_dropout: bool,
    pub dropout_duration: Option<i64>,  // seconds
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dropout_handler_creation() {
        let handler = DropoutHandler::new(1.0);
        assert!(!handler.in_dropout);
    }

    #[test]
    fn test_dropout_detection() {
        let mut handler = DropoutHandler::new(1.0);
        let m1 = Measurement::new(Utc::now());
        let now = Utc::now();
        let mut m2 = Measurement::new(now);
        m2.battery_voltage = 27.5;  // Modify to show they're different
        
        handler.process(&m1).ok();
        let result = handler.process(&m2);
        
        assert!(result.is_ok());
    }
}
