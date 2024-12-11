import os
import tempfile
import pytest
from merge_invoices import InvoiceMerger
from PIL import Image

@pytest.fixture
def merger():
    return InvoiceMerger()

@pytest.fixture
def test_image():
    # 创建一个测试用的图片文件
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        image = Image.new('RGB', (100, 100), color='white')
        image.save(f.name)
        yield f.name
    os.remove(f.name)

def test_process_image(merger, test_image):
    """测试图片处理功能"""
    processed = merger.process_image(test_image)
    assert processed is not None
    assert isinstance(processed, Image.Image)

def test_calculate_image_size(merger):
    """测试图片尺寸计算功能"""
    image = Image.new('RGB', (1000, 2000))
    width, height = merger.calculate_image_size(image, 500, 1000)
    assert width <= 500
    assert height <= 1000
    # 检查宽高比是否保持不变
    original_ratio = 1000 / 2000
    new_ratio = width / height
    assert abs(original_ratio - new_ratio) < 0.01  # 允许小误差
