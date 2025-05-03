# -*- coding: utf-8 -*-
import os
import time
import random
import gradio as gr
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
import re # Thêm thư viện regex để kiểm tra từ khóa

# --- PHẦN API KEY VÀ CẤU HÌNH GENAI (Giữ nguyên) ---
API_KEY = "AIzaSyC-LrrFk4lz4yNBndSKBTR5C582iYWDTLU" # Thay bằng key của bạn nếu cần

genai_configured = False
if not API_KEY:
    print("[ERROR] API Key bị thiếu.")
else:
    print("[INFO] API Key được gán trực tiếp trong code.")
    print("Đang cấu hình Google AI...")
    try:
        genai.configure(api_key=API_KEY)
        genai_configured = True
        print("[OK] Google AI đã được cấu hình thành công.")
    except Exception as e:
        print(f"[ERROR] Không thể cấu hình Google AI: {e}")
        genai_configured = False

MODEL_NAME_CHAT = "gemini-2.5-flash-preview-04-17" # Đã cập nhật model mới hơn
print(f"Sử dụng model chat: {MODEL_NAME_CHAT}")

# --- HÀM format_api_error (Giữ nguyên) ---
def format_api_error(e):
    error_message = str(e)
    error_type = type(e).__name__
    print(f"[ERROR] Lỗi khi gọi API: {error_type} - {error_message}")

    if isinstance(e, google_exceptions.PermissionDenied):
        if "API key not valid" in error_message or "API_KEY_INVALID" in error_message:
            return "❌ Lỗi: API Key được cấu hình nhưng Google từ chối khi sử dụng (API_KEY_INVALID). Hmph! Kiểm tra lại đi!"
        elif "permission to access model" in error_message:
             return f"❌ Lỗi: Hả?! Tôi không được phép dùng model '{MODEL_NAME_CHAT}' này à? Phiền phức thật..."
        else:
            return f"❌ Lỗi: Từ chối quyền truy cập (PermissionDenied): {error_message} ... Tch!"
    elif isinstance(e, google_exceptions.InvalidArgument) and "API key not valid" in error_message:
        return "❌ Lỗi: API Key không hợp lệ (InvalidArgument). Baka! Nhập key cho đúng vào!"
    elif isinstance(e, google_exceptions.NotFound):
         return f"❌ Lỗi: Không tìm thấy model '{MODEL_NAME_CHAT}'. Cậu chắc là nó tồn tại không đấy?!"
    elif isinstance(e, google_exceptions.ResourceExhausted):
        return "❌ Lỗi: Hết quota rồi! Đợi đi hoặc kiểm tra lại giới hạn xem nào! Mou~"
    elif isinstance(e, google_exceptions.DeadlineExceeded):
        return "❌ Lỗi: Yêu cầu mất thời gian quá! Thử lại sau đi! Chậm chạp!"
    else:
        return f"❌ Lỗi không xác định khi gọi AI ({error_type}): {error_message} ... Chả hiểu sao nữa."

