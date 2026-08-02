from fastapi import FastAPI

from .healthcheck.router import router as healthcheck_router
from .product_review.router import router as product_review_router

app = FastAPI(
    title="Product review feedback analysis API",
)

app.include_router(healthcheck_router)
app.include_router(product_review_router)
