import asyncio
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- Database Setup (SQLite for simplicity) ---
# check_same_thread=False is needed for SQLite to handle concurrent requests in this demo
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- The Model ---
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    stock = Column(Integer, default=0)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Startup & Reset ---
@app.on_event("startup")
def startup_event():
    """Initialize DB with 1 item"""
    db = SessionLocal()
    db.query(Item).delete()
    db.add(Item(id=1, name="Limited Edition GPU", stock=1)) 
    db.commit()
    db.close()

@app.get("/reset")
def reset_db(db: Session = Depends(get_db)):
    """Reset stock to 1 for testing"""
    item = db.query(Item).filter(Item.id == 1).first()
    item.stock = 1
    db.commit()
    return {"message": "Stock reset to 1"}

@app.get("/status")
def get_status(db: Session = Depends(get_db)):
    """Check current stock level - useful for seeing the damage"""
    item = db.query(Item).filter(Item.id == 1).first()
    return {"item": item.name, "stock": item.stock}

# 🚨 VULNERABLE ENDPOINT 🚨
@app.post("/buy-vulnerable")
async def buy_vulnerable(db: Session = Depends(get_db)):
    # 1. READ (Time of Check)
    item = db.query(Item).filter(Item.id == 1).first()
    
    if item.stock > 0:
        # Simulate latency (e.g., payment processing, network lag)
        # This gap allows other requests to read the same 'stock > 0' state
        await asyncio.sleep(0.1) 
        
        # 2. WRITE (Time of Use)
        item.stock -= 1
        db.commit()
        return {"status": "success", "message": "Item purchased!"}
    
    return {"status": "fail", "message": "Out of stock"}

# ✅ SECURE ENDPOINT (Atomic Update) ✅
@app.post("/buy-secure")
def buy_secure(db: Session = Depends(get_db)):
    """
    Method 1: Atomic Update
    Instead of calculating in Python, we let the DB handle the logic.
    The WHERE clause ensures the stock is still > 0 at the exact moment of update.
    """
    rows_affected = db.query(Item).filter(Item.id == 1, Item.stock > 0).update(
        {Item.stock: Item.stock - 1}
    )
    db.commit()

    if rows_affected > 0:
        return {"status": "success", "message": "Item purchased!"}
    
    return {"status": "fail", "message": "Out of stock"}

# ✅ SECURE ENDPOINT (Row Locking - Concept) ✅
@app.post("/buy-secure-lock")
def buy_secure_lock(db: Session = Depends(get_db)):
    """
    Method 2: Pessimistic Locking (SELECT FOR UPDATE)
    
    NOTE: SQLite does not support standard row-level locking (SELECT FOR UPDATE) 
    the way Postgres/MySQL do. In a real production environment (Postgres), 
    the code would look like this:
    
    try:
        item = db.query(Item).filter(Item.id == 1).with_for_update().first()
        if item.stock > 0:
            item.stock -= 1
            db.commit()
            return {"status": "success"}
    except:
        db.rollback()
        
    For this demo, we return a message explaining this.
    """
    return {
        "status": "info", 
        "message": "This requires PostgreSQL. See code comments for the implementation."
    }