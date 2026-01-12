"""
Web Application for Thai-Chinese TTS with MeloTTS
Optimized for reduced resource consumption
"""

import os
import atexit
from flask import Flask, render_template, request, jsonify

# Import services (now in the same directory)
from translation_service import TranslationService, TranslationError
from melo_tts_service import MeloTTSService, TTSError

app = Flask(__name__)

# Configure Flask
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size
app.config['JSON_SORT_KEYS'] = False

# Initialize services lazily
# Output dir relative to WebApp static folder
current_dir = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(current_dir, 'static', 'audio')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Services initialized on first use
_translation_service = None
_tts_service = None

def get_translation_service():
    """Lazy initialization of translation service"""
    global _translation_service
    if _translation_service is None:
        print("Initializing translation service...")
        _translation_service = TranslationService()
    return _translation_service

def get_tts_service():
    """Lazy initialization of TTS service"""
    global _tts_service
    if _tts_service is None:
        print("Initializing TTS service (model will load on first request)...")
        _tts_service = MeloTTSService(output_dir=OUTPUT_DIR)
    return _tts_service

def cleanup_services():
    """Cleanup services on shutdown"""
    global _translation_service, _tts_service
    
    if _translation_service:
        print("Shutting down translation service...")
        _translation_service.shutdown()
    
    if _tts_service:
        print("Shutting down TTS service...")
        _tts_service.shutdown()

# Register cleanup handler
atexit.register(cleanup_services)

@app.route('/')
def index():
    """Render main interface"""
    return render_template('index.html')

@app.route('/api/convert', methods=['POST'])
def convert():
    """
    Process: Thai Text -> Chinese Text -> Audio (MeloTTS)
    """
    # Get services (lazy initialization)
    translation_service = get_translation_service()
    tts_service = get_tts_service()
    
    data = request.json
    thai_text = data.get('text', '').strip()
    speed = data.get('speed', 1.0)  # Default speed 1.0
    
    # Validate speed range
    try:
        speed = float(speed)
        speed = max(0.5, min(2.0, speed))  # Clamp to 0.5-2.0
    except (ValueError, TypeError):
        speed = 1.0

    if not thai_text:
        return jsonify({'error': 'No text provided'}), 400

    # 1. Translate Thai -> Chinese
    try:
        chinese_text, mechanism = translation_service.translate(thai_text)
    except TranslationError as e:
        return jsonify({'error': f'Translation failed: {str(e)}'}), 500

    # 2. TTS with MeloTTS
    try:
         filepath = tts_service.generate_speech(chinese_text, speed=speed)
         filename = os.path.basename(filepath)
         
         # Return result
         return jsonify({
             'thai': thai_text,
             'chinese': chinese_text,
             'audio_url': f'/static/audio/{filename}',
             'translator': mechanism,
             'tts_engine': 'MeloTTS',
             'speed': speed
         })
         
    except TTSError as e:
        return jsonify({'error': f'TTS generation failed: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'translation_service': 'initialized' if _translation_service else 'lazy',
        'tts_service': 'initialized' if _tts_service else 'lazy'
    })

if __name__ == '__main__':
    import sys
    
    # Check if running in debug mode
    debug_mode = '--debug' in sys.argv
    
    print(f"Starting Thai-Chinese TTS Web Application...")
    print(f"Debug mode: {debug_mode}")
    print(f"Services will initialize on first request (lazy loading)")
    
    app.run(
        debug=debug_mode,
        host='0.0.0.0',
        port=5001,
        threaded=True
    )