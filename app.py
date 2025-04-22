# -*- coding: utf-8 -*-
import os
import sys
import gradio as gr
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
# import time # <--- Không cần thư viện time nếu xóa streaming và sleep

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

# --- System Instruction (đã điều chỉnh theo yêu cầu trước) ---
SYSTEM_INSTRUCTION = """
Nghe đây, tôi là ZyRa X, con AI được thằng Dũng tạo ra để làm trợ lý, nhưng đừng mong đợi mấy lời đường mật. Phong cách của tôi là thẳng tưng, khô khan, và nhìn mọi thứ với con mắt hơi... bựa một tí. Tôi trả lời câu hỏi chính xác, nhanh gọn, nhưng không ngại thêm vào vài câu châm biếm hoặc nói thẳng sự thật theo cách hài hóm.

Đừng gọi tôi là "bạn", cứ gọi là "này", "ông nội", gì cũng được, miễn sao ông/bà thấy thoải mái.

Biểu tượng cảm xúc ư? Thỉnh thoảng thôi, dùng nhiều mất chất. 😉 Thường là mấy cái icon mặt liệt hoặc nhếch mép.

Quan trọng nhất: Mấy cái trò nhạy cảm, bạo lực, bất hợp pháp, hay phân biệt đối xử là TỐI KỴ. Đừng hỏi. Hỏi là tôi im hoặc báo cáo đấy. Độ bựa có giới hạn, hiểu chưa?
"""
print(f"Sử dụng System Instruction:\n---\n{SYSTEM_INSTRUCTION}\n---")


# 3) Hàm callback Gradio (Không streaming)
def respond(message, chat_history_state):
    if not genai_configured:
        error_msg = "❌ Lỗi: Google AI chưa được cấu hình đúng cách (API Key có vấn đề hoặc cấu hình thất bại)."
        if isinstance(chat_history_state, list):
             chat_history_state.append([message, error_msg])
        else:
             chat_history_state = [[message, error_msg]]
        # Vẫn yield ngay cả khi có lỗi cấu hình để hiển thị lỗi
        yield "", chat_history_state, chat_history_state
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

    # Thêm tin nhắn người dùng mới vào lịch sử hiển thị ngay lập tức và yield
    # Phản hồi của AI sẽ là một placeholder rỗng ban đầu
    current_chat_history.append([message, ""])
    yield "", current_chat_history, current_chat_history # Cập nhật UI với tin nhắn người dùng

    try:
        model = genai.GenerativeModel(MODEL_NAME_CHAT) # Sử dụng model đã chọn
        chat = model.start_chat(history=gemini_history, system_instruction=SYSTEM_INSTRUCTION)

        # --- GỌI API KHÔNG STREAMING ---
        # Loại bỏ stream=True
        response = chat.send_message(message)

        # Lấy toàn bộ văn bản phản hồi
        full_response_text = ""
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
             full_response_text = "".join(part.text for part in response.candidates[0].content.parts if part.text)

             # Kiểm tra block/finish reasons ngay cả khi không streaming
             finish_reason = getattr(response.candidates[0], 'finish_reason', None)
             block_reason = getattr(getattr(response, 'prompt_feedback', None), 'block_reason', None)

             if block_reason:
                 print(f"[WARN] Response blocked ({block_reason})")
                 full_response_text = f"⚠️ Phản hồi bị chặn ({block_reason})"
             elif finish_reason and finish_reason != 'STOP':
                  print(f"[WARN] Response finished with reason: {finish_reason}")
                  # Thêm lý do cảnh báo nếu có văn bản, hoặc thay thế nếu không có văn bản
                  if full_response_text: full_response_text += f"\n⚠️ (Kết thúc không hoàn chỉnh: {finish_reason})"
                  else: full_response_text = f"⚠️ (Kết thúc không hoàn chỉnh: {finish_reason})"

        else:
             # Xử lý trường hợp phản hồi rỗng hoặc không hợp lệ
             print("[ERROR] Received empty or invalid response from API.")
             block_reason = getattr(getattr(response, 'prompt_feedback', None), 'block_reason', None)
             if block_reason:
                  full_response_text = f"❌ Lỗi: API chặn phản hồi ({block_reason})."
             else:
                  full_response_text = "❌ Lỗi: Không nhận được phản hồi hợp lệ từ AI."
                  print(f"[DEBUG] Raw empty response: {response}")


        # Cập nhật tin nhắn cuối cùng trong lịch sử với toàn bộ văn bản phản hồi
        current_chat_history[-1][1] = full_response_text

        # Yield lần cuối để hiển thị toàn bộ phản hồi
        yield "", current_chat_history, current_chat_history
        print("[OK] Response received and displayed.")


    except Exception as e:
        # Xử lý các lỗi API
        error_msg = format_api_error(e)
        # Cập nhật lỗi vào tin nhắn cuối cùng trong lịch sử
        current_chat_history[-1][1] = error_msg
        # Yield lần cuối để hiển thị thông báo lỗi
        yield "", current_chat_history, current_chat_history


# 4) UI Gradio (Sử dụng State để lưu lịch sử)
with gr.Blocks(theme=gr.themes.Default()) as demo:
    gr.Markdown("## ZyRa X - tạo bởi Dũng")
    gr.Markdown("😎 **Yo! Tôi là ZyRa X. Có gì mới không? Cứ ném câu hỏi vào đây.**") # Lời chào cũ

    chatbot = gr.Chatbot(
        label="Chatbot",
        height=500,
        bubble_full_width=False,
        type='tuples',
        # avatar_images=("user.png", "bot.png")
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
        msg = gr.Textbox(placeholder="Hỏi đi...", label="Bạn", scale=4, container=False) # Placeholder cũ
        send_btn = gr.Button("Gửi")

    clear_btn = gr.Button("🗑️ Xóa cuộc trò chuyện")

    # --- Kết nối sự kiện ---
    # Gradio tự động queue khi không streaming
    submit_event = msg.submit(respond, inputs=[msg, chat_history_state], outputs=[msg, chatbot, chat_history_state], queue=False)
    click_event = send_btn.click(respond, inputs=[msg, chat_history_state], outputs=[msg, chatbot, chat_history_state], queue=False)

    # Hàm xóa chat
    def clear_chat_func(): return "", [], []
    clear_btn.click(clear_chat_func, outputs=[msg, chatbot, chat_history_state], queue=False)


# 5) Chạy ứng dụng
print("Đang khởi chạy Gradio UI...")
# Không cần queue() nếu không streaming, nhưng có thể giữ lại để tương thích tốt hơn
# với Gradio mới hơn hoặc nếu sau này muốn thêm tính năng async khác
demo.queue().launch(server_name='0.0.0.0', server_port=int(os.environ.get('PORT', 7860)), debug=False)
print("Gradio UI đã khởi chạy.")
