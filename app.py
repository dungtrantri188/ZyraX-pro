# -*- coding: utf-8 -*-
import os
import sys
import gradio as gr
import google.generativeai as genai
# 'types' có thể không cần thiết nữa nếu chỉ dùng Client API và dictionary config
# from google.generativeai import types
from google.api_core import exceptions as google_exceptions
import traceback

# ================= CẤU HÌNH API KEY XOAY VÒNG =================
API_KEYS = [
    "AIzaSyBybfBSDLx39DdnZbHyLbd21tQAdfHtbeE",
    "AIzaSyCFCj6v8hD49BICKhnHLEpP5o_Wn7hrJgg",
    "AIzaSyBxCiE0J23G9jRJvAX7Q9CmPP2BTfTUP4o",
    "AIzaSyDkeIgLhVdtCKkP3O-E6NtddP1DCdsQJO8",
]
API_KEYS = [key for key in API_KEYS if key and not key.startswith("YOUR_")]
current_key_index = 0

def rotate_api_key():
    global current_key_index
    if not API_KEYS: return None
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    print(f"[INFO] Chuyển sang sử dụng API Key #{current_key_index + 1}")
    return API_KEYS[current_key_index]

# ================= MODEL VÀ CẤU HÌNH =================
MODEL_NAME = "gemini-2.5-pro-exp-03-25"
print(f"[INFO] Sử dụng model: {MODEL_NAME}")

# --- XÓA KHỐI ĐỊNH NGHĨA generation_config TOÀN CỤC ---
# Khối code này đã bị xóa vì gây lỗi AttributeError
# generation_config = types.GenerationConfig(
#     thinking_config=types.ThinkingConfig(
#         thinking_budget=0,
#     ),
#     response_mime_type="text/plain",
# )
# --- KẾT THÚC XÓA ---

# ================= HÀM XỬ LÝ LỖI API (Giữ nguyên) =================
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
         elif "user location is not supported" in error_message.lower():
             user_friendly_message = f"❌ Lỗi: Khu vực của bạn không được hỗ trợ để sử dụng API này (InvalidArgument - Location)."
             is_key_related_error = False # Lỗi này thường không phải do key
         elif "invalid content" in error_message.lower():
             user_friendly_message = f"❌ Lỗi: Dữ liệu gửi đi không hợp lệ (InvalidArgument). Có thể do lịch sử chat bị lỗi."
             is_key_related_error = False # Lỗi này không phải do key
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
    elif isinstance(e, (genai.types.BlockedPromptException, genai.types.StopCandidateException)):
         # Lưu ý: genai.types vẫn có thể cần cho Exception này
         user_friendly_message = f"⚠️ Yêu cầu hoặc phản hồi bị chặn bởi bộ lọc an toàn."
    else: # Các lỗi khác
         user_friendly_message = f"❌ Lỗi không xác định với Key #{key_index + 1} ({error_type}): {error_message}"

    return user_friendly_message, is_key_related_error

# Hàm tiện ích để thêm lỗi vào lịch sử chat (Giữ nguyên)
def append_error_to_history(error_msg, message, chat_history_state):
    if isinstance(chat_history_state, list):
        if not chat_history_state or chat_history_state[-1] != [message, error_msg]:
             chat_history_state.append([message, error_msg])
    else:
        chat_history_state = [[message, error_msg]]
    return "", chat_history_state, chat_history_state

