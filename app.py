# -*- coding: utf-8 -*-
import os
import sys
import time  # Thêm import time
import gradio as gr
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# --- API Key (VẪN CÓ RỦI RO BẢO MẬT CAO KHI ĐỂ TRỰC TIẾP TRONG CODE) ---
# Lưu ý: Key này đã báo lỗi không hợp lệ ở lần kiểm tra trước.
# Nếu nó vẫn không hợp lệ, ứng dụng sẽ báo lỗi trong chat.
API_KEY = "AIzaSyBybfBSDLx39DdnZbHyLbd21tQAdfHtbeE" # <-- RỦI RO BẢO MẬT

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
MODEL_NAME_CHAT = "gemini-2.5-flash-preview-04-17" # Sử dụng model preview
print(f"Sử dụng model chat: {MODEL_NAME_CHAT}")

def format_api_error(e):
    """Định dạng lỗi API của Google thành thông báo thân thiện."""
    error_message = str(e)
    error_type = type(e).__name__
    print(f"[ERROR] Lỗi khi gọi API: {error_type} - {error_message}") # Log lỗi

    if isinstance(e, google_exceptions.PermissionDenied):
        if "API key not valid" in error_message or "API_KEY_INVALID" in error_message:
             return "❌ Lỗi: API Key được cấu hình nhưng Google từ chối khi sử dụng (API_KEY_INVALID). Có thể key đã bị vô hiệu hóa."
        else: # Lỗi quyền truy cập model
             return f"❌ Lỗi: Từ chối quyền truy cập (Permission Denied) cho model '{MODEL_NAME_CHAT}'. API key của bạn có thể không có quyền sử dụng model này hoặc chưa bật 'Generative Language API' trong Google Cloud."
    elif isinstance(e, google_exceptions.InvalidArgument) and "API key not valid" in error_message:
        # Lỗi key không hợp lệ như log trước đó
        return "❌ Lỗi: API Key không hợp lệ (InvalidArgument). Key cung cấp không đúng hoặc đã bị vô hiệu hóa."
    elif isinstance(e, google_exceptions.NotFound):
         return f"❌ Lỗi: Model '{MODEL_NAME_CHAT}' không tìm thấy hoặc không tồn tại với API key của bạn."
    elif isinstance(e, google_exceptions.ResourceExhausted):
         return "❌ Lỗi: Đã vượt quá Hạn ngạch API (Quota) hoặc Tài nguyên đã cạn kiệt (429). Vui lòng thử lại sau."
    elif isinstance(e, google_exceptions.DeadlineExceeded):
         return "❌ Lỗi: Yêu cầu vượt quá thời gian chờ (Timeout/Deadline Exceeded/504)."
    elif isinstance(e, AttributeError) and "start_chat" in error_message:
         return f"❌ Lỗi: Model '{MODEL_NAME_CHAT}' có thể không hỗ trợ phương thức `start_chat`."
    else: # Các lỗi khác
         return f"❌ Lỗi khi gọi AI ({error_type}): {error_message}"


# 3) Hàm callback Gradio (Có ghi nhớ, Streaming chậm, Emoji tạm thời)
def respond(message, chat_history_state):
    """Xử lý tin nhắn người dùng, gọi AI và cập nhật giao diện."""
    if not genai_configured:
        error_msg = "❌ Lỗi: Google AI chưa được cấu hình đúng cách (API Key có vấn đề hoặc cấu hình thất bại)."
        if isinstance(chat_history_state, list):
             chat_history_state.append([message, error_msg])
        else:
             chat_history_state = [[message, error_msg]]
        return "", chat_history_state, chat_history_state

    current_chat_history = list(chat_history_state) # Tạo bản sao để tránh thay đổi state gốc trực tiếp

    # Chuyển đổi lịch sử Gradio sang định dạng Gemini
    gemini_history = []
    for user_msg, model_msg in current_chat_history:
        if user_msg and isinstance(user_msg, str):
             gemini_history.append({'role': 'user', 'parts': [user_msg]})
        # Chỉ thêm tin nhắn thành công của model vào lịch sử gửi đi
        if model_msg and isinstance(model_msg, str) and not model_msg.startswith("❌") and not model_msg.startswith("⚠️"):
             gemini_history.append({'role': 'model', 'parts': [model_msg]})

    print(f"Lịch sử gửi tới Gemini: {gemini_history}")
    print(f"Prompt mới: '{message[:70]}...'")

    # Thêm placeholder cho phản hồi của bot vào lịch sử hiển thị ngay lập tức
    current_chat_history.append([message, ""])
    response_index = len(current_chat_history) - 1 # Index của phần tử cần cập nhật

    full_response_text = ""         # Lưu trữ text gốc từ AI
    final_status_message = ""     # Lưu trữ cảnh báo hoặc lỗi cuối cùng

    try:
        model = genai.GenerativeModel(MODEL_NAME_CHAT)
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(message, stream=True)

        # Xử lý từng chunk trong stream
        for chunk in response:
            try:
                chunk_text = getattr(chunk, 'text', '')
                if chunk_text:
                    # Thêm từng ký tự để tạo hiệu ứng gõ chữ
                    for char in chunk_text:
                        full_response_text += char
                        # Hiển thị text hiện tại + emoji tạm thời
                        display_text = full_response_text + " 🔥💨"
                        current_chat_history[response_index][1] = display_text
                        yield "", current_chat_history, current_chat_history
                        # Dừng một chút để làm chậm tốc độ
                        time.sleep(0.02) # Điều chỉnh giá trị này để thay đổi tốc độ
                else:
                    # Kiểm tra lý do dừng hoặc bị chặn
                    block_reason = getattr(getattr(chunk, 'prompt_feedback', None), 'block_reason', None)
                    finish_reason = getattr(getattr(chunk.candidates[0], 'finish_reason', None)) if chunk.candidates else None
                    reason_text = ""
                    should_stop = False
                    if block_reason: reason_text, should_stop = f"Yêu cầu/Phản hồi bị chặn ({block_reason})", True
                    elif finish_reason and finish_reason != 'STOP': reason_text, should_stop = f"Phản hồi bị dừng ({finish_reason})", True

                    if reason_text:
                        print(f"[WARN] {reason_text}")
                        # Lưu cảnh báo để hiển thị ở cuối cùng
                        final_status_message = f"\n⚠️ ({reason_text})"
                        if should_stop:
                             break # Thoát khỏi vòng lặp xử lý chunk

            except Exception as inner_e:
                # Xử lý lỗi xảy ra trong quá trình xử lý chunk
                print(f"[ERROR] Lỗi khi xử lý chunk stream: {type(inner_e).__name__} - {inner_e}")
                # Lưu thông báo lỗi để hiển thị ở cuối
                final_status_message = f"\n⚠️ (Lỗi khi xử lý phần tiếp theo: {inner_e})"
                break # Thoát khỏi vòng lặp xử lý chunk

        # --- Vòng lặp stream kết thúc ---

        # Dọn dẹp: Xóa emoji và thêm thông báo trạng thái (nếu có)
        final_clean_text = full_response_text
        if final_status_message and final_status_message not in final_clean_text:
             # Chỉ thêm nếu chưa có hoặc không phải là phần của text gốc
             final_clean_text += final_status_message

        # Cập nhật lịch sử với text cuối cùng đã được dọn dẹp
        current_chat_history[response_index][1] = final_clean_text
        # Yield trạng thái cuối cùng
        yield "", current_chat_history, current_chat_history
        print("[OK] Streaming hoàn tất." if not final_status_message else "[WARN/ERROR] Streaming kết thúc với trạng thái.")

    except Exception as e:
        # Xử lý lỗi API chính (ví dụ: key không hợp lệ, không tìm thấy model, hết quota)
        error_msg = format_api_error(e)
        # Cập nhật phần tử placeholder với thông báo lỗi
        current_chat_history[response_index][1] = error_msg
        yield "", current_chat_history, current_chat_history


