import io
from typing import Dict, Any, List
from PIL import Image

class GameAssetService:

    ASSET_TYPES = {
        "character_sprite": {
            "name": "2D Character Sprite",
            "icon": "👾",
            "prompt_suffix": "2D video game character sprite, full body view, centered, clean crisp outlines, isolated on pure solid white background, high quality game asset, no ground shadows, mobile game sprite",
            "negative_prompt": "complex background, scenery, shadows, gradients, realistic skin, noise, watermark, text"
        },
        "sprite_sheet": {
            "name": "Action / Walk Sprite Sheet",
            "icon": "🏃",
            "prompt_suffix": "sprite sheet grid showing animation walk cycle frames of character, sequential action poses, evenly spaced sprite frames, isolated on clean solid white background, 2d game art, pixel-perfect",
            "negative_prompt": "connected frames, overlapping characters, busy background, perspective distortion, blurry"
        },
        "isometric_prop": {
            "name": "Isometric Prop & Building",
            "icon": "🏰",
            "prompt_suffix": "isometric 30-degree orthographic projection, game environment prop building, sharp edges, video game strategy asset, isolated on pure plain white background, ambient occlusion lighting",
            "negative_prompt": "perspective angle, ground terrain, scenic horizon, realistic photography, blurry edges"
        },
        "rpg_item": {
            "name": "RPG Weapon, Armor & Loot Icon",
            "icon": "⚔️",
            "prompt_suffix": "RPG fantasy inventory icon, centered item, crisp detailed game asset, magical aura glow, clean vector stylized, isolated on solid white background, mobile game UI icon",
            "negative_prompt": "human holding weapon, messy backdrop, table, hands, cropped item"
        },
        "pixel_art": {
            "name": "16-Bit / Retro Pixel Art",
            "icon": "🕹️",
            "prompt_suffix": "authentic 16-bit retro pixel art sprite, clean pixel clusters, vibrant retro color palette, sharp pixels, isolated on solid white background, arcade game style",
            "negative_prompt": "vector, anti-aliased smooth gradients, photorealistic, 3d render, blurry pixels"
        },
        "seamless_texture": {
            "name": "Seamless Tileable Texture",
            "icon": "🧱",
            "prompt_suffix": "top-down flat view seamless tileable game texture, repeating pattern material, diffuse map, game level design, evenly illuminated, high resolution surface",
            "negative_prompt": "perspective slant, isometric, shadows, vignette, objects in center, horizon"
        },
        "ui_element": {
            "name": "Game UI & HUD Element",
            "icon": "🛡️",
            "prompt_suffix": "game UI interface element, fantasy menu frame button icon, clean vector graphic, user interface design asset, isolated on clean solid white background",
            "negative_prompt": "gameplay screenshot, busy screen, 3d scene, blurry"
        }
    }

    @staticmethod
    def get_asset_types() -> Dict[str, Any]:
        """Returns metadata and presets for all game asset categories."""
        return GameAssetService.ASSET_TYPES

    @staticmethod
    def build_game_asset_prompt(base_prompt: str, asset_type_key: str) -> Dict[str, str]:
        """
        Enhances the prompt specifically for game dev pipelines:
        ensures solid background isolation, proper style tokens, and negative filters.
        """
        config = GameAssetService.ASSET_TYPES.get(
            asset_type_key,
            GameAssetService.ASSET_TYPES["character_sprite"]
        )

        enhanced_prompt = f"{base_prompt.strip()}, {config['prompt_suffix']}"
        negative = config["negative_prompt"]
        return {
            "prompt": enhanced_prompt,
            "negative_prompt": negative
        }

    @staticmethod
    def remove_background(image_bytes: bytes) -> bytes:
        """
        Uses rembg to remove background from generated game sprites,
        producing a transparent PNG ready for game engines (Unity, Godot, Unreal, Pygame).
        """
        try:
            from rembg import remove
            input_img = Image.open(io.BytesIO(image_bytes))
            output_img = remove(input_img)
            
            out_buffer = io.BytesIO()
            output_img.save(out_buffer, format="PNG")
            return out_buffer.getvalue()
        except Exception as e:
            raise RuntimeError(f"Background removal failed: {str(e)}")
