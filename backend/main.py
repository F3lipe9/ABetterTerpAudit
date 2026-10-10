import logging
import os
from typing import List, Optional
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response
from pydantic import ConfigDict, BaseModel, EmailStr, Field, field_validator
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated
from fastapi.middleware.cors import CORSMiddleware

from bson import ObjectId
from pymongo import AsyncMongoClient
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv
import uuid
import bcrypt
import jwt
import secrets
import time
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from fastapi.concurrency import run_in_threadpool
from datetime import date as date_type, datetime, timedelta, timezone

load_dotenv()
logger = logging.getLogger("uvicorn.error")
MONGO_URL = os.getenv("MONGO_URL")

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    # No configured secret: use a per-process one. Tokens stop working on restart.
    print("WARNING: JWT_SECRET not set; using a random per-process secret")
    JWT_SECRET = secrets.token_urlsafe(48)
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
bearer_scheme = HTTPBearer(auto_error=False)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware FIRST before any routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",  
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
client = AsyncMongoClient(MONGO_URL)
db = client.habit_tracker_db

# Collections
users_collection = db.get_collection("users")
habits_collection = db.get_collection("habits")
affirmations_collection = db.get_collection("affirmations")
water_collection = db.get_collection("water_intake")
exercises_collection = db.get_collection("exercises")
exams_collection = db.get_collection("exams")
assignments_collection = db.get_collection("assignments")
courses_collection = db.get_collection("courses")

def parse_object_id(value: str) -> ObjectId:
    """Parse a path id, answering 400 for malformed input instead of failing later."""
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=400, detail="Invalid id")
    return ObjectId(value)

# Type for MongoDB ObjectId
PyObjectId = Annotated[str, BeforeValidator(str)]

