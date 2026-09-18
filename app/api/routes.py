from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from pathlib import Path

from app.config import get_env_var, save_api_key, OUTPUTS_DIR
from app.services.provider_service import ProviderService, ProviderError
from app.services.prompt_service import PromptService
from app.services.game_asset_service import GameAssetService
from app.services import storage_service

router = APIRouter()

# --- Request Models ---

class SaveKeyRequest(BaseModel):
    provider: str
    api_key: str

class SyncModelsRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None

class EnhancePromptRequest(BaseModel):
    prompt: str
    provider: Optional[str] = "openai"
    api_key: Optional[str] = None
    style: Optional[str] = "cinematic"

class GenerateImageRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None
    model: str
    prompt: str
    negative_prompt: Optional[str] = ""
    aspect_ratio: Optional[str] = "1:1"
    quality: Optional[str] = "standard"
    mode: Optional[str] = "standard"

class GenerateGameAssetRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None
    model: str
    prompt: str
    asset_type: str = "character_sprite"
    aspect_ratio: Optional[str] = "1:1"
    auto_remove_bg: Optional[bool] = False

# --- Endpoints ---

def resolve_api_key(provider: str, req_key: Optional[str] = None) -> str:
    """Resolves API key: uses request key if provided, otherwise reads directly from .env."""
    if req_key and req_key.strip():
        return req_key.strip()
    return get_env_var(f"{provider.upper()}_API_KEY", "").strip()

@router.get("/config/keys")
def get_configured_keys():
    """Returns status of configured keys in .env."""
    openai_key = get_env_var("OPENAI_API_KEY", "").strip()
    gemini_key = get_env_var("GEMINI_API_KEY", "").strip()
    return {
        "openai": {
            "has_key": bool(openai_key),
            "preview": f"{openai_key[:4]}...{openai_key[-4:]}" if len(openai_key) > 8 else ("***" if openai_key else "")
        },
        "gemini": {
            "has_key": bool(gemini_key),
            "preview": f"{gemini_key[:4]}...{gemini_key[-4:]}" if len(gemini_key) > 8 else ("***" if gemini_key else "")
        }
    }

@router.post("/config/save-key")
def save_key(req: SaveKeyRequest):
    """Saves API key to the local .env file."""
    if not req.api_key.strip():
        raise HTTPException(status_code=400, detail="API key cannot be empty.")
    key_name = save_api_key(req.provider, req.api_key.strip())
    return {"status": "success", "message": f"{key_name} saved successfully to .env"}

@router.post("/models/sync")
def sync_models(req: SyncModelsRequest):
    """Dynamically tests key and fetches real models list from the provider using .env or provided key."""
    key = resolve_api_key(req.provider, req.api_key)
    if not key:
        raise HTTPException(
            status_code=400,
            detail=f"No API key found in .env or input for {req.provider.upper()}. Please configure your key in .env or enter it in the key input."
        )

    try:
        models = ProviderService.sync_models(req.provider, key)
        return {"provider": req.provider, "models": models, "source": "env" if not (req.api_key and req.api_key.strip()) else "input"}
    except ProviderError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal sync error: {str(e)}")

@router.get("/prompt/categories")
def get_prompt_categories():
    """Returns curated quick-add prompt tokens."""
    return PromptService.get_prompt_categories()

@router.post("/prompt/enhance")
def enhance_prompt(req: EnhancePromptRequest):
    """Uses connected AI or smart rules to expand prompt."""
    provider = req.provider or "openai"
    key = resolve_api_key(provider, req.api_key)
    enhanced = PromptService.enhance_prompt_with_ai(
        base_prompt=req.prompt,
        provider=provider,
        api_key=key,
        style_preference=req.style or "cinematic"
    )
    return {"original": req.prompt, "enhanced": enhanced}

@router.get("/game-asset/types")
def get_game_asset_types():
    """Returns all game asset categories with metadata."""
    return GameAssetService.get_asset_types()