# 4) UI Gradio (Sử dụng State và CSS tùy chỉnh)

# Định nghĩa CSS tùy chỉnh để áp dụng phông chữ Nunito ExtraBold 800
custom_font_css = """
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@800&display=swap'); /* Yêu cầu weight 800 */

/* Nhắm mục tiêu cụ thể đến các bong bóng chat của bot (AI) */
.gradio-container .chatbot .message.bot {
    font-family: 'Nunito', sans-serif !important; /* Áp dụng phông Nunito */
    font-weight: 800 !important; /* Áp dụng weight 800 (ExtraBold) */
}

/* (Tùy chọn) Bạn có thể đặt phông khác cho người dùng nếu muốn */
/*
.gradio-container .chatbot .message.user {
    font-family: sans-serif !important;
}
*/
"""

# Xây dựng giao diện với Blocks và CSS tùy chỉnh
with gr.Blocks(theme=gr.themes.Default(), css=custom_font_css) as demo:
    gr.Markdown("## ZyRa X - tạo bởi Dũng")
    # Đã xóa cảnh báo bảo mật khỏi UI

    chatbot = gr.Chatbot(
        label="Chatbot",
        height=500,
        bubble_full_width=False,
        type='tuples', # Chỉ định rõ ràng type cho chatbot
        render_markdown=True, # Bật hiển thị markdown
        latex_delimiters=[   # Cấu hình hiển thị LaTeX
            { "left": "$$", "right": "$$", "display": True },
            { "left": "$", "right": "$", "display": False },
        ]
    )
    # Sử dụng State để lưu trữ lịch sử chat giữa các lượt gọi hàm respond
    chat_history_state = gr.State(value=[])

    with gr.Row():
        msg = gr.Textbox(
            placeholder="Nhập câu hỏi của bạn...",
            label="Bạn",
            scale=4,
            container=False # Để textbox và button nằm sát nhau hơn
        )
        send_btn = gr.Button("Gửi")

    clear_btn = gr.Button("🗑️ Xóa cuộc trò chuyện")

    # --- Kết nối các sự kiện với hàm xử lý ---
    # Gửi khi nhấn Enter trong Textbox
    submit_event = msg.submit(
        fn=respond,
        inputs=[msg, chat_history_state],
        outputs=[msg, chatbot, chat_history_state] # msg trống, chatbot cập nhật, state cập nhật
    )
    # Gửi khi nhấn nút "Gửi"
    click_event = send_btn.click(
        fn=respond,
        inputs=[msg, chat_history_state],
        outputs=[msg, chatbot, chat_history_state]
    )

    # Hàm và sự kiện cho nút "Xóa cuộc trò chuyện"
    def clear_chat_func():
        """Xóa nội dung textbox và lịch sử chat."""
        return "", [], [] # Trả về giá trị rỗng cho msg, list rỗng cho chatbot và state
    clear_btn.click(
        fn=clear_chat_func,
        outputs=[msg, chatbot, chat_history_state],
        queue=False # Không cần đưa vào hàng đợi vì hành động nhanh
    )

# 5) Chạy ứng dụng Gradio
print("Đang khởi chạy Gradio UI...")
# Sử dụng server_name='0.0.0.0' để có thể truy cập từ máy khác trong mạng
# Sử dụng PORT từ biến môi trường hoặc mặc định là 7860
demo.queue().launch(
    server_name='0.0.0.0',
    server_port=int(os.environ.get('PORT', 7860)),
    debug=False # Tắt chế độ debug khi triển khai
)
print("Gradio UI đã khởi chạy.")
