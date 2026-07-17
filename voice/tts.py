"""Text-to-speech using gTTS."""
from gtts import gTTS
from pathlib import Path
from config import settings


def synthesize(text: str, out_dir: str = "static") -> str:
    """Synthesize text to speech and save as MP3.
    
    Args:
        text: Text to synthesize
        out_dir: Output directory (must exist)
    
    Returns:
        str: Path to generated audio file (relative to project root)
    """
    if not text or len(text.strip()) == 0:
        raise ValueError("Text cannot be empty")
    
    try:
        # Generate a unique filename with timestamp
        import time
        timestamp = int(time.time() * 1000)
        filename = f"reply_{timestamp}.mp3"
        output_path = Path(out_dir) / filename
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Synthesize and save
        tts = gTTS(text=text, lang=settings.TTS_LANGUAGE, slow=False)
        tts.save(str(output_path))
        
        # Return relative path for serving
        return f"/static/{filename}"
    
    except Exception as e:
        raise RuntimeError(f"Text-to-speech failed: {str(e)}")

