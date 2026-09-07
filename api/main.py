import logging
import time
import uuid

from fastapi import FastAPI, Request

from .routes import health, processing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Conversational Intelligence API")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(f"request_id={request_id} method={request.method} endpoint={request.url.path}")
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logger.info(f"request_id={request_id} endpoint={request.url.path} status={response.status_code} duration={duration:.4f}s")
    
    return response

app.include_router(processing.router)
app.include_router(health.router)
