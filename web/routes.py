import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, current_app, send_file
import io

logger = logging.getLogger("classpush.web.routes")

api_bp = Blueprint("api", __name__, url_prefix="/api")
web_bp = Blueprint("web", __name__)

RATE_LIMIT = {}
RATE_LIMIT_MAX = 10


def _check_rate_limit(ip):
    now = datetime.now().timestamp()
    if ip not in RATE_LIMIT:
        RATE_LIMIT[ip] = []
    RATE_LIMIT[ip] = [t for t in RATE_LIMIT[ip] if now - t < 60]
    if len(RATE_LIMIT[ip]) >= RATE_LIMIT_MAX:
        return False
    RATE_LIMIT[ip].append(now)
    return True


def _check_password():
    config = current_app.config["CONFIG"]
    required_pwd = config.get("network", {}).get("password")
    if not required_pwd:
        return True
    pwd = request.headers.get("X-Password", "")
    if pwd == required_pwd:
        return True
    data = request.get_json(silent=True)
    if data and data.get("password") == required_pwd:
        return True
    return False


@api_bp.route("/auth", methods=["POST"])
def auth():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    pwd = data.get("password", "")
    config = current_app.config["CONFIG"]
    required_pwd = config.get("network", {}).get("password")
    if not required_pwd or pwd == required_pwd:
        return jsonify({"ok": True})
    return jsonify({"error": "\u5bc6\u7801\u9519\u8bef"}), 401


@api_bp.route("/messages", methods=["POST"])
def create_message():
    if not _check_rate_limit(request.remote_addr):
        return jsonify({"error": "Too many requests"}), 429

    if not _check_password():
        return jsonify({"error": "\u5bc6\u7801\u9519\u8bef"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    content = data.get("content", "").strip()
    if not content:
        return jsonify({"error": "Content is required"}), 400
    if len(content) > 500:
        return jsonify({"error": "Content too long (max 500 chars)"}), 400

    msg_data = {
        "type": data.get("type", "\u901a\u77e5")[:20],
        "sender": data.get("sender", "\u8001\u5e08")[:20],
        "content": content,
        "duration_minutes": int(data.get("duration_minutes", 0)),
        "scheduled_at": data.get("scheduled_at"),
    }

    try:
        mm = current_app.config["MM"]
        msg_id = mm.send_message(msg_data)
        msg_data["id"] = msg_id
        msg_data["status"] = "sent"
        msg_data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return jsonify(msg_data), 201
    except Exception as e:
        logger.error("Failed to create message: %s", e)
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/messages", methods=["GET"])
def get_messages():
    mm = current_app.config["MM"]
    limit = request.args.get("limit", 20, type=int)
    offset = request.args.get("offset", 0, type=int)
    messages = mm.get_active_messages(limit=min(limit, 100), offset=offset)
    count = mm.get_active_count()
    return jsonify({"messages": messages, "total": count})


@api_bp.route("/messages/<int:msg_id>", methods=["DELETE"])
def delete_message(msg_id):
    mm = current_app.config["MM"]
    mm.delete(msg_id)
    return "", 204


@api_bp.route("/messages/<int:msg_id>/hide", methods=["POST"])
def hide_message(msg_id):
    mm = current_app.config["MM"]
    mm.hide(msg_id)
    return "", 204


@api_bp.route("/status")
def status():
    config = current_app.config["CONFIG"]
    has_password = bool(config.get("network", {}).get("password"))
    mm = current_app.config["MM"]
    from utils import network as net

    ips = net.get_local_ips()
    return jsonify(
        {
            "online": True,
            "message_count": mm.get_active_count(),
            "ip": ips[0] if ips else "127.0.0.1",
            "port": config.get("network", {}).get("port", 8080),
            "has_password": has_password,
        }
    )


@api_bp.route("/qrcode")
def qrcode():
    from utils.qrcode_gen import qrcode_to_bytes
    from utils import network as net

    ip = net.get_primary_ip()
    port = current_app.config["CONFIG"].get("network", {}).get("port", 8080)
    url = f"http://{ip}:{port}"
    img_bytes = qrcode_to_bytes(url, box_size=8)
    return send_file(io.BytesIO(img_bytes), mimetype="image/png")


@web_bp.route("/")
def index():
    return render_template("index.html")
