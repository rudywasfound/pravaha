//! Python FFI bindings using PyO3
//!
//! Exposes Rust framework to Python as native extension module

#[cfg(feature = "python")]
use pyo3::prelude::*;
use crate::{Measurement, KalmanFilter, ExtendedKalmanFilter, DropoutHandler};

#[cfg(feature = "python")]
#[pyclass]
pub struct PyMeasurement {
    inner: Measurement,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyMeasurement {
    #[new]
    fn new() -> Self {
        Self {
            inner: Measurement::new(chrono::Utc::now()),
        }
    }

    #[getter]
    fn battery_voltage(&self) -> f64 {
        self.inner.battery_voltage
    }

    #[setter]
    fn set_battery_voltage(&mut self, value: f64) {
        self.inner.battery_voltage = value;
    }

    #[getter]
    fn battery_charge(&self) -> f64 {
        self.inner.battery_charge
    }

    #[setter]
    fn set_battery_charge(&mut self, value: f64) {
        self.inner.battery_charge = value;
    }

    fn to_json(&self) -> PyResult<String> {
        self.inner.to_json()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }
}

#[cfg(feature = "python")]
#[pyclass]
pub struct PyKalmanFilter {
    inner: KalmanFilter,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyKalmanFilter {
    #[new]
    fn new(dt: f64) -> Self {
        Self {
            inner: KalmanFilter::new(dt),
        }
    }

    fn update(&mut self, measurement: &PyMeasurement) -> PyResult<()> {
        self.inner.update(&measurement.inner)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }

    fn get_estimate(&self) -> PyResult<String> {
        let est = self.inner.get_estimate();
        Ok(est.to_json())
    }

    fn reset(&mut self) {
        self.inner.reset();
    }
}

#[cfg(feature = "python")]
#[pyclass]
pub struct PyDropoutHandler {
    inner: DropoutHandler,
}

#[cfg(feature = "python")]
#[pymethods]
impl PyDropoutHandler {
    #[new]
    fn new(dt: f64) -> Self {
        Self {
            inner: DropoutHandler::new(dt),
        }
    }

    fn process(&mut self, measurement: &PyMeasurement) -> PyResult<Option<String>> {
        let result = self.inner.process(&measurement.inner)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        
        Ok(result.map(|est| est.to_json()))
    }

    fn reset(&mut self) {
        self.inner.reset();
    }
}

#[cfg(feature = "python")]
#[pymodule]
fn pravaha_core(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyMeasurement>()?;
    m.add_class::<PyKalmanFilter>()?;
    m.add_class::<PyDropoutHandler>()?;
    
    m.add("__version__", crate::VERSION)?;
    
    Ok(())
}
