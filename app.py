from flask import Flask, abort, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_socketio import SocketIO
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import json
import time
import logging
import os
import urllib
from werkzeug.utils import secure_filename


from file_merge_pipeline import process_word_documents  # 你的业务逻辑

app = Flask(__name__)
app.secret_key = 'your-secret-key'

bcrypt = Bcrypt(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

USERS_FILE = "users.json"
AVATAR_FOLDER = 'static/avatars'
ALLOWED_AVATAR_EXT = {'png', 'jpg', 'jpeg', 'gif'}

# ------ 用户数据读写 ------
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        try:
            users = json.load(f)
            if isinstance(users, dict):
                return users
            elif isinstance(users, list):  # 兼容老格式
                return {u["username"]: u for u in users if isinstance(u, dict) and "username" in u}
            else:
                return {}
        except Exception:
            return {}

def save_users(users_dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_dict, f, ensure_ascii=False, indent=2)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[-1].lower() in ALLOWED_AVATAR_EXT

if not os.path.exists(AVATAR_FOLDER):
    os.makedirs(AVATAR_FOLDER, exist_ok=True)

USERS = load_users()

# ------ 用户模型 ------
class User(UserMixin):
    def __init__(self, username, role, nickname=None, avatar_url=None):
        self.id = username
        self.role = role
        self.nickname = nickname
        self.avatar_url = avatar_url

    @staticmethod
    def get(username):
        user = USERS.get(username)
        if not user:
            return None
        return User(
            username,
            user.get('role', 'user'),
            user.get('nickname', username),
            user.get('avatar_url', None)
        )

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def format_seconds_to_hms(seconds):
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

# --------- 用户注册、登录、登出、自注销 -----------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        nickname = request.form.get("nickname","").strip() or username
        if not username or not password:
            flash("用户名和密码不能为空")
            return render_template("register.html")
        if username in USERS:
            flash("用户名已存在")
            return render_template("register.html")
        pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        USERS[username] = {
            "username": username,
            "password_hash": pw_hash,
            "role": "user",
            "nickname": nickname,
            "avatar_url": "",
            "usage_log": []
        }
        save_users(USERS)
        flash("注册成功，请登录")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = USERS.get(username)
        if user and bcrypt.check_password_hash(user['password_hash'], password):
            user_obj = User(username, user['role'], user.get('nickname',username), user.get('avatar_url',""))
            login_user(user_obj)
            user.setdefault("usage_log", []).append(
                {"event":"login", "time":time.strftime("%Y-%m-%d %H:%M:%S")})
            save_users(USERS)
            return redirect(url_for('index'))
        else:
            flash("用户名或密码错误")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route('/unregister', methods=['POST'])
@login_required
def unregister():
    if current_user.role == 'admin':
        flash('管理员账号无法自助注销！')
        return redirect(url_for('index'))
    username = current_user.id
    if username in USERS:
        USERS.pop(username)
        save_users(USERS)
        logout_user()
        flash("注销成功，您的账号已删除")
        return redirect(url_for("register"))
    return jsonify({'status': 'error', 'message': '账号不存在'}), 404

# --------- 使用说明 -----------
@app.route('/usage')
def usage():
    return render_template('usage.html')


# --------- 用户主界面 -----------

@app.route("/")
@login_required
def index():
    # 传递昵称和头像给模板
    userinfo = USERS.get(current_user.id, {})
    return render_template("index.html", 
        nickname = userinfo.get("nickname", current_user.id),
        avatar_url = userinfo.get("avatar_url", None),
        role = userinfo.get("role", "user")
    )

# --------- 管理员用户管理 -----------
@app.route("/admin/users")
@login_required
def admin_users():
    if current_user.role != "admin":
        return "无权限", 403
    users_list = []
    for u in USERS.values():
        users_list.append({
            "username": u["username"],
            "role": u["role"],
            "nickname": u.get("nickname", u["username"]),
            "avatar_url": u.get("avatar_url"),
            "usage_log": u.get("usage_log", [])
        })
    return render_template("admin_users.html", users=users_list)

@app.route("/admin/add_user", methods=["GET", "POST"])
@login_required
def admin_add_user():
    if current_user.role != "admin":
        return "无权限", 403
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form.get("role", "user")
        nickname = request.form.get("nickname","").strip() or username
        if not username or not password:
            flash("用户名和密码不能为空")
            return render_template("admin_add_user.html")
        if username in USERS:
            flash("用户名已存在")
            return render_template("admin_add_user.html")
        pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        USERS[username] = {
            "username": username,
            "password_hash": pw_hash,
            "role": role,
            "nickname": nickname,
            "avatar_url": "",
            "usage_log": []
        }
        save_users(USERS)
        flash("添加成功")
        return redirect(url_for("admin_users"))
    return render_template("admin_add_user.html")

@app.route("/admin/delete_user/<username>", methods=["POST"])
@login_required
def admin_delete_user(username):
    if current_user.role != "admin":
        return "无权限", 403
    if username in USERS:
        if username == current_user.id:
            flash("不能删除自己")
        else:
            USERS.pop(username)
            save_users(USERS)
    return redirect(url_for("admin_users"))

# 管理员重置用户密码
@app.route('/admin/reset_pwd', methods=['POST'])
@login_required
def admin_reset_pwd():
    if current_user.role != 'admin':
        abort(403)
    username = request.form.get('username')
    users = load_users()
    if username in users:
        users[username]['password_hash'] = bcrypt.generate_password_hash('123456').decode('utf-8')
        save_users(users)
        flash(f"用户{username}密码已重置为123456")
    else:
        flash('用户不存在')
    return redirect(url_for('admin_users'))

# --------- 用户资料更新 -----------
@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    nickname = request.form.get('nickname', '').strip()
    avatar = request.files.get('avatar')
    user = USERS.get(current_user.id)
    if not user:
        flash('用户不存在')
        return redirect(url_for('index'))
    if nickname:
        user['nickname'] = nickname
    # 头像上传
    if avatar and allowed_file(avatar.filename):
        ext = avatar.filename.rsplit('.', 1)[-1].lower()
        filename = secure_filename(f"{current_user.id}.{ext}")
        avatar_path = os.path.join(AVATAR_FOLDER, filename)
        avatar.save(avatar_path)
        user['avatar_url'] = f'avatars/{filename}'
    save_users(USERS)
    flash('资料已更新')
    return redirect(url_for('index'))

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_pwd = request.form.get('current_password')
    new_pwd = request.form.get('new_password')
    confirm_pwd = request.form.get('confirm_password')
    user = USERS.get(current_user.id)
    if not user:
        flash('用户不存在')
        return redirect(url_for('index'))
    # 校验原密码
    if not bcrypt.check_password_hash(user['password_hash'], current_pwd):
        flash('当前密码错误', 'danger')
        return redirect(url_for('index'))
    # 新密码一致性
    if new_pwd != confirm_pwd:
        flash('新密码与确认密码不一致', 'danger')
        return redirect(url_for('index'))
    if len(new_pwd) < 6:
        flash('新密码不少于6位', 'danger')
        return redirect(url_for('index'))
    # 修改密码并保存
    user['password_hash'] = bcrypt.generate_password_hash(new_pwd).decode('utf-8')
    save_users(USERS)
    logout_user()
    flash('密码修改成功，请重新登录', 'success')
    return redirect(url_for('login'))

# --------- 业务API -----------

@app.route("/start", methods=["POST"])
@login_required
def start_process():
    # 检查用户权限
    if current_user.role != 'admin':
        return jsonify({"status": "error", "message": "没有权限操作"}), 403

    files = request.files.getlist("files")
    module_config_file = request.files.get("module_config")
    days = int(request.form.get("days", 7))
    if not files:
        return jsonify({"status": "error", "message": "没有上传文件"}), 400
    if not module_config_file:
        return jsonify({"status": "error", "message": "缺少必要参数：模块配置文件"}), 400

    input_dir = os.path.join(os.getcwd(), "uploaded_input")
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
    else:
        # 清空目录
        for root, dirs, files_in_dir in os.walk(input_dir, topdown=False):
            for name in files_in_dir:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

    for f in files:
        rel_path = f.filename
        save_path = os.path.join(input_dir, rel_path)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        f.save(save_path)
    module_config_path = os.path.join(input_dir, module_config_file.filename)
    module_config_file.save(module_config_path)

    output_dir = os.path.join(os.getcwd(), "default_output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    USERS[current_user.id].setdefault("usage_log", []).append(
        {"event": "start_process", "time": time.strftime("%Y-%m-%d %H:%M:%S")}
    )
    save_users(USERS)

    socketio.start_background_task(
        run_process, input_dir, output_dir, days, module_config_path
    )
    return jsonify({"status": "started"})

def run_process(input_dir, output_dir, days, module_config):
    total_start_time = time.time()
    stop_flag = {"stop": False}
    last_progress = {
        "percent": 0,
        "current_step_name": "无",
        "current_step_elapsed": 0,
        "history": [],
    }
    current_step_state = {
        "name": None,
        "start_time": None,
        "elapsed": 0
    }
    def timer_thread():
        while not stop_flag["stop"]:
            now = time.time()
            step_elapsed = 0
            if current_step_state["start_time"] is not None:
                step_elapsed = now - current_step_state["start_time"]
            socketio.emit("progress_update", {
                "percent": last_progress["percent"],
                "current_step_name": current_step_state["name"] or last_progress["current_step_name"],
                "current_step_elapsed": format_seconds_to_hms(step_elapsed),
                "history": [
                    {"name": h["name"], "time": format_seconds_to_hms(h["time"])}
                    for h in (last_progress.get("history") or [])
                ],
                "total_elapsed": format_seconds_to_hms(now - total_start_time)
            })
            socketio.sleep(1)
    socketio.start_background_task(timer_thread)

    def progress_callback(percent, current_step_name=None, current_step_elapsed=None, history=None):
        if current_step_name and current_step_name != current_step_state["name"]:
            current_step_state["name"] = current_step_name
            current_step_state["start_time"] = time.time()
        last_progress.update({
            "percent": percent,
            "current_step_name": current_step_name or last_progress.get("current_step_name"),
            "current_step_elapsed": current_step_elapsed or 0,
            "history": history or last_progress.get("history"),
        })
        now = time.time()
        step_elapsed = 0
        if current_step_state["start_time"] is not None:
            step_elapsed = now - current_step_state["start_time"]
        socketio.emit("progress_update", {
            "percent": percent,
            "current_step_name": current_step_name,
            "current_step_elapsed": format_seconds_to_hms(step_elapsed),
            "history": [
                {"name": h["name"], "time": format_seconds_to_hms(h["time"])}
                for h in (history or [])
            ],
            "total_elapsed": format_seconds_to_hms(now - total_start_time)
        })
        socketio.sleep(0)
    try:
        # 假设处理函数返回输出文件路径
        output_file_path = process_word_documents(
            input_dir=input_dir,
            output_root=output_dir,
            log_root_dir="log",
            days_to_keep=days,
            module_config_file=module_config,
            progress_callback=progress_callback
        )
        stop_flag["stop"] = True
        now = time.time()
        step_elapsed = 0
        if current_step_state["start_time"] is not None:
            step_elapsed = now - current_step_state["start_time"]

        # 拼接可供下载的URL，注意做URL编码
        safe_path = urllib.parse.quote(output_file_path)
        download_url = f"/download?file_path={safe_path}"

        socketio.emit("process_done", {
            "status": "完成",
            "total_elapsed": format_seconds_to_hms(now - total_start_time),
            "download_url": download_url  # 新增
        })
    except Exception as e:
        stop_flag["stop"] = True
        logging.exception("处理异常:")
        socketio.emit("process_error", {"status": "失败", "error": str(e)})

@app.route('/download', methods=['GET'])
@login_required
def download_result_file():
    file_path = request.args.get('file_path')
    if not file_path:
        return abort(400, '缺少文件路径参数')
    # 仅允许下载 output_dir 下文件，防止任意路径下载
    abs_output_dir = os.path.abspath(os.path.join(os.getcwd(), "default_output"))
    abs_file_path = os.path.abspath(file_path)
    if not abs_file_path.startswith(abs_output_dir):
        return abort(403, '非法访问')

    if not os.path.isfile(abs_file_path):
        return abort(404, "文件不存在")

    # 生成一个不重复的文件名，比如加上时间戳或用户id
    ext = os.path.splitext(abs_file_path)[1]
    basename = os.path.splitext(os.path.basename(abs_file_path))[0]
    import time
    import random
    # 例如：result_用户名_20240610_143012.docx
    safe_user = current_user.username if hasattr(current_user, "username") else f"user{current_user.id}"
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    random_part = random.randint(1000, 9999)
    download_name = f"{basename}_{safe_user}_{timestamp}_{random_part}{ext}"

    # Flask 2.0+: use download_name, old Flask use attachment_filename
    return send_file(abs_file_path, as_attachment=True, download_name=download_name)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
