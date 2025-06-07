# -*- coding: utf-8 -*-
import os
import time
import random
import gradio as gr
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# --- PHẦN API KEY VÀ CẤU HÌNH GENAI ---
# THAY API KEY CỦA BẠN VÀO ĐÂY
API_KEY = "YOUR_API_KEY_HERE" 

genai_configured = False
if not API_KEY or API_KEY == "AIzaSyAWrCJv5sesCGjaTx3xfLHLXzu4qi4R9EY":
    print("[ERROR] API Key bị thiếu hoặc chưa được thay đổi. Vui lòng thay thế 'YOUR_API_KEY_HERE'.")
else:
    print("[INFO] API Key đã được cung cấp.")
    print("Đang cấu hình Google AI...")
    try:
        genai.configure(api_key=API_KEY)
        genai_configured = True
        print("[OK] Google AI đã được cấu hình thành công.")
    except Exception as e:
        print(f"[ERROR] Không thể cấu hình Google AI: {e}")
        genai_configured = False

MODEL_NAME_CHAT = "gemini-2.5-pro-preview-06-05" 
print(f"Sử dụng model chat: {MODEL_NAME_CHAT}")


# --- HÀM format_api_error (Giữ nguyên) ---
def format_api_error(e):
    error_message = str(e)
    error_type = type(e).__name__
    print(f"[ERROR] Lỗi khi gọi API: {error_type} - {error_message}")

    if isinstance(e, google_exceptions.PermissionDenied):
        if "API key not valid" in error_message or "API_KEY_INVALID" in error_message:
            return "❌ Lỗi: API Key không hợp lệ. Google đã từ chối key này. Vui lòng kiểm tra lại!"
        elif "permission to access model" in error_message:
            return f"❌ Lỗi: API Key này không có quyền truy cập model '{MODEL_NAME_CHAT}'. Hãy thử một model khác hoặc kiểm tra lại quyền của API Key."
        else:
            return f"❌ Lỗi: Từ chối quyền truy cập (PermissionDenied): {error_message}"
    elif isinstance(e, google_exceptions.InvalidArgument) and "API key not valid" in error_message:
        return "❌ Lỗi: API Key không hợp lệ (InvalidArgument). Vui lòng nhập key cho đúng."
    elif isinstance(e, google_exceptions.NotFound):
        return f"❌ Lỗi: Không tìm thấy model '{MODEL_NAME_CHAT}'. Cậu chắc là nó tồn tại không đấy?!"
    elif isinstance(e, google_exceptions.ResourceExhausted):
        return "❌ Lỗi: Hết quota rồi! Vui lòng kiểm tra giới hạn sử dụng của bạn trên Google AI Studio."
    elif isinstance(e, google_exceptions.DeadlineExceeded):
        return "❌ Lỗi: Yêu cầu mất quá nhiều thời gian để xử lý. Vui lòng thử lại sau."
    else:
        return f"❌ Lỗi không xác định khi gọi AI ({error_type}): {error_message}"

# --- HÀM respond (PHIÊN BẢN CUỐI CÙNG VỚI HIỆU ỨNG GÕ CHỮ) ---
def respond(message, chat_history_state):
    if not genai_configured:
        error_msg = "❌ Lỗi: Google AI chưa được cấu hình đúng cách. Vui lòng kiểm tra lại API KEY trong code."
        chat_history_state = (chat_history_state or []) + [[message, error_msg]]
        return "", chat_history_state, chat_history_state

    if not message or message.strip() == "":
        no_input_responses = [
            "Này! Định hỏi gì thì nói đi chứ?",
            "Im lặng thế? Tính làm gì?",
            "Hửm? Sao không nói gì hết vậy?",
        ]
        response_text = random.choice(no_input_responses)
        chat_history_state = (chat_history_state or []) + [[None, response_text]]
        return "", chat_history_state, chat_history_state

    # Xây dựng lịch sử chat cho API
    history = []
    if chat_history_state:
        for u, m in chat_history_state:
            is_error = m and isinstance(m, str) and (m.startswith("❌") or m.startswith("⚠️"))
            is_no_input_response = u is None
            if u and isinstance(u, str) and u.strip() and not is_no_input_response:
                history.append({'role': 'user', 'parts': [u]})
            if m and isinstance(m, str) and m.strip() and not is_error and not is_no_input_response:
                history.append({'role': 'model', 'parts': [m]})

    # Thêm tin nhắn mới vào giao diện trước khi gọi API
    chat_history_state = (chat_history_state or []) + [[message, ""]]
    idx = len(chat_history_state) - 1

    full_text = ""
    
    try:
        model = genai.GenerativeModel(MODEL_NAME_CHAT)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        chat = model.start_chat(history=history)
        # Yêu cầu API trả về dữ liệu theo kiểu stream
        response = chat.send_message(message, stream=True, safety_settings=safety_settings)

        # Vòng lặp ngoài: Nhận từng chunk (gói dữ liệu) từ API.
        # Vòng lặp này sẽ "dừng" để đợi cho đến khi API gửi về một chunk mới.
        for chunk in response:
            # Xử lý các lỗi có thể xảy ra với chunk (giữ nguyên)
            if hasattr(chunk, 'prompt_feedback') and chunk.prompt_feedback.block_reason:
                block_reason = chunk.prompt_feedback.block_reason_message
                error_msg = f"⚠️ Yêu cầu của bạn đã bị chặn với lý do: {block_reason}. Vui lòng không hỏi những điều nhạy cảm."
                chat_history_state[idx][1] = error_msg
                yield "", chat_history_state, chat_history_state
                return

            # Lấy phần text từ trong chunk
            chunk_text = ""
            if chunk.parts:
                chunk_text = "".join(part.text for part in chunk.parts if hasattr(part, 'text'))

            if chunk_text:
                # Vòng lặp trong: Lặp qua từng KÝ TỰ của chunk đó.
                for char in chunk_text:
                    # Nối từng ký tự vào chuỗi đầy đủ
                    full_text += char
                    # Cập nhật ô trả lời của bot trong lịch sử chat
                    chat_history_state[idx][1] = full_text
                    
                    # ----> ĐÂY LÀ CHÌA KHÓA TẠO HIỆU ỨNG GÕ CHỮ <----
                    # Tạm dừng một chút xíu giữa mỗi ký tự.
                    # Bạn có thể thay đổi số này để gõ nhanh/chậm hơn (ví dụ: 0.01 để nhanh, 0.1 để chậm).
                    time.sleep(0.03)
                    
                    # Cập nhật giao diện ngay sau mỗi ký tự
                    yield "", chat_history_state, chat_history_state

        # Xử lý trường hợp API không trả về gì cả
        if not full_text:
             chat_history_state[idx][1] = "..."
             yield "", chat_history_state, chat_history_state

    except Exception as e:
        error_text = format_api_error(e)
        chat_history_state[idx][1] = error_text
        yield "", chat_history_state, chat_history_state


