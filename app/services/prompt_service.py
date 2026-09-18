import requests
from typing import Dict, Any, List

class PromptService:

    @staticmethod
    def get_prompt_categories() -> Dict[str, List[str]]:
        """Returns structured modifiers for quick addition to prompts."""
        return {
            "Lighting": [
                "cinematic lighting",
                "volumetric god rays",
                "dramatic rim light",
                "neon cyberpunk glow",
                "warm golden hour sunlight",
                "studio softbox lighting",
                "moody chiaroscuro",
                "bioluminescent ambient glow"
            ],
            "Art Style": [
                "photorealistic 8k",
                "digital concept art",
                "anime studio style",
                "vibrant watercolor",
                "oil painting on canvas",
                "3D Octane render",
                "dark fantasy illustration",
                "clean vector art",
                "retro vintage comic book"
            ],
            "Camera & View": [
                "wide angle dynamic shot",
                "close-up macro detail",
                "shallow depth of field bokeh",
                "isometric orthographic view",
                "low-angle heroic perspective",
                "bird's-eye aerial view",
                "telephoto lens compression"
            ],
            "Engine & Quality": [
                "Unreal Engine 5 masterpiece",
                "ArtStation trending",
                "subsurface scattering",
                "hyperdetailed intricate textures",
                "ray traced reflections",
                "sharp crisp focus"
            ]
        }

    @staticmethod
    def enhance_prompt_with_ai(
        base_prompt: str,
        provider: str,
        api_key: str,
        style_preference: str = "cinematic"
    ) -> str:
        """
        Uses the user's connected AI provider (OpenAI or Gemini) to craft an enhanced,
        highly detailed image generation prompt. Falls back to smart rule expansion if needed.
        """
        base_prompt = base_prompt.strip()
        if not base_prompt:
            return ""

        instruction = (
            f"You are an expert prompt engineer for AI image generators (DALL-E 3, Midjourney, Imagen). "
            f"Given this raw concept: '{base_prompt}', expand it into an evocative, visually rich, detailed prompt. "
            f"Style focus: {style_preference}. "
            f"Include lighting, atmosphere, colors, camera framing, textures, and depth. "
            f"Output ONLY the prompt text without quotes, explanation, or prefixes."
        )

        try:
            if provider.lower() == "openai" and api_key:
                return PromptService._enhance_with_openai(api_key, instruction)
            elif provider.lower() in ["gemini", "google"] and api_key:
                return PromptService._enhance_with_gemini(api_key, instruction)
        except Exception:
            pass

        # Smart rule-based fallback
        return PromptService._rule_based_enhance(base_prompt, style_preference)

    @staticmethod
    def _enhance_with_openai(api_key: str, prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 150,
            "temperature": 0.7
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            return content
        return ""

    @staticmethod
    def _enhance_with_gemini(api_key: str, prompt: str) -> str:
        # Try gemini-1.5-flash or gemini-2.0-flash
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key.strip()}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            candidates = resp.json().get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
        return ""

    @staticmethod
    def _rule_based_enhance(prompt: str, style: str) -> str:
        modifiers = {
            "cinematic": "cinematic lighting, dramatic atmosphere, 8k resolution, photorealistic, intricate textures, depth of field",
            "fantasy": "epic fantasy concept art, magical volumetric glow, detailed digital painting, ArtStation trending, high fantasy",
            "anime": "vibrant anime visual style, sharp clean line art, studio anime aesthetic, dynamic lighting, expressive colors",
            "cyberpunk": "cyberpunk neon atmosphere, rain-slicked reflections, dark urban dystopia, volumetric smoke, high contrast",
            "game_asset": "game ready asset, clean silhouette, isolated object, professional studio lighting, 4k texture fidelity"
        }
        add_on = modifiers.get(style, modifiers["cinematic"])
        return f"{prompt}, {add_on}"
