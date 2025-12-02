from fastapi.security import HTTPBearer

MODEL_PATH = "models/model.pkl"
SECRET_KEY = "encoded-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 5

security = HTTPBearer()


fake_users_db = {
    "Ronald_Reagan": {
        "username": "Ronald_Reagan",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "phone": "231-44-956",
        "email": "reagan@example.com",
        "role": "admin",
    },
    "Jimmy Carter": {
        "username": "Jimmy_Carter",
        "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4fYw9iS9G6",
        "phone": "231-12-888",
        "email": "carter@example.com",
        "role": "user",
    },
}
