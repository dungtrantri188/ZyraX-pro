# -*- coding: utf-8 -*-
import os
import sys
import time  # <-- Đã thêm ở lần trước
import gradio as gr
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# --- API Key (VẪN CÓ RỦI RO BẢO MẬT CAO KHI ĐỂ TRONG CODE) ---
API_KEY = "AIzaSyBybfBSDLx39DdnZbHyLbd21tQAdfHtbeE"

genai_configured = False
# 1) Kiểm tra và cấu hình API Key (Giữ nguyên)
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

# 2) Model và Hàm trợ giúp định dạng lỗi (Giữ nguyên)
MODEL_NAME_CHAT = "gemini-2.5-flash-preview-04-17"
print(f"Sử dụng model chat: {MODEL_NAME_CHAT}")

def format_api_error(e):
    # ... (Hàm format_api_error giữ nguyên như phiên bản trước) ...
    error_message = str(e)
    error_type = type(e).__name__
    print(f"[ERROR] Lỗi khi gọi API: {error_type} - {error_message}")

    if isinstance(e, google_exceptions.PermissionDenied):
        if "API key not valid" in error_message or "API_KEY_INVALID" in error_message:
             return "❌ Lỗi: API Key được cấu hình nhưng Google từ chối khi sử dụng (API_KEY_INVALID). Có thể key đã bị vô hiệu hóa."
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


# 3) Hàm callback Gradio (Sửa đổi để thêm emoji 🔥💨 khi đang stream)
def respond(message, chat_history_state):
    if not genai_configured:
        error_msg = "❌ Lỗi: Google AI chưa được cấu hình đúng cách (API Key có vấn đề hoặc cấu hình thất bại)."
        if isinstance(chat_history_state, list):
             chat_history_state.append([message, error_msg])
        else:
             chat_history_state = [[message, error_msg]]
        return "", chat_history_state, chat_history_state

    current_chat_history = list(chat_history_state)
    gemini_history = []
    for user_msg, model_msg in current_chat_history:
        if user_msg and isinstance(user_msg, str):
             gemini_history.append({'role': 'user', 'parts': [user_msg]})
        if model_msg and isinstance(model_msg, str) and not model_msg.startswith("❌") and not model_msg.startswith("⚠️"):
             gemini_history.append({'role': 'model', 'parts': [model_msg]})

    print(f"Lịch sử gửi tới Gemini: {gemini_history}")
    print(f"Prompt mới: '{message[:70]}...'")

    # Thêm placeholder cho phản hồi của bot ngay lập tức
    current_chat_history.append([message, ""])
    response_index = len(current_chat_history) - 1 # Index của phần tử cần cập nhật

    full_response_text = ""
    final_status_message = "" # Lưu trữ cảnh báo hoặc lỗi cuối cùng

    try:
        model = genai.GenerativeModel(MODEL_NAME_CHAT)
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(message, stream=True)

        # --- THAY ĐỔI LOGIC STREAM ---
        for chunk in response:
            try:
                chunk_text = getattr(chunk, 'text', '')
                if chunk_text:
                    for char in chunk_text:
                        full_response_text += char
                        # Văn bản hiển thị tạm thời với emoji ở cuối
                        display_text = full_response_text + " 🔥💨"
                        current_chat_history[response_index][1] = display_text
                        yield "", current_chat_history, current_chat_history
                        time.sleep(0.02) # Giữ độ trễ làm chậm chữ
                else:
                    # (Logic kiểm tra block/finish reason)
                    block_reason = getattr(getattr(chunk, 'prompt_feedback', None), 'block_reason', None)
                    finish_reason = getattr(getattr(chunk.candidates[0], 'finish_reason', None)) if chunk.candidates else None
                    reason_text = ""
                    should_stop = False
                    if block_reason: reason_text, should_stop = f"Yêu cầu/Phản hồi bị chặn ({block_reason})", True
                    elif finish_reason and finish_reason != 'STOP': reason_text, should_stop = f"Phản hồi bị dừng ({finish_reason})", True

                    if reason_text:
                        print(f"[WARN] {reason_text}")
                        # Lưu cảnh báo để thêm vào cuối, không yield ngay
                        final_status_message = f"\n⚠️ ({reason_text})"
                        if should_stop:
                             break # Thoát khỏi vòng lặp chunk nếu cần dừng

            except Exception as inner_e:
                print(f"[ERROR] Lỗi khi xử lý chunk stream: {type(inner_e).__name__} - {inner_e}")
                # Lưu thông báo lỗi để thêm vào cuối
                final_status_message = f"\n⚠️ (Lỗi khi xử lý phần tiếp theo: {inner_e})"
                break # Thoát khỏi vòng lặp chunk

        # --- Vòng lặp stream kết thúc (bình thường hoặc do break) ---
        # Dọn dẹp: Xóa emoji và thêm thông báo trạng thái (nếu có)
        final_clean_text = full_response_text
        if final_status_message and final_status_message not in final_clean_text:
             final_clean_text += final_status_message

        current_chat_history[response_index][1] = final_clean_text
        # Yield trạng thái cuối cùng, đã được dọn dẹp
        yield "", current_chat_history, current_chat_history
        print("[OK] Streaming hoàn tất." if not final_status_message else "[WARN/ERROR] Streaming kết thúc với trạng thái.")
        # --- KẾT THÚC THAY ĐỔI ---

    except Exception as e:
        # Xử lý lỗi API bên ngoài (ví dụ: key không hợp lệ)
        error_msg = format_api_error(e)
        # Cập nhật phần tử placeholder với thông báo lỗi
        current_chat_history[response_index][1] = error_msg
        yield "", current_chat_history, current_chat_history


# 4) UI Gradio (Giữ nguyên)
with gr.Blocks(theme=gr.themes.Default()) as demo:
    gr.Markdown("## ZyRa X - tạo bởi Dũng")

    chatbot = gr.Chatbot(
        label="Chatbot",
        height=500,
        bubble_full_width=False,
        type='tuples',
        render_markdown=True,
        latex_delimiters=[
            { "left": "$$", "right": "$$", "display": True },
            { "left": "$", "right": "$", "display": False },
        ]
    )
    chat_history_state = gr.State(value=[])

    with gr.Row():
        msg = gr.Textbox(placeholder="Nhập câu hỏi của bạn...", label="Bạn", scale=4, container=False)
        send_btn = gr.Button("Gửi")

    clear_btn = gr.Button("🗑️ Xóa cuộc trò chuyện")

    # --- Kết nối sự kiện (Giữ nguyên) ---
    submit_event = msg.submit(respond, inputs=[msg, chat_history_state], outputs=[msg, chatbot, chat_history_state])
    click_event = send_btn.click(respond, inputs=[msg, chat_history_state], outputs=[msg, chatbot, chat_history_state])

    # Hàm xóa chat (Giữ nguyên)
    def clear_chat_func(): return "", [], []
    clear_btn.click(clear_chat_func, outputs=[msg, chatbot, chat_history_state], queue=False)

# 5) Chạy ứng dụng (Giữ nguyên)
print("Đang khởi chạy Gradio UI...")
demo.queue().launch(server_name='0.0.0.0', server_port=int(os.environ.get('PORT', 7860)), debug=False)
print("Gradio UI đã khởi chạy.")
