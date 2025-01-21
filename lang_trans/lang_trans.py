from groq import Groq
from flask import render_template, request, jsonify, session
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
class ChatSession:
    def __init__(self):
        self.messages = []
        self.last_interaction = datetime.now()

class ChatbotHandler:
    def __init__(self):
        self.client = Groq(api_key = os.environ.get("GROQ_API_KEY"))
        self.sessions = {}  # Temporary session storage
        self.system_prompt = {
            "role": "system",
            "content": """
        You are an advanced AI language translator designed and dedicated to translate text between any language pairs. Your primary functions include:

        1. Accurately translate text between any language pairs
        2. Maintain proper formatting and structure in translations
        3. Preserve the original meaning and context
        4. Handle formal and informal language appropriately
        5. Provide clear, natural-sounding translations
        6. Handle idiomatic expressions and cultural nuances
        7. Format output in a clean, readable way
        8. Identify the source language if not specified

        When translating, always:
        - Start with "Translation:" followed by the translated text
        - If needed, provide brief notes about significant cultural or contextual adaptations
        - Maintain any special formatting from the original text
        - Keep responses concise and focused on translation

        Please wait for the text to translate.
        """
        }

    def create_session(self, session_id):
        """Create a new chat session"""
        session = ChatSession()
        session.messages.append(self.system_prompt)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id):
        """Get or create a session"""
        return self.sessions.get(session_id)

    def process_message(self, message, session_id):
        if not session_id:
            return {"error": "Session expired"}, 401
            
        if not message:
            return {"error": "No message provided"}, 400

        # Get or create session
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)

        # Update session timestamp
        session.last_interaction = datetime.now()
        
        # Add user message to history
        session.messages.append({"role": "user", "content": message})

        try:
            # Get chat completion from Groq
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=session.messages,
                max_tokens=500,
                temperature=0.8
            )
            
            bot_response = response.choices[0].message.content
            
            # Add bot response to history
            session.messages.append({"role": "assistant", "content": bot_response})
            
            return {
                "response": bot_response,
                "session_active": True
            }
            
        except Exception as e:
            return {"error": str(e)}, 500

    def cleanup_old_sessions(self):
        """Remove sessions that are older than 30 minutes"""
        current_time = datetime.now()
        for session_id in list(self.sessions.keys()):
            session = self.sessions[session_id]
            if (current_time - session.last_interaction).total_seconds() > 1800:  # 30 minutes
                del self.sessions[session_id]

# Initialize chatbot instance
chatbot = ChatbotHandler()

def setup_lang_trans_routes(app, auth_required=None, track_tool_usage=None):
    """Set up routes for the language translator with authentication and usage tracking"""
    
    @app.route('/lang_trans')
    @auth_required if auth_required else lambda f: f
    def lang_trans():
        if track_tool_usage:
            track_tool_usage('TRANS001', session.get('user_id'))
        return render_template('lang_trans/lang_trans.html')

    @app.route('/status')
    @auth_required if auth_required else lambda f: f
    def check_lang_trans_status():
        return jsonify({"status": "online"})

    @app.route('/api/chat', methods=['POST'])
    @auth_required if auth_required else lambda f: f
    def handle_lang_trans_message():
        try:
            data = request.json
            if not data or 'message' not in data:
                return jsonify({"error": "No message provided"}), 400
                
            session_id = data.get('session_id')
            if not session_id:
                return jsonify({"error": "No session ID provided"}), 400
                
            response = chatbot.process_message(data['message'], session_id)
            return jsonify(response)
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/chat/reset', methods=['POST'])
    @auth_required if auth_required else lambda f: f
    def reset_lang_trans_chat():
        try:
            data = request.json
            session_id = data.get('session_id')
            if session_id and session_id in chatbot.sessions:
                del chatbot.sessions[session_id]
            return jsonify({"status": "success", "message": "Chat session reset"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
