import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from agents.main_agent import MainAgent
from datetime import datetime
from typing import Dict, Any
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set")

class IBPApplication:
    def __init__(self):
        """Initialize the IBP application with Flask and MainAgent."""
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for all routes
        self.main_agent = MainAgent(api_key=GROQ_API_KEY)
        self._setup_routes()
        self.session_data = {}

    def _setup_routes(self) -> None:
        """Set up Flask routes."""
        self.app.route('/chat', methods=['POST'])(self.handle_chat)
        self.app.route('/health', methods=['GET'])(self.health_check)
        
        # Error handlers
        self.app.errorhandler(400)(self.bad_request_error)
        self.app.errorhandler(500)(self.internal_server_error)

    def _validate_chat_request(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate the chat request data."""
        if not data:
            return False, "No data provided"
        if 'message' not in data:
            return False, "No message field in request"
        if not isinstance(data['message'], str):
            return False, "Message must be a string"
        if not data['message'].strip():
            return False, "Message cannot be empty"
        return True, ""

    def handle_chat(self):
        """Handle incoming chat requests."""
        try:
            # Get request data
            data = request.get_json()
            
            # Validate request
            is_valid, error_message = self._validate_chat_request(data)
            if not is_valid:
                return jsonify({
                    "error": error_message,
                    "status": "error"
                }), 400

            # Log incoming request
            logger.info(f"Received chat request: {data['message'][:100]}...")

            # Process message through MainAgent
            start_time = datetime.now()
            response = self.main_agent.process_query(data['message'])
            processing_time = (datetime.now() - start_time).total_seconds()

            # Log processing time
            logger.info(f"Request processed in {processing_time:.2f} seconds")

            # Prepare response
            return jsonify({
                "response": response,
                "status": "success",
                "processing_time": processing_time
            })

        except Exception as e:
            logger.error(f"Error processing chat request: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                "error": "An error occurred processing your request",
                "status": "error",
                "details": str(e) if self.app.debug else "Internal server error"
            }), 500

    def health_check(self):
        """Health check endpoint."""
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        })

    @staticmethod
    def bad_request_error(error):
        """Handle 400 Bad Request errors."""
        return jsonify({
            "error": "Bad Request",
            "message": str(error),
            "status": "error"
        }), 400

    @staticmethod
    def internal_server_error(error):
        """Handle 500 Internal Server Error."""
        logger.error(f"Internal Server Error: {str(error)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "status": "error"
        }), 500

    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the Flask application."""
        logger.info(f"Starting IBP application on port {port}")
        self.app.run(host=host, port=port, debug=debug)

# Application entry point
def create_app() -> IBPApplication:
    """Create and configure the IBP application."""
    return IBPApplication()

if __name__ == '__main__':
    ibp_app = create_app()
    ibp_app.run(debug=True)