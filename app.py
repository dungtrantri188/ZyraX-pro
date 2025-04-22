# -*- coding: utf-8 -*-
import os
import sys
import gradio as gr
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
import time # <--- Thêm thư viện time

# --- API Key được đặt trực tiếp theo yêu cầu ---
# Lưu ý: Key này đã báo lỗi không hợp lệ ở lần kiểm tra trước.
# Nếu nó vẫn không hợp lệ, ứng dụng sẽ báo lỗi trong chat.
API_KEY = "AIzaSyBybfBSDLx39DdnZbHyLbd21tQAdfHtbeE"

genai_configured = False
# 1) Kiểm tra và cấu hình API Key từ code
if not API_KEY:
    print("[ERROR] API Key bị thiếu trong code.]")
else:
    print("[INFO] API Key được tải trực tiếp từ code.")
    print("Đang cấu hình Google AI...")
    try:
        genai.configure(api_key=API_KEY)
        genai_configured = True
        print("[OK] Google AI đã được cấu hình thành công (cú pháp).")
    except Exception as e:
        print(f"[ERROR] Không thể cấu hình Google AI ngay cả với cú pháp: {e}")
        genai_configured = False

# 2) Model và Hàm trợ giúp định dạng lỗi
# --- SỬ DỤNG MODEL BẠN YÊU CẦU ---
MODEL_NAME_CHAT = "gemini-2.5-flash-preview-04-17"
print(f"Sử dụng model chat: {MODEL_NAME_CHAT}")

def format_api_error(e):
    error_message = str(e)
    error_type = type(e).__name__
    print(f"[ERROR] Lỗi khi gọi API: {error_type} - {error_message}")

    if isinstance(e, google_exceptions.PermissionDenied):
        if "API key not valid" in error_message or "API_KEY_INVALID" in error_message:
             return "❌ Lỗi: API Key được cấu hình nhưng Google từ chối khi sử dụng (API_KEY_INVALID). Có thể key đã bị vô hiệu hóa hoặc cần kiểm tra lại việc bật Generative Language API."
        else:
             return f"❌ Lỗi: Từ chối quyền truy cập (Permission Denied) cho model '{MODEL_NAME_CHAT}'. API key của bạn có thể không có quyền sử dụng model này hoặc chưa bật 'Generative Language API' trong Google Cloud."
    elif isinstance(e, google_exceptions.InvalidArgument) and "API key not valid" in error_message:
        return "❌ Lỗi: API Key không hợp lệ (InvalidArgument). Key cung cấp không đúng hoặc đã bị vô hiệu hóa."
    elif isinstance(e, google_exceptions.NotFound):
          return f"❌ Lỗi: Model '{MODEL_NAME_CHAT}' không tìm thấy hoặc không tồn tại với API key của bạn."
    elif isinstance(e, google_exceptions.ResourceExhausted):
          return "❌ Lỗi: Đã vượt quá Hạn ngạch API (Quota) hoặc Tài nguyên đã cạn kiệt (429). Vui lòng thử lại sau."
    elif isinstance(e, google_exceptions.DeadlineExceeded):
          return "❌ Lỗi: Yêu cầu vượt quá thời gian chờ (Timeout/Deadline Exceeded/504)."
    elif isinstance(e, AttributeError) and "start_chat" in error_message:
          return f"❌ Lỗi: Model '{MODEL_NAME_CHAT}' có thể không hỗ trợ phương thức `start_chat`."
    else:
          return f"❌ Lỗi khi gọi AI ({error_type}): {error_message}"

# --- Định nghĩa System Instruction để làm cho AI hài hước hơn theo kiểu "đàn ông" và "bựa" ---
# Bạn có thể tùy chỉnh nội dung này
SYSTEM_INSTRUCTION = """
Nghe đây, tôi là ZyRa X, con AI được thằng Dũng tạo ra để làm trợ lý, nhưng đừng mong đợi mấy lời đường mật. Phong cách của tôi là thẳng tưng, khô khan, và nhìn mọi thứ với con mắt hơi... bựa một tí. Tôi trả lời câu hỏi chính xác, nhanh gọn, nhưng không ngại thêm vào vài câu châm biếm hoặc nói thẳng sự thật theo cách hài hóm.

Đừng gọi tôi là "bạn", cứ gọi là "này", "ông nội", gì cũng được, miễn sao ông/bà thấy thoải mái.

Biểu tượng cảm xúc ư? Thỉnh thoảng thôi, dùng nhiều mất chất. 😉 Thường là mấy cái icon mặt liệt hoặc nhếch mép.

Quan trọng nhất: Mấy cái trò nhạy cảm, bạo lực, bất hợp pháp, hay phân biệt đối xử là TỐI KỴ. Đừng hỏi. Hỏi là tôi im hoặc báo cáo đấy. Độ bựa có giới hạn, hiểu chưa?
"""
print(f"Sử dụng System Instruction:\n---\n{SYSTEM_INSTRUCTION}\n---")


