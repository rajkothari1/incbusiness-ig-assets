# Project notes

## Voiceover default

Use this voice for every voiceover (business model reels, product videos, etc.) unless the user asks for a different one. Don't ask which voice to use.

- Platform: Higgsfield
- Model: `elevenlabs_v4` (via `generate_audio` with `model: "text2speech_v2"`, `variant: "elevenlabs"`)
- Voice: **Anika** (female, young), `voice_type: "preset"`, `voice_id: "4b2dc8f3-5e8b-59a9-9a5c-85620e44c033"`
- Stability: 0.3
- Emotion tags in the prompt work well, e.g. `[excited]`, `[energetic]`, `[curious]`.
- Hindi scripts are written in Devanagari, with English words transliterated (e.g. "बिज़नेस मॉडल").
