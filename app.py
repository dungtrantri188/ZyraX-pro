# -*- coding: utf-8 -*-
import os
import sys
import gradio as gr
import google.generativeai as genai
from google.generativeai import types # Cần thiết cho ThinkingConfig và Content
from google.api_core import exceptions as google_exceptions
import traceback # Để in lỗi chi tiết hơn

# ================= CẤU HÌNH API KEY XOAY VÒNG =================
# --- THAY THẾ CÁC KEY NÀY BẰNG KEY GEMINI THỰC TẾ CỦA BẠN ---
API_KEYS = [
    "AIzaSyBybfBSDLx39DdnZbHyLbd21tQAdfHtbeE",  # Key 1 (Key cũ của bạn - có thể không hợp lệ)
    "AIzaSyCFCj6v8hD49BICKhnHLEpP5o_Wn7hrJgg",                          # Key 2
    "AIzaSyBxCiE0J23G9jRJvAX7Q9CmPP2BTfTUP4o",                          # Key 3
    "AIzaSyDkeIgLhVdtCKkP3O-E6NtddP1DCdsQJO8",                          # Key 4
    # Thêm các key khác nếu cần
]

# Lọc bỏ các key placeholder hoặc trống (nếu có)
API_KEYS = [key for key in API_KEYS if key and not key.startswith("YOUR_")]

current_key_index = 0
# Không cần biến genai_configured nữa vì Client sẽ được tạo mỗi lần gọi

# Hàm xoay vòng API Key
def rotate_api_key():
    global current_key_index
    if not API_KEYS:
        return None # Không có key nào hợp lệ
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    print(f"[INFO] Chuyển sang sử dụng API Key #{current_key_index + 1}")
    return API_KEYS[current_key_index]

# ================= MODEL VÀ CẤU HÌNH =================
# --- SỬ DỤNG MODEL MỚI VÀ THINKING CONFIG ---
MODEL_NAME = "gemini-2.5-pro-exp-03-25" # Giữ nguyên model theo yêu cầu của bạn
print(f"[INFO] Sử dụng model: {MODEL_NAME}")

# --- SỬA LỖI TẠI ĐÂY ---
# Cấu hình cho generate_content với thinking
# thinking_budget=0 có nghĩa là nó sẽ hiển thị trạng thái thinking nếu quá trình xử lý lâu
generation_config = types.GenerationConfig( # <<< SỬA 1: Đổi tên lớp thành GenerationConfig
    thinking_config=types.ThinkingConfig(
        thinking_budget=0, # =0 để bật thinking UI khi cần
    ),
    response_mime_type="text/plain", # Yêu cầu phản hồi dạng text
)
# --- KẾT THÚC SỬA LỖI ---

