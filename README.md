# AetherGen — AI Image & Game Asset Studio

An AI image generation web application built with **FastAPI**, **Python 3.11**, and modern vanilla web technologies.

Featuring 100% real live integrations, dynamic model syncing via API keys, AI-assisted prompt enhancement, a dedicated **Game Assets & Sprites Studio**, local transparent background removal (`rembg`), and seamless download options.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)
![rembg](https://img.shields.io/badge/rembg-Transparent%20Alpha-purple.svg)

---

## Features

- **Multi-Provider Support**: Connects directly to **OpenAI** (DALL-E 3, DALL-E 2, GPT-Image models) and **Google Gemini / Imagen** (Imagen 3 High Quality & Fast).
- **Dynamic Model Syncing**: Query the provider API with your API key to fetch available image models in real time.
- **Dedicated Game Assets & Sprites Studio**:
  - 👾 2D Character Sprites
  - 🏃 Walk/Action Sprite Sheets
  - 🏰 Isometric Props & Buildings
  - ⚔️ RPG Weapon, Armor & Loot Icons
  - 🕹️ 16-Bit / Retro Pixel Art
  - 🧱 Seamless Tileable Textures
  - 🛡️ Game UI & HUD Elements
- **One-Click Transparent Sprite Extraction**: Uses local `rembg` (no extra API charges) to isolate clean transparent PNG sprites with alpha channels.
- **Prompt Engineering Center**:
  - Quick "Add to Prompt" chips for Lighting, Art Styles, Camera Lenses, and Render Engines.
  - "✨ AI Enhance" to expand concepts into detailed cinematic prompts.
- **Multiple Download Locations**:
  - Download buttons in the top toolbar, image hover overlay, bottom footer, and session history cards.
- **Local Persistence**:
  - Session history tracked in SQLite (`data/history.db`).
  - Secure `.env` storage for provider API keys.

---

## Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/mahethekiller/Image-Generation.git
   cd Image-Generation
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Add your keys or save them directly inside the web application UI:
   ```env
   OPENAI_API_KEY=your_openai_key_here
   GEMINI_API_KEY=your_gemini_key_here
   HOST=127.0.0.1
   PORT=8000
   ```

4. **Run the Application**:
   ```bash
   python run.py
   ```
   Open your browser at: **http://127.0.0.1:8000**

---

## License
MIT License
