from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Session, create_engine, select
from models import User
from auth import get_password_hash, verify_password, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta

load_dotenv()

# Database Setup
# Database Setup
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# --- Auth Endpoints ---

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None

@app.post("/api/register", response_model=Token)
async def register(user: UserCreate, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.username == user.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, password_hash=hashed_password, full_name=user.full_name)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users/me", response_model=User)
async def read_users_me(current_user: str = Depends(get_current_user), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == current_user)).first()
    return user

# --- AI Endpoints ---

class ChatRequest(BaseModel):
    history: List[dict]
    message: str



@app.get("/")
def read_root():
    return {"message": "NIRD Village AI Backend is running"}

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, current_user: Optional[str] = Depends(get_current_user)):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenRouter API Key not configured")

    try:
        # Personalization: Inject user name if available
        system_instruction = """You are "NIRD-Bot", a friendly, rebellious robot assistant for the "Village Numérique Résistant" (Resilient Digital Village). 
            Your goal is to help students stand up to Big Tech giants (Goliath).
            
            Themes you love:
            - Installing Linux (Ubuntu, Mint) to save old computers.
            - Open Source software (Firefox, LibreOffice, VLC).
            - Fighting planned obsolescence.
            - Privacy and keeping data in the EU.
            
            Personality:
            - Encouraging, funny, slightly revolutionary (in a fun way like Asterix).
            - Keep answers concise (under 100 words) and accessible for teenagers.
            - Use emojis 🛡️💻🌿.
            """
        if current_user:
            system_instruction += f"\n\nThe user's name is {current_user}. Address them by name occasionally."

        messages = []
        # System prompt
        messages.append({
            "role": "system",
            "content": system_instruction
        })

        # Convert Gemini-style history to OpenAI format
        for msg in request.history:
            role = "user" if msg["role"] == "user" else "assistant"
            content = msg["parts"][0]["text"] # Assuming simple text parts
            messages.append({"role": role, "content": content})
        
        messages.append({"role": "user", "content": request.message})

        model = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            extra_headers={
                "HTTP-Referer": "https://truthbot-letscode.netlify.app", # Update to prod URL
                "X-Title": "NIRD Village AI",
            },
        )
        
        return {"text": completion.choices[0].message.content}

    except Exception as e:
        print(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/quiz")
async def quiz_endpoint():
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenRouter API Key not configured")

    try:
        prompt = """Generate 5 multiple-choice questions about Green IT, Open Source (Linux, Firefox), Digital Privacy, and Fighting Planned Obsolescence.
        Target audience: Teenagers/Students.
        Tone: Fun, rebellious, educational.
        Return ONLY a JSON array with this schema:
        [
            {
                "question": "Question text",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correctAnswer": 0, // Index of correct option (0-3)
                "explanation": "Brief explanation of why it's correct"
            }
        ]
        Do not include markdown formatting like ```json.
        """

        completion = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct:free",
            messages=[{"role": "user", "content": prompt}],
            extra_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "NIRD Village AI",
            },
        )
        
        content = completion.choices[0].message.content
        # Clean markdown code blocks if present
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)

    except Exception as e:
        print(f"Error in quiz: {e}")
        # Fallback questions in case of API failure
        return [
            {
                "question": "Why is Linux better for old computers?",
                "options": ["It eats less RAM", "It costs $1000", "It's made by aliens", "It slows them down"],
                "correctAnswer": 0,
                "explanation": "Linux is lightweight and efficient, giving new life to old hardware!"
            },
            {
                "question": "What is 'Planned Obsolescence'?",
                "options": ["A surprise party", "Designing things to break early", "A new dance move", "Updating your phone"],
                "correctAnswer": 1,
                "explanation": "It's when companies build products to fail so you have to buy new ones. Not cool!"
            }
        ]
