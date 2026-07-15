# Task-04: 分池排名算法

## 关联验收点
- G6: 分池排名算法
- G7: 分池排名开关

## 目标
实现分池排名算法：按 categories 分池、池内排序、按配额截取、补足、全局重排。

## 修改文件
- `services/backend/core/ddo_pulse_core/digest/pool_ranker.py`（新建）

## 具体改动

### pool_ranker.py（新建）
实现 `rank_with_pools()` 函数：

```python
def rank_with_pools(
    candidates: list[dict],
    ai_tags: list[str],
    dev_tags: list[str],
    ai_quota: int,
    dev_quota: int,
    other_quota: int,
    top_n: int,
) -> list[dict]:
    """
    1. 分池：按 categories 标签分入 ai/dev/other
    2. 池内排序：按 composite_score DESC
    3. 按配额截取
    4. 补足：不足时从其他池高分文章补入
    5. 全局重排：按 composite_score DESC
    6. 截取 top_n
    """
```

实现 `categorize_article()` 辅助函数：
```python
def categorize_article(categories: list[str], ai_tags: list[str], dev_tags: list[str]) -> str:
    """返回 'ai' / 'dev' / 'other'"""
```

## 验证
运行 G6、G7 的 cmd 测试项。
