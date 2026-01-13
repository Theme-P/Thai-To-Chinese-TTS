"""
TTS Service - MeloTTS Speech Synthesis
Chinese text-to-speech with voice selection using MeloTTS
Optimized with lazy loading and automatic cleanup
"""

import os
import sys
import io
import tempfile
from pathlib import Path

# Fix OpenMP conflict on Windows
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from typing import Dict, Optional, List, Tuple

from melo.api import TTS

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("Warning: pydub not available, MP3 conversion disabled")


class MeloTTSService:
    """Chinese Text-to-Speech Service using MeloTTS with Lazy Loading"""
    
    def __init__(self, device: str = 'auto'):
        """
        Initialize MeloTTS service
        
        Args:
            device: 'auto', 'cpu', 'cuda', or 'mps'
        """
        self.device = device
        
        # Lazy initialization
        self._model = None
        self._speaker_ids = None
        self._speakers = None
        self._voices = None
    
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
    
    def generate_speech(self, text: str, speed: float = 1.0) -> Tuple[bytes, str]:
        """
        Generate speech from Chinese text using MeloTTS, converted to MP3.
        
        Args:
            text: Chinese text to synthesize
            speed: Speech speed (0.5-2.0)
        
        Returns:
            Tuple of (audio_bytes, format) where format is 'mp3' or 'wav'
        """
        if not text.strip():
            raise TTSError("Text cannot be empty")
        
        # Trigger model loading if needed
        model = self.model
        
        # Use first (and only) Chinese speaker
        speaker_id = self._speaker_ids[self._speakers[0]]
        
        tmp_wav_path = None
        tmp_mp3_path = None
        
        try:
            # Create a temporary WAV file to capture MeloTTS output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_wav_path = tmp_file.name
            
            # Generate speech with MeloTTS to temp WAV file
            model.tts_to_file(
                text=text,
                speaker_id=speaker_id,
                output_path=tmp_wav_path,
                speed=speed,
                quiet=True
            )
            
            # Try to convert WAV to MP3 using pydub
            if PYDUB_AVAILABLE:
                try:
                    # Load WAV file
                    audio = AudioSegment.from_wav(tmp_wav_path)
                    
                    # Create temporary MP3 file
                    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                        tmp_mp3_path = tmp_file.name
                    
                    # Export as MP3 (bitrate 192k for good quality)
                    audio.export(tmp_mp3_path, format='mp3', bitrate='192k')
                    
                    # Read MP3 file into memory
                    with open(tmp_mp3_path, 'rb') as f:
                        audio_bytes = f.read()
                    
                    audio_format = 'mp3'
                    print("Successfully converted to MP3")
                    
                except Exception as conv_error:
                    # Fallback to WAV if conversion fails (e.g., ffmpeg not installed)
                    print(f"MP3 conversion failed ({conv_error}), falling back to WAV")
                    with open(tmp_wav_path, 'rb') as f:
                        audio_bytes = f.read()
                    audio_format = 'wav'
            else:
                # Fallback to WAV if pydub not available
                print("pydub not available, returning WAV format")
                with open(tmp_wav_path, 'rb') as f:
                    audio_bytes = f.read()
                audio_format = 'wav'
            
            return audio_bytes, audio_format
            
        except Exception as e:
            raise TTSError(f"Failed to generate speech: {e}")
        finally:
            # Clean up temp files
            if tmp_wav_path and os.path.exists(tmp_wav_path):
                os.unlink(tmp_wav_path)
            if tmp_mp3_path and os.path.exists(tmp_mp3_path):
                os.unlink(tmp_mp3_path)
    
    def shutdown(self):
        """Cleanup resources"""
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
