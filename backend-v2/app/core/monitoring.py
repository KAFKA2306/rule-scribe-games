"""
Monitoring and metrics setup
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import FastAPI, Response
import time
import structlog

logger = structlog.get_logger()

# Metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
active_connections = Gauge('websocket_connections_active', 'Active WebSocket connections')
ai_requests = Counter('ai_requests_total', 'Total AI requests', ['provider', 'task_type'])
ai_errors = Counter('ai_errors_total', 'Total AI errors', ['provider'])


def setup_monitoring(app: FastAPI):
    """Setup monitoring endpoints and middleware"""
    
    @app.middleware("http")
    async def add_metrics_middleware(request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        # Record metrics
        process_time = time.time() - start_time
        request_count.labels(method=request.method, endpoint=request.url.path).inc()
        request_duration.observe(process_time)
        
        return response
    
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(generate_latest(), media_type="text/plain")
    
    logger.info("Monitoring setup complete")