/// Hidden State Inference for satellite causal graph during telemetry dropout.
///
/// When observables stop flowing (telemetry dropout), we can still infer intermediate
/// (unobservable) states using:
/// 1. Hidden Markov Model structure from the causal graph
/// 2. Kalman Filter predictions to maintain state continuity
/// 3. Backward inference to estimate what hidden states would produce observed changes
///
/// This enables the causal graph to reason about missing observations while maintaining
/// causal path consistency and confidence bounds.

use std::collections::HashMap;
use crate::kalman_filter::{PowerSystemKalmanFilter, KalmanState};

/// Estimate of hidden (intermediate) state during dropout
#[derive(Clone, Debug)]
pub struct HiddenStateEstimate {
    pub node_name: String,
    pub estimated_value: f64,    // Point estimate
    pub lower_bound: f64,         // 95% CI lower
    pub upper_bound: f64,         // 95% CI upper
    pub confidence: f64,          // 0-1, where 1 = full certainty
    pub inference_source: String, // "kalman", "backward", "hybrid"
    pub timestamp: u32,
}

impl HiddenStateEstimate {
    /// Create a new hidden state estimate
    pub fn new(
        node_name: &str,
        estimated_value: f64,
        confidence: f64,
        inference_source: &str,
    ) -> Self {
        let bounds_width = (1.0 - confidence) * 0.2;
        Self {
            node_name: node_name.to_string(),
            estimated_value,
            lower_bound: (estimated_value - bounds_width).max(0.0),
            upper_bound: (estimated_value + bounds_width).min(1.0),
            confidence,
            inference_source: inference_source.to_string(),
            timestamp: 0,
        }
    }
}

/// Infers unobservable intermediate states from causal graph + Kalman predictions
pub struct HiddenStateInferenceEngine {
    kf: PowerSystemKalmanFilter,
}

impl HiddenStateInferenceEngine {
    /// Create inference engine
    pub fn new(kf: PowerSystemKalmanFilter) -> Self {
        Self { kf }
    }
    
    /// Infer hidden states during dropout using Kalman + causal graph
    ///
    /// Process:
    /// 1. Kalman Filter predicts observables forward
    /// 2. Map observables to intermediate nodes
    /// 3. Trace backward through causal paths to estimate root causes
    /// 4. Combine with path weights for confidence
    pub fn infer_hidden_states(
        &mut self,
        gap_duration_samples: u32,
        load_power: f64,
    ) -> HashMap<String, HiddenStateEstimate> {
        let mut estimates = HashMap::new();
        
        // Step 1: Kalman predictions over the gap
        let mut final_prediction = self.kf.predict(load_power);
        for _ in 1..gap_duration_samples {
            final_prediction = self.kf.predict(load_power);
        }
        
        // Step 2: Map Kalman state to intermediate nodes
        
        // battery_state is a composite of charge, voltage, efficiency
        let battery_state_estimate = self.estimate_battery_state(
            final_prediction.charge,
            final_prediction.voltage,
            final_prediction.efficiency,
            gap_duration_samples,
        );
        estimates.insert("battery_state".to_string(), battery_state_estimate);
        
        // solar_input is directly from Kalman
        let uncertainty = self.kf.uncertainty();
        let confidence = self.confidence_from_uncertainty(uncertainty);
        let solar_estimate = HiddenStateEstimate {
            node_name: "solar_input".to_string(),
            estimated_value: final_prediction.solar,
            lower_bound: (final_prediction.solar - 2.0 * uncertainty.sqrt()).max(0.0),
            upper_bound: (final_prediction.solar + 2.0 * uncertainty.sqrt()).min(600.0),
            confidence,
            inference_source: "kalman".to_string(),
            timestamp: 0,
        };
        estimates.insert("solar_input".to_string(), solar_estimate);
        
        // battery_efficiency is directly from Kalman
        let efficiency_estimate = HiddenStateEstimate {
            node_name: "battery_efficiency".to_string(),
            estimated_value: final_prediction.efficiency,
            lower_bound: (final_prediction.efficiency - 0.05).max(0.5),
            upper_bound: (final_prediction.efficiency + 0.05).min(1.0),
            confidence,
            inference_source: "kalman".to_string(),
            timestamp: 0,
        };
        estimates.insert("battery_efficiency".to_string(), efficiency_estimate);
        
        // Step 3: Backward inference for root causes
        let root_causes = self.backward_infer_root_causes(&estimates);
        estimates.extend(root_causes);
        
        estimates
    }
    
    /// Estimate battery_state (intermediate node) from Kalman outputs
    fn estimate_battery_state(
        &self,
        charge: f64,
        voltage: f64,
        efficiency: f64,
        gap_duration: u32,
    ) -> HiddenStateEstimate {
        // Composite battery_state metric
        let charge_component = charge / 100.0;           // Normalize to [0, 1]
        let voltage_component = voltage / 28.0;          // Normalize relative to nominal
        let efficiency_component = efficiency;            // Already in [0, 1]
        
        // Weighted average of health indicators
        let battery_state = 0.4 * charge_component 
            + 0.3 * voltage_component 
            + 0.3 * efficiency_component;
        let battery_state = battery_state.clamp(0.0, 1.0);
        
        // Confidence degrades with gap duration (exponential decay)
        let confidence = (-0.05 * gap_duration as f64).exp();
        
        HiddenStateEstimate::new("battery_state", battery_state, confidence, "kalman")
    }
    
