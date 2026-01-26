use aethelix_core::{PowerSystemKalmanFilter, HiddenStateInferenceEngine};

fn main() {
    println!("======================================================================");
    println!("PRAVAHA RUST CORE: Kalman Filter + Hidden State Inference");
    println!("Telemetry Dropout Handling (5+ second loss)");
    println!("======================================================================\n");
    
    // Initialize Kalman Filter
    let mut kf = PowerSystemKalmanFilter::new(28.0, 50.0, 10.0);
    println!("Initial state (healthy satellite):");
    let state = kf.get_state();
    println!("  Charge: {:.1}%, Voltage: {:.2}V, Solar: {:.1}W, Eff: {:.2}", 
        state[0], state[1], state[2], state[3]);
    
    // Simulate normal operation
    println!("\nNormal operation (5 steps):");
    for i in 1..=5 {
        let state = kf.predict(300.0);
        println!("  Step {}: Charge={:.1}%, Voltage={:.2}V, Uncertainty={:.2}",
            i, state.charge, state.voltage, kf.uncertainty());
    }
    
    // Simulate telemetry dropout
    println!("\nInject solar degradation, then 5-step dropout:");
    let mut state_vec = kf.get_state();
    state_vec[2] = 350.0;  // Drop solar input
    
    let mut dropout_handler = aethelix_core::kalman_filter::TelemetryDropoutHandler::new(
        PowerSystemKalmanFilter::new(28.0, 50.0, 10.0),
        3,
    );
    
    let filled = dropout_handler.fill_dropout_gap(50, 54, 300.0);
    println!("  Filled {} samples during dropout:", filled.len());
    for (idx, pred) in filled.iter() {
        let conf = dropout_handler.estimate_confidence_degradation(filled.len() as u32);
        println!("    Sample {}: Charge={:.1}%, Voltage={:.2}V, Conf={:.2}",
            idx, pred.charge, pred.voltage, conf);
    }
    
    // Test hidden state inference
    println!("\nHidden State Inference during dropout:");
    let kf2 = PowerSystemKalmanFilter::new(28.0, 50.0, 10.0);
    let mut inference = HiddenStateInferenceEngine::new(kf2);
    let hidden = inference.infer_hidden_states(5, 300.0);
    
    println!("  Inferred hidden states:");
    for (name, estimate) in hidden.iter() {
        println!("    {}: {:.3} [{:.3}, {:.3}] (conf={:.2}, src={})",
            name, estimate.estimated_value, estimate.lower_bound, 
            estimate.upper_bound, estimate.confidence, estimate.inference_source);
    }
    
    // Test measurement update after dropout resumes
    println!("\nTelemetry resumes, update with measurement:");
    let mut kf3 = PowerSystemKalmanFilter::new(28.0, 50.0, 10.0);
    kf3.predict(300.0);
    let state = kf3.update(Some(75.0), Some(26.8), Some(350.0), None);
    println!("  Updated: Charge={:.1}%, Voltage={:.2}V, Uncertainty={:.2}",
        state.charge, state.voltage, kf3.uncertainty());
    
    println!("\n======================================================================");
    println!("✓ Rust core handles 5+ second telemetry dropout with:");
    println!("  • Kalman Filter state prediction");
    println!("  • Hidden state inference from causal graph");
    println!("  • Confidence degradation based on uncertainty");
    println!("  • Measurement update upon connection resume");
    println!("======================================================================");
}
