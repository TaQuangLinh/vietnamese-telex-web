// static/script.js
let currentText = "";
let currentGroups = [];
let inSuggestionMode = false;
let suggestionList = [];

// DOM elements
const textDisplay = document.getElementById('text-display');
const cursor = document.getElementById('cursor');

// Hiển thị văn bản (thay vì innerText → giữ nguyên khoảng trắng)
// function updateTextDisplay() {
//     textDisplay.textContent = currentText;
//     // Đảm bảo cuộn xuống cuối
//     textDisplay.scrollTop = textDisplay.scrollHeight;
// }

// Trong static/script.js

function updateTextDisplay() {
    // Thêm con trỏ nhấp nháy vào cuối văn bản
    textDisplay.innerHTML = currentText.replace(/\s$/g, '&nbsp;') + '<span id="cursor">|</span>';
    // Cuộn xuống cuối
    textDisplay.scrollTop = textDisplay.scrollHeight;
}

// Hiển thị 3 nhóm
function updateGroupsDisplay() {
    for (let i = 0; i < 3; i++) {
        const el = document.getElementById(`group${i+1}`);
        if (i < currentGroups.length && Array.isArray(currentGroups[i])) {
            el.textContent = currentGroups[i].join(', ');
        } else {
            el.textContent = "";
        }
    }
}

// Hiển thị gợi ý
function updateSuggestionsDisplay(words) {
    const el = document.getElementById('suggestions');
    if (words.length === 0 || (words.length === 1 && words[0] === "(không có)")) {
        el.textContent = "(Không có gợi ý)";
    } else {
        el.textContent = words.join(', ');
    }
}

// Gọi API: load nhóm gốc
async function loadInitialGroups() {
    const res = await fetch('/api/initial_groups');
    currentGroups = await res.json();
    updateGroupsDisplay();
    inSuggestionMode = false;
    // Cập nhật gợi ý ban đầu
    const words = currentText.trim().split(/\s+/);
    const prefix = words.length > 0 ? words[words.length - 1] : "";
    loadSuggestions(prefix);
}

// Gọi API: lấy gợi ý
async function loadSuggestions(prefix) {
    const res = await fetch('/api/get_suggestions', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({prefix: prefix})
    });
    const words = await res.json();
    updateSuggestionsDisplay(words);
}

// Áp dụng ký tự
async function applyChar(key) {
    if (key === "gợi ý") {
        enterSuggestionMode();
        return;
    }

    const res = await fetch('/api/apply_char', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text: currentText, key: key})
    });
    const data = await res.json();
    currentText = data.text;
    updateTextDisplay();

    // Reset về gốc
    loadInitialGroups();
}

// Vào chế độ chọn gợi ý
async function enterSuggestionMode() {
    const words = currentText.trim().split(/\s+/);
    const prefix = words.length > 0 ? words[words.length - 1] : "";
    const res = await fetch('/api/get_suggestions', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({prefix: prefix})
    });
    suggestionList = await res.json();
    if (suggestionList.length === 0) suggestionList = ["(không có)"];
    
    inSuggestionMode = true;
    currentGroups = splitInto3(suggestionList);
    updateGroupsDisplay();
    document.getElementById('suggestions').textContent = "Đang chọn từ...";
}

// Chia nhóm
function splitInto3(items) {
    const n = items.length;
    if (n === 0) return [[], [], []];
    const s1 = Math.ceil(n / 3);
    const s2 = Math.ceil((n - s1) / 2);
    return [items.slice(0, s1), items.slice(s1, s1 + s2), items.slice(s1 + s2)];
}

// Xử lý chọn nhóm
async function selectGroup(index) {
    if (index >= currentGroups.length) return;
    const group = currentGroups[index];
    if (!Array.isArray(group) || group.length === 0) return;

    if (group.length > 1) {
        currentGroups = splitInto3(group);
        updateGroupsDisplay();
    } else {
        const key = group[0];
        if (inSuggestionMode) {
            // Chèn từ
            const words = currentText.trim().split(/\s+/);
            if (words.length > 0 && words[0] !== "") {
                words[words.length - 1] = key;
                currentText = words.join(' ') + ' ';
            } else {
                currentText = key + ' ';
            }
            updateTextDisplay();
            loadInitialGroups();
        } else {
            applyChar(key);
        }
    }
}

// Ràng buộc phím
document.addEventListener('keydown', (e) => {
    if (e.key === '1') selectGroup(0);
    else if (e.key === '2') selectGroup(1);
    else if (e.key === '3') selectGroup(2);
});


// === HIỂN THỊ HƯỚNG DẪN ===
document.addEventListener('DOMContentLoaded', () => {
    const helpBtn = document.getElementById('help-btn');
    const modal = document.getElementById('help-modal');
    const closeBtn = document.querySelector('.close-btn');
    const helpContent = document.getElementById('help-content');

    // Tải nội dung hướng dẫn
    fetch('/api/help_content')
        .then(response => response.text())
        .then(text => {
            helpContent.textContent = text;
        })
        .catch(err => {
            helpContent.textContent = "Không tải được hướng dẫn.";
        });

    // Mở modal
    helpBtn.addEventListener('click', () => {
        modal.style.display = 'block';
    });

    // Đóng modal
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // Đóng khi click ngoài modal
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
});

// Khởi chạy
loadInitialGroups();