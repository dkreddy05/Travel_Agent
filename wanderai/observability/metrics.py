"""
wanderai/observability/metrics.py
Prometheus metrics definitions.
"""
try:
    from prometheus_flask_exporter import PrometheusMetrics
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

_metrics = None


def init_metrics(app):
    """Attach Prometheus metrics to the Flask app."""
    global _metrics
    if not PROMETHEUS_AVAILABLE:
        return None
    _metrics = PrometheusMetrics(app, path="/metrics")

    # Custom metrics
    _metrics.info("wanderai_app_info", "Application info", version=app.config.get("APP_VERSION", "2.0.0"))
    return _metrics


def get_metrics():
    return _metrics