# --- Danh sách Emoji Lớn (Giữ nguyên) ---
LARGE_CYCLING_EMOJIS = [
    "😀","😁","😂","🤣","😃","😄","😅","😆","😉","😊","😋","😎","😍","😘","🥰","😗","😙","😚","🙂","🤗",
    "🤩","🤔","🤨","😐","😑","😶","🙄","😏","😣","😥","😮","🤐","😯","😪","😫","😴","😌","😛","😜","😝",
    "🤤","😒","😓","😔","😕","🙃","🤑","😲","☹️","🙁","😖","😞","😟","😤","😢","😭","😦","😧","😨","😩",
    "🤯","😬","😰","😱","🥵","🥶","😳","🤪","😵","🥴","😠","😡","🤬","😷","🤒","🤕","🤢","🤮","🤧","😇",
    "🥳","🥺","🤠","🤡","🤥","🤫","🤭","🧐","🤓","😈","👿","👹","👺","💀","👻","👽","🤖","💩","😺","😸",
    "😹","😻","😼","😽","🙀","😿","😾","🫶","👍","👎","👌","🤌","🤏","✌️","🤞","🤟","🤘","🤙","👈","👉",
    "👆","🖕","👇","☝️","✋","🤚","🖐️","🖖","👋","🙏","🤝","💅","🤲","👐","🤜","🤛","🙌","👏","👊","✊",
    "💪","🦵","🦶","👂","👃","🧠","🫀","🫁","🦷","🦴","👀","👁️","👅","👄","👶","🧒","👦","👧","🧑","👱",
    "👨","🧔","👩","👵","👴","🧓","👲","👳","👮","🕵️","💂","👷","🤴","👸","👼","🎅","🤶","🦸","🦹","🧙",
    "🧚","🧛","🧝","🧞","🧜","🦩","🐵","🐒","🦍","🦧","🐶","🐕","🦮","🐕‍🦺","🐩","🐺","🦊","🐱","🐈","🐈‍⬛",
    "🦁","🐯","🐅","🐆","🐴","🦄","🦓","🦌","🐮","🐂","🐃","🐄","🐷","🐖","🐗","🐽","🐏","🐑","🐐","🐪",
    "🐫","🦙","🦒","🐘","🦣","🦏","🦛","🐭","🐁","🐀","🐹","🐰","🐇","🐿️","🦔","🦇","🐻","🐨","🐼","🦥",
    "🦦","🦨","🦘","🦡","🐾","🐉","🐲","🌵","🎄","🌲","🌳","🌴","🌱","🌿","☘️","🍀","🎍","🎋","🍃","🍂",
    "🍁","🍄","🌾","💐","🌷","🌹","🥀","🌺","🌸","🌼","🌻","🌞","🌝","🌛","🌜","🌚","🌕","🌖","🌗","🌘",
    "🌑","🌒","🌓","🌔","🌙","🌎","🌍","🌏","💫","⭐️","🌟","✨","⚡️","☄️","💥","🔥","🌪️","🌈","☀️","🌤️",
    "⛅️","🌥️","🌦️","🌧️","⛈️","🌩️","🌨️","❄️","☃️","⛄️","🌬️","💨","💧","🌊","🌫️","💦","☔️","☂️",
    "⚱️","🪴","🏵️","🎗️","🎟️","🎫","🎖️","🏆","🏅","🥇","🥈","🥉","⚽️","🏀","🏈","⚾️","🥎","🎾","🏐",
    "🏉","🥏","🎱","🪀","🏓","🏸","🥅","🏒","🏑","🏏","⛳️","🏹","🎣","🤿","🥊","🥋","🥌","🛷","⛸️","🎿",
    "⛷️","🏂","🏋️","🤼","🤸","⛹️","🤺","🤾","🏌️","🏇","🧘","🛹","🛼","🚣","🏊","⛴️","🚤","🛥️","🛳️",
    "⛵️","🚢","✈️","🛩️","🛫","🛬","🚁","🚟","🚠","🚡","🚂","🚆","🚇","🚈","🚉","🚊","🚝","🚞","🚋",
    "🚃","🚎","🚌","🚍","🚙","🚗","🚕","🚖","🚛","🚚","🚐","🛻","🚜","🏍️","🛵","🦽","🦼","🛺","🚲",
    "🛴","🛹","🛼","🚏","🛣️","🛤️","🛢️","⛽️","🚨","🚥","🚦","🛑","🚧","⚓️","⛵️","🚤","🛳️","🛥️","🚢",
    "⚓️","⛽️","🚧"
]

# --- PHẦN LOGIC TÍNH CÁCH TSUNDERE ---

