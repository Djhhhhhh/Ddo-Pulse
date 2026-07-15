# Task 01: 新增封面图拼合工具

## 目标

创建 `services/backend/tools/publishers/cover_merger.py`，实现 `merge_cover_images()` 函数。

## 关联验收点

- G1 cmd1: 模块可导入
- G1 cmd2: 拼合后尺寸正确 (1283×383)
- G1 cmd3: 尺寸不匹配时自动 resize

## 实现要求

1. 创建 `cover_merger.py` 文件
2. 实现 `merge_cover_images(large_cover, small_cover, output_path)` 函数
3. 使用 Pillow 打开两张图片
4. 验证/调整尺寸：large → 900×383，small → 383×383
5. 创建 1283×383 的空白画布（白色背景）
6. 将 large 粘贴到 (0, 0)，small 粘贴到 (900, 0)
7. 保存为 PNG
8. 输入文件不存在时抛出 FileNotFoundError

## 文件清单

- 新增：`services/backend/tools/publishers/cover_merger.py`
