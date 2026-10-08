# Cloud voice via GitHub Codespace (Kokoro TTS server)

Runs the same open-source Kokoro-82M voice (hexgrad/kokoro, Apache-2.0) on a
free GitHub Codespace instead of in your browser. The generator sends each
story passage to your codespace with `POST /tts` and plays back the WAV.
**This is the Firefox-safe neural option** — zero local compute, just network.

Free tier: ~60 hours/month of codespace time (2-core). A full 2,500-word story
needs roughly 30–60 minutes of server time (mostly idle while audio plays).

## One-time setup (~10 minutes, mostly waiting)

You do NOT fork anything — there is no template repo. The server code lives in
your generator (`src/codespace/`, also attached as a zip in chat). You just
create a normal new repo under your account and upload the files.

1. **Download the files.** Get `fog-tts-codespace.zip` from the chat, extract
   it. You should have: `app.py`, `requirements.txt`, `README.md`, and a
   `.devcontainer/` folder containing `devcontainer.json`.
   (If the `.devcontainer` folder is invisible on your computer, that's normal
   — it's a hidden folder. Either show hidden files, or skip it for now: after
   creating the repo, use `Add file ▾` → `Create new file`, name it
   `.devcontainer/devcontainer.json`, and paste in the contents.)
2. **Create a repo.** Go to https://github.com/new — owner `hops1010-cmyk`,
   name `fog-tts`, Public or Private (either works), do NOT tick "Add a
   README" (keep it empty). Create it, then click `uploading an existing file`
   and drag in everything from the zip (files + the `.devcontainer` folder).
   Commit.
   Final layout: `app.py`, `requirements.txt`, `.devcontainer/devcontainer.json`
   (+ this README, optional).
3. **Make port 8000 public.** In the codespace bottom panel open the `PORTS`
   tab → right-click port `8000` → `Port Visibility` → `Public`.
   (Private ports need GitHub login, which the generator can't do — Public skips
   auth for anyone who knows the obscure URL. Don't share the URL publicly.)
4. **Copy the URL.** Hover the port's `Forwarded Address` → copy. It looks like
   `https://ominous-umbrella-abc123-8000.app.github.dev` (no trailing slash).
5. **Paste it in the generator.** In Narration → `Cloud voice (Codespaces)` →
   paste the URL → `Test`. You should see "Connected … + short sample OK".
   Then press play.

## Day-to-day use

- The codespace **sleeps after 30 minutes idle**. If narration suddenly fails,
  go back to the codespace tab (it wakes on open) or press `Test` (first
  request after sleep takes ~30–60s while the model reloads).
- Stopped codespaces keep your files; just start a new session on the same repo
  when needed. Delete idle codespaces to save your free hours.
- First-ever synthesis downloads the Kokoro weights (~300MB) — one slow passage,
  then fast.

## Troubleshooting

- `Test` says "not reachable": port 8000 must be **Public**, and the server
  must be running — in the codespace terminal run
  `python -m uvicorn app:app --host 0.0.0.0 --port 8000`, or check
  `/tmp/kokoro-tts.log`.
- `unknown voice`: the generator only sends voices from its dropdown; all are
  in the server's list. American voices (`af_*`, `am_*`) and British voices
  (`bf_*`, `bm_*`) each load their own pipeline on first use (one-time pause).
- `HTTP 400 empty text`: never sent by the generator (passages are non-empty).

## API contract (for tinkerers)

- `GET /` → service info. `GET /health` → `{ok, model_loaded, uptime_s}`.
- `GET /voices` → `{voices: [...]}`.
- `POST /tts` with JSON `{"text": "...≤800 chars...", "voice": "af_heart"}`
  → `audio/wav` bytes (24kHz mono) or a JSON `{"detail": ...}` error.
- CORS is wide open (`*`) so the perchance.org iframe can call it directly.
