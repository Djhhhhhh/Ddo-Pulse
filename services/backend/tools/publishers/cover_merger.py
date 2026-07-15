"""微信公众号封面图拼合工具。

将大封面 (900×383, 2.35:1) 和小封面 (383×383, 1:1) 拼合为
一张 1283×383 的图片，适配微信公众号同时使用两种裁切比例。
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

LARGE_SIZE = (900, 383)
SMALL_SIZE = (383, 383)
CANVAS_SIZE = (1283, 383)


def merge_cover_images(
    large_cover: Path | str,
    small_cover: Path | str,
    output_path: Path | str,
) -> Path:
    """将大封面和小封面拼合为微信公众号兼容的封面图。

    Args:
        large_cover: 大封面图片路径 (目标 900×383)
        small_cover: 小封面图片路径 (目标 383×383)
        output_path: 输出图片路径 (1283×383 PNG)

    Returns:
        输出图片的 Path 对象

    Raises:
        FileNotFoundError: 输入文件不存在
        ImportError: Pillow 未安装
    """
    try:
        from PIL import Image
    except ImportError:
        raise ImportError(
            "Pillow is required for cover merging. "
            "Install it with: pip install Pillow"
        )

    large_cover = Path(large_cover)
    small_cover = Path(small_cover)
    output_path = Path(output_path)

    if not large_cover.exists():
        raise FileNotFoundError(f"Large cover not found: {large_cover}")
    if not small_cover.exists():
        raise FileNotFoundError(f"Small cover not found: {small_cover}")

    # 打开并调整尺寸
    large_img = Image.open(large_cover).convert("RGB")
    if large_img.size != LARGE_SIZE:
        logger.info("Resizing large cover from %s to %s", large_img.size, LARGE_SIZE)
        large_img = large_img.resize(LARGE_SIZE, Image.LANCZOS)

    small_img = Image.open(small_cover).convert("RGB")
    if small_img.size != SMALL_SIZE:
        logger.info("Resizing small cover from %s to %s", small_img.size, SMALL_SIZE)
        small_img = small_img.resize(SMALL_SIZE, Image.LANCZOS)

    # 创建画布并拼合
    canvas = Image.new("RGB", CANVAS_SIZE, (255, 255, 255))
    canvas.paste(large_img, (0, 0))
    canvas.paste(small_img, (LARGE_SIZE[0], 0))

    # 保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(str(output_path), "PNG")
    logger.info("Cover merged: %s", output_path)

    return output_path