# --- GIAO DIỆN GRADIO (Giữ nguyên) ---
with gr.Blocks(theme=gr.themes.Default()) as demo:
    gr.HTML('''
        <style>
        /* (Toàn bộ CSS của bạn được giữ nguyên ở đây) */
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@800&display=swap');
        body, .gradio-container { background-color: #f5f4ed !important; }
        * { font-family: 'Nunito', sans-serif !important; }
        .gradio-container .prose h2 { color: #CC7F66 !important; text-align: center; margin-bottom: 1rem; }
        .chatbot .message.user p, .chatbot .message.bot p { color: #8B4513 !important; }
        .chatbot .message.bot span:first-child:contains("❌"), .chatbot .message.bot span:first-child:contains("⚠️") { color: #D2691E !important; font-weight: bold; }
        .gradio-textbox textarea, .gradio-button span { color: #8B4513 !important; }
        .gradio-textbox textarea::placeholder { color: #A0522D; opacity: 0.7; }
        .chatbot .message.bot, .chatbot .message.user {
            border: 1px solid #FFDAB9 !important; border-radius: 15px !important;
            padding: 10px 15px !important; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            max-width: 85%; word-wrap: break-word; overflow-wrap: break-word; white-space: pre-wrap; margin-bottom: 8px;
        }
        .chatbot .message.user { background: #FFF5E1 !important; border-radius: 15px 15px 0 15px !important; margin-left: auto; margin-right: 10px; }
        .chatbot .message.bot { background: #ffffff !important; border-radius: 15px 15px 15px 0 !important; margin-right: auto; margin-left: 10px; }
        .gradio-button { background-color: #FFDAB9 !important; border: 1px solid #CC7F66 !important; }
        .gradio-button:hover { background-color: #FFCFAF !important; box-shadow: 0 2px 4px rgba(0,0,0,0.15); }
        </style>
    ''')
    gr.Markdown("## ZyraX - tạo bởi Dũng")

    chatbot = gr.Chatbot(
        label="Cuộc trò chuyện",
        height=500,
        bubble_full_width=False,
        latex_delimiters=[{"left": "$$", "right": "$$", "display": True}, {"left": "$", "right": "$", "display": False}]
    )
    state = gr.State([])

    with gr.Row():
        txt = gr.Textbox(placeholder="Hỏi tôi điều gì đó...", label="Bạn", scale=4)
        btn = gr.Button("Gửi", variant="primary")

    clr = gr.Button("🗑️ Xóa cuộc trò chuyện")

    # Kết nối sự kiện
    txt.submit(respond, [txt, state], [txt, chatbot, state])
    btn.click(respond, [txt, state], [txt, chatbot, state])
    clr.click(lambda: (None, [], []), outputs=[txt, chatbot, state], queue=False)

# --- KHỞI CHẠY APP ---
print("Đang khởi chạy Gradio UI...")
# Bắt buộc phải có .queue() để xử lý các hàm generator (yield)
demo.queue().launch(
    server_name='0.0.0.0',
    server_port=int(os.environ.get('PORT', 7860)),
    debug=False,
)
print("Gradio UI đã khởi chạy.")
