"""
Backend verification test suite for AetherGen
"""
import io
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app.services.game_asset_service import GameAssetService
from app.services import storage_service

client = TestClient(app)

def test_routes():
    print("Testing GET / ...")
    r = client.get("/")
    assert r.status_code == 200, f"Index failed: {r.status_code}"
    print("GET / OK")

    print("Testing GET /api/config/keys ...")
    r = client.get("/api/config/keys")
    assert r.status_code == 200, f"Keys status failed: {r.status_code}"
    data = r.json()
    assert "openai" in data and "gemini" in data
    print("Config keys OK:", data)

    print("Testing GET /api/prompt/categories ...")
    r = client.get("/api/prompt/categories")
    assert r.status_code == 200
    cats = r.json()
    assert "Lighting" in cats and "Art Style" in cats
    print(f"Prompt categories OK ({len(cats)} categories)")

    print("Testing GET /api/game-asset/types ...")
    r = client.get("/api/game-asset/types")
    assert r.status_code == 200
    types = r.json()
    assert "character_sprite" in types and "sprite_sheet" in types
    print(f"Game asset types OK ({len(types)} types)")

    print("Testing GET /api/history ...")
    r = client.get("/api/history")
    assert r.status_code == 200
    print("History endpoint OK")

def test_rembg_integration():
    print("Testing rembg background removal integration...")
    # Create a simple 64x64 white box on colored background
    img = Image.new("RGBA", (64, 64), (255, 255, 255, 255))
    for x in range(20, 44):
        for y in range(20, 44):
            img.putpixel((x, y), (255, 0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    # Process via GameAssetService
    transparent_bytes = GameAssetService.remove_background(raw_bytes)
    assert len(transparent_bytes) > 0
    res_img = Image.open(io.BytesIO(transparent_bytes))
    assert res_img.mode == "RGBA"
    print("rembg integration verified successfully!")

if __name__ == "__main__":
    print("Running backend tests...")
    test_routes()
    test_rembg_integration()
    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")
