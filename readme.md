# FastAPI Race Condition Demo

> Security scanners catch XSS and SQLi. They often miss race conditions.

This repo demonstrates a **Time-of-Check to Time-of-Use (TOCTOU)** vulnerability in a simulated e-commerce inventory system—and how to fix it using FastAPI and SQLAlchemy.

---

## The Scenario

| Condition | Details |
|-----------|---------|
| **Inventory** | 1 Limited Edition GPU |
| **Traffic** | 10 users click "Buy" at the exact same millisecond |
| **Vulnerable Endpoint** | Sells 10 GPUs (Overselling by 9) |
| **Secure Endpoint** | Sells 1 GPU, rejects 9 |

---

## Why This Matters

Race conditions are **business logic vulnerabilities**. In production, they cause:

- 📦 Inventory overselling
- 💸 Double-spend in payment systems
- 💰 Negative balances in wallets
- 🗃️ Data corruption

---

## The Fix

The vulnerability exists because we check the stock in Python application memory, wait (network latency), and then write to the database.

### ❌ Vulnerable Code (Check-then-Act)

```python
# Two separate DB operations. Not atomic.
if item.stock > 0:
    # A context switch here allows other threads to enter
    item.stock -= 1
    db.commit()
```

### ✅ Secure Code (Atomic Update)

We move the logic to the database layer. The database ensures atomicity.

```python
# One operation. The DB handles the lock.
db.query(Item).filter(Item.id == 1, Item.stock > 0).update(
    {Item.stock: Item.stock - 1}
)
```

---

## How to Run

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
uvicorn main:app --reload
```

### 3. Run the Attack Script (In a new terminal)

```bash
python attack.py
```

---

## Results

Below is the actual console output from the attack script. Notice how the vulnerable endpoint allows 10 successful purchases despite only having 1 item in stock.

```
════════════════════════════════════
⚔️  ATTACKING ENDPOINT: buy-vulnerable
════════════════════════════════════
📉 Starting Stock: 1
🚀 Firing 10 concurrent requests...
📊 Results:
   - Successful 'Buys': 10 (Expected: 1)
   - Final Stock Count: 0

❌ RACE CONDITION DETECTED!
   FAILURE: We sold 10 items but only had 1 in stock.
   (Type: Lost Update - Everyone read '1' and wrote '0')

════════════════════════════════════
⚔️  ATTACKING ENDPOINT: buy-secure
════════════════════════════════════
📉 Starting Stock: 1
🚀 Firing 10 concurrent requests...
📊 Results:
   - Successful 'Buys': 1 (Expected: 1)
   - Final Stock Count: 0

✅ SECURE.
   We correctly sold 1 item.
   Inventory is safe.
```

---

## Tech Stack

- **FastAPI** — Modern Python web framework
- **SQLAlchemy** — ORM with atomic update support
- **SQLite** — Lightweight database for demo
- **asyncio** — Concurrent request simulation

---

## About

Built by **Christopher Heintzelman** to demonstrate the intersection of Backend Engineering and Application Security.
