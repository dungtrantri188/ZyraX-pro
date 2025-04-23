# -*- coding: utf-8 -*-
import os
import sys
import time
import random
import gradio as gr
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
import unicodedata # Thêm để kiểm tra emoji (tùy chọn)

# --- Thêm import cho thư viện emoji và random ---
try:
    import emoji
except ImportError:
    print("[ERROR] Thư viện 'emoji' chưa được cài đặt.")
    print("Vui lòng chạy: pip install emoji")
    print("Sử dụng danh sách emoji mặc định giới hạn.")
    emoji = None # Đánh dấu là không có thư viện
import random
# --- Kết thúc thêm import ---


# --- API Key (VẪN CÓ RỦI RO BẢO MẬT CAO KHI ĐỂ TRỰC TIẾP TRONG CODE) ---
API_KEY = "AIzaSyBybfBSDLx39DdnZbHyLbd21tQAdfHtbeE" # <-- RỦI RO BẢO MẬT

genai_configured = False
# 1) Kiểm tra và cấu hình API Key từ code (Giữ nguyên)
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
MODEL_NAME_CHAT = "Gemini-2.5-Pro-Exp-03-25" # Sử dụng model mới hơn nếu có thể
# MODEL_NAME_CHAT = "gemini-pro" # Hoặc model ổn định hơn
print(f"Sử dụng model chat: {MODEL_NAME_CHAT}")

def format_api_error(e):
    # ... (Hàm format_api_error giữ nguyên như trong code gốc của bạn) ...
    error_message = str(e)
    error_type = type(e).__name__
    print(f"[ERROR] Lỗi khi gọi API: {error_type} - {error_message}")

    if isinstance(e, google_exceptions.PermissionDenied):
        if "API key not valid" in error_message or "API_KEY_INVALID" in error_message:
             return f"❌ Lỗi: API Key được cấu hình nhưng Google từ chối khi sử dụng (API_KEY_INVALID) cho model '{MODEL_NAME_CHAT}'. Có thể key đã bị vô hiệu hóa hoặc không có quyền truy cập model này."
        elif "User location is not supported" in error_message:
             return f"❌ Lỗi: Vị trí của bạn không được hỗ trợ để sử dụng API này (User location is not supported)."
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
    elif isinstance(e, AttributeError) and "'GenerativeModel' object has no attribute 'start_chat'" in error_message:
         # Lỗi này thường xảy ra nếu model không hỗ trợ chat hoặc có vấn đề cấu hình
         return f"❌ Lỗi: Model '{MODEL_NAME_CHAT}' dường như không hỗ trợ phương thức `start_chat` hoặc có lỗi cấu hình genai."
    elif isinstance(e, google_exceptions.InternalServerError):
         return f"❌ Lỗi: Lỗi máy chủ nội bộ từ Google (Internal Server Error/500). Vui lòng thử lại sau."
    elif isinstance(e, google_exceptions.ServiceUnavailable):
         return f"❌ Lỗi: Dịch vụ Google AI tạm thời không khả dụng (Service Unavailable/503). Vui lòng thử lại sau."
    else:
         return f"❌ Lỗi khi gọi AI ({error_type}): {error_message}"


