//! Error types for the framework

use thiserror::Error;

pub type Result<T> = std::result::Result<T, Error>;

#[derive(Error, Debug)]
pub enum Error {
    #[error("Invalid measurement: {0}")]
    InvalidMeasurement(String),

    #[error("Out of range: {0} (expected {1} to {2})")]
    OutOfRange(String, f64, f64),

    #[error("Dropout detected: gap of {0} seconds")]
    DropoutDetected(f64),

    #[error("Matrix error: {0}")]
    MatrixError(String),

    #[error("Kalman filter divergence: covariance trace = {0}")]
    FilterDivergence(f64),

    #[error("Physics model error: {0}")]
    PhysicsError(String),

    #[error("Serialization error: {0}")]
    SerializationError(String),

    #[error("Stream processing error: {0}")]
    StreamError(String),

    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("JSON error: {0}")]
    JsonError(#[from] serde_json::error::Error),
}
