import uvicorn
from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import redis
import json
import os
import random

os.makedirs("templates", exist_ok=True)

# Khởi tạo FastAPI app
app = FastAPI(title="Ứng dụng học từ vựng")

# Kết nối tới Redis (localhost:6379)
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Khởi tạo templates
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, search: str = None):
    # Lấy tất cả từ vựng từ Redis
    all_words = []
    words = r.hgetall("vocabulary")

    # Nếu có từ khóa tìm kiếm
    if search:
        filtered_words = {}
        for word, meaning in words.items():
            if search.lower() in word.lower() or search.lower() in meaning.lower():
                filtered_words[word] = meaning
        words = filtered_words

    for word, meaning in words.items():
        all_words.append({"word": word, "meaning": meaning})

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "words": all_words, "search": search or ""}
    )

@app.post("/add", response_class=HTMLResponse)
async def add_word(
    request: Request,
    word: str = Form(...),
    meaning: str = Form(...)
):
    # Lưu từ vào Redis
    r.hset("vocabulary", word, meaning)

    # Lấy lại danh sách từ vựng
    all_words = []
    words = r.hgetall("vocabulary")
    for word, meaning in words.items():
        all_words.append({"word": word, "meaning": meaning})

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "words": all_words}
    )

# Endpoint API để lấy tất cả từ vựng (cho JavaScript fetch)
@app.get("/api/words")
async def get_words():
    words = r.hgetall("vocabulary")
    return [{"word": word, "meaning": meaning} for word, meaning in words.items()]

# API xóa từ vựng
@app.delete("/api/words/{word}")
async def delete_word(word: str):
    # Kiểm tra xem từ có tồn tại không
    if not r.hexists("vocabulary", word):
        return {"success": False, "message": f"Từ '{word}' không tồn tại"}

    # Xóa từ khỏi Redis
    r.hdel("vocabulary", word)
    return {"success": True, "message": f"Đã xóa từ '{word}'"}

# API lấy một từ ngẫu nhiên để ôn tập
@app.get("/api/random-word")
async def get_random_word():
    words = r.hgetall("vocabulary")
    if not words:
        return {"success": False, "message": "Không có từ vựng nào"}

    # Chọn một từ ngẫu nhiên
    random_word = random.choice(list(words.keys()))
    meaning = words[random_word]

    return {"success": True, "word": random_word, "meaning": meaning}

# Trang ôn tập từ vựng
@app.get("/review", response_class=HTMLResponse)
async def review_page(request: Request):
    return templates.TemplateResponse(
        "review.html",
        {"request": request}
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
