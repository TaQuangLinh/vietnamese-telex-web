# app.py
import os
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# --- TẢI TỪ ĐIỂN TỪ FILE vietnamese_dict.txt ---
def load_dictionary():
    words = []
    dict_path = os.path.join(os.path.dirname(__file__), 'vietnamese_dict.txt')
    if os.path.exists(dict_path):
        with open(dict_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if word:
                    words.append(word)
    return words

VI_WORDS = load_dictionary()

# --- CẤU HÌNH TELEX TIẾNG VIỆT ---
BASE_VOWELS = "aăâeêioôơuưy"

MARK_MAP = {
    'a': {'s': 'á', 'f': 'à', 'r': 'ả', 'x': 'ã', 'j': 'ạ'},
    'ă': {'s': 'ắ', 'f': 'ằ', 'r': 'ẳ', 'x': 'ẵ', 'j': 'ặ'},
    'â': {'s': 'ấ', 'f': 'ầ', 'r': 'ẩ', 'x': 'ẫ', 'j': 'ậ'},
    'e': {'s': 'é', 'f': 'è', 'r': 'ẻ', 'x': 'ẽ', 'j': 'ẹ'},
    'ê': {'s': 'ế', 'f': 'ề', 'r': 'ể', 'x': 'ễ', 'j': 'ệ'},
    'o': {'s': 'ó', 'f': 'ò', 'r': 'ỏ', 'x': 'õ', 'j': 'ọ'},
    'ô': {'s': 'ố', 'f': 'ồ', 'r': 'ổ', 'x': 'ỗ', 'j': 'ộ'},
    'ơ': {'s': 'ớ', 'f': 'ờ', 'r': 'ở', 'x': 'ỡ', 'j': 'ợ'},
    'u': {'s': 'ú', 'f': 'ù', 'r': 'ủ', 'x': 'ũ', 'j': 'ụ'},
    'ư': {'s': 'ứ', 'f': 'ừ', 'r': 'ử', 'x': 'ữ', 'j': 'ự'},
    'y': {'s': 'ý', 'f': 'ỳ', 'r': 'ỷ', 'x': 'ỹ', 'j': 'ỵ'},
}

def is_base_vowel(c):
    return c in BASE_VOWELS

def has_diacritic(c):
    return c.isalpha() and c.lower() not in BASE_VOWELS

def telex_transform(text, key):
    if key not in "sfrxjw":
        return text + key
    if key == 'w':
        if text.endswith('a'): return text[:-1] + 'ă'
        if text.endswith('e'): return text[:-1] + 'ê'
        if text.endswith('o'): return text[:-1] + 'ơ'
        if text.endswith('u'): return text[:-1] + 'ư'
        if text.endswith('d'): return text[:-1] + 'đ'
        if text.endswith('A'): return text[:-1] + 'Ă'
        if text.endswith('E'): return text[:-1] + 'Ê'
        if text.endswith('O'): return text[:-1] + 'Ơ'
        if text.endswith('U'): return text[:-1] + 'Ư'
        if text.endswith('D'): return text[:-1] + 'Đ'
        return text + key
    if not text:
        return text + key
    last_char = text[-1]
    if has_diacritic(last_char) or not is_base_vowel(last_char.lower()):
        return text + key
    base = last_char.lower()
    if base in MARK_MAP and key in MARK_MAP[base]:
        new_char = MARK_MAP[base][key]
        if last_char.isupper():
            new_char = new_char.upper()
        return text[:-1] + new_char
    return text + key

# === HÀM TELEX NÂNG CAO — XỬ LÝ TOÀN BỘ CHUỖI ===
def apply_telex_fully(text):
    """
    Xử lý toàn bộ chuỗi theo chuẩn Telex, từ trái sang phải.
    Hỗ trợ: aa→â, oo→ô, uw→ư, và dấu (s,f,r,x,j).
    """
    result = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        # Xử lý tổ hợp 2 ký tự
        if i + 1 < n:
            next_c = text[i + 1]
            # Xử lý 'w' — nhưng chỉ khi là tổ hợp
            if c == 'a' and next_c == 'w':
                result.append('ă')
                i += 2
                continue
            if c == 'a' and next_c == 'a':
                result.append('â')
                i += 2
                continue
            elif c == 'e' and next_c == 'e':
                result.append('ê')
                i += 2
                continue
            elif c == 'o' and next_c == 'o':
                result.append('ô')
                i += 2
                continue
            elif c == 'u' and next_c == 'w':
                result.append('ư')
                i += 2
                continue
            elif c == 'o' and next_c == 'w':
                result.append('ơ')
                i += 2
                continue
            elif c == 'd' and next_c == 'd':
                result.append('đ')
                i += 2
                continue
            # Xử lý dấu — chỉ áp dụng nếu ký tự hiện tại là nguyên âm cơ sở
            elif c in "aăâeêoôơuưy" and next_c in "sfrxj":
                base = c
                mark_key = next_c
                # Ánh xạ dấu
                mark_map_local = {
                    'a': {'s': 'á', 'f': 'à', 'r': 'ả', 'x': 'ã', 'j': 'ạ'},
                    'ă': {'s': 'ắ', 'f': 'ằ', 'r': 'ẳ', 'x': 'ẵ', 'j': 'ặ'},
                    'â': {'s': 'ấ', 'f': 'ầ', 'r': 'ẩ', 'x': 'ẫ', 'j': 'ậ'},
                    'e': {'s': 'é', 'f': 'è', 'r': 'ẻ', 'x': 'ẽ', 'j': 'ẹ'},
                    'ê': {'s': 'ế', 'f': 'ề', 'r': 'ể', 'x': 'ễ', 'j': 'ệ'},
                    'o': {'s': 'ó', 'f': 'ò', 'r': 'ỏ', 'x': 'õ', 'j': 'ọ'},
                    'ô': {'s': 'ố', 'f': 'ồ', 'r': 'ổ', 'x': 'ỗ', 'j': 'ộ'},
                    'ơ': {'s': 'ớ', 'f': 'ờ', 'r': 'ở', 'x': 'ỡ', 'j': 'ợ'},
                    'u': {'s': 'ú', 'f': 'ù', 'r': 'ủ', 'x': 'ũ', 'j': 'ụ'},
                    'ư': {'s': 'ứ', 'f': 'ừ', 'r': 'ử', 'x': 'ữ', 'j': 'ự'},
                    'y': {'s': 'ý', 'f': 'ỳ', 'r': 'ỷ', 'x': 'ỹ', 'j': 'ỵ'},
                }
                if base in mark_map_local and mark_key in mark_map_local[base]:
                    result.append(mark_map_local[base][mark_key])
                    i += 2
                    continue
        # Nếu không khớp tổ hợp → thêm ký tự thô
        result.append(c)
        i += 1
    return ''.join(result)

# --- NHÓM KÝ TỰ GỐC (ĐÃ CẬP NHẬT THEO YÊU CẦU CỦA BẠN) ---
ROOT_GROUPS = [
    list("abcdeghiklmnopqtuvy"),
    list("fsxrjwz0123456789"),
    ["delete", "enter", "backspace", "spacebar", "gợi ý", ".", ",", "?", "!", ":", ";", "(", ")", '"', "-", "...", "'", "/"]
]

# --- HÀM HỖ TRỢ ---
def get_suggestions(prefix):
    if not prefix:
        return VI_WORDS[:10]
    prefix = prefix.lower().strip()
    exact = [w for w in VI_WORDS if w.lower().startswith(prefix)]
    partial = [w for w in VI_WORDS if prefix in w.lower() and w not in exact]
    return (exact + partial)[:10]

def split_into_3(items):
    n = len(items)
    if n == 0:
        return [[], [], []]
    s1 = (n + 2) // 3
    s2 = (n - s1 + 1) // 2
    return [items[:s1], items[s1:s1 + s2], items[s1 + s2:]]



# === SỬA HÀM XỬ LÝ KÝ TỰ ===
def process_key(current_text, key):
    """
    Xử lý phím theo ngữ cảnh:
    - Nếu là phím Telex → thêm vào, rồi áp dụng Telex toàn bộ.
    - Nếu là phím chức năng → xử lý riêng.
    """
    if key == "delete":
        # Xóa từ cuối cùng (đến dấu cách gần nhất)
        words = current_text.rstrip().split(' ')
        if len(words) <= 1 and words[0] == '':
            return ""
        elif len(words) == 1:
            return ""
        else:
            # Giữ nguyên dấu cách ở cuối nếu có
            new_text = ' '.join(words[:-1])
            if current_text.endswith(' '):
                new_text += ' '
            return new_text
    elif key == "backspace":
        return current_text[:-1]
    elif key == "enter":
        return current_text + "\n"
    elif key == "spacebar":
        return current_text + " "
    else:
        # Thêm ký tự, rồi xử lý Telex toàn bộ
        new_text = current_text + key
        return apply_telex_fully(new_text)
# --- API ENDPOINTS ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/initial_groups')
def initial_groups():
    return jsonify(ROOT_GROUPS)

@app.route('/api/split_group', methods=['POST'])
def split_group():
    data = request.get_json()
    items = data.get('items', [])
    return jsonify(split_into_3(items))

# @app.route('/api/apply_char', methods=['POST'])
# def apply_char():
#     data = request.get_json()
#     current_text = data.get('text', '')
#     key = data.get('key', '')

   

#     if key == "delete":
#         new_text = process_key(current_text, key)
#     elif key == "backspace":
#         new_text = current_text[:-1]
#     elif key == "enter":
#         new_text = current_text + "\n"
#     elif key == "spacebar":
#         new_text = current_text + " "
#     else:
#         new_text = telex_transform(current_text, key)
#     return jsonify({"text": new_text})

@app.route('/api/apply_char', methods=['POST'])
def apply_char():
    data = request.get_json()
    current_text = data.get('text', '')
    key = data.get('key', '')
    new_text = process_key(current_text, key)
    return jsonify({"text": new_text})

@app.route('/api/get_suggestions', methods=['POST'])
def get_suggestions_api():
    data = request.get_json()
    prefix = data.get('prefix', '')
    words = get_suggestions(prefix)
    return jsonify(words)



@app.route('/api/help_content')
def help_content():
    help_path = os.path.join(os.path.dirname(__file__), 'huong-dan.txt')
    if os.path.exists(help_path):
        with open(help_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    return "File hướng dẫn không tồn tại."


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)