# ================= HÀM XỬ LÝ LỖI API =================
def format_api_error(e, key_index):
    error_message = str(e)
    error_type = type(e).__name__
    print(f"[ERROR][Key #{key_index + 1}] Lỗi khi gọi API: {error_type} - {error_message}")
    traceback.print_exc() # In stack trace để debug

    # Phân loại lỗi để quyết định có nên xoay key hay không
    is_key_related_error = False
    user_friendly_message = f"❌ Lỗi với Key #{key_index + 1} ({error_type})"

    if isinstance(e, google_exceptions.PermissionDenied):
        if "API key not valid" in error_message or "API_KEY_INVALID" in error_message:
            user_friendly_message = f"❌ Lỗi: API Key #{key_index + 1} không hợp lệ hoặc đã bị vô hiệu hóa (PermissionDenied)."
            is_key_related_error = True
        else: # Lỗi quyền truy cập model
            user_friendly_message = f"❌ Lỗi: Từ chối quyền truy cập (Permission Denied) cho model '{MODEL_NAME}' với Key #{key_index + 1}. Key có thể không có quyền sử dụng model này hoặc chưa bật 'Generative Language API'."
            is_key_related_error = True # Thường là vấn đề key/quyền
    elif isinstance(e, google_exceptions.InvalidArgument):
         if "API key not valid" in error_message:
            user_friendly_message = f"❌ Lỗi: API Key #{key_index + 1} không hợp lệ (InvalidArgument)."
            is_key_related_error = True
         elif "invalid content" in error_message.lower():
             user_friendly_message = f"❌ Lỗi: Dữ liệu gửi đi không hợp lệ (InvalidArgument). Có thể do lịch sử chat bị lỗi."
             # Lỗi này không phải do key, không nên xoay vòng
         else:
            user_friendly_message = f"❌ Lỗi: Tham số không hợp lệ (InvalidArgument) với Key #{key_index + 1}: {error_message}"
            # Có thể do key, có thể không, tạm coi là không để tránh xoay vòng vô ích
    elif isinstance(e, google_exceptions.NotFound):
         user_friendly_message = f"❌ Lỗi: Model '{MODEL_NAME}' không tìm thấy hoặc không tồn tại với API key #{key_index + 1}."
         is_key_related_error = True # Có thể do key không có quyền truy cập model này
    elif isinstance(e, google_exceptions.ResourceExhausted):
         user_friendly_message = f"❌ Lỗi: Key #{key_index + 1} đã vượt quá Hạn ngạch API (Quota) hoặc Tài nguyên đã cạn kiệt (429)."
         is_key_related_error = True
    elif isinstance(e, google_exceptions.DeadlineExceeded):
         user_friendly_message = f"❌ Lỗi: Yêu cầu với Key #{key_index + 1} vượt quá thời gian chờ (Timeout/Deadline Exceeded/504)."
         # Có thể do mạng hoặc server quá tải, không chắc do key
    elif isinstance(e, (genai.types.BlockedPromptException, genai.types.StopCandidateException)):
         user_friendly_message = f"⚠️ Yêu cầu hoặc phản hồi bị chặn bởi bộ lọc an toàn."
         # Không phải lỗi key
    else: # Các lỗi khác
         user_friendly_message = f"❌ Lỗi không xác định với Key #{key_index + 1} ({error_type}): {error_message}"
         # Mặc định coi là không liên quan đến key để tránh xoay vòng sai

    return user_friendly_message, is_key_related_error

# Hàm tiện ích để thêm lỗi vào lịch sử chat
def append_error_to_history(error_msg, message, chat_history_state):
    if isinstance(chat_history_state, list):
        # Tránh thêm lỗi trùng lặp nếu message giống hệt
        if not chat_history_state or chat_history_state[-1] != [message, error_msg]:
             chat_history_state.append([message, error_msg])
    else:
        chat_history_state = [[message, error_msg]]
    return "", chat_history_state, chat_history_state


