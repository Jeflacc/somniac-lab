import os
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
import models
from dotenv import load_dotenv

load_dotenv()

payments_router = APIRouter()

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")
# Use 'https://api-m.sandbox.paypal.com' for testing or 'https://api-m.paypal.com' for live
PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com" if "sandbox" in (PAYPAL_CLIENT_ID or "").lower() else "https://api-m.paypal.com"
# Actually, the user provided keys look like live or sandbox. I'll default to sandbox if not sure, but the user provided specific keys.
# Let's assume sandbox for now unless they say live.
PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com" 

async def get_paypal_access_token():
    url = f"{PAYPAL_BASE_URL}/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
    }
    data = {"grant_type": "client_credentials"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url, 
            auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET), 
            data=data, 
            headers=headers
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Could not authenticate with PayPal")
        return resp.json()["access_token"]

@payments_router.post("/paypal/capture/{order_id}")
async def capture_paypal_order(order_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    token = await get_paypal_access_token()
    url = f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers)
        data = resp.json()
        
        if resp.status_code == 201 and data.get("status") == "COMPLETED":
            # Upgrade user to Pro
            current_user.is_pro = True
            db.commit()
            return {"status": "success", "message": "Upgraded to Somniac Pro!"}
        else:
            raise HTTPException(status_code=400, detail=f"Payment capture failed: {data.get('message', 'Unknown error')}")
