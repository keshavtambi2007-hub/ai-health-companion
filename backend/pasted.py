from fastapi import FastAPI, UploadFile, File, Request
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests
import random

app = FastAPI(title="Zero-Friction AI Health Companion")

# -----------------------------
# CONFIG
# -----------------------------
AQI_API_KEY = "demo_key"  # Replace with real API key
AQI_URL = f"https://api.waqi.info/feed/here/?token={AQI_API_KEY}"

# -----------------------------
# GLOBAL USER STATE (SIMULATION)
# -----------------------------
user_state: Dict[str, Any] = {
    "last_active": None,
    "activity_log": [],
    "food_log": []
}


# -----------------------------
# ACTIVITY TRACKING
# -----------------------------
def track_activity() -> None:
    """Track user activity timestamps (last 24 hours only)."""
    now = datetime.now()

    user_state["last_active"] = now
    user_state["activity_log"].append(now)

    # Keep only last 24 hours
    user_state["activity_log"] = [
        t for t in user_state["activity_log"]
        if now - t < timedelta(hours=24)
    ]


# -----------------------------
# FOOD SERVICE (MOCK AI ONLY)
# -----------------------------
def analyze_food(file: UploadFile) -> Dict[str, Any]:
    """Mock food analysis (AI integration later)."""
    food_data = {
        "food_items": ["dal", "rice"],
        "calories": 450,
        "oil": random.choice(["low", "medium", "high"]),
        "score": round(random.uniform(6, 9), 2)
    }

    user_state["food_log"].append({
        "time": datetime.now(),
        "food": food_data
    })

    return food_data


# -----------------------------
# AQI SERVICE (REAL API)
# -----------------------------
def get_aqi() -> int:
    """Fetch real-time AQI."""
    try:
        response = requests.get(AQI_URL, timeout=5)
        data = response.json()
        return data["data"]["aqi"]
    except Exception:
        return 120  # fallback


# -----------------------------
# SLEEP INFERENCE
# -----------------------------
def infer_sleep() -> float:
    """Infer sleep duration based on activity gaps."""
    logs: List[datetime] = user_state["activity_log"]

    if len(logs) < 2:
        return 6.0  # default assumption

    gaps = [
        (logs[i] - logs[i - 1]).total_seconds() / 3600
        for i in range(1, len(logs))
    ]

    longest_gap = max(gaps) if gaps else 6.0
    return round(longest_gap, 2)


# -----------------------------
# SCREEN TIME INFERENCE
# -----------------------------
def infer_screen_time() -> float:
    """Estimate screen time from activity frequency."""
    logs = user_state["activity_log"]
    return min(len(logs) * 0.5, 12.0)


# -----------------------------
# MEAL ANALYSIS
# -----------------------------
def analyze_meals() -> (int, List[str]):
    """Check meal patterns and detect skipped meals."""
    today = datetime.now().date()

    meals_today = [
        entry for entry in user_state["food_log"]
        if entry["time"].date() == today
    ]

    count = len(meals_today)
    warnings: List[str] = []
    current_hour = datetime.now().hour

    if current_hour > 9 and count < 1:
        warnings.append("Skipped breakfast")

    if current_hour > 14 and count < 2:
        warnings.append("Skipped lunch")

    if current_hour > 21 and count < 3:
        warnings.append("Skipped dinner")

    return count, warnings


# -----------------------------
# STRESS ANALYSIS
# -----------------------------
def analyze_stress(screen_time: float, sleep: float) -> Dict[str, Any]:
    """Calculate stress level based on inferred metrics."""
    score = 0
    factors: List[str] = []

    if screen_time > 8:
        score += 3
        factors.append("High screen usage")

    if sleep < 6:
        score += 4
        factors.append("Poor sleep")

    if screen_time > 10 and sleep < 5:
        score += 2
        factors.append("Burnout risk")

    if score >= 7:
        level = "High"
    elif score >= 4:
        level = "Moderate"
    else:
        level = "Low"

    return {
        "score": score,
        "level": level,
        "factors": factors
    }


# -----------------------------
# HEALTH SCORE
# -----------------------------
def calculate_health(
    food_score: float,
    sleep: float,
    stress_score: int,
    aqi: int
) -> (float, str):
    """Compute overall health score."""
    nutrition = food_score * 10
    sleep_score = min(100, sleep * 12)
    stress_val = max(0, 100 - stress_score * 10)
    environment = max(0, 100 - aqi)

    final_score = (
        nutrition * 0.3 +
        sleep_score * 0.3 +
        stress_val * 0.2 +
        environment * 0.2
    )

    if final_score > 75:
        status = "Good"
    elif final_score > 50:
        status = "Moderate"
    else:
        status = "Poor"

    return round(final_score, 2), status


# -----------------------------
# NUDGE ENGINE
# -----------------------------
def generate_nudges(
    aqi: int,
    sleep: float,
    screen: float,
    meal_warnings: List[str]
) -> List[str]:
    """Generate smart health nudges."""
    nudges: List[str] = []

    if aqi > 150:
        nudges.append("Avoid going outside, air quality is poor")

    if sleep < 6:
        nudges.append("You slept less, try resting earlier")

    if screen > 8:
        nudges.append("Reduce screen time to avoid stress")

    nudges.extend(meal_warnings)

    return nudges


# -----------------------------
# MIDDLEWARE
# -----------------------------
@app.middleware("http")
async def track_user_activity(request: Request, call_next):
    track_activity()
    response = await call_next(request)
    return response


# -----------------------------
# ROUTES
# -----------------------------
@app.get("/")
def home():
    return {"message": "Zero-Friction AI Health Backend Running 🚀"}


@app.post("/analyze-food")
async def food_endpoint(file: UploadFile = File(...)):
    return analyze_food(file)


@app.get("/analyze")
def analyze():
    """Main endpoint: zero-input health analysis."""

    aqi = get_aqi()
    sleep = infer_sleep()
    screen = infer_screen_time()

    meal_count, meal_warnings = analyze_meals()
    stress = analyze_stress(screen, sleep)

    food_score = (
        user_state["food_log"][-1]["food"]["score"]
        if user_state["food_log"] else 7.0
    )

    health_score, status = calculate_health(
        food_score,
        sleep,
        stress["score"],
        aqi
    )

    nudges = generate_nudges(aqi, sleep, screen, meal_warnings)

    return {
        "aqi": aqi,
        "sleep_hours_inferred": sleep,
        "screen_time_inferred": screen,
        "meals_today": meal_count,
        "stress": stress,
        "health_score": health_score,
        "status": status,
        "nudges": nudges
    }