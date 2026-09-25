# =====================================================================
#  CẤU HÌNH BOT TRAVIAN
#  Copy file này thành "config.py" rồi điền thông tin của bạn.
#  config.py đã nằm trong .gitignore nên mật khẩu không bị đẩy lên git.
# =====================================================================

# Khi đổi server game, CHỈ cần sửa dòng này (không có dấu "/" ở cuối).
SERVER_URL = "https://finals.travian.com"

# Tên làng cần nâng cấp mỏ (text hiển thị trong danh sách làng, là duy nhất).
SIM_VILLAGE_NAME = "oo SIM"

# Tài khoản
USERNAME = "your_email@example.com"
PASSWORD = "your_password"

# Proxy (để "" nếu không dùng)
PROXY = "http://user:pass@host:port"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0."
)

# Thời gian nghỉ giữa 2 vòng chạy (giây)
MIN_CYCLE_SLEEP = 180
MAX_CYCLE_SLEEP = 300

# Độ lệch khi click so với tâm element (0 = luôn click đúng tâm, 0.5 = tới sát mép).
# 0.25 nghĩa là điểm click được chọn ngẫu nhiên trong khoảng 25%-75% chiều rộng/cao.
CLICK_OFFSET = 0.25
