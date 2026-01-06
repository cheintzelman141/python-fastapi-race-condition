# FastAPI Race Condition Demo

Security scanners catch XSS and SQLi. They often miss race conditions.

This repo demonstrates a **Time-of-Check to Time-of-Use (TOCTOU)** vulnerability in a simulated e-commerce inventory system—and how to fix it using FastAPI and SQLAlchemy.

## The Scenario
* **Inventory:** 1 Limited Edition GPU
* **Traffic:** 10 users click "Buy" at the exact same millisecond
* **Vulnerable Endpoint:** Sells 10 GPUs (Overselling by 9)
* **Secure Endpoint:** Sells 1 GPU, rejects 9

## Why This Matters
Race conditions are **business logic vulnerabilities**. In production, they cause:
* Inventory overselling
* Double-spend in payment systems
* Negative balances in wallets
* Data corruption

## The Fix
The vulnerability exists because we check the stock in Python application memory, wait (network latency), and then write to the database.

### Vulnerable Code (Check-then-Act)
```python
# ❌ Two separate DB operations. Not atomic.
if item.stock > 0:
    # A context switch here allows other threads to enter
    item.stock -= 1
    db.commit()# python-fastapi-race-condition
