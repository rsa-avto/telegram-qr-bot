from flask import Flask, send_from_directory
import os

app = Flask(__name__)

EXPORT_DIR = r"C:\Users\New\telegram-qr-bot\exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

@app.route("/downloads/<filename>")
def download_file(filename):
    file_path = os.path.join(EXPORT_DIR, filename)
    if not os.path.exists(file_path):
        return "❌ Файл не найден", 404
    return send_from_directory(EXPORT_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
