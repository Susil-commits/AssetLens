import os
import uuid
import logging
import threading
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import imageio_ffmpeg
from faster_whisper import WhisperModel
from backend.config import settings

logger = logging.getLogger("assetlens.transcription")

class Transcriber:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Transcriber, cls).__new__(cls)
                cls._instance._model = None
                cls._instance._model_lock = threading.Lock()
            return cls._instance

    def _get_model(self) -> WhisperModel:
        with self._model_lock:
            if self._model is None:
                device = "cpu"  # Robust and fast with int8 quantization
                compute_type = "int8"
                model_name = getattr(settings, "WHISPER_MODEL_NAME", "base")
                logger.info(f"Loading faster-whisper model '{model_name}' on {device} ({compute_type})...")
                self._model = WhisperModel(model_name, device=device, compute_type=compute_type)
            return self._model

    def extract_audio(self, video_path: Path, output_wav: Path) -> bool:
        """Extracts 16kHz mono PCM WAV audio track from video using FFmpeg."""
        try:
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            cmd = [
                ffmpeg_exe, "-y",
                "-i", str(video_path),
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                str(output_wav)
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
            if res.returncode == 0 and output_wav.exists() and output_wav.stat().st_size > 1000:
                return True
            logger.warning(f"Audio extraction from {video_path.name} produced no valid audio (exit code {res.returncode})")
            return False
        except Exception as e:
            logger.warning(f"Failed to extract audio from {video_path.name}: {e}")
            return False

    def transcribe_video(self, video_path: Path) -> List[Dict[str, Any]]:
        """
        Transcribes speech audio from video and returns timestamped segments.
        Gracefully returns an empty list if video has no audio or transcription fails.
        """
        temp_wav = settings.DERIVED_DIR / f"_temp_audio_{uuid.uuid4().hex[:8]}.wav"
        try:
            has_audio = self.extract_audio(video_path, temp_wav)
            if not has_audio:
                return []

            model = self._get_model()
            segments, info = model.transcribe(str(temp_wav), beam_size=1)
            
            results = []
            for s in segments:
                text_clean = s.text.strip()
                if text_clean:
                    results.append({
                        "start": round(float(s.start), 2),
                        "end": round(float(s.end), 2),
                        "text": text_clean
                    })
            logger.info(f"Transcribed {len(results)} speech segments from {video_path.name}")
            return results
        except Exception as e:
            logger.warning(f"Transcription failed for video {video_path.name}: {e}. Falling back to visual-only search.")
            return []
        finally:
            if temp_wav.exists():
                try:
                    temp_wav.unlink()
                except Exception:
                    pass

transcriber = Transcriber()