# --- TẠO DANH SÁCH EMOJI LỚN TỪ THƯ VIỆN ---
ALL_AVAILABLE_EMOJIS = []
if emoji:
    try:
        # Lấy tất cả emoji từ thư viện (keys là ký tự emoji)
        # Lọc các emoji ngôn ngữ 'en' để có bộ chuẩn nhất
        emoji_dict_en = emoji.EMOJI_DATA
        all_emoji_chars = list(emoji_dict_en.keys())

        # Tùy chọn: Lọc bỏ các emoji không phổ biến hoặc ký tự đặc biệt (có thể gây lỗi hiển thị)
        # Ví dụ: Chỉ giữ lại những ký tự đơn và thuộc danh mục 'So' (Symbol, other)
        # filtered_emojis = [
        #     e for e in all_emoji_chars
        #     if len(e) == 1 and unicodedata.category(e) == 'So'
        # ]
        # ALL_AVAILABLE_EMOJIS = filtered_emojis

        # Hiện tại dùng tất cả, chấp nhận rủi ro hiển thị
        ALL_AVAILABLE_EMOJIS = all_emoji_chars

        # Xáo trộn danh sách để thay đổi ngẫu nhiên hơn
        random.shuffle(ALL_AVAILABLE_EMOJIS)
        print(f"[INFO] Đã tạo danh sách gồm {len(ALL_AVAILABLE_EMOJIS)} emoji từ thư viện.")
        if len(ALL_AVAILABLE_EMOJIS) < 2000:
            print("[WARN] Số lượng emoji tìm thấy ít hơn mong đợi (< 2000).")

    except Exception as e:
        print(f"[ERROR] Không thể tạo danh sách emoji từ thư viện: {e}")
        # Sử dụng danh sách dự phòng nhỏ nếu lỗi
        ALL_AVAILABLE_EMOJIS = list("😀😁😂🤣😃😄😅😆😉😊😋😎😍😘🥰😗😙😚🙂🤗🤩🤔🤨😐😑😶🙄😏😣😥😮🤐😯😪😫😴😌😛😜😝🤤😒😓😔😕🙃🤑😲☹🙁😖😞😟😤😢😭😦😧😨😩🤯😬😰😱🥵🥶😳🤪😵🥴😠😡🤬😷🤒🤕🤢🤮🤧😇🥳🥺🤠🤡🤥🤫🤭🧐🤓😈👿👹👺💀👻👽🤖💩😺😸😹😻😼😽🙀😿😾👍👎")
        print(f"[WARN] Sử dụng danh sách emoji dự phòng ({len(ALL_AVAILABLE_EMOJIS)}).")
else:
    # Danh sách dự phòng nếu thư viện emoji không được cài đặt
    ALL_AVAILABLE_EMOJIS = list("😀😁😂🤣😃😄😅😆😉😊😋😎😍😘🥰😗😙😚🙂🤗🤩🤔🤨😐😑😶🙄😏😣😥😮🤐😯😪😫😴😌😛😜😝🤤😒😓😔😕🙃🤑😲☹🙁😖😞😟😤😢😭😦😧😨😩🤯😬😰😱🥵🥶😳🤪😵🥴😠😡🤬😷🤒🤕🤢🤮🤧😇🥳🥺🤠🤡🤥🤫🤭🧐🤓😈👿👹👺💀👻👽🤖💩😺😸😹😻😼😽🙀😿😾👍👎")
    print(f"[WARN] Sử dụng danh sách emoji dự phòng ({len(ALL_AVAILABLE_EMOJIS)}) do thiếu thư viện 'emoji'.")

# Đảm bảo danh sách không bao giờ rỗng
if not ALL_AVAILABLE_EMOJIS:
    ALL_AVAILABLE_EMOJIS = ["❓", "❗"]
# --- KẾT THÚC TẠO DANH SÁCH EMOJI ---


