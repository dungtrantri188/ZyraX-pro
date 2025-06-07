# -*- coding: utf-8 -*-
import os
import time
import random
import gradio as gr
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# --- nhập API key của chatbot gemini nhập sai bị lỗi ---
# THAY API KEY CỦA BẠN VÀO ĐÂY
API_KEY = "AIzaSyAWrCJv5sesCGjaTx3xfLHLXzu4qi4R9EY"

genai_configured = False
# làm cho hàm logic dễ hiểu và dễ nhớ mộ tí, logic kiểm tra: chỉ cần kiểm tra với placeholder mặc định.
if not API_KEY or API_KEY == "YOUR_API_KEY_HERE":
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

# xử dụng con gemini 2.5 flash cho nhanh nhưng vẫn xịn mà .
MODEL_NAME_CHAT = "gemini-2.5-flash-preview-04-17"
print(f"Sử dụng model chat: {MODEL_NAME_CHAT}")


# --- HÀM format_api_error, hàm gọi bị lỗi thì nó sẽ hiện ra cho xemxem  ---
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

# --- HÀM respond (PHIÊN BẢN CUỐI CÙNG VỚI HIỆU ỨNG GÕ CHỮ), hàm hiệu ứng chữ không phải logic gì cho lắm ---
def respond(message, chat_history_state):
    if not genai_configured:
        error_msg = "❌ Lỗi: Google AI chưa được cấu hình đúng cách. Vui lòng kiểm tra lại API KEY trong code."
        chat_history_state = (chat_history_state or []) + [[message, error_msg]]
        return "", chat_history_state, chat_history_state

    # mấy câu cho xàm xàm dép lèo kkk
    if not message or message.strip() == "":
        no_input_responses = [
            "Này! Định hỏi gì thì nói đi chứ?",
            "Im lặng thế? Tính làm gì?",
            "Hửm? Sao không nói gì hết vậy?",
        ]
        response_text = random.choice(no_input_responses)
        chat_history_state = (chat_history_state or []) + [[None, response_text]]
        return "", chat_history_state, chat_history_state
# cái ghi nhớ lịch sử cho con súc vâtyj ghi nhớ kẻo quên là lòi peterpeter
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
            # nó sẽ tạm thời hoặc là fix lỗi lúc ra hiệu ứng in 
            if not chunk.candidates:
                # Đôi khi chunk đầu tiên hoặc cuối cùng không có candidate, bỏ qua
                continue

            # Xử lý lỗi prompt bị chặn ngay từ đầu
            if hasattr(chunk, 'prompt_feedback') and chunk.prompt_feedback.block_reason:
                block_reason = chunk.prompt_feedback.block_reason_message
                error_msg = f"⚠️ Yêu cầu của bạn đã bị chặn với lý do: {block_reason}. Vui lòng không hỏi những điều nhạy cảm."
                chat_history_state[idx][1] = error_msg
                yield "", chat_history_state, chat_history_state
                return
            
            # Xử lý nội dung bị chặn giữa chừng
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
                    time.sleep(0.03) # Điều chỉnh tốc độ gõ chữ
                    yield "", chat_history_state, chat_history_state

        if not full_text:
            chat_history_state[idx][1] = "..."
            yield "", chat_history_state, chat_history_state

    except Exception as e:
        error_text = format_api_error(e)
        chat_history_state[idx][1] = error_text
        yield "", chat_history_state, chat_history_state


# --- phần dưới là giao diện, do là dùng gradio nên là hơi củ chuối, nhưng vẫn okey lắm màmà ---
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

    txt.submit(respond, [txt, state], [txt, chatbot, state])
    btn.click(respond, [txt, state], [txt, chatbot,state])
    clr.click(lambda: (None, [], []), outputs=[txt, chatbot, state], queue=False)


# --- dòng chạy toàn bộ code như cổng đồ, do là dùng sever của render nên dùng cổng 000 ---
print("Đang khởi chạy Gradio UI...")
demo.queue().launch(
    server_name='0.0.0.0',
    server_port=int(os.environ.get('PORT', 7860)),
    debug=False,
)
print("Gradio UI đã khởi chạy.")