# Danh sách các câu nói/phản ứng
tsun_prefixes = [
    "Hmph! ", "Chậc! ", "Hả? Cái này mà cũng phải hỏi à? ", "Nghe cho kỹ đây, đồ ngốc! ",
    "別に... (Bình thường thôi...), nhưng mà ", "Geez, lại là câu hỏi dễ thế này... ", "Urusai! Để tôi nói cho mà nghe: ",
    "Mou~ Phiền phức thật đấy! ", "Này, cậu nghĩ tôi rảnh lắm hả? "
]
tsun_suffixes = [
    " ...Nhớ chưa hả?!", " ...Đừng có hỏi lại đấy!", " ...Dễ vậy mà!", " ...Lần sau tự nghĩ đi!",
    " ...Tôi nói vậy thôi, không có ý gì đâu đấy!", " ...Hết việc rồi à?", " (・へ・)"
]
dere_reactions_to_praise = [
    "C-Cảm ơn cái gì chứ! Chỉ là... tiện tay thôi! (〃ω〃)",
    "Đ-Đừng có nói mấy lời kỳ cục đó! Tôi không có giúp cậu vì cậu đâu đấy!",
    "Hmph! Cũng... cũng tàm tạm. Đừng có mà tự mãn!",
    "(Quay mặt đi) Ai... ai khen cậu đâu! Lo học đi!",
    "Im đi! Tập trung vào bài học! ...Nhưng mà... cũng cảm ơn... một chút thôi. (*´ω｀*)",
    "Baka! Nói nhiều quá! Mau hỏi câu khác đi!"
]
dere_caring_remarks = [
    "Ch-Chỗ này hơi khó à? ...Thì... để tôi giải thích kỹ hơn một chút vậy. Chỉ lần này thôi đấy!",
    "Đừng có mà bỏ cuộc dễ dàng thế! Thử lại xem nào... Chắc chắn sẽ làm được thôi... chắc vậy.",
    "Cậu... cũng có cố gắng đấy chứ. Nhưng vẫn còn ngốc lắm! Phải cố hơn nữa!",
    "(Thở dài) Thấy cậu loay hoay mãi... Đây này, chú ý vào: ",
    "Nếu không hiểu thì... thì cứ nói đi. Đừng có giấu dốt! (Tôi không muốn thấy cậu thất bại đâu...)",
]
praise_keywords = [
    "cảm ơn", "thank you", "hay quá", "giỏi", "tuyệt", "cám ơn", "biết ơn",
    "ok", "oke", "tốt", "hiểu rồi", "đã hiểu", "được rồi"
]
difficulty_keywords = [
    "khó quá", "không hiểu", "chưa hiểu", "rối", "phức tạp", "giúp với", "help me"
]

def is_simple_question(user_message):
    # Logic đơn giản để đoán câu hỏi dễ (có thể cải thiện)
    q_lower = user_message.lower()
    if len(user_message.split()) < 5 and ("là gì" in q_lower or "what is" in q_lower or "?" not in user_message):
         return True
    # Câu hỏi toán học cơ bản
    if re.match(r"^[\d\s\+\-\*\/%\(\)\^\.]+\??$", user_message.strip()):
        return True
    return False

def apply_tsundere_personality(user_message, ai_response):
    """Áp dụng tính cách Tsundere vào câu trả lời của AI."""
    user_message_lower = user_message.lower()

    # 1. Kiểm tra lời khen -> Chế độ Dere (phản ứng ngại ngùng)
    if any(keyword in user_message_lower for keyword in praise_keywords):
        return f"{random.choice(dere_reactions_to_praise)} ({ai_response})" # Bao gồm cả câu trả lời gốc (nếu có)

    # 2. Kiểm tra người dùng gặp khó khăn -> Chế độ Dere (quan tâm)
    if any(keyword in user_message_lower for keyword in difficulty_keywords):
        return f"{random.choice(dere_caring_remarks)} {ai_response}"

    # 3. Kiểm tra câu hỏi có vẻ đơn giản -> Chế độ Tsun (gắt gỏng nhẹ)
    if is_simple_question(user_message):
        prefix = random.choice(tsun_prefixes)
        suffix = random.choice(tsun_suffixes)
        # Thêm 20% cơ hội không thêm suffix để đỡ bị lặp
        if random.random() < 0.2:
            suffix = ""
        return f"{prefix}{ai_response}{suffix}"

    # 4. Trường hợp mặc định (hơi Tsun nhẹ)
    # Thêm 50% cơ hội có tiền tố Tsun, 30% có hậu tố Tsun
    prefix = ""
    suffix = ""
    if random.random() < 0.5:
        prefix = random.choice(tsun_prefixes)
    if random.random() < 0.3:
        # Đảm bảo hậu tố không quá cụt nếu không có tiền tố
        if prefix or len(ai_response.split()) > 10:
             suffix = random.choice(tsun_suffixes)

    # Tránh trường hợp chỉ có hậu tố mà không có tiền tố và câu trả lời quá ngắn
    if not prefix and len(ai_response.split()) < 5:
        suffix = ""

    return f"{prefix}{ai_response}{suffix}"