# 3) Hàm callback Gradio (Sử dụng danh sách emoji lớn và tốc độ nhanh hơn)
def respond(message, chat_history_state):
    if not genai_configured:
        error_msg = "❌ Lỗi: Google AI chưa được cấu hình đúng cách (API Key có vấn đề hoặc cấu hình thất bại)."
        # Đảm bảo chat_history_state là list trước khi append
        if not isinstance(chat_history_state, list):
            chat_history_state = []
        chat_history_state.append((message, error_msg)) # Sử dụng tuple (user, bot)
        return "", chat_history_state, chat_history_state

    # --- Khởi tạo lịch sử ---
    # Đảm bảo chat_history_state là list, nếu không thì khởi tạo rỗng
    if not isinstance(chat_history_state, list):
         current_chat_history = []
         print("[WARN] chat_history_state không phải list, đã reset.")
    else:
         # Chuyển đổi từ list của tuples sang list của lists để dễ chỉnh sửa
         current_chat_history = [list(item) for item in chat_history_state]

    # --- Xây dựng lịch sử cho Gemini ---
    gemini_history = []
    for user_msg, model_msg in current_chat_history:
        # Bỏ qua các cặp có lỗi hoặc không hợp lệ
        if user_msg and isinstance(user_msg, str):
            gemini_history.append({'role': 'user', 'parts': [user_msg]})
        if model_msg and isinstance(model_msg, str) and not model_msg.startswith("❌") and not model_msg.startswith("⚠️"):
            # Chỉ thêm phản hồi hợp lệ của model vào lịch sử
            gemini_history.append({'role': 'model', 'parts': [model_msg]})

    print(f"Lịch sử gửi tới Gemini (size={len(gemini_history)}): {str(gemini_history)[:200]}...") # In ngắn gọn
    print(f"Prompt mới: '{message[:70]}...'")

    # Thêm tin nhắn mới của người dùng vào cuối (tạm thời để hiển thị)
    current_chat_history.append([message, ""]) # Thêm dưới dạng list [user, bot]
    response_index = len(current_chat_history) - 1 # Vị trí của phản hồi đang chờ

    full_response_text = ""
    final_status_message = ""
    emoji_cycle_index = 0 # Reset chỉ số emoji cho mỗi lần gọi

    try:
        model = genai.GenerativeModel(MODEL_NAME_CHAT)
        chat = model.start_chat(history=gemini_history)
        # --- Cấu hình an toàn (Tùy chọn) ---
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
        ]
        # --- Gửi tin nhắn với stream và cấu hình an toàn ---
        response = chat.send_message(
            message,
            stream=True,
            safety_settings=safety_settings
        )

        for chunk in response:
            try:
                chunk_text = getattr(chunk, 'text', '')
                if chunk_text:
                    for char in chunk_text:
                        full_response_text += char

                        # --- Thay đổi Emoji Liên Tục từ danh sách LỚN ---
                        if ALL_AVAILABLE_EMOJIS: # Kiểm tra xem danh sách có emoji không
                            current_emoji = ALL_AVAILABLE_EMOJIS[emoji_cycle_index % len(ALL_AVAILABLE_EMOJIS)]
                            emoji_cycle_index += 1
                            display_text = full_response_text + f" {current_emoji}" # Thêm emoji đang thay đổi
                        else:
                            display_text = full_response_text + "..." # Hoặc dấu ba chấm nếu không có emoji

                        # --- Cập nhật UI ---
                        # Chuyển đổi lại thành tuple trước khi yield nếu Gradio yêu cầu
                        history_tuples = [tuple(item) for item in current_chat_history]
                        history_tuples[response_index] = (history_tuples[response_index][0], display_text) # Cập nhật phần bot message

                        yield "", history_tuples, history_tuples # Yield history dạng list của tuples
                        # --- GIẢM THỜI GIAN SLEEP ĐỂ NHANH HƠN ---
                        time.sleep(0.01) # Giảm từ 0.02 xuống 0.01
                        # --- KẾT THÚC GIẢM THỜI GIAN SLEEP ---

                        # --- Hiệu Ứng Lag Giả Ngẫu Nhiên (Giữ nguyên) ---
                        lag_probability = 0.005
                        if random.random() < lag_probability:
                            lag_duration = random.uniform(0.8, 1.5) # Giảm nhẹ thời gian lag
                            print(f"[INFO] Simulating high load pause for {lag_duration:.2f}s...")
                            time.sleep(lag_duration)
                        # --- Kết Thúc Hiệu Ứng Lag ---

                # --- Xử lý Block/Finish Reason (Cải thiện) ---
                # Cách lấy lý do chặn/kết thúc có thể khác nhau giữa các phiên bản API/SDK
                block_reason = None
                finish_reason = None
                try:
                    # Thử lấy từ prompt_feedback trước (thường cho block)
                    block_reason = chunk.prompt_feedback.block_reason.name if chunk.prompt_feedback else None
                except AttributeError:
                    pass # Bỏ qua nếu không có prompt_feedback

                try:
                     # Thử lấy từ candidates (thường cho finish reason)
                    if chunk.candidates:
                         # Lấy finish_reason từ candidate đầu tiên
                         finish_reason_enum = chunk.candidates[0].finish_reason
                         # Chuyển enum thành string (nếu cần)
                         finish_reason = finish_reason_enum.name if hasattr(finish_reason_enum, 'name') else str(finish_reason_enum)
                except (AttributeError, IndexError):
                     pass # Bỏ qua nếu không có candidates hoặc finish_reason

                reason_text = ""
                should_stop = False
                if block_reason and block_reason != 'BLOCK_REASON_UNSPECIFIED':
                    reason_text, should_stop = f"Yêu cầu/Phản hồi bị chặn ({block_reason})", True
                elif finish_reason and finish_reason not in ['STOP', 'FINISH_REASON_UNSPECIFIED', 'UNKNOWN']: # Các lý do dừng bình thường
                    # Các lý do khác STOP là bất thường (SAFETY, RECITATION, MAX_TOKENS, OTHER)
                    reason_text, should_stop = f"Phản hồi bị dừng ({finish_reason})", True

                if reason_text:
                    print(f"[WARN] {reason_text}")
                    # Chỉ thêm nếu chưa có trong tin nhắn cuối
                    if reason_text not in final_status_message:
                        final_status_message += f"\n⚠️ ({reason_text})"
                    if should_stop:
                        break # Dừng xử lý stream nếu bị chặn hoặc dừng bất thường

            except StopIteration:
                 print("[INFO] Stream kết thúc (StopIteration).")
                 break # Kết thúc vòng lặp stream một cách bình thường
            except Exception as inner_e:
                print(f"[ERROR] Lỗi khi xử lý chunk stream: {type(inner_e).__name__} - {inner_e}")
                # Chỉ thêm nếu chưa có trong tin nhắn cuối
                error_info = f"Lỗi xử lý chunk: {inner_e}"
                if error_info not in final_status_message:
                    final_status_message += f"\n⚠️ ({error_info})"
                # Không nên break ở đây trừ khi lỗi nghiêm trọng, để thử xử lý chunk tiếp theo
                # break

        # --- Dọn dẹp cuối cùng ---
        final_clean_text = full_response_text.strip() # Xóa khoảng trắng thừa
        if final_status_message and final_status_message not in final_clean_text:
             final_clean_text += final_status_message

        # Cập nhật lần cuối vào history dạng list
        current_chat_history[response_index][1] = final_clean_text
        # Chuyển đổi lại history sang dạng list của tuples cho Gradio
        final_history_tuples = [tuple(item) for item in current_chat_history]

        yield "", final_history_tuples, final_history_tuples # Yield history cuối cùng
        print("[OK] Streaming hoàn tất." if not final_status_message else "[WARN/ERROR] Streaming kết thúc với trạng thái.")

    except AttributeError as e:
         # Xử lý lỗi AttributeError cụ thể hơn (ví dụ: start_chat không tồn tại)
         error_msg = format_api_error(e)
         # Đảm bảo current_chat_history là list để có thể truy cập index
         if isinstance(current_chat_history, list) and len(current_chat_history) > response_index:
             current_chat_history[response_index][1] = error_msg
         else: # Xử lý trường hợp history không hợp lệ
             current_chat_history.append([message, error_msg])
         final_history_tuples = [tuple(item) for item in current_chat_history]
         yield "", final_history_tuples, final_history_tuples

    except Exception as e:
        # Xử lý lỗi API chính
        error_msg = format_api_error(e)
         # Đảm bảo current_chat_history là list để có thể truy cập index
        if isinstance(current_chat_history, list) and len(current_chat_history) > response_index:
            current_chat_history[response_index][1] = error_msg
        else: # Xử lý trường hợp history không hợp lệ
            current_chat_history.append([message, error_msg])
        final_history_tuples = [tuple(item) for item in current_chat_history]
        yield "", final_history_tuples, final_history_tuples