# ---------------------------
# Models
# ---------------------------
class UserModel(BaseModel):
    id: PyObjectId | None = Field(alias="_id", default=None)
    username: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    model_config = ConfigDict(
        populate_by_name=True,
    )

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_.-]+$")
    email: EmailStr = Field(..., max_length=254)
    password: str = Field(..., min_length=8)

    @field_validator("username", mode="before")
    @classmethod
    def _strip_username(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("email", mode="after")
    @classmethod
    def _lower_email(cls, v):
        return v.lower()

    @field_validator("password")
    @classmethod
    def _password_fits_bcrypt(cls, v):
        if len(v.encode("utf-8")) > 72:  # bcrypt input limit
            raise ValueError("Password must be at most 72 bytes")
        if not v.strip():
            raise ValueError("Password cannot be blank")
        return v

class HabitModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str = Field(...)
    title: str = Field(..., min_length=1)
    description: str = Field(default="")

class HabitCreate(BaseModel):
    title: str
    description: str | None = ""

class AffirmationModel(BaseModel):
    id: PyObjectId | None = Field(alias="_id", default=None)
    text: str = Field(..., min_length=1)
    model_config = ConfigDict(
        populate_by_name=True,
    )

class AffirmationCreate(BaseModel):
    text: str

# Bounds shared by every water model
BOTTLE_NAME = dict(min_length=1, max_length=50)
BOTTLE_OZ = dict(ge=1, le=256)
DAILY_GOAL_OZ = dict(ge=1, le=1000)
CURRENT_OZ = dict(ge=0, le=10000)

class WaterIntakeModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str = Field(...)
    bottleName: str = Field(..., **BOTTLE_NAME)
    bottleOz: int = Field(..., **BOTTLE_OZ)
    dailyGoal: int = Field(..., **DAILY_GOAL_OZ)
    currentOz: int = Field(default=0, **CURRENT_OZ)

class WaterIntakeUpsert(BaseModel):
    bottleName: str = Field(..., **BOTTLE_NAME)
    bottleOz: int = Field(..., **BOTTLE_OZ)
    dailyGoal: int = Field(..., **DAILY_GOAL_OZ)
    currentOz: int = Field(default=0, **CURRENT_OZ)

class ExerciseModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str = Field(...)
    name: str = Field(..., min_length=1)
    muscle: str = Field(default="Other")
    equipment: str = Field(default="Other")
    compound: bool = Field(default=False)
    category: str = Field(default="Strength")  # "Strength" | "Cardio"
    createdByUser: bool = Field(default=True)

class ExerciseCreate(BaseModel):
    name: str
    muscle: str = "Other"
    equipment: str = "Other"
    compound: bool = False
    category: str = "Strength"

class ExerciseUpdate(BaseModel):
    name: Optional[str] = None
    muscle: Optional[str] = None
    equipment: Optional[str] = None
    compound: Optional[bool] = None
    category: Optional[str] = None

EXAM_MIN_YEAR, EXAM_MAX_YEAR = 2000, 2100

def validate_exam_date(v: str) -> str:
    """Accept only a real calendar date, YYYY-MM-DD, within a sane year range."""
    try:
        d = date_type.fromisoformat(v)
    except (TypeError, ValueError):
        raise ValueError("Date must be a valid YYYY-MM-DD date")
    if len(v) != 10 or not EXAM_MIN_YEAR <= d.year <= EXAM_MAX_YEAR:
        raise ValueError(f"Date must be YYYY-MM-DD with a year between {EXAM_MIN_YEAR} and {EXAM_MAX_YEAR}")
    return v

class ExamCreate(BaseModel):
    course: str = Field(..., min_length=1, max_length=100)
    date: str
    planned_hours: int = Field(..., ge=0, le=1000)

    _check_date = field_validator("date")(validate_exam_date)

# Assignment Models
class AssignmentBase(BaseModel):
    title: str
    course: str
    dueDate: str
    status: str = "pending"
    priority: str = "medium"
    type: str = "homework"
    points: str = "0"

class AssignmentCreate(AssignmentBase):
    pass

class Assignment(AssignmentBase):
    username: str = ""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class CourseBase(BaseModel):
    code: str
    name: str
    professor: str

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ExamUpdate(BaseModel):
    course: str | None = None
    date: str | None = None
    planned_hours: int | None = Field(default=None, ge=0, le=1000)
    score: int | None = None
    done: bool | None = None

    @field_validator("date")
    @classmethod
    def _check_date(cls, v):
        return v if v is None else validate_exam_date(v)

# ---------------------------
# Default Data
# ---------------------------
DEFAULT_STRENGTH_EXERCISES = [
    {"id": "bench", "name": "Barbell Bench Press", "muscle": "Chest", "equipment": "Barbell", "compound": True, "category": "Strength", "createdByUser": False},
    {"id": "squat", "name": "Back Squat", "muscle": "Legs", "equipment": "Barbell", "compound": True, "category": "Strength", "createdByUser": False},
    {"id": "deadlift", "name": "Deadlift", "muscle": "Legs", "equipment": "Barbell", "compound": True, "category": "Strength", "createdByUser": False},
    {"id": "ohp", "name": "Overhead Press", "muscle": "Shoulders", "equipment": "Barbell", "compound": True, "category": "Strength", "createdByUser": False},
    {"id": "row", "name": "Barbell Row", "muscle": "Back", "equipment": "Barbell", "compound": True, "category": "Strength", "createdByUser": False},
    {"id": "pullup", "name": "Pull-Ups", "muscle": "Back", "equipment": "Bodyweight", "compound": True, "category": "Strength", "createdByUser": False},
    {"id": "latpull", "name": "Lat Pulldown", "muscle": "Back", "equipment": "Cable", "compound": False, "category": "Strength", "createdByUser": False},
    {"id": "legpress", "name": "Leg Press", "muscle": "Legs", "equipment": "Machine", "compound": True, "category": "Strength", "createdByUser": False},
    {"id": "curl", "name": "Dumbbell Curl", "muscle": "Arms", "equipment": "Dumbbell", "compound": False, "category": "Strength", "createdByUser": False},
    {"id": "tricep", "name": "Triceps Pushdown", "muscle": "Arms", "equipment": "Cable", "compound": False, "category": "Strength", "createdByUser": False},
    {"id": "lateral", "name": "Lateral Raises", "muscle": "Shoulders", "equipment": "Dumbbell", "compound": False, "category": "Strength", "createdByUser": False},
]

DEFAULT_CARDIO_EXERCISES = [
    {"id": "tread", "name": "Treadmill Run", "muscle": "Cardio", "equipment": "Treadmill", "compound": False, "category": "Cardio", "createdByUser": False},
    {"id": "bike", "name": "Stationary Bike", "muscle": "Cardio", "equipment": "Bike", "compound": False, "category": "Cardio", "createdByUser": False},
    {"id": "rower", "name": "Rowing Machine", "muscle": "Cardio", "equipment": "Rower", "compound": False, "category": "Cardio", "createdByUser": False},
    {"id": "elliptical", "name": "Elliptical", "muscle": "Cardio", "equipment": "Elliptical", "compound": False, "category": "Cardio", "createdByUser": False},
    {"id": "stairs", "name": "Stair Climber", "muscle": "Cardio", "equipment": "Machine", "compound": False, "category": "Cardio", "createdByUser": False},
    {"id": "jumprope", "name": "Jump Rope", "muscle": "Cardio", "equipment": "Bodyweight", "compound": False, "category": "Cardio", "createdByUser": False},
]

DEFAULT_EXERCISES = DEFAULT_STRENGTH_EXERCISES + DEFAULT_CARDIO_EXERCISES

# ---------------------------
# Helper Functions
# ---------------------------
async def initialize_default_affirmations():
    """Initialize default affirmations if collection is empty"""
    count = await affirmations_collection.count_documents({})
    if count == 0:
        defaults = [
            "I am capable of achieving my goals.",
            "I grow stronger and wiser every day.",
            "I choose progress over perfection.",
            "I embrace challenges and learn from them.",
            "I am worthy of success and happiness.",
            "I bring value to my work and my community.",
            "Today I will be kind to myself and others.",
            "My potential to succeed is infinite.",
            "I trust my intuition and make clear decisions.",
            "I am focused, persistent, and will never quit."
        ]
        
        for text in defaults:
            await affirmations_collection.insert_one({"text": text})

async def ensure_default_exercises(username: str):
    """Seed default exercises for this user if they don't already have any."""
    count = await exercises_collection.count_documents({"username": username})
    if count > 0:
        return

    docs = []
    for ex in DEFAULT_EXERCISES:
        docs.append({**ex, "username": username})
    if docs:
        await exercises_collection.insert_many(docs)


# ---------------------------
# ROUTES
# ---------------------------
@app.on_event("startup")
async def startup_event():
    """Initialize database with default data on startup"""
    await initialize_default_affirmations()
    # Unique indexes make registration collisions atomic (no check-then-insert race)
    try:
        await users_collection.create_index("username", unique=True)
        await users_collection.create_index("email", unique=True)
    except Exception as e:
        print(f"WARNING: could not create unique user indexes: {e}")
    # Removed: await initialize_sample_data()  # Don't auto-populate sample assignments

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")

def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("ascii"))
    except ValueError:  # malformed hash (e.g. legacy plaintext) or password over 72 bytes
        return False

