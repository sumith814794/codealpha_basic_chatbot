import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Check for templates and static folder location
if os.path.exists(os.path.join(BASE_DIR, "templates")):
    template_dir = os.path.join(BASE_DIR, "templates")
    static_dir = os.path.join(BASE_DIR, "static")
else:
    template_dir = os.path.abspath(os.path.join(BASE_DIR, "..", "templates"))
    static_dir = os.path.abspath(os.path.join(BASE_DIR, "..", "static"))

app = Flask(
    __name__,
    template_folder=template_dir,
    static_folder=static_dir
)

# Configure the API key
API_KEY = os.environ.get("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)

# List of models to fall back through if one hits its rate limit
FALLBACK_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-3.8-flash"
]

SYSTEM_INSTRUCTION = "You are Aura, a friendly, modern, and helpful advanced AI assistant."

def get_bot_response(user_input):
    user_input = user_input.strip()
    
    if not API_KEY:
        return "I need a Gemini API Key to answer any question! Please set the 'GEMINI_API_KEY' in your environment variables."

    # Try each model in sequence in case one has exceeded quota
    last_error = None
    for model_name in FALLBACK_MODELS:
        try:
            model = genai.GenerativeModel(
                model_name,
                system_instruction=SYSTEM_INSTRUCTION
            )
            response = model.generate_content(user_input)
            if response and response.text:
                return response.text
        except Exception as e:
            last_error = e
            continue

    # Graceful message instead of raw JSON error dump
    return "I'm experiencing high traffic right now and my free API quota is momentarily cooling down. Please try again in a little while!"

# Serve static files explicitly
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(static_dir, filename)

# Route matching for all common variations
@app.route("/", methods=["GET"])
@app.route("/api", methods=["GET"])
@app.route("/api/index", methods=["GET"])
@app.route("/api/index.py", methods=["GET"])
@app.route("/index", methods=["GET"])
@app.route("/index.html", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/get_response", methods=["POST"])
@app.route("/api/get_response", methods=["POST"])
@app.route("/api/index/get_response", methods=["POST"])
def chat():
    data = request.json or {}
    user_msg = data.get("message")
    
    if not user_msg:
        return jsonify({"response": "Please say something!"})
        
    bot_reply = get_bot_response(user_msg)
    return jsonify({"response": bot_reply})

# Bulletproof fallback for any unexpected rewrite path from Vercel
@app.errorhandler(404)
def handle_404(e):
    if request.method == "POST":
        return chat()
    if request.path.startswith("/static/"):
        filename = request.path.replace("/static/", "", 1)
        return send_from_directory(static_dir, filename)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5001)
