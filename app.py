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
API_KEY = "AIzaSyBybfBSDLx39DdnZbHyLbd21tQAdfHtbeE" # !!! CẢNH BÁO: Key này có thể không hợp lệ !!!

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
# !!! CẢNH BÁO: Tên model "gemini-2.5-flash-preview-04-17" rất có thể không hợp lệ.
# Nếu gặp lỗi NotFound, hãy thay bằng tên model đúng (ví dụ: 'gemini-1.5-flash-latest').
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
          # Thông báo lỗi này rất có thể xuất hiện nếu tên model không đúng
          return f"❌ Lỗi: Model '{MODEL_NAME_CHAT}' không tìm thấy hoặc không tồn tại với API key của bạn. Vui lòng kiểm tra lại tên model."
    elif isinstance(e, google_exceptions.ResourceExhausted):
          return "❌ Lỗi: Đã vượt quá Hạn ngạch API (Quota) hoặc Tài nguyên đã cạn kiệt (429). Vui lòng thử lại sau."
    elif isinstance(e, google_exceptions.DeadlineExceeded):
          return "❌ Lỗi: Yêu cầu vượt quá thời gian chờ (Timeout/Deadline Exceeded/504)."
    elif isinstance(e, AttributeError) and "start_chat" in error_message:
          # Lỗi này ít xảy ra với các model Gemini hiện đại, nhưng vẫn giữ lại
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


# 3) Hàm callback Gradio (ĐÃ ĐƯỢC CẬP NHẬT - Không streaming, xử lý state đúng)
def respond(message, chat_history_state):
    if not genai_configured:
        error_msg = "❌ Lỗi: Google AI chưa được cấu hình đúng cách (API Key có vấn đề hoặc cấu hình thất bại)."
        # Tạo lịch sử tạm thời chỉ để hiển thị lỗi ngay lập tức
        temp_display_history = list(chat_history_state)
        temp_display_history.append([message, error_msg])
        # Yield để cập nhật UI hiển thị lỗi, nhưng KHÔNG cập nhật state
        yield "", temp_display_history, chat_history_state
        return

    # --- Xây dựng lịch sử cho Gemini TỪ TRẠNG THÁI HIỆN TẠI ---
    # Chỉ sử dụng chat_history_state để xây dựng ngữ cảnh cho API
    gemini_history = []
    for user_msg, model_msg in chat_history_state: # Dùng state gốc
        if user_msg and isinstance(user_msg, str):
             gemini_history.append({'role': 'user', 'parts': [user_msg]})
        # Chỉ thêm tin nhắn model hợp lệ vào lịch sử API
        if model_msg and isinstance(model_msg, str) and not model_msg.startswith("❌") and not model_msg.startswith("⚠️"):
             gemini_history.append({'role': 'model', 'parts': [model_msg]})

    print(f"Lịch sử gửi tới Gemini: {gemini_history}")
    print(f"Prompt mới: '{message[:70]}...'")

    # --- Chuẩn bị lịch sử để hiển thị trên UI ---
    # Bắt đầu bằng lịch sử state hiện tại
    current_display_history = list(chat_history_state)
    # Thêm tin nhắn người dùng mới và placeholder cho bot
    current_display_history.append([message, ""]) # Placeholder là chuỗi rỗng

    # --- Yield lần 1: Chỉ cập nhật UI (hiển thị tin nhắn người dùng), KHÔNG cập nhật State ---
    # Trả về state gốc (chat_history_state) cho output state thứ 3
    yield "", current_display_history, chat_history_state

    try:
        model = genai.GenerativeModel(MODEL_NAME_CHAT) # Sử dụng model đã chọn
        chat = model.start_chat(history=gemini_history, system_instruction=SYSTEM_INSTRUCTION)

        response = chat.send_message(message) # Không streaming

        full_response_text = ""
        # Xử lý response
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
             full_response_text = "".join(part.text for part in response.candidates[0].content.parts if part.text)
             # Kiểm tra block/finish reasons
             finish_reason = getattr(response.candidates[0], 'finish_reason', None)
             block_reason = getattr(getattr(response, 'prompt_feedback', None), 'block_reason', None)
             if block_reason:
                 print(f"[WARN] Response blocked ({block_reason})")
                 full_response_text = f"⚠️ Phản hồi bị chặn ({block_reason})"
             elif finish_reason and finish_reason != 'STOP':
                  print(f"[WARN] Response finished with reason: {finish_reason}")
                  # Thêm cảnh báo vào cuối nếu có text, nếu không thì thay thế
                  if full_response_text: full_response_text += f"\n⚠️ (Kết thúc không hoàn chỉnh: {finish_reason})"
                  else: full_response_text = f"⚠️ (Kết thúc không hoàn chỉnh: {finish_reason})"
        else:
             # Xử lý trường hợp response rỗng hoặc không hợp lệ
             print("[ERROR] Received empty or invalid response from API.")
             block_reason = getattr(getattr(response, 'prompt_feedback', None), 'block_reason', None)
             if block_reason:
                  full_response_text = f"❌ Lỗi: API chặn phản hồi ({block_reason})."
             else:
                  full_response_text = "❌ Lỗi: Không nhận được phản hồi hợp lệ từ AI."
                  print(f"[DEBUG] Raw empty response: {response}")


        # Cập nhật placeholder trong lịch sử *hiển thị* (current_display_history)
        current_display_history[-1][1] = full_response_text

        # Chuẩn bị lịch sử *cuối cùng* để lưu vào state
        final_state_history = list(chat_history_state) # Bắt đầu lại từ state gốc trước đó
        final_state_history.append([message, full_response_text]) # Thêm lượt chat đã hoàn thành

        # --- Yield lần cuối: Cập nhật UI VÀ Cập nhật State ---
        # UI hiển thị current_display_history, State lưu final_state_history
        yield "", current_display_history, final_state_history
        print("[OK] Response received and displayed.")


    except Exception as e:
        # Xử lý các lỗi API
        error_msg = format_api_error(e)
        # Cập nhật placeholder trong lịch sử *hiển thị* với lỗi
        current_display_history[-1][1] = error_msg

        # Chuẩn bị lịch sử *cuối cùng* để lưu vào state (với lỗi)
        final_state_history = list(chat_history_state) # Bắt đầu lại từ state gốc trước đó
        final_state_history.append([message, error_msg]) # Thêm lượt chat bị lỗi

        # --- Yield lần cuối (lỗi): Cập nhật UI VÀ Cập nhật State ---
        yield "", current_display_history, final_state_history
        print("[ERROR] API call failed, error message displayed.")