def create_access_token(user_id: str, username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "username": username,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> str:
    """Return the authenticated username from a valid Bearer token, else 401."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if creds is None:
        raise unauthorized
    try:
        payload = jwt.decode(
            creds.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError:
        raise unauthorized
    return payload["username"]

DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(16))

# REGISTER USER
@app.post(
    "/register",
    response_description="Register new user",
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute")
async def register_user(request: Request, data: RegisterRequest):
    """
    Register a new user.
    """
    # Same generic failure whether the username or the email is taken, and the hash
    # is computed first so a collision does not answer measurably faster.
    hashed = await run_in_threadpool(hash_password, data.password)
    failure = HTTPException(status_code=400, detail="Registration failed")

    taken = await users_collection.find_one(
        {"$or": [{"username": data.username}, {"email": data.email}]}
    )
    if taken:
        raise failure

    try:
        result = await users_collection.insert_one({
            "username": data.username,
            "email": data.email,
            "password": hashed,
        })
    except DuplicateKeyError:
        raise failure

    return {"message": "User registered successfully", "user_id": str(result.inserted_id)}

# Per-username login backoff (in-memory: per process, reset on restart)
LOGIN_FREE_ATTEMPTS = 5      # failures allowed before any lockout
LOGIN_BASE_LOCK_S = 30       # first lockout; doubles with each further failure
LOGIN_MAX_LOCK_S = 900       # lockout cap (15 min), limits abuse as a lockout-DoS
LOGIN_FAILURE_TTL_S = 900    # failure count is forgotten after this much quiet
_login_failures: dict[str, tuple[int, float, float]] = {}  # name -> (count, locked_until, last_failure)

def _login_retry_after(username: str) -> int:
    entry = _login_failures.get(username)
    remaining = entry[1] - time.monotonic() if entry else 0
    return int(remaining) + 1 if remaining > 0 else 0

def _record_login_failure(username: str) -> None:
    now = time.monotonic()
    if len(_login_failures) > 10000:  # bound memory against junk usernames
        for k in [k for k, v in _login_failures.items() if now - v[2] > LOGIN_FAILURE_TTL_S]:
            del _login_failures[k]
    count, _, last = _login_failures.get(username, (0, 0.0, now))
    if now - last > LOGIN_FAILURE_TTL_S:
        count = 0
    count += 1
    lock = 0.0
    if count >= LOGIN_FREE_ATTEMPTS:
        lock = min(LOGIN_BASE_LOCK_S * 2 ** (count - LOGIN_FREE_ATTEMPTS), LOGIN_MAX_LOCK_S)
    _login_failures[username] = (count, now + lock, now)

# LOGIN USER
@app.post("/login")
@limiter.limit("10/minute")
async def login_user(request: Request, data: LoginRequest):
    """
    Authenticate user with username and password.
    """
    # Applies to unknown usernames too, so lockout does not reveal which accounts exist.
    retry_after = _login_retry_after(data.username)
    if retry_after:
        raise HTTPException(
            status_code=429,
            detail="Too many failed attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    user = await users_collection.find_one({"username": data.username})

    # Verify against a dummy hash when the user does not exist so timing does not reveal it
    stored_hash = user.get("password", "") if user else DUMMY_PASSWORD_HASH
    password_ok = await run_in_threadpool(verify_password, data.password, stored_hash)
    if not user or not password_ok:
        _record_login_failure(data.username)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    _login_failures.pop(data.username, None)
    
    return {
        "message": f"Login successful for {data.username}",
        "user_id": str(user["_id"]),
        "username": user["username"],
        "access_token": create_access_token(str(user["_id"]), user["username"]),
        "token_type": "bearer",
    }

# HABITS endpoints
@app.get("/habits", response_description="Get user habits")
async def get_habits(current_user: str = Depends(get_current_user)):
    """
    Get all habits for a specific user.
    """
    try:
        habits = await habits_collection.find({"username": current_user}).to_list(1000)
        
        # Convert ObjectId to string for JSON serialization
        for habit in habits:
            if "_id" in habit:
                habit["_id"] = str(habit["_id"])
        
        return habits
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error fetching habits")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post(
    "/habits",
    response_description="Create new habit",
    status_code=status.HTTP_201_CREATED,
)
async def create_habit(h: HabitCreate, current_user: str = Depends(get_current_user)):
    """
    Create a new habit for a user.
    """
    try:
        # Generate UUID for the habit
        habit_id = str(uuid.uuid4())
        
        new_habit = {
            "id": habit_id,
            "username": current_user,
            "title": h.title,
            "description": h.description or ""
        }
        
        result = await habits_collection.insert_one(new_habit)
        new_habit["_id"] = str(result.inserted_id)
        
        return {
            "message": "Habit created successfully",
            "habit": new_habit
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error creating habit")
        raise HTTPException(status_code=500, detail="Internal server error")

# Delete habit endpoint
@app.delete("/habits/{habit_id}", response_description="Delete habit")
async def delete_habit(habit_id: str, current_user: str = Depends(get_current_user)):
    """
    Delete a habit by ID.
    """
    delete_result = await habits_collection.delete_one({"id": habit_id, "username": current_user})
    
    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    raise HTTPException(status_code=404, detail="Habit not found")

# AFFIRMATIONS endpoints
@app.get("/affirmations", response_description="Get all affirmations")
async def get_affirmations(current_user: str = Depends(get_current_user)):
    """
    Get all affirmations.
    """
    affirmations = await affirmations_collection.find().to_list(1000)
    
    # Extract just the text for backward compatibility
    # Or return full objects with IDs
    result = []
    for aff in affirmations:
        result.append({
            "id": str(aff["_id"]),
            "text": aff["text"]
        })
    
    return result

@app.post(
    "/affirmations",
    response_description="Create new affirmation",
    status_code=status.HTTP_201_CREATED,
)
async def create_affirmation(a: AffirmationCreate, current_user: str = Depends(get_current_user)):
    """
    Create a new affirmation.
    """
    try:
        new_aff = {"text": a.text}
        result = await affirmations_collection.insert_one(new_aff)
        new_aff["_id"] = str(result.inserted_id)
        return {
            "message": "Affirmation created successfully",
            "affirmation": new_aff
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error creating affirmation")
        raise HTTPException(status_code=500, detail="Internal server error")

# WATER INTAKE endpoints
@app.get("/water", response_description="Get water intake settings")
async def get_water(current_user: str = Depends(get_current_user)):
    """Return water setup for a user."""
    try:
        doc = await water_collection.find_one({"username": current_user})
        if doc:
            doc["_id"] = str(doc.get("_id"))
            return doc
        return {
            "username": current_user,
            "bottleName": "",
            "bottleOz": 0,
            "dailyGoal": 0,
            "currentOz": 0,
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error fetching water intake")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/water", response_description="Upsert water intake settings", status_code=status.HTTP_201_CREATED)
async def upsert_water(w: WaterIntakeUpsert, current_user: str = Depends(get_current_user)):
    """Create or update water intake settings for a user."""
    try:
        payload = {
            "username": current_user,
            "bottleName": w.bottleName,
            "bottleOz": w.bottleOz,
            "dailyGoal": w.dailyGoal,
            "currentOz": w.currentOz or 0,
        }
        result = await water_collection.update_one(
            {"username": current_user},
            {"$set": payload},
            upsert=True,
        )

        if result.upserted_id:
            payload["_id"] = str(result.upserted_id)
        else:
            existing = await water_collection.find_one({"username": current_user})
            if existing:
                payload["_id"] = str(existing.get("_id"))

        return {"message": "Water intake saved", "water": payload}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error saving water intake")
        raise HTTPException(status_code=500, detail="Internal server error")
    
# EXERCISES endpoints
@app.get("/exercises", response_description="Get user exercises")
async def get_exercises(current_user: str = Depends(get_current_user)):
    """
    Returns the exercise library for a user.
    Seeds defaults on first access.
    """
    try:
        await ensure_default_exercises(current_user)

        exercises = await exercises_collection.find({"username": current_user}).to_list(2000)

        for ex in exercises:
            if "_id" in ex:
                ex["_id"] = str(ex["_id"])

        return exercises
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error fetching exercises")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/exercises", response_description="Create custom exercise", status_code=status.HTTP_201_CREATED)
async def create_exercise(ex: ExerciseCreate, current_user: str = Depends(get_current_user)):
    """
    Create a custom exercise for a user.
    """
    try:
        new_ex = {
            "id": str(uuid.uuid4()),
            "username": current_user,
            "name": ex.name,
            "muscle": ex.muscle or "Other",
            "equipment": ex.equipment or "Other",
            "compound": bool(ex.compound) if ex.category == "Strength" else False,
            "category": ex.category or "Strength",
            "createdByUser": True,
        }

        result = await exercises_collection.insert_one(new_ex)
        new_ex["_id"] = str(result.inserted_id)

        return {"message": "Exercise created", "exercise": new_ex}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error creating exercise")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/exercises/{exercise_id}", response_description="Update exercise")
async def update_exercise(exercise_id: str, patch: ExerciseUpdate, current_user: str = Depends(get_current_user)):
    """
    Update an exercise by its 'id' field (not Mongo _id).
    Works for both defaults and custom exercises.
    """
    try:
        update_doc = {k: v for k, v in patch.model_dump().items() if v is not None}

        if "category" in update_doc and update_doc["category"] == "Cardio":
            update_doc["compound"] = False

        if not update_doc:
            raise HTTPException(status_code=400, detail="No fields provided to update")

        updated = await exercises_collection.find_one_and_update(
            {"id": exercise_id, "username": current_user},
            {"$set": update_doc},
            return_document=ReturnDocument.AFTER,
        )

        if not updated:
            raise HTTPException(status_code=404, detail="Exercise not found")

        updated["_id"] = str(updated.get("_id"))
        return {"message": "Exercise updated", "exercise": updated}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error updating exercise")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/exercises/{exercise_id}", response_description="Delete exercise")
async def delete_exercise(exercise_id: str, current_user: str = Depends(get_current_user)):
    """
    Delete an exercise by its 'id' field.
    """
    try:
        delete_result = await exercises_collection.delete_one({"id": exercise_id, "username": current_user})

        if delete_result.deleted_count == 1:
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        raise HTTPException(status_code=404, detail="Exercise not found")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error deleting exercise")
        raise HTTPException(status_code=500, detail="Internal server error")

# EXAMS endpoints
@app.post("/exams", response_description="Create exam", status_code=status.HTTP_201_CREATED)
async def create_exam(exam: ExamCreate, current_user: str = Depends(get_current_user)):
    """
    Create an exam document in MongoDB.
    """
    try:
        doc = {**exam.model_dump(), "username": current_user}
        result = await exams_collection.insert_one(doc)
        return {"id": str(result.inserted_id), "message": "Exam created"}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error creating exam")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/exams", response_description="Get exams for user")
async def get_exams(current_user: str = Depends(get_current_user)):
    """
    Get all exams for a specific user.
    """
    try:
        exams = await exams_collection.find({"username": current_user}).to_list(1000)
        for ex in exams:
            ex["_id"] = str(ex["_id"])
        return exams
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error fetching exams")
        raise HTTPException(status_code=500, detail="Internal server error")

# -----------------------------------------------------------
# ASSIGNMENTS endpoints
# -----------------------------------------------------------
@app.get("/assignments", response_description="Get all assignments", response_model=List[Assignment])
async def get_assignments(current_user: str = Depends(get_current_user)):
    """
    Get the caller's assignments.
    """
    try:
        assignments = await assignments_collection.find({"username": current_user}).to_list(1000)
        return assignments
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error fetching assignments")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/assignments/{assignment_id}", response_description="Get assignment by ID", response_model=Assignment)
async def get_assignment(assignment_id: str, current_user: str = Depends(get_current_user)):
    """
    Get a specific assignment by ID.
    """
    try:
        assignment = await assignments_collection.find_one({"_id": parse_object_id(assignment_id), "username": current_user})
        if assignment is None:
            raise HTTPException(status_code=404, detail="Assignment not found")
        return assignment
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error fetching assignment")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/assignments", response_description="Create new assignment", status_code=status.HTTP_201_CREATED, response_model=Assignment)
async def create_assignment(assignment: AssignmentCreate, current_user: str = Depends(get_current_user)):
    """
    Create a new assignment.
    """
    try:
        assignment_dict = {**assignment.model_dump(), "username": current_user}
        result = await assignments_collection.insert_one(assignment_dict)
        created_assignment = await assignments_collection.find_one({"_id": result.inserted_id})
        return created_assignment
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error creating assignment")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/assignments/{assignment_id}", response_description="Update assignment", response_model=Assignment)
async def update_assignment(assignment_id: str, assignment: AssignmentCreate, current_user: str = Depends(get_current_user)):
    """
    Update an assignment.
    """
    try:
        assignment_dict = assignment.model_dump(exclude_unset=True)
        
        if len(assignment_dict) >= 1:
            update_result = await assignments_collection.update_one(
                {"_id": parse_object_id(assignment_id), "username": current_user},
                {"$set": assignment_dict}
            )
            
            if update_result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Assignment not found")
        
        updated_assignment = await assignments_collection.find_one({"_id": parse_object_id(assignment_id), "username": current_user})
        if updated_assignment is None:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        return updated_assignment
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error updating assignment")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/assignments/{assignment_id}", response_description="Delete assignment")
async def delete_assignment(assignment_id: str, current_user: str = Depends(get_current_user)):
    """
    Delete an assignment.
    """
    try:
        delete_result = await assignments_collection.delete_one({"_id": parse_object_id(assignment_id), "username": current_user})
        
        if delete_result.deleted_count == 1:
            return {"success": True, "id": assignment_id}
        
        raise HTTPException(status_code=404, detail="Assignment not found")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error deleting assignment")
        raise HTTPException(status_code=500, detail="Internal server error")

# -----------------------------------------------------------
# COURSES endpoints
# -----------------------------------------------------------
@app.get("/courses", response_description="Get all courses", response_model=List[Course])
async def get_courses(current_user: str = Depends(get_current_user)):
    """
    Get all courses.
    """
    try:
        courses = await courses_collection.find().to_list(1000)
        return courses
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error fetching courses")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/courses", response_description="Create new course", status_code=status.HTTP_201_CREATED, response_model=Course)
async def create_course(course: CourseCreate, current_user: str = Depends(get_current_user)):
    """
    Create a new course.
    """
    try:
        course_dict = course.model_dump()
        result = await courses_collection.insert_one(course_dict)
        created_course = await courses_collection.find_one({"_id": result.inserted_id})
        return created_course
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error creating course")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/courses/{course_code}", response_description="Get course by code", response_model=Course)
async def get_course_by_code(course_code: str, current_user: str = Depends(get_current_user)):
    """
    Get a course by its code.
    """
    try:
        course = await courses_collection.find_one({"code": course_code})
        if course is None:
            raise HTTPException(status_code=404, detail="Course not found")
        return course
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error fetching course")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/exams/{exam_id}", response_description="Update exam")
async def update_exam(exam_id: str, patch: ExamUpdate, current_user: str = Depends(get_current_user)):
    """
    Update an exam document by Mongo _id.
    """
    try:
        update_doc = {k: v for k, v in patch.model_dump().items() if v is not None}
        if not update_doc:
            raise HTTPException(status_code=400, detail="No fields provided to update")

        updated = await exams_collection.find_one_and_update(
            {"_id": parse_object_id(exam_id), "username": current_user},
            {"$set": update_doc},
            return_document=ReturnDocument.AFTER,
        )

        if not updated:
            raise HTTPException(status_code=404, detail="Exam not found")

        updated["_id"] = str(updated["_id"])
        return {"message": "Exam updated", "exam": updated}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error updating exam")
        raise HTTPException(status_code=500, detail="Internal server error")