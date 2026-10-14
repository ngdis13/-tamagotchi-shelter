import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import psycopg2
from psycopg2.extras import RealDictCursor

# Подключение к PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@localhost:5432/tamagotchi_db")

INSTANCE_ID = os.getenv("APP_INSTANCE_ID", "Instance-A")


def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pets (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                species VARCHAR(50) NOT NULL,
                fullness INT DEFAULT 50
            );
        """)
        conn.commit()
    conn.close()
    yield

# Инициализируем приложение с отключенным строгим контролем слэшей
app = FastAPI(lifespan=lifespan, redirect_slashes=False)


class PetCreate(BaseModel):
    name: str
    species: str

# Эндпоинты регистрируем ДО добавления CORS middleware


@app.get("/api/pets")
def get_pets():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM pets ORDER BY id DESC;")
        pets = cur.fetchall()
    conn.close()
    return {
        "instance": INSTANCE_ID,
        "data": [dict(pet) for pet in pets]
    }


@app.post("/api/pets")
def create_pet(pet: PetCreate):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO pets (name, species) VALUES (%s, %s) RETURNING *;",
            (pet.name, pet.species)
        )
        new_pet = cur.fetchone()
        conn.commit()
    conn.close()
    return new_pet


@app.post("/api/pets/{pet_id}/feed")
def feed_pet(pet_id: int):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM pets WHERE id = %s;", (pet_id,))
        pet = cur.fetchone()
        if not pet:
            conn.close()
            raise HTTPException(status_code=404, detail="Питомец не найден")

        new_fullness = min(100, pet['fullness'] + 10)
        cur.execute(
            "UPDATE pets SET fullness = %s WHERE id = %s RETURNING *;",
            (new_fullness, pet_id)
        )
        updated_pet = cur.fetchone()
        conn.commit()
    conn.close()
    return updated_pet

# Эндпоинт: Удалить питомца из базы данных (Отпустить на волю)


@app.delete("/api/pets/{pet_id}")
def delete_pet(pet_id: int):
    conn = get_db_connection()
    with conn.cursor() as cur:
        # Проверяем, существует ли питомец
        cur.execute("SELECT * FROM pets WHERE id = %s;", (pet_id,))
        pet = cur.fetchone()
        if not pet:
            conn.close()
            raise HTTPException(status_code=404, detail="Питомец не найден")

        # Удаляем из базы
        cur.execute("DELETE FROM pets WHERE id = %s;", (pet_id,))
        conn.commit()
    conn.close()
    return {"message": f"Питомец {pet['name']} успешно отпущен на волю! 🌸"}


# ВАЖНО: Добавляем CORS Middleware в самом конце, после всех путей!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