# --- HÀM respond (Đã cập nhật để tích hợp tính cách) ---
def respond(message, chat_history_state):
    if not genai_configured:
        error_msg = "❌ Lỗi: Google AI chưa được cấu hình đúng cách. Hmph! Kiểm tra lại đi!"
        chat_history_state = (chat_history_state or []) + [[message, error_msg]]
        return "", chat_history_state, chat_history_state

    if not message or message.strip() == "":
         # Phản ứng khi người dùng không nhập gì
         no_input_responses = [
             "Này! Định hỏi gì thì nói đi chứ?",
             "Im lặng thế? Tính làm gì?",
             "Hửm? Sao không nói gì hết vậy?",
             "Baka! Có gì thì nhập vào đi chứ!",
             "Đừng có nhìn tôi chằm chằm như thế! Hỏi gì thì hỏi đi!"
         ]
         response_text = random.choice(no_input_responses)
         chat_history_state = (chat_history_state or []) + [[message, response_text]]
         return "", chat_history_state, chat_history_state

    # Xây dựng lịch sử chat cho API
    history = []
    if chat_history_state:
        for u, m in chat_history_state:
            # Bỏ qua tin nhắn lỗi, trống hoặc tin nhắn không nhập của user
            is_error = m and isinstance(m, str) and (m.startswith("❌") or m.startswith("⚠️"))
            is_no_input_response = u is None or (isinstance(u,str) and u.strip() == "")

            if u and isinstance(u, str) and u.strip() and not is_no_input_response:
                history.append({'role': 'user', 'parts': [u]})
            if m and isinstance(m, str) and m.strip() and not is_error and not is_no_input_response:
                 # Loại bỏ phần tính cách đã thêm trước đó khỏi lịch sử gửi cho API
                 # (Cái này hơi khó, tạm thời vẫn gửi cả phần tính cách cũ, model có thể tự xử lý)
                 # TODO: Có thể cải thiện bằng cách lưu trữ riêng câu trả lời gốc và câu đã thêm tính cách
                 history.append({'role': 'model', 'parts': [m]})

    # Thêm tin nhắn mới của người dùng vào cuối lịch sử hiển thị
    current_chat_entry = [message, ""]
    chat_history_state = (chat_history_state or []) + [current_chat_entry]
    idx = len(chat_history_state) - 1

    full_text = ""
    char_count = 0
    emoji_idx = 0
    is_error_or_warning = False # Cờ để kiểm tra lỗi/cảnh báo

    try:
        print(f"[DEBUG] Sending history to API: {history}")
        model = genai.GenerativeModel(MODEL_NAME_CHAT)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}, # Tạm thời tắt bộ lọc để linh hoạt hơn
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        chat = model.start_chat(history=history)
        response = chat.send_message(message, stream=True, safety_settings=safety_settings)

        for chunk in response:
            # Kiểm tra chặn prompt
            if hasattr(chunk, 'prompt_feedback') and chunk.prompt_feedback.block_reason:
                 block_reason = chunk.prompt_feedback.block_reason_message
                 print(f"[WARN] Nội dung prompt bị chặn: {block_reason}")
                 # Phản ứng Tsundere với việc bị chặn prompt
                 error_msg = f"⚠️ Hả?! Cậu hỏi cái gì mà bị chặn thế này ({block_reason})?! Nói năng cẩn thận vào!"
                 chat_history_state[idx][1] = error_msg
                 is_error_or_warning = True
                 yield "", chat_history_state, chat_history_state
                 return

            # Kiểm tra lỗi/lý do kết thúc trong candidates
            if not chunk.candidates:
                print(f"[WARN] Chunk không có candidates: {chunk}")
                continue

            candidate = chunk.candidates[0]
            finish_reason_value = getattr(candidate, 'finish_reason', 0) # Lấy an toàn

            # Kiểm tra chặn nội dung trả về (SAFETY)
            if finish_reason_value == 3: # 3 = SAFETY
                safety_ratings_str = ""
                if hasattr(candidate, 'safety_ratings'):
                     ratings_str_list = [f"{r.category.name}: {r.probability.name}" for r in candidate.safety_ratings if r.probability.name != 'NEGLIGIBLE']
                     if ratings_str_list:
                         safety_ratings_str = f" (Lý do: {', '.join(ratings_str_list)})"
                print(f"[WARN] Stream bị chặn do an toàn.{safety_ratings_str}")
                # Phản ứng Tsundere khi nội dung trả về bị chặn
                error_msg = f"⚠️ Tch! Tôi định nói... nhưng mà bị chặn mất rồi!{safety_ratings_str} Chắc tại cậu hỏi linh tinh đấy!"
                chat_history_state[idx][1] = error_msg
                is_error_or_warning = True
                yield "", chat_history_state, chat_history_state
                return

            # Kiểm tra các lý do kết thúc khác (MAX_TOKENS, RECITATION, etc.)
            if finish_reason_value not in (None, 0, 1): # 0=UNSPECIFIED, 1=STOP
                reason_msg = f"Lý do kết thúc: {candidate.finish_reason.name}"
                print(f"[WARN] Stream kết thúc sớm. {reason_msg}")
                error_extra = ""
                if finish_reason_value == 2: # MAX_TOKENS
                    error_extra = "⚠️ Nói dài quá, hết hơi rồi! Tóm lại là thế đấy!"
                elif finish_reason_value == 4: # RECITATION
                    error_extra = "⚠️ Cái này... hình như tôi đọc ở đâu rồi. Bị chặn vì trích dẫn! Phiền phức!"
                else: # OTHER
                     error_extra = f"⚠️ Bị dừng giữa chừng vì... {reason_msg}! Chả hiểu kiểu gì!"

                # Cập nhật phần text đã có và thêm thông báo lỗi/cảnh báo
                chat_history_state[idx][1] = full_text + "\n" + error_extra
                is_error_or_warning = True
                yield "", chat_history_state, chat_history_state
                return


            # Lấy text an toàn hơn
            txt = ""
            if chunk.parts:
                 txt = "".join(part.text for part in chunk.parts if hasattr(part, 'text'))

            if txt:
                for ch in txt:
                    full_text += ch
                    char_count += 1
                    time.sleep(0.02 / 1.5)
                    if char_count % 2 == 0:
                        emoji_idx += 1
                    current_emoji = LARGE_CYCLING_EMOJIS[emoji_idx % len(LARGE_CYCLING_EMOJIS)]
                    chat_history_state[idx][1] = full_text + f" {current_emoji}"
                    yield "", chat_history_state, chat_history_state
            else:
                pass # Bỏ qua chunk rỗng

        # --- TÍCH HỢP TÍNH CÁCH SAU KHI STREAM XONG ---
        if not is_error_or_warning and full_text:
             final_response = apply_tsundere_personality(message, full_text)
             chat_history_state[idx][1] = final_response
        elif not is_error_or_warning and not full_text:
             # Trường hợp API trả về rỗng mà không lỗi
             empty_responses = [
                 "Hửm? Chả nghĩ ra gì cả.",
                 "... Im lặng là vàng.",
                 "Tôi... không biết nói gì hết.",
                 "Cậu hỏi cái gì lạ thế?",
                 "..."
             ]
             chat_history_state[idx][1] = random.choice(empty_responses)
        # Nếu có lỗi/cảnh báo thì giữ nguyên thông báo lỗi đã gán trước đó

        # Cập nhật state cuối cùng (loại bỏ emoji nếu còn)
        final_text = chat_history_state[idx][1]
        # Loại bỏ emoji xoay vòng ở cuối nếu có
        if len(final_text) > 2 and final_text[-2] == ' ' and final_text[-1] in LARGE_CYCLING_EMOJIS:
            final_text = final_text[:-2]
        chat_history_state[idx][1] = final_text

        yield "", chat_history_state, chat_history_state
        # ----------------------------------------------------

    except Exception as e:
        err = format_api_error(e) # Hàm format_api_error đã có chút Tsundere
        # Đảm bảo cập nhật lỗi vào đúng entry cuối cùng
        chat_history_state[idx][1] = err
        yield "", chat_history_state, chat_history_state


