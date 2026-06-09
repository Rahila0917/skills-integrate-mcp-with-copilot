"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(
    title="Mergington High School API",
    description="API for viewing and signing up for extracurricular activities",
)

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(Path(__file__).parent, "static")),
    name="static",
)

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ACCESS_TOKEN_EXPIRE_SECONDS = 3600
security = HTTPBearer()


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def base64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    return hmac.compare_digest(hash_password(password, salt), password_hash)


def create_access_token(email: str, role: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": email,
        "role": role,
        "exp": int((datetime.utcnow() + timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS)).timestamp()),
    }
    header_b = base64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b = base64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = hmac.new(
        SECRET_KEY.encode(), f"{header_b}.{payload_b}".encode(), hashlib.sha256
    ).digest()
    signature_b = base64url_encode(signature)
    return f"{header_b}.{payload_b}.{signature_b}"


def decode_access_token(token: str) -> Dict[str, str]:
    try:
        header_b, payload_b, signature_b = token.split(".")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token format")

    expected_signature = hmac.new(
        SECRET_KEY.encode(), f"{header_b}.{payload_b}".encode(), hashlib.sha256
    ).digest()
    if not hmac.compare_digest(base64url_encode(expected_signature), signature_b):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    try:
        payload = json.loads(base64url_decode(payload_b))
    except ValueError:
        raise HTTPException(status_code=401, detail="Malformed token payload")

    if payload.get("exp", 0) < int(datetime.utcnow().timestamp()):
        raise HTTPException(status_code=401, detail="Token expired")

    return payload


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    payload = decode_access_token(credentials.credentials)
    email = payload.get("sub")
    if email not in users:
        raise HTTPException(status_code=401, detail="Invalid user token")
    user_data = users[email]
    return {
        "email": email,
        "full_name": user_data["full_name"],
        "role": user_data["role"],
    }


def require_admin(user: Dict[str, str] = Depends(get_current_user)) -> Dict[str, str]:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user


def create_user(email: str, password: str, full_name: str, role: str = "student"):
    if role not in ("student", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")
    if email in users:
        raise HTTPException(status_code=400, detail="User already exists")

    salt = secrets.token_hex(8)
    users[email] = {
        "full_name": full_name,
        "password_salt": salt,
        "password_hash": hash_password(password, salt),
        "role": role,
    }
    return users[email]


# In-memory user database with a default admin and a student for testing.
users = {}
create_user("admin@mergington.edu", "adminpass", "School Admin", role="admin")
create_user("student@mergington.edu", "studentpass", "Student User")


# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"],
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"],
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
    },
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""
    role: str = "student"


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/register")
def register_user(request: RegisterRequest):
    """Register a new student account."""
    if request.role == "admin":
        raise HTTPException(status_code=403, detail="Admin registration is not allowed")
    create_user(
        request.email,
        request.password,
        request.full_name or request.email.split("@")[0].title(),
        request.role,
    )
    return {"message": "User registered successfully", "email": request.email, "role": request.role}


@app.post("/login")
def login_user(request: LoginRequest):
    """Authenticate a user and return a bearer token."""
    user = users.get(request.email)
    if not user or not verify_password(request.password, user["password_salt"], user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(email=request.email, role=user["role"])
    return {"access_token": token, "token_type": "bearer", "email": request.email, "role": user["role"]}


@app.get("/users/me")
def get_me(user: Dict[str, str] = Depends(get_current_user)):
    return user


@app.get("/users")
def list_users(admin: Dict[str, str] = Depends(require_admin)):
    return [{"email": email, "full_name": data["full_name"], "role": data["role"]} for email, data in users.items()]


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str = "",
    user: Dict[str, str] = Depends(get_current_user),
):
    """Sign up a student for an activity."""
    if not email:
        email = user["email"]

    if user["role"] == "student" and email != user["email"]:
        raise HTTPException(status_code=403, detail="Students can only sign up themselves")

    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]
    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str = "",
    user: Dict[str, str] = Depends(get_current_user),
):
    """Unregister a student from an activity."""
    if not email:
        email = user["email"]

    if user["role"] == "student" and email != user["email"]:
        raise HTTPException(status_code=403, detail="Students can only unregister themselves")

    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]
    if email not in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
