"""
TTS Service - MeloTTS Speech Synthesis
Chinese text-to-speech with voice selection using MeloTTS
Optimized with lazy loading and automatic cleanup
"""

import os
import sys
import time
import threading
from pathlib import Path

# Fix OpenMP conflict on Windows
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from datetime import datetime, timedelta
from typing import Dict, Optional, List

from melo.api import TTS


class MeloTTSService:
    """Chinese Text-to-Speech Service using MeloTTS with Lazy Loading"""
    
    # Cleanup configuration
    CLEANUP_INTERVAL_SECONDS = 3600  # 1 hour
    MAX_FILE_AGE_SECONDS = 3600  # 1 hour
    
    def __init__(self, output_dir: str = 'output', device: str = 'auto', auto_cleanup: bool = True):
        """
        Initialize MeloTTS service
        
        Args:
            output_dir: Directory to save audio files
            device: 'auto', 'cpu', 'cuda', or 'mps'
            auto_cleanup: Enable automatic cleanup of old audio files
        """
        self.output_dir = output_dir
        self.device = device
        os.makedirs(output_dir, exist_ok=True)
        
        # Lazy initialization
        self._model = None
        self._speaker_ids = None
        self._speakers = None
        self._voices = None
        
        # Cleanup thread
        self._cleanup_enabled = auto_cleanup
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        
        if self._cleanup_enabled:
            self._start_cleanup_thread()
    
    @property
    def model(self):
        """Lazy initialization of MeloTTS model"""
        if self._model is None:
            print("Loading MeloTTS Chinese model...")
            self._model = TTS(language='ZH', device=self.device)
            
            # Get available speakers from model
            self._speaker_ids = self._model.hps.data.spk2id
            self._speakers = list(self._speaker_ids.keys())
            
            # Create voice mapping for API compatibility
            self._voices = self._build_voice_mapping()
            print(f"MeloTTS loaded. Available speakers: {self._speakers}")
        return self._model
    
    def _build_voice_mapping(self) -> Dict[str, Dict[str, str]]:
        """Build voice mapping from MeloTTS speakers"""
        if self._speaker_ids is None:
            # Trigger model loading
            _ = self.model
        
        voices = {}
        labels = {
            'ZH': 'Chinese Female',
        }
        
        for idx, speaker in enumerate(self._speakers, 1):
            key = str(idx)
            label = labels.get(speaker, speaker)
            voices[key] = {
                'name': speaker,
                'label': label,
                'speaker_id': self._speaker_ids[speaker]
            }
        
        return voices
    
    def get_voices(self) -> Dict[str, Dict[str, str]]:
        """Get available voices"""
        if self._voices is None:
            # Trigger model loading
            _ = self.model
        return self._voices
    
    def get_voice_labels(self) -> List[str]:
        """Get formatted voice labels for display"""
        return [f"{key}. {v['label']}" for key, v in self._voices.items()]
    
    def get_voice_name(self, choice: str) -> Optional[str]:
        """Get voice name from choice number"""
        if choice in self._voices:
            return self._voices[choice]['name']
        return None
    
    def get_speaker_id(self, choice: str) -> Optional[int]:
        """Get speaker ID from choice number"""
        if choice in self._voices:
            return self._voices[choice]['speaker_id']
        return None
    
    def is_valid_choice(self, choice: str) -> bool:
        """Check if voice choice is valid"""
        if self._voices is None:
            _ = self.model
        return choice in self._voices
    
    def generate_speech(self, text: str, speed: float = 1.0) -> str:
        """
        Generate speech from Chinese text using MeloTTS.
        
        Args:
            text: Chinese text to synthesize
            speed: Speech speed (0.5-2.0)
        
        Returns:
            filepath to generated audio (WAV format)
        """
        if not text.strip():
            raise TTSError("Text cannot be empty")
        
        # Trigger model loading if needed
        model = self.model
        
        # Use first (and only) Chinese speaker
        speaker_id = self._speaker_ids[self._speakers[0]]
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"melo_tts_{timestamp}.wav"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # Generate speech with MeloTTS
            model.tts_to_file(
                text=text,
                speaker_id=speaker_id,
                output_path=filepath,
                speed=speed,
                quiet=True
            )
            return filepath
        except Exception as e:
            raise TTSError(f"Failed to generate speech: {e}")
    
    def get_file_size_kb(self, filepath: str) -> float:
        """Get file size in KB"""
        return os.path.getsize(filepath) / 1024
    
    def _cleanup_old_files(self):
        """Remove audio files older than MAX_FILE_AGE_SECONDS"""
        try:
            now = time.time()
            audio_dir = Path(self.output_dir)
            
            if not audio_dir.exists():
                return
            
            removed_count = 0
            for audio_file in audio_dir.glob("*.wav"):
                try:
                    file_age = now - audio_file.stat().st_mtime
                    if file_age > self.MAX_FILE_AGE_SECONDS:
                        audio_file.unlink()
                        removed_count += 1
                except Exception as e:
                    print(f"Error removing file {audio_file}: {e}")
            
            if removed_count > 0:
                print(f"Cleaned up {removed_count} old audio files")
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def _cleanup_worker(self):
        """Background worker for periodic cleanup"""
        while not self._stop_cleanup.is_set():
            self._cleanup_old_files()
            # Wait with ability to interrupt
            self._stop_cleanup.wait(self.CLEANUP_INTERVAL_SECONDS)
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._stop_cleanup.clear()
            self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
            self._cleanup_thread.start()
            print("Started automatic audio file cleanup")
    
    def stop_cleanup(self):
        """Stop background cleanup thread"""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._stop_cleanup.set()
            self._cleanup_thread.join(timeout=2)
            print("Stopped automatic audio file cleanup")
    
    def cleanup_now(self):
        """Manually trigger cleanup"""
        self._cleanup_old_files()
    
    def shutdown(self):
        """Cleanup resources"""
        self.stop_cleanup()
        # Clear model from memory
        self._model = None
        self._speaker_ids = None
        self._speakers = None
        self._voices = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.shutdown()
        return False


class TTSError(Exception):
    """Custom exception for TTS errors"""
    pass
