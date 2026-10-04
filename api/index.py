import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Check for templates folder location (inside api/ or in parent directory)
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

model = None
if API_KEY:
    genai.configure(api_key=API_KEY)
    # Using Gemini 3.8 Flash configured as Aura AI
    model = genai.GenerativeModel(
        'gemini-3.8-flash',
        system_instruction="You are Aura, a friendly, modern, and helpful advanced AI assistant."
    )

def get_bot_response(user_input):
    user_input = user_input.strip()
    
    # Check if Gemini API is available
    if not model:
        return "I need a Gemini API Key to answer any question! Please set the 'GEMINI_API_KEY' in your environment variables."
        
    try:
        # Generate a response using the AI model
        response = model.generate_content(user_input)
        return response.text
    except Exception as e:
        return f"Oops! I encountered an error while thinking: {str(e)}"

# Route matching for all common variations
@app.route("/", methods=["GET"])
@app.route("/index", methods=["GET"])
@app.route("/index.html", methods=["GET"])
def home():
    return render_template("index.html")

@app.errorhandler(404)
def not_found(e):
    if request.method == "GET" and not request.path.startswith("/get_response"):
        return render_template("index.html")
    return jsonify({"error": "Not found"}), 404

@app.route("/get_response", methods=["POST"])
def chat():
    data = request.json or {}
    user_msg = data.get("message")
    
    if not user_msg:
        return jsonify({"response": "Please say something!"})
        
    bot_reply = get_bot_response(user_msg)
    return jsonify({"response": bot_reply})

if __name__ == "__main__":
    app.run(debug=True, port=5001)