# ================= HÀM CALLBACK CHÍNH CỦA GRADIO =================
def respond(message, chat_history_state):
    global current_key_index
    from google.generativeai import types as genai_types # Import cục bộ nếu cần cho Exception

    if not API_KEYS:
        error_msg = "❌ Lỗi cấu hình: Danh sách API Key trống!"
        return append_error_to_history(error_msg, message, chat_history_state)
    if not message or message.strip() == "":
        # Không làm gì nếu message trống
        return "", chat_history_state, chat_history_state

    current_chat_history = list(chat_history_state)
    contents = []
    for user_msg, model_msg in current_chat_history:
        # Cần import Part ở đây nếu chưa import types ở trên cùng
        from google.generativeai.types import Part
        if user_msg and isinstance(user_msg, str):
            contents.append({'role': 'user', 'parts': [Part.from_text(text=user_msg)]})
        if model_msg and isinstance(model_msg, str) and not model_msg.startswith("❌") and not model_msg.startswith("⚠️"):
            contents.append({'role': 'model', 'parts': [Part.from_text(text=model_msg)]})
    # Thêm tin nhắn mới nhất (cũng cần Part)
    from google.generativeai.types import Part
    contents.append({'role': 'user', 'parts': [Part.from_text(text=message)]})

    print(f"[INFO] Lịch sử gửi đi ('contents' length): {len(contents)}")
    print(f"[INFO] Prompt mới: '{message[:100]}...'")

    initial_key_index = current_key_index
    for attempt in range(len(API_KEYS)):
        active_key = API_KEYS[current_key_index]
        print(f"[INFO] Đang thử với API Key #{current_key_index + 1}...")
        try:
            client = genai.Client(api_key=active_key)

            # --- SỬA LỖI TẠI ĐÂY ---
            # Truyền cấu hình trực tiếp dưới dạng dictionary
            response_stream = client.models.generate_content_stream(
                model=f"models/{MODEL_NAME}",
                contents=contents,
                generation_config={ # <<< TRUYỀN DICTIONARY
                    "thinking_config": {
                        "thinking_budget": 0,
                    },
                    "response_mime_type": "text/plain",
                    # Bạn có thể thêm các tham số khác của GenerationConfig vào đây
                    # ví dụ: "temperature": 0.7, "max_output_tokens": 2048
                },
                stream=True,
            )
            # --- KẾT THÚC SỬA LỖI ---

            current_chat_history.append([message, ""])
            full_response_text = ""
            thinking_active = False
            for chunk in response_stream:
                if chunk.thinking_state:
                    if not thinking_active:
                        print("[INFO] ZyraX is ThinKing...")
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

                # Xử lý Block/Finish Reason (cần kiểm tra lại nếu cần genai_types)
                block_reason = getattr(getattr(chunk, 'prompt_feedback', None), 'block_reason', None)
                finish_reason = None
                if hasattr(chunk, 'candidates') and chunk.candidates:
                     finish_reason = getattr(chunk.candidates[0], 'finish_reason', None)
                reason_text = ""
                should_stop = False
                # Có thể cần kiểm tra kiểu enum từ thư viện gốc nếu dùng trực tiếp
                # Ví dụ: from google.ai.generativelanguage import SafetySetting
                if block_reason: # Giả sử block_reason trả về giá trị có thể đánh giá là True
                    reason_text, should_stop = f"Yêu cầu/Phản hồi bị chặn ({block_reason})", True
                elif finish_reason and finish_reason != 'STOP': # Giả sử finish_reason là string
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
            # Check if genai_types is needed for exception handling
            if isinstance(e, (genai_types.BlockedPromptException, genai_types.StopCandidateException)):
                 error_msg, is_key_error = format_api_error(e, current_key_index) # Gọi hàm cũ
                 # Lỗi này không liên quan đến key
                 print(f"[ERROR] Gặp lỗi chặn nội dung, dừng thử.")
                 return append_error_to_history(error_msg, message, current_chat_history)
            else:
                # Xử lý các lỗi khác như cũ
                error_msg, is_key_error = format_api_error(e, current_key_index)
                if is_key_error:
                    rotate_api_key()
                    if current_key_index == initial_key_index and attempt == len(API_KEYS) - 1:
                        print("[ERROR] Đã thử tất cả API Key nhưng đều thất bại.")
                        final_error_msg = f"❌ Đã thử tất cả {len(API_KEYS)} API Key. Lỗi cuối: {error_msg}"
                        return append_error_to_history(final_error_msg, message, current_chat_history)
                    continue
                else:
                    print(f"[ERROR] Lỗi không liên quan key, dừng thử.")
                    return append_error_to_history(error_msg, message, current_chat_history)

    print("[ERROR] Không thể hoàn thành yêu cầu sau khi thử tất cả API Key.")
    final_error_msg = f"❌ Đã thử tất cả {len(API_KEYS)} API Key nhưng không thành công."
    return append_error_to_history(final_error_msg, message, current_chat_history)