    /// Use causal paths to infer root causes from intermediate estimates
    fn backward_infer_root_causes(
        &self,
        intermediate: &HashMap<String, HiddenStateEstimate>,
    ) -> HashMap<String, HiddenStateEstimate> {
        let mut root_estimates = HashMap::new();
        // If battery_state is degraded, likely battery_aging is active
        if let Some(battery_state) = intermediate.get("battery_state") {
            if battery_state.estimated_value < 0.7 {
                let degradation = 1.0 - battery_state.estimated_value;
                let confidence = battery_state.confidence * 0.8;  // Confidence degrades in backward pass
                
                let aging_estimate = HiddenStateEstimate {
                    node_name: "battery_aging".to_string(),
                    estimated_value: degradation,
                    lower_bound: (0.8 - battery_state.estimated_value).max(0.0),
                    upper_bound: (1.2 - battery_state.estimated_value).min(1.0),
                    confidence,
                    inference_source: "backward".to_string(),
                    timestamp: 0,
                };
                root_estimates.insert("battery_aging".to_string(), aging_estimate);
            }
        }
        
        // If solar_input is low, likely solar_degradation
        if let Some(solar) = intermediate.get("solar_input") {
            if solar.estimated_value < 300.0 {
                let degradation = 1.0 - (solar.estimated_value / 400.0).min(1.0);
                let confidence = solar.confidence * 0.8;
                
                let solar_degrad_estimate = HiddenStateEstimate {
                    node_name: "solar_degradation".to_string(),
                    estimated_value: degradation,
                    lower_bound: (1.0 - (solar.upper_bound / 400.0).min(1.0)).max(0.0),
                    upper_bound: (1.0 - (solar.lower_bound / 400.0).max(0.0)).min(1.0),
                    confidence,
                    inference_source: "backward".to_string(),
                    timestamp: 0,
                };
                root_estimates.insert("solar_degradation".to_string(), solar_degrad_estimate);
            }
        }
        
        root_estimates
    }
    
    /// Convert Kalman uncertainty to confidence score
    fn confidence_from_uncertainty(&self, uncertainty: f64) -> f64 {
        1.0 / (1.0 + uncertainty / 50.0)
    }
}

/// Wrapper that handles telemetry dropouts in the causal inference pipeline
pub struct DropoutAwareInference {
    inference: HiddenStateInferenceEngine,
}

impl DropoutAwareInference {
    /// Create dropout-aware inference
    pub fn new(kf: PowerSystemKalmanFilter) -> Self {
        Self {
            inference: HiddenStateInferenceEngine::new(kf),
        }
    }
    
    /// Detect gaps in sample indices (telemetry dropout)
    pub fn detect_gaps(sample_indices: &[u32]) -> Vec<(u32, u32)> {
        let mut gaps = Vec::new();
        
        for i in 0..sample_indices.len().saturating_sub(1) {
            let diff = sample_indices[i + 1].saturating_sub(sample_indices[i]);
            if diff > 1 {
                gaps.push((sample_indices[i], sample_indices[i + 1]));
            }
        }
        
        gaps
    }
    
    /// Analyze with automatic dropout detection and handling
    pub fn analyze_with_dropout_handling(
        &mut self,
        sample_indices: &[u32],
        load_power: f64,
    ) -> HashMap<String, HiddenStateEstimate> {
        let gaps = Self::detect_gaps(sample_indices);
        
        if gaps.is_empty() {
            return HashMap::new();
        }
        
        let mut all_estimates = HashMap::new();
        
        for (gap_start, gap_end) in gaps {
            let gap_duration = gap_end.saturating_sub(gap_start);
            
            let hidden = self.inference.infer_hidden_states(gap_duration, load_power);
            all_estimates.extend(hidden);
        }
        
        all_estimates
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::kalman_filter::PowerSystemKalmanFilter;
    
    #[test]
    fn test_hidden_state_inference() {
        let kf = PowerSystemKalmanFilter::new(28.0, 50.0, 10.0);
        let mut inference = HiddenStateInferenceEngine::new(kf);
        
        let estimates = inference.infer_hidden_states(5, 300.0);
        
        assert!(estimates.contains_key("battery_state"));
        assert!(estimates.contains_key("solar_input"));
        assert!(estimates.contains_key("battery_efficiency"));
    }
    
    #[test]
    fn test_gap_detection() {
        let sample_indices = vec![0, 1, 2, 3, 10, 11, 12];
        let gaps = DropoutAwareInference::detect_gaps(&sample_indices);
        
        assert_eq!(gaps.len(), 1);
        assert_eq!(gaps[0], (3, 10));
    }
    
    #[test]
    fn test_confidence_degradation() {
        let kf = PowerSystemKalmanFilter::new(28.0, 50.0, 10.0);
        let mut inference = HiddenStateInferenceEngine::new(kf);
        
        let short_gap = inference.infer_hidden_states(2, 300.0);
        let long_gap = inference.infer_hidden_states(10, 300.0);
        
        // Longer gap should have lower confidence
        let battery_state_short = short_gap.get("battery_state").unwrap();
        let battery_state_long = long_gap.get("battery_state").unwrap();
        
        assert!(battery_state_short.confidence > battery_state_long.confidence);
    }
}
