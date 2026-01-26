//! CLI binary for Satellite Telemetry State Estimation Framework

use std::io::{self, BufRead};
use aethelix_core::{Measurement, KalmanFilter, MeasurementValidator};

fn main() {
    env_logger::init();
    
    println!("═══════════════════════════════════════════════════════════");
    println!("Satellite Telemetry State Estimation Framework v{}", aethelix_core::VERSION);
    println!("═══════════════════════════════════════════════════════════\n");

    let mut kalman = KalmanFilter::new(1.0);
    let validator = MeasurementValidator::default();
    
    println!("Reading telemetry from stdin (JSON format)");
    println!("Example: {{\"battery_voltage\": 28.5, \"battery_charge\": 95.0, ...}}\n");
    
    let stdin = io::stdin();
    let handle = stdin.lock();
    
    let mut count = 0;
    for line in handle.lines() {
        match line {
            Ok(json_line) => {
                if json_line.trim().is_empty() {
                    continue;
                }
                
                match Measurement::from_json(&json_line) {
                    Ok(measurement) => {
                        // Validate
                        match validator.validate(&measurement) {
                            Ok(_) => {
                                // Update Kalman filter
                                match kalman.update(&measurement) {
                                    Ok(_) => {
                                        let estimate = kalman.get_estimate();
                                        println!("[{}] {}", count, estimate.to_json());
                                        count += 1;
                                    }
                                    Err(e) => {
                                        eprintln!("Filter error: {}", e);
                                    }
                                }
                            }
                            Err(e) => {
                                eprintln!("Invalid measurement: {}", e);
                            }
                        }
                    }
                    Err(e) => {
                        eprintln!("JSON parse error: {}", e);
                    }
                }
            }
            Err(e) => {
                eprintln!("IO error: {}", e);
                break;
            }
        }
    }
    
    println!("\nProcessed {} measurements", count);
}
