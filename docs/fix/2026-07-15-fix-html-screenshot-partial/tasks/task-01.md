# Task 01: 修改 screenshot.py 实现完整截图

## 任务描述

修改 `services/backend/tools/publishers/screenshot.py` 文件，实现以下功能：

1. **修复幻灯片截图截断问题**：将 `page.screenshot()` 调用添加 `full_page=True` 参数
2. **新增封面图生成功能**：添加 `generate_covers()` 函数，生成头条封面（900×383）和次条封面（200×200）

## 关联验收点

- G1: 幻灯片截图完整性
- G2: 头条封面图
- G3: 次条封面图

## 具体修改

### 1. 修改截图调用（第 47 行）

```python
# 修改前
page.screenshot(path=str(screenshot_path))

# 修改后
page.screenshot(path=str(screenshot_path), full_page=True)
```

### 2. 新增 generate_covers() 函数

```python
def generate_covers(
    html_path: Path,
    output_dir: Path
) -> dict:
    """生成公众号封面图
    
    Returns:
        dict: {"main": Path, "sub": Path}
    """
    # 头条封面（900×383）
    # 次条封面（200×200）
```

## 输出产物

- 修改后的 `screenshot.py` 文件
- 新增 `generate_covers()` 函数

## 依赖

无