# ================= GIAO DIỆN GRADIO (Giữ nguyên) =================
custom_theme = gr.themes.Soft(
    primary_hue="emerald", secondary_hue="gray",
).set(
    button_primary_background_fill="*primary_500",
    button_primary_background_fill_hover="*primary_400",
    chatbot_code_background_color="*primary_50",
)

with gr.Blocks(theme=custom_theme, title="ZyRa X - Gemini Pro (Thinking)") as demo:
    with gr.Row():
        gr.HTML("""
            <div style="text-align: center; width: 100%;">
                <h1 style="font-family: 'Segoe UI', sans-serif; color: #2ecc71;">
                    <img src="https://i.ibb.co/3yRk2L2/ai-icon.png" style="height: 40px; vertical-align: middle; margin-right: 10px;">ZyRa X
                </h1>
                <p style="color: #7f8c8d;">Model: Gemini 2.5 Pro Exp (Thinking Enabled) - Multi API Key</p>
            </div>
        """)
    chatbot = gr.Chatbot(
        label="Lịch sử Chat", height=600,
        avatar_images=("https://i.ibb.co/rdZC7LZ/user-avatar.png", "https://i.ibb.co/3yRk2L2/ai-icon.png"),
        bubble_full_width=False, render_markdown=True, show_label=False,
        latex_delimiters=[{"left": "$$", "right": "$$", "display": True}, {"left": "$", "right": "$", "display": False},
                          {"left": "\\[", "right": "\\]", "display": True}, {"left": "\\(", "right": "\\)", "display": False}]
    )
    chat_history_state = gr.State([])
    key_index_state = gr.State(current_key_index)
    with gr.Row():
        with gr.Column(scale=8):
            msg = gr.Textbox(placeholder="Nhập câu hỏi hoặc yêu cầu của bạn ở đây...", lines=2, max_lines=5, label="Tin nhắn", container=False, show_label=False)
        with gr.Column(scale=1, min_width=80):
            send_btn = gr.Button("Gửi", variant="primary", size="sm")
        with gr.Column(scale=1, min_width=80):
            clear_btn = gr.Button("🗑️ Xóa", variant="secondary", size="sm")
    with gr.Accordion("ⓘ Trạng thái API", open=False):
         key_status_display = gr.Markdown(f"Sẵn sàng sử dụng Key #{current_key_index + 1} / {len(API_KEYS) if API_KEYS else 0}", elem_id="key-status")

    def submit_message(message, history, key_idx_state):
        # Sử dụng yield from để chạy respond và cập nhật msg, chatbot, history
        yield from respond(message, history)
        # Sau khi respond chạy xong, cập nhật trạng thái key
        new_key_idx = current_key_index
        key_info = f"Đang dùng Key #{new_key_idx + 1} / {len(API_KEYS) if API_KEYS else 0}"
        yield gr.Markdown(value=key_info) # Trả về update cho key_status_display

    msg.submit(submit_message, inputs=[msg, chat_history_state, key_index_state], outputs=[msg, chatbot, chat_history_state, key_status_display])
    send_btn.click(submit_message, inputs=[msg, chat_history_state, key_index_state], outputs=[msg, chatbot, chat_history_state, key_status_display])

    def clear_chat_func():
        global current_key_index
        key_info = f"Đang dùng Key #{current_key_index + 1} / {len(API_KEYS) if API_KEYS else 0}"
        return "", [], gr.Markdown(value=key_info)

    clear_btn.click(clear_chat_func, outputs=[msg, chatbot, chat_history_state, key_status_display], queue=False)

# ================= CHẠY ỨNG DỤNG (Giữ nguyên) =================
if __name__ == "__main__":
    if not API_KEYS:
        print("\n" + "="*50)
        print("⚠️ CẢNH BÁO: Không tìm thấy API Key hợp lệ nào.")
        print("="*50 + "\n")
    print("Đang khởi chạy Gradio UI...")
    demo.queue().launch(
        server_name='0.0.0.0', server_port=int(os.environ.get('PORT', 7860)),
        share=False, debug=False, favicon_path="https://i.ibb.co/3yRk2L2/ai-icon.png"
    )
    print("Gradio UI đã khởi chạy.")
