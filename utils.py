import os
import pickle
from typing import Optional
from datetime import timedelta, datetime
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status
import jwt
from passlib.context import CryptContext
from config import fake_users_db, ALGORITHM, SECRET_KEY
from schemas import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def get_password_hash(password):
    """
    Хэширует пароль.
    """
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    """
    Проверяет пароль на соответствие.
    """
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str):
    """
    Аутентификация пользователя на основе имени пользователя и пароля.
    """
    user = fake_users_db.get(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Создаёт JWT для доступа на основе предоставленных данных.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=20)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Извлекает текущего пользователя на основе предоставленного Bearer-токена.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
    except jwt.PyJWTError as exc:
        raise credentials_exception from exc
    user = fake_users_db.get(username)
    if user is None:
        raise credentials_exception
    return User(username=username, role=role)


def load_model(model_path: str):
    """
    Загружает обученную ML-модель из файла.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Модель не найдена: {model_path}")

    with open(model_path, "rb") as f:
        model = pickle.load(f)
        return model