# ================= HÀM CALLBACK CHÍNH CỦA GRADIO =================
def respond(message, chat_history_state):
    global current_key_index

    if not API_KEYS:
        error_msg = "❌ Lỗi cấu hình: Danh sách API Key trống! Vui lòng thêm key vào biến `API_KEYS` trong code."
        return append_error_to_history(error_msg, message, chat_history_state)

    if not message or message.strip() == "":
        error_msg = "⚠️ Vui lòng nhập nội dung tin nhắn."
        return "", chat_history_state, chat_history_state # Trả về trạng thái hiện tại


    current_chat_history = list(chat_history_state)

    # Xây dựng cấu trúc 'contents' từ lịch sử chat cho API mới
    contents = []
    for user_msg, model_msg in current_chat_history:
        if user_msg and isinstance(user_msg, str):
            contents.append(types.Content(role='user', parts=[types.Part.from_text(text=user_msg)]))
        if model_msg and isinstance(model_msg, str) and not model_msg.startswith("❌") and not model_msg.startswith("⚠️"):
            contents.append(types.Content(role='model', parts=[types.Part.from_text(text=model_msg)]))

    contents.append(types.Content(role='user', parts=[types.Part.from_text(text=message)]))

    print(f"[INFO] Lịch sử gửi đi ('contents' length): {len(contents)}")
    print(f"[INFO] Prompt mới: '{message[:100]}...'")

    initial_key_index = current_key_index
    for attempt in range(len(API_KEYS)):
        active_key = API_KEYS[current_key_index]
        print(f"[INFO] Đang thử với API Key #{current_key_index + 1}...")

        try:
            client = genai.Client(api_key=active_key)

            # --- SỬA LỖI TẠI ĐÂY ---
            response_stream = client.models.generate_content_stream(
                model=f"models/{MODEL_NAME}",
                contents=contents,
                generation_config=generation_config, # <<< SỬA 2: Đổi tên biến/tham số thành generation_config
                stream=True,
            )
            # --- KẾT THÚC SỬA LỖI ---

            current_chat_history.append([message, ""])
            full_response_text = ""
            thinking_active = False

            for chunk in response_stream:
                if chunk.thinking_state:
                    if not thinking_active:
                        print("[INFO] ZyraX is ThinKing...") # Giữ nguyên log của bạn
                        thinking_active = True
                        current_chat_history[-1][1] = full_response_text + "..."
                        yield "", current_chat_history, current_chat_history
                    continue

                chunk_text = getattr(chunk, 'text', '')
                if chunk_text:
                    if thinking_active:
                        current_chat_history[-1][1] = full_response_text
                        thinking_active = False
                    full_response_text += chunk_text
                    current_chat_history[-1][1] = full_response_text
                    yield "", current_chat_history, current_chat_history

                block_reason = getattr(getattr(chunk, 'prompt_feedback', None), 'block_reason', None)
                finish_reason = None
                if hasattr(chunk, 'candidates') and chunk.candidates:
                     finish_reason = getattr(chunk.candidates[0], 'finish_reason', None)

                reason_text = ""
                should_stop = False
                if block_reason and block_reason != 'BLOCK_REASON_UNSPECIFIED':
                    reason_text, should_stop = f"Yêu cầu/Phản hồi bị chặn ({block_reason})", True
                elif finish_reason and finish_reason not in ['STOP', 'FINISH_REASON_UNSPECIFIED']:
                    reason_text, should_stop = f"Phản hồi bị dừng sớm ({finish_reason})", True

                if reason_text:
                    print(f"[WARN] {reason_text}")
                    warning_msg = f"\n⚠️ ({reason_text})"
                    if not current_chat_history[-1][1] or current_chat_history[-1][1].isspace():
                         current_chat_history[-1][1] = warning_msg.strip()
                    elif warning_msg not in current_chat_history[-1][1]:
                         current_chat_history[-1][1] += warning_msg
                    yield "", current_chat_history, current_chat_history
                    if should_stop:
                        print("[INFO] Dừng xử lý do block/finish reason.")
                        return

            print(f"[OK] Hoàn thành streaming với Key #{current_key_index + 1}.")
            return

        except Exception as e:
            error_msg, is_key_error = format_api_error(e, current_key_index)
            if is_key_error:
                rotate_api_key()
                if current_key_index == initial_key_index and attempt == len(API_KEYS) - 1:
                    print("[ERROR] Đã thử tất cả API Key nhưng đều thất bại.")
                    final_error_msg = f"❌ Đã thử tất cả {len(API_KEYS)} API Key nhưng không thành công. Lỗi cuối cùng: {error_msg}"
                    return append_error_to_history(final_error_msg, message, current_chat_history)
                continue
            else:
                print(f"[ERROR] Gặp lỗi không liên quan đến API key, dừng thử các key khác cho yêu cầu này.")
                return append_error_to_history(error_msg, message, current_chat_history)

    print("[ERROR] Không thể hoàn thành yêu cầu sau khi thử tất cả các API Key.")
    final_error_msg = f"❌ Đã thử tất cả {len(API_KEYS)} API Key nhưng không thành công."
    return append_error_to_history(final_error_msg, message, current_chat_history)


# ================= GIAO DIỆN GRADIO (Giữ nguyên) =================
custom_theme = gr.themes.Soft(
    primary_hue="emerald",
    secondary_hue="gray",
).set(
    button_primary_background_fill="*primary_500",
    button_primary_background_fill_hover="*primary_400",
    chatbot_code_background_color="*primary_50",
)

