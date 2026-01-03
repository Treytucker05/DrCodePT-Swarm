from PIL import Image
from agent.adapters.openrouter_adapter import OpenRouterAdapter
from agent.adapters.openai_adapter import OpenAIAdapter


def test_openrouter_encode_image_with_pil(tmp_path):
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    adapter = OpenRouterAdapter(api_key="dummy")
    data_uri = adapter._encode_image(img)
    assert data_uri.startswith("data:image/png;base64,")


def test_openai_encode_image_with_path(tmp_path):
    img_path = tmp_path / "img.png"
    Image.new("RGB", (8, 8), color=(255, 0, 0)).save(img_path)
    adapter = OpenAIAdapter(api_key="dummy")
    data_uri = adapter._encode_image(img_path)
    assert data_uri.startswith("data:image/png;base64,")
