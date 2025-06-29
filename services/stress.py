def compute_stress(sensor: dict) -> float:
    rage = sensor.get("rage_probability", 0) / 100
    hr = sensor.get("heart_rate") or sensor.get("heart_rate_bpm") or 0
    return min(1.0, 0.6 * rage + 0.4 * max(0, hr - 75) / 40)