# 4) UI Gradio (Giữ nguyên CSS tăng kích thước chữ)
custom_font_and_size_css = f"""
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@800&display=swap');

/* Áp dụng phông và kích thước cho bot */
.gradio-container .chatbot .message.bot {{
    font-family: 'Nunito', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.8em !important; /* Giữ nguyên kích thước chữ lớn */
    line-height: 1.5 !important;
    word-break: break-word; /* Giúp xuống dòng tốt hơn */
}}

/* Áp dụng kích thước chữ cho người dùng */
.gradio-container .chatbot .message.user {{
    font-size: 1.8em !important; /* Giữ nguyên kích thước chữ lớn */
    line-height: 1.5 !important;
    word-break: break-word; /* Giúp xuống dòng tốt hơn */
}}
"""

# Xây dựng giao diện với Blocks và CSS tùy chỉnh
with gr.Blocks(theme=gr.themes.Default(font=[gr.themes.GoogleFont("Nunito"), "Arial", "sans-serif"]), css=custom_font_and_size_css) as demo:
    gr.Markdown("# ✨ ZyRa X - Tạo bởi Dũng ✨")

    # Sử dụng state để lưu lịch sử dưới dạng list của tuples [(user1, bot1), (user2, bot2)]
    # Đây là định dạng mà Gradio Chatbot component thường mong đợi
    chat_history_state = gr.State(value=[])

    chatbot = gr.Chatbot(
        label="Cuộc trò chuyện",
        height=600, # Tăng chiều cao một chút
        bubble_full_width=False,
        # type='tuples', # Không cần chỉ định type ở đây nữa nếu dùng State đúng cách
        value=[], # Khởi tạo rỗng
        render_markdown=True,
        latex_delimiters=[
            { "left": "$$", "right": "$$", "display": True },
            { "left": "$", "right": "$", "display": False },
        ],
        show_label=False # Ẩn label "Chatbot" nếu muốn
    )


    with gr.Row():
        msg = gr.Textbox(
            placeholder="Nhập câu hỏi của bạn ở đây...",
            label="Tin nhắn của bạn",
            scale=4, # Chiếm nhiều không gian hơn
            container=False,
            show_label=False # Ẩn label nếu không cần
        )
        send_btn = gr.Button(" Gửi 🚀", variant="primary", scale=1) # Thêm icon và làm nút chính

    clear_btn = gr.Button("🗑️ Xóa cuộc trò chuyện")

    # --- Kết nối sự kiện ---
    # Sử dụng hàm wrapper để đảm bảo state được truyền đúng cách
    def wrapped_respond(message, history_list_of_tuples):
        # Hàm respond giờ nhận và trả về list của tuples
        # Hàm respond nội bộ sẽ xử lý chuyển đổi sang list của lists khi cần
        # chat_history_state sẽ tự động cập nhật vì nó là đầu ra
        return respond(message, history_list_of_tuples)

    # Kết nối msg.submit và send_btn.click
    submit_event = msg.submit(
        fn=wrapped_respond,
        inputs=[msg, chat_history_state],
        outputs=[msg, chatbot, chat_history_state], # chatbot nhận trực tiếp list of tuples từ state
        api_name="send_message" # Đặt tên cho API endpoint (tùy chọn)
    )
    click_event = send_btn.click(
        fn=wrapped_respond,
        inputs=[msg, chat_history_state],
        outputs=[msg, chatbot, chat_history_state], # chatbot nhận trực tiếp list of tuples từ state
        api_name="send_message_button" # Đặt tên khác nếu muốn
    )

    # Hàm xóa chat
    def clear_chat_func():
        print("[INFO] Đã xóa lịch sử chat.")
        return "", [], [] # msg rỗng, chatbot rỗng (list), state rỗng (list)

    clear_btn.click(
        fn=clear_chat_func,
        inputs=None, # Không cần input
        outputs=[msg, chatbot, chat_history_state], # msg, chatbot, và state cần được xóa
        queue=False # Chạy ngay lập tức, không cần xếp hàng
    )

# 5) Chạy ứng dụng Gradio (Giữ nguyên)
print("Đang khởi chạy Gradio UI...")
demo.queue().launch(
    server_name='0.0.0.0',
    server_port=int(os.environ.get('PORT', 7860)),
    debug=False, # Tắt debug trong môi trường production
    # share=True # Bật nếu bạn muốn tạo link public tạm thời (Nguy hiểm nếu API key lộ)
)
print("Gradio UI đã khởi chạy.")
