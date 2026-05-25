from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./home_stock.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

app = FastAPI(title="Home Stock Assistant MVP")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Base(DeclarativeBase):
    pass


class ListType(str, Enum):
    personal = "personal"
    family = "family"


class ItemStatus(str, Enum):
    pending = "pending"
    bought = "bought"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(100))
    family_id: Mapped[Optional[int]] = mapped_column(ForeignKey("families.id"), nullable=True)
    family = relationship("Family", back_populates="members")


class Family(Base):
    __tablename__ = "families"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    members = relationship("User", back_populates="family")


class ShoppingItem(Base):
    __tablename__ = "shopping_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    family_id: Mapped[Optional[int]] = mapped_column(ForeignKey("families.id"), nullable=True)
    list_type: Mapped[ListType] = mapped_column(SAEnum(ListType))
    name: Mapped[str] = mapped_column(String(255))
    qty_needed: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[ItemStatus] = mapped_column(SAEnum(ItemStatus), default=ItemStatus.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Token(Base):
    __tablename__ = "tokens"
    token: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime)


Base.metadata.create_all(bind=engine)

ALIASES = {
    "牛奶": {"牛奶", "鮮乳", "鮮奶", "保久乳", "阿猴鮮奶"},
    "蔬菜": {"青菜", "蔬菜", "高麗菜", "葉菜"},
    "水果": {"水果", "蘋果", "香蕉", "芭樂", "葡萄"},
}


def normalize_name(name: str) -> str:
    cleaned = name.strip().lower().replace(" ", "")
    for canonical, words in ALIASES.items():
        norm_words = {w.lower().replace(" ", "") for w in words}
        if cleaned in norm_words or any(w in cleaned for w in norm_words):
            return canonical
    return name.strip()


def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(db_session)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    tk = authorization.replace("Bearer ", "")
    token = db.get(Token, tk)
    if not token or token.expires_at < datetime.utcnow():
        raise HTTPException(401, "Invalid token")
    user = db.get(User, token.user_id)
    if not user:
        raise HTTPException(401, "Invalid user")
    return user


class RegisterReq(BaseModel):
    email: str
    password: str
    name: str


class LoginReq(BaseModel):
    email: str
    password: str


class FamilyCreateReq(BaseModel):
    name: str


class InviteReq(BaseModel):
    member_email: str


class ItemCreateReq(BaseModel):
    name: str
    qty_needed: int = Field(1, ge=1)
    list_type: ListType


class PurchaseReq(BaseModel):
    item_name: str
    for_list_type: ListType


class VoiceReq(BaseModel):
    phrase: str
    list_type: ListType = ListType.personal


@app.get("/")
def root():
    return FileResponse("app/static/index.html")


app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/health")
def health():
    return {"status": "ok", "db": "connected"}


@app.post("/auth/register")
def register(payload: RegisterReq, db: Session = Depends(db_session)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(400, "Email exists")
    user = User(email=payload.email, password=payload.password, name=payload.name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"user_id": user.id, "email": user.email, "name": user.name}


@app.post("/auth/login")
def login(payload: LoginReq, db: Session = Depends(db_session)):
    user = db.query(User).filter(User.email == payload.email, User.password == payload.password).first()
    if not user:
        raise HTTPException(401, "Login failed")
    token = f"tk_{user.id}_{secrets.token_hex(8)}"
    db.add(Token(token=token, user_id=user.id, expires_at=datetime.utcnow() + timedelta(days=30)))
    db.commit()
    return {"token": token, "user_id": user.id, "name": user.name}


@app.post("/family/create")
def create_family(payload: FamilyCreateReq, user: User = Depends(get_current_user), db: Session = Depends(db_session)):
    family = Family(name=payload.name, owner_id=user.id)
    db.add(family)
    db.commit()
    db.refresh(family)
    user.family_id = family.id
    db.commit()
    return {"family_id": family.id, "name": family.name}


@app.post("/family/add-member")
def add_member(payload: InviteReq, user: User = Depends(get_current_user), db: Session = Depends(db_session)):
    if not user.family_id:
        raise HTTPException(400, "Create family first")
    member = db.query(User).filter(User.email == payload.member_email).first()
    if not member:
        raise HTTPException(404, "Member not found")
    member.family_id = user.family_id
    db.commit()
    return {"added_user_id": member.id, "family_id": user.family_id}


@app.post("/items")
def create_item(payload: ItemCreateReq, user: User = Depends(get_current_user), db: Session = Depends(db_session)):
    if payload.list_type == ListType.family and not user.family_id:
        raise HTTPException(400, "No family")
    item = ShoppingItem(
        owner_user_id=user.id if payload.list_type == ListType.personal else None,
        family_id=user.family_id if payload.list_type == ListType.family else None,
        list_type=payload.list_type,
        name=normalize_name(payload.name),
        qty_needed=payload.qty_needed,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "name": item.name, "list_type": item.list_type, "qty_needed": item.qty_needed}


@app.get("/items/me")
def get_my_items(user: User = Depends(get_current_user), db: Session = Depends(db_session)):
    personal = db.query(ShoppingItem).filter(ShoppingItem.owner_user_id == user.id, ShoppingItem.status == ItemStatus.pending).all()
    family = []
    if user.family_id:
        family = db.query(ShoppingItem).filter(ShoppingItem.family_id == user.family_id, ShoppingItem.status == ItemStatus.pending).all()
    return {
        "personal": [{"id": i.id, "name": i.name, "qty_needed": i.qty_needed} for i in personal],
        "family": [{"id": i.id, "name": i.name, "qty_needed": i.qty_needed} for i in family],
    }


@app.post("/purchase")
def purchase(payload: PurchaseReq, user: User = Depends(get_current_user), db: Session = Depends(db_session)):
    target_name = normalize_name(payload.item_name)
    q = db.query(ShoppingItem).filter(ShoppingItem.name == target_name, ShoppingItem.status == ItemStatus.pending)
    if payload.for_list_type == ListType.personal:
        q = q.filter(ShoppingItem.owner_user_id == user.id)
    else:
        if not user.family_id:
            raise HTTPException(400, "No family")
        q = q.filter(ShoppingItem.family_id == user.family_id)
    item = q.first()
    if not item:
        raise HTTPException(404, "No pending item")
    item.qty_needed -= 1
    if item.qty_needed <= 0:
        item.status = ItemStatus.bought
    db.commit()
    return {"action": "deducted", "item_id": item.id, "remaining": max(item.qty_needed, 0)}


@app.post("/voice/siri")
def siri_voice(payload: VoiceReq, user: User = Depends(get_current_user), db: Session = Depends(db_session)):
    if payload.list_type == ListType.family and not user.family_id:
        raise HTTPException(400, "No family")
    item = ShoppingItem(
        owner_user_id=user.id if payload.list_type == ListType.personal else None,
        family_id=user.family_id if payload.list_type == ListType.family else None,
        list_type=payload.list_type,
        name=normalize_name(payload.phrase),
        qty_needed=1,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"added": item.name, "list_type": item.list_type}
