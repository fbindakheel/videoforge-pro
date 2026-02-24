<p align="center">
  <h1>🎬 VideoForge Pro</h1>
  <p>A powerful, modern Python desktop app for video compression, conversion, filtering, and audio processing — powered by FFmpeg.</p>
</p>

---

## ✨ Features

| Category | Feature |
|---|---|
| **Compression** | Adjustable CRF (0–51), estimated output size preview |
| **Resolution** | 4K → 360p presets, custom W×H, Lanczos scaling |
| **Format** | MP4, MKV, MOV, AVI, WEBM, GIF |
| **Audio** | AAC, MP3, WAV, OPUS, mute, normalize (dynaudnorm) |
| **FPS Limiter** | Cap output frame rate (1–120 fps) |
| **Rotate & Flip** | 90°/180° rotation, horizontal/vertical flip |
| **Speed Control** | 0.25× slow-mo to 4× fast-forward |
| **Subtitle Burn-in** | Burn .srt / .ass subtitles into video |
| **Trim** | Start/end time trim |
| **GIF Export** | High-quality palette-based GIF creation |
| **Extract Audio** | Rip audio to MP3 / AAC / WAV |
| **Merge Videos** | Concatenate multiple videos via concat filter |
| **Batch Processing** | Queue multiple files, threaded processing |
| **Hardware Accel** | NVENC, AMD AMF, Apple VideoToolbox, Intel QSV |
| **Presets** | 8 built-in presets + save your own |
| **Video Info Panel** | Live metadata display (codec, FPS, bitrate, etc.) |
| **Settings Memory** | Last-used settings saved between sessions |
| **Log Export** | Save FFmpeg log to .txt |
| **Tray Notification** | Windows balloon when batch finishes |
| **Dark Mode** | Full dark-mode UI (PyQt6) |

---

## 📸 Screenshot

> _Drop video files onto the drop zone, configure settings in the tabbed panel, and hit Start._

---

## 📋 Requirements

- **Python 3.10+**
- **FFmpeg** (must be on PATH or in common install location)
- **PyQt6**

---

## 🚀 Installation

### 1. Install FFmpeg

**Windows** (recommended):
```powershell
winget install Gyan.FFmpeg
```
Or download from [ffmpeg.org](https://ffmpeg.org/download.html). Ensure `ffmpeg` is accessible on your `PATH`.

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install ffmpeg
```

### 2. Clone & Install Python Dependencies

```bash
git clone https://github.com/YOUR_USERNAME/videoforge-pro.git
cd videoforge-pro
pip install -r requirements.txt
```

### 3. Run

```bash
python main.py
```

---

## 🎛 Usage

1. **Add files** — Drag & drop videos onto the drop zone, or click **➕ Add Files**
2. **View info** — The **File Info** card updates automatically when you select a file
3. **Configure** — Use the tabbed settings panel on the right:
   - 🗜 **Compress** — CRF quality + encoding speed + GPU acceleration
   - 📺 **Resolution** — Choose output resolution or set custom size
   - 🔄 **Format** — Output container (MP4, MKV, WebM, GIF…)
   - 🔊 **Audio** — Bitrate, format, mute, or normalize
   - ✂️ **Trim & Edit** — Trim, GIF creation, merge, extract audio
   - 🎨 **Filters** — FPS limit, Rotate/Flip, Speed, Subtitle burn-in
   - ⭐ **Presets** — Apply built-in presets or save your own
4. **Process** — Click **▶ Start Processing**
5. **Monitor** — Watch progress bars + live FFmpeg log (collapse/expand with ▼)
6. **Done** — Get a system tray notification when the batch finishes

---

## ⚡ Built-in Presets

| Preset | Description |
|---|---|
| WhatsApp Size | 640px, high CRF, 64 kbps audio |
| Email Size | 640px, normalized audio |
| YouTube 1080p | Full HD, CRF 18, high quality |
| Instagram Reel | 1080×1920 vertical, 30 fps cap |
| Twitter / X GIF | 480px animated GIF, 15s max |
| Extract Audio (MP3) | 192 kbps MP3 |
| Podcast Audio (WAV) | WAV, normalized |
| High Quality Archive | MKV, CRF 18, veryslow |

---

## 🗂 File Structure

```
videoforge-pro/
├── main.py                        # Entry point
├── requirements.txt
├── README.md
├── LICENSE
├── CONTRIBUTING.md
└── app/
    ├── core/
    │   ├── ffmpeg_manager.py      # FFmpeg detection + ffprobe
    │   ├── video_processor.py     # FFmpeg command builder + QThread
    │   ├── batch_processor.py     # Job queue manager
    │   ├── presets.py             # JobConfig + PresetManager
    │   ├── settings_store.py      # Settings persistence
    │   └── utils.py               # Helpers
    └── ui/
        ├── styles.py              # QSS dark theme
        ├── main_window.py         # Root window
        └── widgets/
            ├── drop_zone.py       # Drag & drop widget
            ├── file_list.py       # Batch file queue
            ├── video_info_panel.py # Metadata card (NEW)
            ├── settings_panel.py  # 7-tab settings panel
            └── progress_panel.py  # Progress + log
```

---

## 🖥 Hardware Acceleration

Automatically detected and used if available:
- **NVIDIA** — `h264_nvenc` (requires CUDA driver)
- **AMD** — `h264_amf` (requires AMF SDK)
- **Apple** — `h264_videotoolbox` (macOS only)
- **Intel** — `h264_qsv` (Intel Quick Sync)

Falls back to software `libx264` if none found.

---

## 🔧 Troubleshooting

**"FFmpeg not found"** — Run `ffmpeg -version` in a terminal to verify it's on PATH.

**Processing fails** — Check the FFmpeg Log panel for detailed error output. Save it with 💾 Save Log.

**GIF is very large** — GIFs are uncompressed color images. Keep clips under 5–10s for web sharing.

**Subtitle burn-in fails** — Ensure the subtitle file path has no special characters and the file encoding is UTF-8.

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute.

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.

> **Note on PyQt6**: PyQt6 is licensed under GPL for open-source use. If you wish to use this project in a closed-source/commercial product, a PyQt6 commercial license is required.
