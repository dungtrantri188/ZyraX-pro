# -*- coding: utf-8 -*-
import os
import sys
import time
import random # Đảm bảo đã import random
import gradio as gr
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# --- API Key (VẪN CÓ RỦI RO BẢO MẬT CAO KHI ĐỂ TRỰC TIẾP TRONG CODE) ---
# CẢNH BÁO: Để API Key trực tiếp trong code là rất không an toàn.
API_KEY = "AIzaSyBybfBSDLx39DdnZbHyLbd21tQAdfHtbeE" # <-- RỦI RO BẢO MẬT CAO

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
MODEL_NAME_CHAT = "gemini-2.5-pro-exp-03-25" # Model theo yêu cầu trước
print(f"Sử dụng model chat: {MODEL_NAME_CHAT}")

def format_api_error(e):
    # ... (Hàm format_api_error giữ nguyên như trước) ...
    error_message = str(e)
    error_type = type(e).__name__
    print(f"[ERROR] Lỗi khi gọi API: {error_type} - {error_message}")

    if isinstance(e, google_exceptions.PermissionDenied):
        if "API key not valid" in error_message or "API_KEY_INVALID" in error_message:
             return f"❌ Lỗi: API Key được cấu hình nhưng Google từ chối khi sử dụng (API_KEY_INVALID) cho model '{MODEL_NAME_CHAT}'. Có thể key đã bị vô hiệu hóa."
        else:
             return f"❌ Lỗi: Từ chối quyền truy cập (Permission Denied) cho model '{MODEL_NAME_CHAT}'. API key của bạn có thể không có quyền sử dụng model này hoặc chưa bật 'Generative Language API' trong Google Cloud."
    elif isinstance(e, google_exceptions.InvalidArgument) and "API key not valid" in error_message:
        return "❌ Lỗi: API Key không hợp lệ (InvalidArgument). Key cung cấp không đúng hoặc đã bị vô hiệu hóa."
    elif isinstance(e, google_exceptions.NotFound):
         return f"❌ Lỗi: Model '{MODEL_NAME_CHAT}' không tìm thấy hoặc không tồn tại với API key của bạn. Hãy kiểm tra lại tên model hoặc quyền truy cập."
    elif isinstance(e, google_exceptions.ResourceExhausted):
         return "❌ Lỗi: Đã vượt quá Hạn ngạch API (Quota) hoặc Tài nguyên đã cạn kiệt (429). Vui lòng thử lại sau."
    elif isinstance(e, google_exceptions.DeadlineExceeded):
         return "❌ Lỗi: Yêu cầu vượt quá thời gian chờ (Timeout/Deadline Exceeded/504)."
    elif isinstance(e, AttributeError) and "start_chat" in error_message:
         return f"❌ Lỗi: Model '{MODEL_NAME_CHAT}' có thể không hỗ trợ phương thức `start_chat` (thường dùng cho chat)."
    else:
         return f"❌ Lỗi khi gọi AI ({error_type}): {error_message}"

# --- Danh sách Emoji Lớn (Giữ nguyên) ---
LARGE_CYCLING_EMOJIS = [
    "😀", "😁", "😂", "🤣", "😃", "😄", "😅", "😆", "😉", "😊", "😋", "😎", "😍", "😘", "🥰", "😗", "😙", "😚", "🙂", "🤗",
    "🤩", "🤔", "🤨", "😐", "😑", "😶", "🙄", "😏", "😣", "😥", "😮", "🤐", "😯", "😪", "😫", "😴", "😌", "😛", "😜", "😝",
    "🤤", "😒", "😓", "😔", "😕", "🙃", "🤑", "😲", "☹️", "🙁", "😖", "😞", "😟", "😤", "😢", "😭", "😦", "😧", "😨", "😩",
    "🤯", "😬", "😰", "😱", "🥵", "🥶", "😳", "🤪", "😵", "🥴", "😠", "😡", "🤬", "😷", "🤒", "🤕", "🤢", "🤮", "🤧", "😇",
    "🥳", "🥺", "🤠", "🤡", "🤥", "🤫", "🤭", "🧐", "🤓", "😈", "👿", "👹", "👺", "💀", "👻", "👽", "🤖", "💩", "😺", "😸",
    "😹", "😻", "😼", "😽", "🙀", "😿", "😾", "🫶", "👍", "👎", "👌", "🤌", "🤏", "✌️", "🤞", "🤟", "🤘", "🤙", "👈", "👉",
    "👆", "🖕", "👇", "☝️", "✋", "🤚", "🖐️", "🖖", "👋", "🙏", "🧠", "🫀", "🫁", "🦷", "🦴", "👀", "👁️", "👅", "👄", "👶",
    "🧒", "👦", "👧", "🧑", "👱", "👨", "🧔", "👩", "👠", "👑", "💍", "💎", "🐵", "🐶", "🐺", "🐱", "🦁", "🐯", "🦒", "🦊",
    "🦝", "🐮", "🐷", "🐗", "🐭", "🐹", "🐰", "🐸", "🐨", "🐼", "🐻", "🐧", "🐦", "🐤", "🦋", "🐛", "🐝", "🐞", "🦂", "🦀",
    "🐍", "🐢", "🐠", "🐳", "🐬", "🐙", "🍎", "🍌", "🍇", "🍓", "🍕", "🍔", "🍟", "⚽️", "🏀", "🏈", "⚾️", "🎾", "🏐", "🎱",
    "🎮", "🎰", "🚀", "✈️", "🚗", "🚲", "📱", "💻", "💡", "💰", "📈", "📉", "⚙️", "🔧", "🔨", "⚔️", "🛡️", "⏳", "⏰", "🎉",
    "🎁", "🎈", "✉️", "❤️", "💔", "⭐️", "🌟", "⚡️", "💥", "💨", "💦", "💧", "🌊", "☀️", "🌙", "☁️", "🔥", "🌈", "⛄️", "❄️"
]
# --- Kết Thúc Danh Sách Emoji ---

