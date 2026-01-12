"""
Translation Service - Hybrid Thai to Chinese Translation
Uses googletrans (primary) with deep-translator fallback.
Optimized with caching and lazy initialization.
"""

import concurrent.futures
import asyncio
from typing import Optional, Tuple
from functools import lru_cache
from deep_translator import GoogleTranslator
from googletrans import Translator

class TranslationService:
    """Hybrid Thai-Chinese Translation Service with Caching"""
    
    SHORT_TEXT_THRESHOLD = 500
    CACHE_SIZE = 100  # Maximum cached translations
    
    def __init__(self):
        """Initialize translation service"""
        self._deep_translator = None  # Lazy initialization
        self._executor = None  # Lazy initialization
        self._future: Optional[concurrent.futures.Future] = None
        
        # Create cached translation method
        self._cached_translate = lru_cache(maxsize=self.CACHE_SIZE)(self._translate_impl)

    @property
    def deep_translator(self):
        """Lazy initialization of deep translator"""
        if self._deep_translator is None:
            self._deep_translator = GoogleTranslator(source='th', target='zh-CN')
        return self._deep_translator
    
    @property
    def executor(self):
        """Lazy initialization of thread pool executor"""
        if self._executor is None:
            self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        return self._executor
    
    def _translate_google_sync(self, text: str) -> str:
        """
        Wrapper to run googletrans synchronously.
        """
        try:
            # Instantiate here to avoid thread safety issues
            translator = Translator()
            result = translator.translate(text, src='th', dest='zh-cn')
            return result.text
        except Exception as e:
            raise RuntimeError(f"Googletrans error: {str(e)}")

    def _translate_impl(self, text: str) -> Tuple[str, str]:
        """
        Internal translate implementation (cached).
        Translate Thai text to Chinese using hybrid approach.
        Returns: (translated_text, translator_used)
        """
        # Strategy: Use googletrans for short text, deep-translator for long text
        use_googletrans_first = len(text) <= self.SHORT_TEXT_THRESHOLD
        
        if use_googletrans_first:
            try:
                # Try Googletrans
                result = self._translate_google_sync(text)
                return result, "googletrans"
            except Exception as e:
                print(f"Googletrans failed ({e}), switching to fallback...")
                try:
                    # Fallback to Deep Translator
                    result = self.deep_translator.translate(text)
                    return result, "deep-translator (fallback)"
                except Exception as ex:
                    raise TranslationError(f"All translators failed. Google: {e}, Deep: {ex}")
        else:
            # Long text: Deep Translator first
            try:
                result = self.deep_translator.translate(text)
                return result, "deep-translator"
            except Exception:
                try:
                    result = self._translate_google_sync(text)
                    return result, "googletrans (fallback)"
                except Exception as ex:
                     raise TranslationError(f"All translators failed: {ex}")
    
    def translate(self, text: str) -> Tuple[str, str]:
        """
        Translate Thai text to Chinese using hybrid approach with caching.
        Returns: (translated_text, translator_used)
        """
        text = text.strip()
        if not text:
            return "", "none"
        
        # Use cached implementation
        return self._cached_translate(text)

    def translate_async(self, text: str) -> None:
        """Start translation in background thread"""
        self._future = self.executor.submit(self.translate, text)
    
    def get_translation_result(self, timeout: float = 30.0) -> Tuple[str, str]:
        """Get result from background translation."""
        if self._future is None:
            raise TranslationError("No translation in progress")
        
        try:
            return self._future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TranslationError("Translation timed out")
        except Exception as e:
            raise TranslationError(f"Translation failed: {e}")
    
    def is_translation_done(self) -> bool:
        """Check if background translation is complete"""
        return self._future is not None and self._future.done()
    
    def shutdown(self):
        """Cleanup executor and clear cache"""
        if self._executor:
            self._executor.shutdown(wait=False)
        # Clear translation cache
        self._cached_translate.cache_clear()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.shutdown()
        return False
    
    def get_cache_info(self):
        """Get cache statistics"""
        return self._cached_translate.cache_info()


class TranslationError(Exception):
    """Custom exception for translation errors"""
    pass
