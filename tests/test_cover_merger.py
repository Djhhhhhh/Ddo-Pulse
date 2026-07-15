"""封面图拼合工具测试。"""
import tempfile
from pathlib import Path

import pytest
from PIL import Image


class TestCoverMergerImport:
    """G1 cmd1: cover_merger 模块可导入"""

    def test_import(self):
        from tools.publishers.cover_merger import merge_cover_images
        assert callable(merge_cover_images)


class TestCoverMergerMerge:
    """G1 cmd2: 拼合后尺寸正确 (1283×383)"""

    def test_merge_correct_size(self):
        from tools.publishers.cover_merger import merge_cover_images

        large = Image.new("RGB", (900, 383), "red")
        small = Image.new("RGB", (383, 383), "blue")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f1:
            large.save(f1.name)
            lp = f1.name
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f2:
            small.save(f2.name)
            sp = f2.name
        out = tempfile.mktemp(suffix=".png")

        result = merge_cover_images(lp, sp, out)
        img = Image.open(result)
        assert img.size == (1283, 383), f"Expected (1283, 383), got {img.size}"

        Path(lp).unlink()
        Path(sp).unlink()
        Path(out).unlink()


class TestCoverMergerResize:
    """G1 cmd3: 尺寸不匹配时自动 resize"""

    def test_auto_resize(self):
        from tools.publishers.cover_merger import merge_cover_images

        large = Image.new("RGB", (800, 300), "red")
        small = Image.new("RGB", (400, 400), "blue")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f1:
            large.save(f1.name)
            lp = f1.name
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f2:
            small.save(f2.name)
            sp = f2.name
        out = tempfile.mktemp(suffix=".png")

        result = merge_cover_images(lp, sp, out)
        img = Image.open(result)
        assert img.size == (1283, 383), f"Expected (1283, 383), got {img.size}"

        Path(lp).unlink()
        Path(sp).unlink()
        Path(out).unlink()


class TestCoverMergerFileNotFound:
    """输入文件不存在时抛出异常"""

    def test_missing_file(self):
        from tools.publishers.cover_merger import merge_cover_images

        with pytest.raises(FileNotFoundError):
            merge_cover_images(
                Path("/nonexistent/large.png"),
                Path("/nonexistent/small.png"),
                Path("/tmp/out.png"),
            )
