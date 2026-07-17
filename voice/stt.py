"""Speech-to-text using Whisper.

Automatically locates the FFmpeg binary via imageio-ffmpeg if ffmpeg is not
on the system PATH, so voice transcription works out-of-the-box on Windows.
"""
import os
import whisper
from config import settings

# ---------------------------------------------------------------------------
# Ensure FFmpeg is discoverable by Whisper
# ---------------------------------------------------------------------------
try:
    import imageio_ffmpeg
    _ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    # Add the directory containing ffmpeg.exe to PATH so Whisper can find it
    _ffmpeg_dir = os.path.dirname(_ffmpeg_exe)
    if _ffmpeg_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = _ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
    print(f"FFmpeg located at: {_ffmpeg_exe}")
except ImportError:
    print("imageio-ffmpeg not installed; assuming ffmpeg is on system PATH.")
except Exception as e:
    print(f"Warning: Could not locate ffmpeg via imageio-ffmpeg: {e}")

# ---------------------------------------------------------------------------
# Whisper model (loaded once, cached)
# ---------------------------------------------------------------------------
_model = None


def get_model():
    """Load Whisper model lazily on first use.

    In Docker, WHISPER_DOWNLOAD_ROOT points to the pre-downloaded model baked
    into the image at build time, avoiding runtime downloads and SHA256 mismatches.
    """
    global _model
    if _model is None:
        download_root = os.environ.get("WHISPER_DOWNLOAD_ROOT", None)
        print(f"Loading Whisper model ({settings.STT_MODEL})"
              + (f" from {download_root}" if download_root else "") + "...")
        _model = whisper.load_model(settings.STT_MODEL, download_root=download_root)
    return _model


def transcribe(audio_path: str) -> str:
    """Transcribe an audio file to text using Whisper.

    Args:
        audio_path: Path to audio file (supports .webm, .mp3, .wav, .m4a, etc.)

    Returns:
        str: Transcribed text
    """
    try:
        model = get_model()
        result = model.transcribe(audio_path, language="en")
        text = result["text"].strip()
        return text
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {str(e)}")