# 4) UI Gradio (Sử dụng State để lưu lịch sử)
with gr.Blocks(theme=gr.themes.Default()) as demo:
    gr.Markdown("## ZyRa X - tạo bởi Dũng")
    gr.Markdown("😎 **Yo! Tôi là ZyRa X. Có gì mới không? Cứ ném câu hỏi vào đây.**")

    chatbot = gr.Chatbot(
        label="Chatbot",
        height=500,
        bubble_full_width=False,
        # type='tuples', # Không cần thiết nữa với Gradio > 4.x, nhưng để lại cũng không sao
        render_markdown=True,
        latex_delimiters=[
            { "left": "$$", "right": "$$", "display": True },
            { "left": "$", "right": "$", "display": False },
             { "left": "\\[", "right": "\\]", "display": True },
             { "left": "\\(", "right": "\\)", "display": False }
        ]
    )
    # Khởi tạo state là một list rỗng để chứa các cặp [user_msg, model_msg]
    chat_history_state = gr.State(value=[])

    with gr.Row():
        msg = gr.Textbox(placeholder="Hỏi đi...", label="Bạn", scale=4, container=False, show_label=False) # Ẩn label "Bạn" cho gọn
        send_btn = gr.Button("Gửi")

    clear_btn = gr.Button("🗑️ Xóa cuộc trò chuyện")

    # --- Kết nối sự kiện ---
    # Khi nhấn Enter (submit) hoặc click nút "Gửi"
    # Inputs: nội dung textbox (msg), state hiện tại (chat_history_state)
    # Outputs: textbox rỗng (msg), cập nhật chatbot, cập nhật state (chat_history_state)
    # queue=False vì chúng ta không dùng streaming, Gradio sẽ tự xử lý queue cơ bản
    submit_event = msg.submit(respond, inputs=[msg, chat_history_state], outputs=[msg, chatbot, chat_history_state], queue=False)
    click_event = send_btn.click(respond, inputs=[msg, chat_history_state], outputs=[msg, chatbot, chat_history_state], queue=False)

    # Hàm xóa chat
    def clear_chat_func(): return "", [], [] # Trả về textbox rỗng, chatbot rỗng, state rỗng
    clear_btn.click(clear_chat_func, outputs=[msg, chatbot, chat_history_state], queue=False)


# 5) Chạy ứng dụng
print("Đang khởi chạy Gradio UI...")
# queue() có thể không cần thiết khi queue=False ở các event, nhưng giữ lại không sao
demo.queue().launch(server_name='0.0.0.0', server_port=int(os.environ.get('PORT', 7860)), debug=False)
# demo.launch(server_name='0.0.0.0', server_port=int(os.environ.get('PORT', 7860)), debug=False) # Cũng hoạt động
print("Gradio UI đã khởi chạy.")
