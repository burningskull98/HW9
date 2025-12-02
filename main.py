from datetime import timedelta
import logging
import numpy as np
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse

from config import MODEL_PATH, fake_users_db, ACCESS_TOKEN_EXPIRE_MINUTES
from schemas import PredictionRequest, PredictionResponse, Token, UserLogin, User
from utils import load_model, verify_password, create_access_token, get_current_user


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    """
    Событие запуска приложения: загрузка модели.
    """
    try:
        app.state.model = load_model(MODEL_PATH)
        logger.info("Модель успешно загружена")
    except FileNotFoundError as e:
        logger.error(f"Файл модели не найден: {e}")
        raise
    except IOError as e:
        logger.error(f"Ошибка ввода-вывода при загрузке модели: {e}")
        app.state.model = None
    except ValueError as e:
        logger.error(f"Некорректное значение при загрузке модели: {e}")
        app.state.model = None


@app.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """
    Аутентификация пользователя и выдача JWT-токена.
    """
    user = fake_users_db.get(user_credentials.username)
    if not user or not verify_password(
        user_credentials.password, user["hashed_password"]
    ):
        raise HTTPException(status_code=401, detail="Неверные учетные данные")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/predict", response_model=PredictionResponse)
async def predict(
    request: PredictionRequest, current_user: User = Depends(get_current_user)
):
    """
    Функция для получения предсказания по входным признакам.
    Доступно для аутентифицированных пользователей.
    """
    if app.state.model is None:
        logger.error("Модель не загружена")
        raise HTTPException(status_code=503, detail="Модель не загружена")

    try:
        features = np.array(request.features)

        if len(request.features) != app.state.model.n_features_in_:
            logger.warning(
                f"Неверное количество признаков: ожидалось {app.state.model.n_features_in_}, "
                f"получено {len(request.features)}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Ожидалось {app.state.model.n_features_in_} признаков, "
                f"получено {len(request.features)}",
            )

        features_reshaped = features.reshape(1, -1)
        prediction = app.state.model.predict(features_reshaped)[0]

        if hasattr(app.state.model, "predict_proba"):
            probabilities = app.state.model.predict_proba(features_reshaped)[0].tolist()
        else:
            probabilities = None

        logger.info(
            f"Предсказание выполнено для пользователя {current_user.username}: {prediction}"
        )
        return PredictionResponse(
            prediction=float(prediction), probabilities=probabilities
        )

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
    except Exception as e:
        logger.error(f"Ошибка при предсказании: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера") from e


@app.get("/health")
async def health_check():
    """
    Проверка работоспособности сервиса с реальной проверкой состояния модели.
    """
    if app.state.model is None:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "model_loaded": False,
                "detail": "Модель не загружена",
            },
        )

    try:
        if hasattr(app.state.model, "n_features_in_"):
            dummy_input = np.zeros((1, app.state.model.n_features_in_))
            _ = app.state.model.predict(dummy_input)
        logger.info("Проверка модели в /health прошла успешно")
        return {"status": "healthy", "model_loaded": True}
    except (ValueError, TypeError) as e:
        logger.error(f"Ошибка при проверке модели в /health: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "model_loaded": True,
                "detail": f"Модель неисправна: {str(e)}",
            },
        )


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Получает информацию о текущем пользователе.
    """
    return current_user


@app.get("/users/")
async def read_users():
    return fake_users_db


@app.get("/")
def root():
    """
    Обработчик корневого маршрута.
    """
    return {"message": "Добро пожаловать!"}