@router.post("/generate")
def generate_standard_image(req: GenerateImageRequest):
    """Generates real image via provider and saves to disk."""
    key = resolve_api_key(req.provider, req.api_key)
    if not key:
        raise HTTPException(status_code=400, detail=f"No API key for {req.provider.upper()}. Please enter or save one in .env.")

    try:
        img_bytes = ProviderService.generate_image(
            provider=req.provider,
            api_key=key,
            model=req.model,
            prompt=req.prompt,
            aspect_ratio=req.aspect_ratio or "1:1",
            quality=req.quality or "standard",
            negative_prompt=req.negative_prompt or ""
        )

        record = storage_service.save_generation(
            provider=req.provider,
            model=req.model,
            prompt=req.prompt,
            negative_prompt=req.negative_prompt,
            mode=req.mode or "standard",
            aspect_ratio=req.aspect_ratio or "1:1",
            image_bytes=img_bytes,
            extension="png"
        )
        return {"status": "success", "data": record}
    except ProviderError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@router.post("/game-asset/generate")
def generate_game_asset(req: GenerateGameAssetRequest):
    """Generates specialized game asset and handles optional background removal."""
    key = resolve_api_key(req.provider, req.api_key)
    if not key:
        raise HTTPException(status_code=400, detail=f"No API key for {req.provider.upper()}. Please enter or save one in .env.")

    try:
        # Build specialized game prompt
        tailored = GameAssetService.build_game_asset_prompt(req.prompt, req.asset_type)

        img_bytes = ProviderService.generate_image(
            provider=req.provider,
            api_key=key,
            model=req.model,
            prompt=tailored["prompt"],
            aspect_ratio=req.aspect_ratio or "1:1",
            quality="standard",
            negative_prompt=tailored["negative_prompt"]
        )

        record = storage_service.save_generation(
            provider=req.provider,
            model=req.model,
            prompt=req.prompt,
            negative_prompt=tailored["negative_prompt"],
            mode=f"game_asset:{req.asset_type}",
            aspect_ratio=req.aspect_ratio or "1:1",
            image_bytes=img_bytes,
            extension="png"
        )

        if req.auto_remove_bg and record:
            try:
                transparent_bytes = GameAssetService.remove_background(img_bytes)
                record = storage_service.update_transparent_version(record["id"], transparent_bytes)
            except Exception as bg_err:
                print(f"Auto background removal failed: {bg_err}")

        return {"status": "success", "data": record}
    except ProviderError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Game asset generation failed: {str(e)}")

@router.post("/game-asset/remove-bg/{generation_id}")
def remove_background_endpoint(generation_id: str):
    """Processes background removal using rembg for an existing generation."""
    item = storage_service.get_generation(generation_id)
    if not item:
        raise HTTPException(status_code=404, detail="Generation not found.")

    img_path = OUTPUTS_DIR / item["image_filename"]
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Original image file missing.")

    try:
        with open(img_path, "rb") as f:
            raw_bytes = f.read()
        transparent_bytes = GameAssetService.remove_background(raw_bytes)
        updated = storage_service.update_transparent_version(generation_id, transparent_bytes)
        return {"status": "success", "data": updated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Background removal failed: {str(e)}")

@router.get("/history")
def get_history(limit: int = 40):
    """Returns previous generations list."""
    return storage_service.get_recent_generations(limit=limit)

@router.get("/download/{generation_id}")
def download_image(generation_id: str, format: str = Query("original")):
    """Serves real direct file download with attachment header."""
    item = storage_service.get_generation(generation_id)
    if not item:
        raise HTTPException(status_code=404, detail="Generation not found.")

    if format == "transparent" and item.get("transparent_filename"):
        file_path = OUTPUTS_DIR / item["transparent_filename"]
        dl_filename = f"sprite_{generation_id[:8]}_transparent.png"
    else:
        file_path = OUTPUTS_DIR / item["image_filename"]
        dl_filename = f"image_{generation_id[:8]}.png"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found on disk.")

    return FileResponse(
        path=str(file_path),
        media_type="image/png",
        filename=dl_filename
    )
