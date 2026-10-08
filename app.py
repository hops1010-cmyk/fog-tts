"""Kokoro TTS server for Fog & Footprints — run on a GitHub Codespace.

Open-source voice (hexgrad/kokoro, Apache-2.0). The generator sends story
passages here with POST /tts and plays back the WAV — so even browsers that
can't run the neural model locally (e.g. Firefox) get full neural narration.

Run:  python -m uvicorn app:app --host 0.0.0.0 --port 8000
Health: GET /health   Voices: GET /voices   Synth: POST /tts
"""
import io
import time

import numpy as np
import soundfile as sf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

SAMPLE_RATE = 24000
MAX_CHARS = 800

# Kokoro voice id -> pipeline language ('a' = American, 'b' = British).
VOICES = {
    "af_heart": "a", "af_bella": "a", "af_nicole": "a", "af_aoede": "a",
    "af_kore": "a", "af_sarah": "a", "af_nova": "a", "af_sky": "a",
    "af_alloy": "a", "af_jessica": "a", "af_river": "a",
    "am_michael": "a", "am_fenrir": "a", "am_puck": "a", "am_echo": "a",
    "am_eric": "a", "am_liam": "a", "am_onyx": "a", "am_adam": "a",
    "am_santa": "a",
    "bf_alice": "b", "bf_emma": "b", "bf_isabella": "b", "bf_lily": "b",
    "bm_daniel": "b", "bm_fable": "b", "bm_george": "b", "bm_lewis": "b",
}

app = FastAPI(title="Fog & Footprints Kokoro TTS")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # generator calls from a perchance.org iframe
    allow_methods=["*"],
    allow_headers=["*"],
)

_pipelines = {}
_started = time.time()


def _pipeline(lang):
    if lang not in _pipelines:
        from kokoro import KPipeline
        _pipelines[lang] = KPipeline(lang_code=lang)
    return _pipelines[lang]


class TTSRequest(BaseModel):
    text: str = Field(max_length=MAX_CHARS)
    voice: str = "af_heart"


@app.get("/")
def root():
    return {
        "service": "Fog & Footprints Kokoro TTS",
        "usage": "POST /tts with {text, voice} -> audio/wav",
        "health": "/health",
        "voices": "/voices",
    }


@app.get("/health")
def health():
    return {"ok": True, "model_loaded": bool(_pipelines),
            "uptime_s": round(time.time() - _started)}


@app.get("/voices")
def voices():
    return {"voices": sorted(VOICES.keys())}


@app.post("/tts")
def tts(req: TTSRequest):
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="empty text")
    if req.voice not in VOICES:
        raise HTTPException(status_code=400,
                            detail="unknown voice '%s'" % req.voice)
    try:
        pipe = _pipeline(VOICES[req.voice])
        parts = []
        for _, _, audio in pipe(text, voice=req.voice):
            parts.append(audio)
        if not parts:
            raise RuntimeError("synthesis produced no audio")
        wav = np.concatenate(parts)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail="synthesis failed: %s" % e)
    buf = io.BytesIO()
    sf.write(buf, wav, SAMPLE_RATE, format="WAV")
    return Response(content=buf.getvalue(), media_type="audio/wav")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