with gr.Blocks(theme=custom_theme, title="ZyRa X - Gemini Pro (Thinking)") as demo:
    # Header
    with gr.Row():
        gr.HTML("""
            <div style="text-align: center; width: 100%;">
                <h1 style="font-family: 'Segoe UI', sans-serif; color: #2ecc71;">
                    <img src="https://i.ibb.co/3yRk2L2/ai-icon.png"
                         style="height: 40px; vertical-align: middle; margin-right: 10px;">ZyRa X
                </h1>
                <!-- Cập nhật tiêu đề để phản ánh đúng model bạn dùng -->
                <p style="color: #7f8c8d;">Model: Gemini 2.5 Pro Exp (Thinking Enabled) - Multi API Key</p>
            </div>
        """)

    # Chat Interface
    chatbot = gr.Chatbot(
        label="Lịch sử Chat",
        height=600,
        avatar_images=(
            "https://i.ibb.co/rdZC7LZ/user-avatar.png", # Avatar người dùng
            "https://i.ibb.co/3yRk2L2/ai-icon.png"      # Avatar AI
        ),
        bubble_full_width=False,
        render_markdown=True,
        show_label=False,
         latex_delimiters=[
            { "left": "$$", "right": "$$", "display": True },
            { "left": "$", "right": "$", "display": False },
            { "left": "\\[", "right": "\\]", "display": True },
            { "left": "\\(", "right": "\\)", "display": False }
        ]
    )

    # State để lưu lịch sử chat
    chat_history_state = gr.State([])
    # State để lưu chỉ số key hiện tại (có thể dùng để hiển thị nếu muốn)
    key_index_state = gr.State(current_key_index)

    # Control Panel
    with gr.Row():
        with gr.Column(scale=8):
            msg = gr.Textbox(
                placeholder="Nhập câu hỏi hoặc yêu cầu của bạn ở đây...",
                lines=2,
                max_lines=5,
                label="Tin nhắn",
                container=False,
                show_label=False,
            )
        with gr.Column(scale=1, min_width=80):
            send_btn = gr.Button("Gửi", variant="primary", size="sm")
        with gr.Column(scale=1, min_width=80):
            clear_btn = gr.Button("🗑️ Xóa", variant="secondary", size="sm")

    # Hiển thị trạng thái Key
    with gr.Accordion("ⓘ Trạng thái API", open=False):
         key_status_display = gr.Markdown(f"Sẵn sàng sử dụng Key #{current_key_index + 1} / {len(API_KEYS) if API_KEYS else 0}", elem_id="key-status")

    # --- Kết nối sự kiện ---
    def submit_message(message, history, key_idx_state):
        yield from respond(message, history)
        new_key_idx = current_key_index
        key_info = f"Đang dùng Key #{new_key_idx + 1} / {len(API_KEYS) if API_KEYS else 0}"
        # Cần trả về một bản cập nhật Gradio cho Markdown
        yield gr.Markdown(value=key_info)

    submit_event = msg.submit(
        submit_message,
        inputs=[msg, chat_history_state, key_index_state],
        # msg, chatbot, chat_history_state được cập nhật bởi yield from respond
        # key_status_display được cập nhật bởi yield gr.Markdown cuối cùng
        outputs=[msg, chatbot, chat_history_state, key_status_display]
    )
    click_event = send_btn.click(
        submit_message,
        inputs=[msg, chat_history_state, key_index_state],
        outputs=[msg, chatbot, chat_history_state, key_status_display]
    )

    # Hàm xóa chat
    def clear_chat_func():
        global current_key_index
        key_info = f"Đang dùng Key #{current_key_index + 1} / {len(API_KEYS) if API_KEYS else 0}"
        # Cập nhật trạng thái key và xóa các thành phần khác
        return "", [], gr.Markdown(value=key_info) # Trả về update cho Markdown

    clear_btn.click(
        clear_chat_func,
        outputs=[msg, chatbot, chat_history_state, key_status_display],
        queue=False
    )

# ================= CHẠY ỨNG DỤNG =================
if __name__ == "__main__":
    if not API_KEYS:
        print("\n" + "="*50)
        print("⚠️ CẢNH BÁO: Không tìm thấy API Key hợp lệ nào trong danh sách `API_KEYS`.")
        print("   Vui lòng chỉnh sửa file app.py và thêm các API Key của bạn.")
        print("="*50 + "\n")

    print("Đang khởi chạy Gradio UI...")
    demo.queue().launch(
        server_name='0.0.0.0',
        server_port=int(os.environ.get('PORT', 7860)),
        share=False,
        debug=False,
        favicon_path="https://i.ibb.co/3yRk2L2/ai-icon.png"
    )
    print("Gradio UI đã khởi chạy.")
