import os
import time
import random
import gradio as gr
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse

# --- ĐỌC API KEY TỪ BIẾN MÔI TRƯỜNG CỦA RENDER ---
# Chúng ta sẽ thiết lập biến 'GEMINI_API_KEY' trong giao diện của Render sau.
API_KEY = os.environ.get("GEMINI_API_KEY")

genai_configured = False
if not API_KEY:
    print("[ERROR] Biến môi trường GEMINI_API_KEY không được tìm thấy.")
else:
    try:
        genai.configure(api_key=API_KEY)
        genai_configured = True
        print("[OK] Google AI đã được cấu hình thành công.")
    except Exception as e:
        print(f"[ERROR] Không thể cấu hình Google AI: {e}")

# --- PHẦN LOGIC CỦA BẠN (GIỮ NGUYÊN) ---
MODEL_NAME_CHAT = "gemini-1.5-flash-latest"
print(f"Sử dụng model chat: {MODEL_NAME_CHAT}")

def format_api_error(e):
    error_message = str(e)
    error_type = type(e).__name__
    print(f"[ERROR] Lỗi khi gọi API: {error_type} - {error_message}")
    if isinstance(e, google_exceptions.PermissionDenied):
        if "API key not valid" in error_message or "API_KEY_INVALID" in error_message:
            return "❌ Lỗi: API Key không hợp lệ. Google đã từ chối key này. Vui lòng kiểm tra lại biến môi trường trên Render!"
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

def respond(message, chat_history_state):
    if not genai_configured:
        error_msg = "❌ Lỗi: Google AI chưa được cấu hình. Quản trị viên vui lòng kiểm tra GEMINI_API_KEY trên server."
        chat_history_state = (chat_history_state or []) + [[message, error_msg]]
        return "", chat_history_state, chat_history_state
    if not message or message.strip() == "":
        no_input_responses = ["Này! Định hỏi gì thì nói đi chứ?", "Im lặng thế? Tính làm gì?", "Hửm? Sao không nói gì hết vậy?"]
        response_text = random.choice(no_input_responses)
        chat_history_state = (chat_history_state or []) + [[None, response_text]]
        return "", chat_history_state, chat_history_state
    history = []
    if chat_history_state:
        for u, m in chat_history_state:
            is_error = m and isinstance(m, str) and (m.startswith("❌") or m.startswith("⚠️"))
            is_no_input_response = u is None
            if u and isinstance(u, str) and u.strip() and not is_no_input_response:
                history.append({'role': 'user', 'parts': [u]})
            if m and isinstance(m, str) and m.strip() and not is_error and not is_no_input_response:
                history.append({'role': 'model', 'parts': [m]})
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
        response = chat.send_message(message, stream=True, safety_settings=safety_settings)
        for chunk in response:
            if not chunk.candidates: continue
            if hasattr(chunk, 'prompt_feedback') and chunk.prompt_feedback.block_reason:
                block_reason = chunk.prompt_feedback.block_reason_message
                error_msg = f"⚠️ Yêu cầu của bạn đã bị chặn với lý do: {block_reason}. Vui lòng không hỏi những điều nhạy cảm."
                chat_history_state[idx][1] = error_msg
                yield "", chat_history_state, chat_history_state
                return
            finish_reason = getattr(chunk.candidates[0], 'finish_reason', None)
            if finish_reason and finish_reason.name != "STOP" and finish_reason.name != "UNSPECIFIED":
                error_msg = f"⚠️ Câu trả lời đã bị dừng đột ngột. Lý do: {finish_reason.name}."
                chat_history_state[idx][1] = full_text + f"\n{error_msg}"
                yield "", chat_history_state, chat_history_state
                return
            chunk_text = ""
            if chunk.parts:
                chunk_text = "".join(part.text for part in chunk.parts if hasattr(part, 'text'))
            if chunk_text:
                for char in chunk_text:
                    full_text += char
                    chat_history_state[idx][1] = full_text
                    time.sleep(0.02)
                    yield "", chat_history_state, chat_history_state
        if not full_text:
            chat_history_state[idx][1] = "..."
            yield "", chat_history_state, chat_history_state
    except Exception as e:
        error_text = format_api_error(e)
        chat_history_state[idx][1] = error_text
        yield "", chat_history_state, chat_history_state

# --- Tạo giao diện Gradio ---
with gr.Blocks() as demo:
    state = gr.State([])
    
    # Các components này chỉ để Gradio biết cấu trúc, chúng sẽ không hiện ra
    # vì giao diện thật nằm ở file index.html
    with gr.Row(visible=False):
        txt_input = gr.Textbox(label="Internal Input")
        chatbot_history = gr.Chatbot(label="Internal History")

    # Liên kết hàm 'respond' với các components ẩn
    txt_input.submit(respond, [txt_input, state], [txt_input, chatbot_history, state])


# --- Dùng FastAPI để phục vụ cả Gradio và file index.html ---
app = FastAPI()

# Định nghĩa một route gốc ("/") để trả về file index.html
@app.get("/")
def read_root():
    return FileResponse("index.html")

# Gắn (mount) ứng dụng Gradio vào một đường dẫn con là "/gradio"
# Toàn bộ API của Gradio sẽ nằm dưới đường dẫn này
app = gr.mount_gradio_app(app, demo, path="/gradio")
