from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import database
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Bet(BaseModel):
    username: str
    date_key: str
    number: int
    amount: int

class BreakLimit(BaseModel):
    date_key: str
    limit_amount: int

class PowerNumber(BaseModel):
    date_key: str
    power_number: int

class UserComZa(BaseModel):
    username: str
    com: int
    za: int

# API Endpoints

@app.get("/bets/", response_model=List[Bet])
async def get_bets(username: Optional[str] = None, date_key: Optional[str] = None):
    return await database.get_user_bets(username, date_key)

@app.post("/bets/")
async def create_bet(bet: Bet):
    await database.save_user_bet(bet.username, bet.date_key, bet.number, bet.amount)
    return {"message": "Bet saved successfully"}

@app.delete("/bets/")
async def delete_bet(bet: Bet):
    success = await database.delete_user_bet(bet.username, bet.date_key, bet.number, bet.amount)
    if not success:
        raise HTTPException(status_code=404, detail="Bet not found")
    return {"message": "Bet deleted successfully"}

@app.get("/break-limits/{date_key}", response_model=BreakLimit)
async def get_break_limit(date_key: str):
    limit = await database.get_break_limit(date_key)
    if limit is None:
        raise HTTPException(status_code=404, detail="Break limit not found")
    return {"date_key": date_key, "limit_amount": limit}

@app.post("/break-limits/")
async def set_break_limit(limit: BreakLimit):
    await database.save_break_limit(limit.date_key, limit.limit_amount)
    return {"message": "Break limit set successfully"}

@app.get("/power-numbers/{date_key}", response_model=PowerNumber)
async def get_power_number(date_key: str):
    pnum = await database.get_power_number(date_key)
    if pnum is None:
        raise HTTPException(status_code=404, detail="Power number not found")
    return {"date_key": date_key, "power_number": pnum}

@app.post("/power-numbers/")
async def set_power_number(pnum: PowerNumber):
    await database.save_power_number(pnum.date_key, pnum.power_number)
    return {"message": "Power number set successfully"}

@app.get("/users/", response_model=List[UserComZa])
async def get_all_users():
    users = await database.get_all_users()
    return [{"username": u, "com": c, "za": z} for u, (c, z) in [(user, await database.get_user_com_za(user)) for user in users]]

@app.post("/users/")
async def create_or_update_user(user: UserComZa):
    await database.save_user_com_za(user.username, user.com, user.za)
    return {"message": "User data saved successfully"}

@app.get("/dates/")
async def get_available_dates():
    return await database.get_available_dates()

@app.delete("/dates/{date_key}")
async def delete_date_data(date_key: str):
    await database.delete_date_data(date_key)
    return {"message": f"Data for {date_key} deleted successfully"}
