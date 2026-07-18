from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db
from app.models import Item
from app.schemas import HealthResponse, ItemCreate, ItemResponse

app = FastAPI(
    title="GreenCloud App API",
    version="0.1.0",
    docs_url="/docs",
)

# Create tables on startup
Base.metadata.create_all(bind=engine)


@app.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """Check API and database health."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        database=db_status,
        environment=settings.environment,
    )


@app.get("/api/v1/items", response_model=list[ItemResponse])
async def list_items(db: Session = Depends(get_db)) -> list[ItemResponse]:
    """List all items."""
    items = db.query(Item).order_by(Item.created_at.desc()).all()
    return items


@app.post("/api/v1/items", response_model=ItemResponse, status_code=201)
async def create_item(
    item: ItemCreate, db: Session = Depends(get_db)
) -> ItemResponse:
    """Create a new item."""
    db_item = Item(name=item.name, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.get("/api/v1/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int, db: Session = Depends(get_db)) -> ItemResponse:
    """Get a single item by ID."""
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.delete("/api/v1/items/{item_id}", status_code=204)
async def delete_item(item_id: int, db: Session = Depends(get_db)) -> None:
    """Delete an item by ID."""
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
