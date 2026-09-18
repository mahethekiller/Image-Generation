import base64
import httpx
import requests
from typing import List, Dict, Any, Optional

class ProviderError(Exception):
    """Custom exception for provider-specific API errors."""
    pass

class ProviderService:

    @staticmethod
    def sync_models(provider: str, api_key: str) -> List[Dict[str, Any]]:
        """
        Dynamically queries the provider's API with the provided API key
        to validate credentials and retrieve available models.
        """
        provider = provider.lower().strip()
        if not api_key:
            raise ProviderError("API key is required to sync models.")

        if provider == "openai":
            return ProviderService._sync_openai_models(api_key)
        elif provider in ["gemini", "google"]:
            return ProviderService._sync_gemini_models(api_key)
        else:
            raise ProviderError(f"Unsupported provider: {provider}")

    @staticmethod
    def _sync_openai_models(api_key: str) -> List[Dict[str, Any]]:
        url = "https://api.openai.com/v1/models"
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "User-Agent": "AI-ImageGen-App/1.0"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                err_data = resp.json().get("error", {})
                err_msg = err_data.get("message", resp.text)
                raise ProviderError(f"OpenAI API Error ({resp.status_code}): {err_msg}")

            data = resp.json()
            models_data = data.get("data", [])
            
            # Filter and prioritize image generation models
            image_models = []
            known_image_models = ["dall-e-3", "dall-e-2", "gpt-image-1", "gpt-image-1-mini"]

            # First add known image models if accessible
            all_model_ids = {m.get("id") for m in models_data if "id" in m}
            for km in known_image_models:
                if km in all_model_ids:
                    image_models.append({
                        "id": km,
                        "name": f"OpenAI {km.upper()}",
                        "type": "image",
                        "description": "Image generation model"
                    })
                elif km in ["dall-e-3", "dall-e-2"]:
                    # Ensure primary dall-e models are available options
                    image_models.append({
                        "id": km,
                        "name": f"OpenAI {km.upper()}",
                        "type": "image",
                        "description": "Standard OpenAI Image Model"
                    })

            # Check for any other models with 'dall-e' or 'image'
            for m in models_data:
                mid = m.get("id", "")
                if ("dall-e" in mid or "gpt-image" in mid or mid.startswith("image-")) and mid not in [im["id"] for im in image_models]:
                    image_models.append({
                        "id": mid,
                        "name": f"OpenAI {mid}",
                        "type": "image",
                        "description": "Image model"
                    })

            return image_models
        except requests.RequestException as e:
            raise ProviderError(f"Failed to connect to OpenAI: {str(e)}")

    @staticmethod
    def _sync_gemini_models(api_key: str) -> List[Dict[str, Any]]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key.strip()}"
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200:
                err_data = resp.json().get("error", {})
                err_msg = err_data.get("message", resp.text)
                raise ProviderError(f"Google Gemini API Error ({resp.status_code}): {err_msg}")

            data = resp.json()
            models_list = data.get("models", [])
            
            found_models = []
            known_imagen_ids = [
                "imagen-3.0-generate-002",
                "imagen-3.0-fast-generate-001",
                "imagen-3.0-generate-001"
            ]

            available_names = [m.get("name", "").replace("models/", "") for m in models_list]

            # Match returned models
            for km in known_imagen_ids:
                if km in available_names:
                    found_models.append({
                        "id": km,
                        "name": f"Google {km}",
                        "type": "image",
                        "description": "Google Imagen 3 image generation"
                    })
            
            # If Google API key is valid (status 200) but imagen models weren't listed in the general models list,
            # include the standard Imagen 3 endpoints which are active on generative AI keys
            if not found_models:
                found_models = [
                    {
                        "id": "imagen-3.0-generate-002",
                        "name": "Google Imagen 3 (High Quality)",
                        "type": "image",
                        "description": "Highest quality photorealistic & artistic output"
                    },
                    {
                        "id": "imagen-3.0-fast-generate-001",
                        "name": "Google Imagen 3 (Fast)",
                        "type": "image",
                        "description": "Rapid generation model"
                    }
                ]

            return found_models
        except requests.RequestException as e:
            raise ProviderError(f"Failed to connect to Google Gemini: {str(e)}")

    @staticmethod
    def generate_image(
        provider: str,
        api_key: str,
        model: str,
        prompt: str,
        aspect_ratio: str = "1:1",
        quality: str = "standard",
        negative_prompt: str = ""
    ) -> bytes:
        """
        Executes real image generation request to the chosen provider.
        Returns raw image bytes.
        """
        provider = provider.lower().strip()
        if not api_key:
            raise ProviderError("API key is required for generation.")
        if not prompt or not prompt.strip():
            raise ProviderError("Prompt cannot be empty.")

        if provider == "openai":
            return ProviderService._generate_openai(api_key, model, prompt, aspect_ratio, quality)
        elif provider in ["gemini", "google"]:
            return ProviderService._generate_gemini(api_key, model, prompt, aspect_ratio, negative_prompt)
        else:
            raise ProviderError(f"Unsupported provider: {provider}")

    @staticmethod
    def _generate_openai(
        api_key: str,
        model: str,
        prompt: str,
        aspect_ratio: str = "1:1",
        quality: str = "standard"
    ) -> bytes:
        url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json"
        }

        # Size mapping based on aspect ratio for DALL-E 3
        # DALL-E 3 supports: 1024x1024 (1:1), 1024x1792 (9:16), 1792x1024 (16:9)
        if model == "dall-e-3":
            if aspect_ratio == "16:9":
                size = "1792x1024"
            elif aspect_ratio == "9:16":
                size = "1024x1792"
            else:
                size = "1024x1024"
        else:
            # DALL-E 2 supports 1024x1024, 512x512, 256x256
            size = "1024x1024"

        payload: Dict[str, Any] = {
            "model": model or "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": size
        }

        if model == "dall-e-3":
            payload["quality"] = "hd" if quality == "hd" else "standard"

        resp = requests.post(url, headers=headers, json=payload, timeout=90)
        if resp.status_code != 200:
            err_msg = resp.text
            try:
                err_data = resp.json()
                err_msg = err_data.get("error", {}).get("message", resp.text)
            except Exception:
                pass
            raise ProviderError(f"OpenAI Image Generation Error ({resp.status_code}): {err_msg}")

        data = resp.json()
        items = data.get("data", [])
        if not items:
            raise ProviderError("OpenAI did not return any image data.")

        item = items[0]
        # Handle b64_json directly if returned (e.g. gpt-image models)
        if "b64_json" in item and item["b64_json"]:
            return base64.b64decode(item["b64_json"])

        # Handle CDN URL if returned (e.g. dall-e-3 / dall-e-2 standard)
        if "url" in item and item["url"]:
            img_resp = requests.get(item["url"], timeout=60)
            if img_resp.status_code == 200:
                return img_resp.content
            raise ProviderError(f"Failed to retrieve image from OpenAI URL ({img_resp.status_code})")

        raise ProviderError("OpenAI response did not contain b64_json or url image data.")

    @staticmethod
    def _generate_gemini(
        api_key: str,
        model: str,
        prompt: str,
        aspect_ratio: str = "1:1",
        negative_prompt: str = ""
    ) -> bytes:
        # Standardize aspect ratio format: "1:1", "3:4", "4:3", "9:16", "16:9"
        valid_ratios = ["1:1", "3:4", "4:3", "9:16", "16:9"]
        if aspect_ratio not in valid_ratios:
            aspect_ratio = "1:1"

        clean_model = model.replace("models/", "") if model else "imagen-3.0-generate-002"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:predict?key={api_key.strip()}"
        
        headers = {"Content-Type": "application/json"}
        parameters: Dict[str, Any] = {
            "sampleCount": 1,
            "aspectRatio": aspect_ratio,
            "outputMimeType": "image/png"
        }
        if negative_prompt and negative_prompt.strip():
            parameters["negativePrompt"] = negative_prompt.strip()

        payload = {
            "instances": [
                {"prompt": prompt}
            ],
            "parameters": parameters
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=90)
        if resp.status_code != 200:
            err_msg = resp.text
            try:
                err_data = resp.json()
                err_msg = err_data.get("error", {}).get("message", resp.text)
            except Exception:
                pass
            raise ProviderError(f"Google Imagen Error ({resp.status_code}): {err_msg}")

        data = resp.json()
        predictions = data.get("predictions", [])
        if not predictions:
            raise ProviderError("Google Imagen did not return any image predictions.")

        img_b64 = predictions[0].get("bytesBase64Encoded")
        if not img_b64:
            raise ProviderError("No image data found in Google Imagen response.")

        return base64.b64decode(img_b64)
