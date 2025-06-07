# -*- coding: utf-8 -*-
import os
import time
import random
import gradio as gr

# Thêm các thư viện cần thiết cho server
from fastapi import FastAPI
from fastapi.responses import FileResponse
# Thêm thư viện để sửa lỗi 403 Forbidden
from fastapi.middleware.cors import CORSMiddleware


# --- HÀM LOGIC GIẢ LẬP ĐỂ THỬ NGHIỆM ---
# Không dùng đến Google AI và API Key
def respond(message, chat_history_state):
    # Nếu không nhập gì
    if not message or message.strip() == "":
        return "", chat_history_state, chat_history_state

    # Hàm trả lời giả: chỉ lặp lại lời người dùng để kiểm tra kết nối
    response_text = f"Máy chủ đã nhận được: {message}"

    # Thêm tin nhắn vào lịch sử
    chat_history_state = (chat_history_state or []) + [[message, ""]]
    idx = len(chat_history_state) - 1

    # Hiệu ứng gõ chữ giả
    full_text = ""
    for char in response_text:
        full_text += char
        chat_history_state[idx][1] = full_text
        time.sleep(0.05)
        yield "", chat_history_state, chat_history_state


# --- PHẦN SERVER CẦN THIẾT CHO RENDER (Giữ nguyên) ---
with gr.Blocks() as demo:
    state = gr.State([])
    with gr.Row(visible=False):
        txt_input = gr.Textbox(label="Internal Input")
        chatbot_history = gr.Chatbot(label="Internal History")
    txt_input.submit(respond, [txt_input, state], [txt_input, chatbot_history, state])

app = FastAPI()

# *** DÒNG CODE MỚI ĐỂ SỬA LỖI 403 ***
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các domain
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả các phương thức
    allow_headers=["*"],  # Cho phép tất cả các header
)
# *************************************

@app.get("/")
def read_root():
    return FileResponse("index.html")

app = gr.mount_gradio_app(app, demo, path="/gradio")
