# -*- coding: utf-8 -*-
import os
import time
import gradio as gr
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Lớp để định nghĩa dữ liệu nhận vào từ giao diện
class ChatRequest(BaseModel):
    message: str
    history: list

# --- PHẦN CONFIG GỐC CỦA BẠN ---
API_KEY = "AIzaSyCbqVFyf92xhi4Spn1awjrt59Y_JTtjCz0" # Dùng API Key mới của bạn
MODEL_NAME_CHAT = "gemini-1.5-flash-latest"

# Cấu hình Google AI
try:
    genai.configure(api_key=API_KEY)
    print("[OK] Google AI đã được cấu hình thành công.")
except Exception as e:
    print(f"[ERROR] Không thể cấu hình Google AI: {e}")

app = FastAPI()

# Thêm middleware để cho phép kết nối
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route để phục vụ giao diện (file index.html)
@app.get("/")
def read_root():
    return FileResponse("index.html")

# Route API để xử lý chat
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    print(f"Nhận được tin nhắn: {request.message}")
    history = []
    for user_msg, model_msg in request.history:
        history.append({'role': 'user', 'parts': [user_msg]})
        history.append({'role': 'model', 'parts': [model_msg]})

    try:
        model = genai.GenerativeModel(MODEL_NAME_CHAT)
        chat_session = model.start_chat(history=history)
        response = chat_session.send_message(request.message)
        print(f"AI trả lời: {response.text}")
        return {"reply": response.text}
    except Exception as e:
        print(f"[ERROR] Lỗi khi gọi Gemini: {e}")
        raise HTTPException(status_code=500, detail=str(e))