# 3) Hàm callback Gradio
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

    current_chat_history.append([message, ""])
    response_index = len(current_chat_history) - 1

    full_response_text = ""
    final_status_message = ""
    # emoji_cycle_index không còn dùng để chọn emoji nữa

    try:
        model = genai.GenerativeModel(MODEL_NAME_CHAT)
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(message, stream=True)

        for chunk in response:
            try:
                chunk_text = getattr(chunk, 'text', '')
                if chunk_text:
                    for char in chunk_text:
                        full_response_text += char

                        # --- THAY ĐỔI: Chọn Emoji Ngẫu Nhiên ---
                        current_emoji = random.choice(LARGE_CYCLING_EMOJIS) # Chọn ngẫu nhiên từ danh sách lớn
                        display_text = full_response_text + f" {current_emoji}" # Thêm emoji ngẫu nhiên
                        # --- Kết Thúc Thay Đổi Emoji ---

                        current_chat_history[response_index][1] = display_text
                        yield "", current_chat_history, current_chat_history

                        # Tốc độ in văn bản nhanh (giữ nguyên từ lần trước)
                        time.sleep(0.01)

                        # Hiệu Ứng Lag Giả Ngẫu Nhiên (Giữ nguyên)
                        lag_probability = 0.005
                        if random.random() < lag_probability:
                            lag_duration = random.uniform(1.0, 1.75)
                            print(f"[INFO] Simulating high load pause for {lag_duration:.2f}s...")
                            time.sleep(lag_duration)

                else:
                    # ... (xử lý block/finish reason giữ nguyên như trước) ...
                    block_reason = getattr(getattr(chunk, 'prompt_feedback', None), 'block_reason', None)
                    finish_reason_obj = chunk.candidates[0].finish_reason if chunk.candidates else None
                    finish_reason = finish_reason_obj.name if finish_reason_obj else None

                    reason_text = ""
                    should_stop = False
                    if block_reason:
                        reason_text, should_stop = f"Yêu cầu/Phản hồi bị chặn ({block_reason})", True
                    elif finish_reason and finish_reason != 'STOP':
                        reason_text, should_stop = f"Phản hồi bị dừng ({finish_reason})", True

                    if reason_text:
                        print(f"[WARN] {reason_text}")
                        final_status_message = f"\n⚠️ ({reason_text})"
                        if should_stop: break

            except Exception as inner_e:
                # ... (xử lý lỗi inner_e giữ nguyên) ...
                print(f"[ERROR] Lỗi khi xử lý chunk stream: {type(inner_e).__name__} - {inner_e}")
                final_status_message = f"\n⚠️ (Lỗi khi xử lý phần tiếp theo: {inner_e})"
                break

        # --- Dọn dẹp cuối cùng (giữ nguyên) ---
        final_clean_text = full_response_text
        if final_status_message and final_status_message not in final_clean_text:
             final_clean_text += final_status_message
        current_chat_history[response_index][1] = final_clean_text
        yield "", current_chat_history, current_chat_history
        print("[OK] Streaming hoàn tất." if not final_status_message else "[WARN/ERROR] Streaming kết thúc với trạng thái.")

    except Exception as e:
        # ... (xử lý lỗi API chính giữ nguyên) ...
        error_msg = format_api_error(e)
        current_chat_history[response_index][1] = error_msg
        yield "", current_chat_history, current_chat_history


# 4) UI Gradio (Giữ nguyên CSS và cấu trúc)
custom_font_and_size_css = f"""
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@800&display=swap');
/* ... (CSS giữ nguyên như trước) ... */
.gradio-container .chatbot .message.bot {{
    font-family: 'Nunito', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.8em !important;
    line-height: 1.5 !important;
}}
.gradio-container .chatbot .message.user {{
    font-size: 1.8em !important;
    line-height: 1.5 !important;
}}
"""

with gr.Blocks(theme=gr.themes.Default(), css=custom_font_and_size_css) as demo:
    gr.Markdown("## ZyRa X - tạo bởi Dũng")
    chatbot = gr.Chatbot(
        label="Chatbot",
        height=500,
        bubble_full_width=False,
        render_markdown=True,
        latex_delimiters=[
            { "left": "$$", "right": "$$", "display": True },
            { "left": "$", "right": "$", "display": False },
        ]
    )
    chat_history_state = gr.State(value=[])
    with gr.Row():
        msg = gr.Textbox(
            placeholder="Nhập câu hỏi của bạn...",
            label="Bạn",
            scale=4,
            container=False
        )
        send_btn = gr.Button("Gửi")
    clear_btn = gr.Button("🗑️ Xóa cuộc trò chuyện")

    # --- Kết nối sự kiện (Giữ nguyên) ---
    submit_event = msg.submit(
        fn=respond,
        inputs=[msg, chat_history_state],
        outputs=[msg, chatbot, chat_history_state]
    )
    click_event = send_btn.click(
        fn=respond,
        inputs=[msg, chat_history_state],
        outputs=[msg, chatbot, chat_history_state]
    )
    def clear_chat_func():
        print("[INFO] Clearing chat history.")
        return "", [], []
    clear_btn.click(
        fn=clear_chat_func,
        inputs=None,
        outputs=[msg, chatbot, chat_history_state],
        queue=False
    )

# 5) Chạy ứng dụng Gradio (Giữ nguyên)
print("Đang khởi chạy Gradio UI...")
demo.queue().launch(
    server_name='0.0.0.0',
    server_port=int(os.environ.get('PORT', 7860)),
    debug=False
)
print("Gradio UI đã khởi chạy.")
