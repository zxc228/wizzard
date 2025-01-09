from fastapi import FastAPI
from pydantic import BaseModel
import hashlib
import requests

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Разрешаем запросы с любого источника (временно для локальной разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Можно указать ["http://localhost:3000"] для безопасности
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы (POST, GET, OPTIONS и т.д.)
    allow_headers=["*"],
)

TAROT_CARDS = [
    {"name": "The Fool", "meaning": "New beginnings, adventure, spontaneity"},
    {"name": "The Magician", "meaning": "Manifestation, resourcefulness, power"},
    {"name": "The High Priestess", "meaning": "Intuition, mystery, wisdom"},
    {"name": "The Empress", "meaning": "Nurturing, abundance, beauty"},
    {"name": "The Emperor", "meaning": "Authority, structure, stability"},
    {"name": "The Hierophant", "meaning": "Tradition, spirituality, guidance"},
    {"name": "The Lovers", "meaning": "Love, harmony, choices"},
    {"name": "The Chariot", "meaning": "Determination, control, victory"},
    {"name": "Strength", "meaning": "Courage, patience, inner strength"},
    {"name": "The Hermit", "meaning": "Reflection, solitude, wisdom"},
]

OLLAMA_URL = "http://localhost:11434/api/generate"  # Адрес локального Ollama

class Question(BaseModel):
    text: str
    lang: str = "en"  # По умолчанию английский

def hash_to_indices(text: str, num_cards: int, deck_size: int):
    """
    Преобразует текст в хеш и выбирает уникальные индексы карт.
    """
    hash_digest = hashlib.sha256(text.encode()).hexdigest()
    indices = [int(hash_digest[i : i + 2], 16) % deck_size for i in range(0, num_cards * 2, 2)]
    return list(set(indices))[:num_cards]  # Гарантируем уникальность карт

def select_tarot_cards(question: str, num_cards: int = 3):
    """
    Выбирает карты на основе текста вопроса.
    """
    indices = hash_to_indices(question, num_cards, len(TAROT_CARDS))
    return [TAROT_CARDS[i] for i in indices]

def get_mistral_response(prompt: str):
    """
    Отправляет запрос в Ollama (Mistral) и получает ответ.
    """
    response = requests.post(
        OLLAMA_URL,
        json={"model": "mistral", "prompt": prompt, "stream": False},
    )
    if response.status_code == 200:
        return response.json().get("response", "No response from Mistral.")
    return "Error communicating with Ollama."

def get_tarot_prediction(question: str, cards: list):
    """
    Генерирует предсказание с помощью Mistral.
    """
    prompt = f"""You are a tarot reader. A user asked: '{question}'. 
    The following tarot cards were drawn:
    {', '.join([f"{card['name']} ({card['meaning']})" for card in cards])}.
    Provide a detailed mystical and intuitive interpretation of this reading.
    """
    return get_mistral_response(prompt)

def translate_text(text: str, target_lang: str):
    """
    Использует Mistral для перевода текста.
    """
    if target_lang == "ru":
        prompt = f"Translate the following text to Russian:\n\n{text}"
    else:
        return text  # Если язык английский, оставляем как есть

    return get_mistral_response(prompt)

@app.post("/tarot")
def get_tarot_reading(question: Question):
    selected_cards = select_tarot_cards(question.text)  # Выбираем карты на основе текста
    prediction = get_tarot_prediction(question.text, selected_cards)

    if question.lang == "ru":
        prediction = translate_text(prediction, "ru")

    return {
        "question": question.text,
        "cards": selected_cards,
        "prediction": prediction,
        "language": question.lang
    }
