import os, uuid, redis, json, logging
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}'
)
log = logging.getLogger(__name__)

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD") or None,
    decode_responses=True
)
MAX_TTL = int(os.getenv("MAX_TTL_SECONDS", 604800))


@app.route("/health")
def health():
    try:
        r.ping()
        return jsonify({"status": "ok", "redis": "connected"}), 200
    except Exception as e:
        log.error(f"Health check failed: {e}")
        return jsonify({"status": "error", "redis": "disconnected"}), 503


@app.route("/api/secret", methods=["POST"])
def create_secret():
    data = request.get_json()
    if not data or not data.get("ciphertext"):
        return jsonify({"error": "ciphertext is required"}), 400
    ciphertext = data["ciphertext"]
    ttl = int(data.get("ttl", 3600))
    one_time = bool(data.get("one_time", True))
    if ttl > MAX_TTL:
        return jsonify({"error": f"TTL max is {MAX_TTL}s"}), 400
    if len(ciphertext) > 65536:
        return jsonify({"error": "Secret too large (max 64 KB)"}), 400
    sid = str(uuid.uuid4())
    r.setex(sid, ttl, json.dumps({"ciphertext": ciphertext, "one_time": one_time}))
    log.info(f"created id={sid} ttl={ttl} one_time={one_time}")
    return jsonify({"id": sid}), 201


@app.route("/api/secret/<sid>", methods=["GET"])
def get_secret(sid):
    """Devolve o ciphertext SEM eliminar — a eliminacao e feita pelo /confirm"""
    raw = r.get(sid)
    if raw is None:
        log.info(f"not found id={sid}")
        return jsonify({"error": "Secret not found or already read"}), 404
    payload = json.loads(raw)
    log.info(f"fetched id={sid} one_time={payload.get('one_time')}")
    return jsonify({
        "ciphertext": payload["ciphertext"],
        "one_time": payload.get("one_time", True)
    }), 200


@app.route("/api/secret/<sid>/confirm", methods=["DELETE"])
def confirm_read(sid):
    """Chamado pelo browser APOS decifragem bem-sucedida — so entao elimina"""
    raw = r.get(sid)
    if raw is None:
        return jsonify({"error": "Not found"}), 404
    r.delete(sid)
    log.info(f"consumed id={sid}")
    return jsonify({"status": "deleted"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