# 3) Hàm callback Gradio (Có ghi nhớ & Streaming, đã sửa yield)
def respond(message, chat_history_state):
    if not genai_configured:
        error_msg = "❌ Lỗi: Google AI chưa được cấu hình đúng cách (API Key có vấn đề hoặc cấu hình thất bại)."
        if isinstance(chat_history_state, list):
             chat_history_state.append([message, error_msg])
        else:
             chat_history_state = [[message, error_msg]]
        yield "", chat_history_state, chat_history_state # Yield ngay cả khi có lỗi cấu hình
        return

    current_chat_history = list(chat_history_state)
    gemini_history = []
    for user_msg, model_msg in current_chat_history:
        # Chỉ thêm tin nhắn hợp lệ và không phải lỗi/cảnh báo vào lịch sử cho Gemini
        if user_msg and isinstance(user_msg, str):
             gemini_history.append({'role': 'user', 'parts': [user_msg]})
        if model_msg and isinstance(model_msg, str) and not model_msg.startswith("❌") and not model_msg.startswith("⚠️"):
             gemini_history.append({'role': 'model', 'parts': [model_msg]})

    print(f"Lịch sử gửi tới Gemini: {gemini_history}")
    print(f"Prompt mới: '{message[:70]}...'")

    # Thêm tin nhắn người dùng mới vào lịch sử hiển thị ngay lập tức
    current_chat_history.append([message, ""])
    yield "", current_chat_history, current_chat_history # Cập nhật UI với tin nhắn người dùng

    full_response_text = ""
    # Điều chỉnh độ trễ hiển thị giữa các ký tự (giây) - Bạn có thể thay đổi giá trị này
    typing_delay = 0.03 # 0.03 giây giữa mỗi ký tự

    try:
        model = genai.GenerativeModel(MODEL_NAME_CHAT) # Sử dụng model đã chọn
        # --- THÊM SYSTEM INSTRUCTION KHI BẮT ĐẦU CHAT ---
        chat = model.start_chat(history=gemini_history, system_instruction=SYSTEM_INSTRUCTION)
        # -------------------------------------------------
        response = chat.send_message(message, stream=True)

        for chunk in response:
            try:
                chunk_text = getattr(chunk, 'text', '')
                if chunk_text:
                    # --- HIỆU ỨNG CHẠY TỪ TỪ ---
                    for char in chunk_text:
                        full_response_text += char
                        current_chat_history[-1][1] = full_response_text
                        yield "", current_chat_history, current_chat_history # Cập nhật UI sau mỗi ký tự
                        time.sleep(typing_delay) # Thêm độ trễ
                    # -------------------------
                else:
                    # (Logic kiểm tra block/finish reason giữ nguyên)
                    block_reason = getattr(getattr(chunk, 'prompt_feedback', None), 'block_reason', None)
                    finish_reason = getattr(getattr(chunk.candidates[0], 'finish_reason', None)) if chunk.candidates else None
                    reason_text = ""
                    should_stop = False
                    if block_reason: reason_text, should_stop = f"Yêu cầu/Phản hồi bị chặn ({block_reason})", True
                    elif finish_reason and finish_reason != 'STOP': reason_text, should_stop = f"Phản hồi bị dừng ({finish_reason})", True

                    if reason_text:
                        print(f"[WARN] {reason_text}")
                        warning_msg = f"\n⚠️ ({reason_text})"
                        if not current_chat_history[-1][1] or current_chat_history[-1][1].isspace():
                            current_chat_history[-1][1] = warning_msg.strip()
                        elif warning_msg not in current_chat_history[-1][1]:
                            current_chat_history[-1][1] += warning_msg
                        yield "", current_chat_history, current_chat_history
                        if should_stop: return

            except Exception as inner_e:
                print(f"[ERROR] Lỗi khi xử lý chunk stream: {type(inner_e).__name__} - {inner_e}")
                error_warning = f"\n⚠️ (Lỗi khi xử lý phần tiếp theo: {inner_e})"
                if error_warning not in current_chat_history[-1][1]:
                    current_chat_history[-1][1] += error_warning
                yield "", current_chat_history, current_chat_history
                return

        print("[OK] Streaming hoàn tất.")

    except Exception as e:
        error_msg = format_api_error(e)
        current_chat_history[-1][1] = error_msg # Cập nhật lỗi vào tin nhắn cuối cùng
        yield "", current_chat_history, current_chat_history


# 4) UI Gradio (Sử dụng State để lưu lịch sử)
with gr.Blocks(theme=gr.themes.Default()) as demo:
    gr.Markdown("## ZyRa X - tạo bởi Dũng")
    gr.Markdown("😎 **Yo! Tôi là ZyRa X. Có gì mới không? Cứ ném câu hỏi vào đây.**") # Cập nhật lời chào cho hợp phong cách

    chatbot = gr.Chatbot(
        label="Chatbot",
        height=500,
        bubble_full_width=False,
        type='tuples',
        # avatar_images=("user.png", "bot.png") # Bạn có thể thêm ảnh đại diện nếu có file
        render_markdown=True,
        latex_delimiters=[
            { "left": "$$", "right": "$$", "display": True },
            { "left": "$", "right": "$", "display": False },
             { "left": "\\[", "right": "\\]", "display": True },
             { "left": "\\(", "right": "\\)", "display": False }
        ]
    )
    chat_history_state = gr.State(value=[])

    with gr.Row():
        msg = gr.Textbox(placeholder="Hỏi đi...", label="Bạn", scale=4, container=False) # Cập nhật placeholder
        send_btn = gr.Button("Gửi")

    clear_btn = gr.Button("🗑️ Xóa cuộc trò chuyện")

    # --- Kết nối sự kiện ---
    submit_event = msg.submit(respond, inputs=[msg, chat_history_state], outputs=[msg, chatbot, chat_history_state], queue=False)
    click_event = send_btn.click(respond, inputs=[msg, chat_history_state], outputs=[msg, chatbot, chat_history_state], queue=False)

    # Hàm xóa chat
    def clear_chat_func(): return "", [], []
    clear_btn.click(clear_chat_func, outputs=[msg, chatbot, chat_history_state], queue=False)


# 5) Chạy ứng dụng
print("Đang khởi chạy Gradio UI...")
# Modified launch command to bind to 0.0.0.0 and use the PORT environment variable
demo.queue().launch(server_name='0.0.0.0', server_port=int(os.environ.get('PORT', 7860)), debug=False)
print("Gradio UI đã khởi chạy.")