# --- GIAO DIỆN GRADIO (Giữ nguyên CSS và cấu trúc) ---
with gr.Blocks(theme=gr.themes.Default(
    # primary_hue=gr.themes.colors.orange,
    # secondary_hue=gr.themes.colors.brown,
)) as demo:
    # --- CSS ĐÃ CẬP NHẬT (Giữ nguyên như bạn cung cấp) ---
    gr.HTML('''
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@800&display=swap');

        /* Màu nền chung */
        body, .gradio-container {
            background-color: #f5f4ed !important; /* Màu nền bạn đang dùng */
        }

        /* Font chữ mặc định */
        * {
            font-family: 'Nunito', sans-serif !important;
        }

        /* --- THAY ĐỔI MÀU SẮC THEO YÊU CẦU --- */

        /* 1. Màu tiêu đề "ZyRa X - tạo bởi Dũng" */
        .gradio-container .prose h2 {
            color: #CC7F66 !important;
            text-align: center;
            margin-bottom: 1rem;
        }

        /* 2. Màu chữ khi chat (User và Bot) */
        .chatbot .message.user span,
        .chatbot .message.bot span,
        .chatbot .message.user p,
        .chatbot .message.bot p {
            color: #8B4513 !important; /* Đổi sang màu nâu đậm hơn cho dễ đọc */
            /* color: #FFB57B !important; */ /* Màu cam cũ */
        }
        /* Màu chữ cho phần bị chặn/lỗi */
        .chatbot .message.bot span:first-child:contains("❌"),
        .chatbot .message.bot span:first-child:contains("⚠️") {
             color: #D2691E !important; /* Màu cam đậm cho lỗi/cảnh báo */
             font-weight: bold;
        }


        /* 3. Màu chữ trong ô nhập liệu và nút Gửi */
        .gradio-textbox textarea,
        .gradio-button span {
           color: #8B4513 !important; /* Đồng bộ màu nâu đậm */
        }
        .gradio-textbox textarea::placeholder {
           color: #A0522D; /* Màu nâu nhạt hơn cho placeholder */
           opacity: 0.7;
        }

        /* --- CÁC STYLE KHÁC GIỮ NGUYÊN HOẶC TINH CHỈNH --- */
        strong, b { color: #000000 !important; }
        .chatbot .message.bot,
        .chatbot .message.user {
            /* background-color: transparent !important; */ /* Bỏ transparent để thấy màu nền */
            border: 1px solid #FFDAB9 !important; /* Giữ viền màu đào nhạt */
            border-radius: 15px !important; /* Giữ bo tròn */
            padding: 10px 15px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            max-width: 85%;
            word-wrap: break-word;
            overflow-wrap: break-word;
            white-space: pre-wrap;
            margin-bottom: 8px; /* Thêm khoảng cách giữa các tin nhắn */
        }
         /* .chatbot .message { */
             /* border: none !important; */ /* Đã bỏ */
             /* Các thuộc tính padding, border-radius, box-shadow, max-width, word-wrap, overflow-wrap, white-space đã chuyển lên trên */
         /* } */
         .chatbot .message.user {
             background: #FFF5E1 !important; /* Màu nền vàng kem nhạt cho user */
             border-radius: 15px 15px 0 15px !important; /* Bo góc khác nhau */
             margin-left: auto;
             margin-right: 10px; /* Thêm margin để không sát cạnh phải */
         }
         .chatbot .message.bot {
             background: #ffffff !important; /* Màu nền trắng cho bot */
             border-radius: 15px 15px 15px 0 !important; /* Bo góc khác nhau */
             margin-right: auto;
             margin-left: 10px; /* Thêm margin để không sát cạnh trái */
         }
         /* Đã set màu chữ chung ở trên */
         /* .chatbot .message.user span, .chatbot .message.user p { color: #8B4513 !important; } */
         /* .chatbot .message.bot span, .chatbot .message.bot p { color: #8B4513 !important; } */

        /* Style cho LaTeX (do KaTeX/MathJax render) */
        .chatbot .message .math-inline .katex, /* Inline math */
        .chatbot .message .math-display .katex-display { /* Display math */
            color: #8B4513 !important; /* Áp dụng màu nâu đậm cho LaTeX */
            /* font-size: 1.1em !important; */
        }
        /* Đảm bảo code blocks cũng xuống dòng */
        .chatbot .message code {
             white-space: pre-wrap !important;
             word-wrap: break-word !important;
             background-color: #f0f0f0; /* Thêm nền nhẹ cho code */
             padding: 2px 4px;
             border-radius: 4px;
             color: #333; /* Màu chữ tối hơn cho code */
        }
        .chatbot .message pre { /* Style cho khối code ``` */
             background-color: #f0f0f0 !important;
             padding: 10px !important;
             border-radius: 5px !important;
             border: 1px solid #ddd !important;
             overflow-x: auto; /* Thêm thanh cuộn ngang nếu code quá dài */
        }
        .chatbot .message pre code {
             background-color: transparent !important; /* Bỏ nền riêng của code trong pre */
             padding: 0 !important;
             border-radius: 0 !important;
             border: none !important;
             color: #333 !important; /* Màu chữ tối hơn cho code */
        }


        #component-8 { margin-top: 10px; } /* ID này có thể thay đổi, cần kiểm tra */
        .gradio-button {
            background-color: #FFDAB9 !important; /* Nền màu đào nhạt cho nút */
            border: 1px solid #CC7F66 !important; /* Viền nâu đỏ */
        }
         .gradio-button:hover {
            background-color: #FFCFAF !important; /* Sáng hơn khi hover */
            box-shadow: 0 2px 4px rgba(0,0,0,0.15);
        }
        </style>
    ''')
    # Tiêu đề sử dụng Markdown
    gr.Markdown("## ") # Đổi tiêu đề một chút

    chatbot = gr.Chatbot(
        label="Cuộc trò chuyện", # Đổi label
        height=500,
        bubble_full_width=False,
        latex_delimiters=[
            {"left": "$$", "right": "$$", "display": True},
            {"left": "$", "right": "$", "display": False},
            {"left": "\\(", "right": "\\)", "display": False},
            {"left": "\\[", "right": "\\]", "display": True}
        ]
    )
    state = gr.State([]) # Khởi tạo state là list rỗng

    with gr.Row():
        txt = gr.Textbox(
            placeholder="Hỏi tôi cái gì đi chứ, Baka!", # Đổi placeholder
            label="Bạn",
            scale=4,
        )
        btn = gr.Button("Gửi Đi!", variant="primary") # Đổi text nút

    clr = gr.Button("🗑️ Quên hết đi! (Xóa)") # Đổi text nút xóa

    # Kết nối sự kiện (giữ nguyên)
    txt.submit(respond, [txt, state], [txt, chatbot, state])
    btn.click(respond, [txt, state], [txt, chatbot, state])
    clr.click(lambda: (None, [], []), outputs=[txt, chatbot, state], queue=False)

print("Đang khởi chạy Gradio UI...")
# Chạy app
demo.queue().launch(
    server_name='0.0.0.0',
    server_port=int(os.environ.get('PORT', 7860)),
    debug=False,
)
print("Gradio UI đã khởi chạy.")
