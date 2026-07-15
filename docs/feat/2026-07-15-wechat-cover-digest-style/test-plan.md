# Ddo-Pulse 测试计划

> 基于已确认的 spec.md 生成的验收测试 checklist。

## G1. 封面图拼合（AC-1, AC-2）

- [ ] cmd: python -c "from tools.publishers.cover_merger import merge_cover_images; print('import ok')"
- [ ] cmd: python -c "
from PIL import Image
from tools.publishers.cover_merger import merge_cover_images
import tempfile, os
# 创建测试图片
large = Image.new('RGB', (900, 383), 'red')
small = Image.new('RGB', (383, 383), 'blue')
with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f1:
    large.save(f1.name); lp = f1.name
with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f2:
    small.save(f2.name); sp = f2.name
out = tempfile.mktemp(suffix='.png')
result = merge_cover_images(lp, sp, out)
img = Image.open(result)
assert img.size == (1283, 383), f'Expected (1283, 383), got {img.size}'
assert img.mode == 'RGB' or img.mode == 'RGBA'
os.unlink(lp); os.unlink(sp); os.unlink(out)
print('merge ok')
"
- [ ] cmd: python -c "
from PIL import Image
from tools.publishers.cover_merger import merge_cover_images
import tempfile, os
# 测试尺寸不匹配的自动 resize
large = Image.new('RGB', (800, 300), 'red')
small = Image.new('RGB', (400, 400), 'blue')
with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f1:
    large.save(f1.name); lp = f1.name
with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f2:
    small.save(f2.name); sp = f2.name
out = tempfile.mktemp(suffix='.png')
result = merge_cover_images(lp, sp, out)
img = Image.open(result)
assert img.size == (1283, 383), f'Expected (1283, 383), got {img.size}'
os.unlink(lp); os.unlink(sp); os.unlink(out)
print('resize ok')
"
- [ ] human: 用拼合后的图片上传到微信公众号，检查首图（2.35:1 裁切）和小图（1:1 裁切）是否均显示完整内容

通过标准：所有自动化测试 exit code 为 0，拼合图片尺寸正确（1283×383），微信公众号上传后两种裁切均正常。

## G2. digest.md 排版优化（AC-3）

- [ ] cmd: python -c "
from tools.publishers.markdown import generate_digest_md
from pathlib import Path
import tempfile
# 测试空文章
out = Path(tempfile.mktemp(suffix='.md'))
generate_digest_md('2026-07-15', [], out)
content = out.read_text()
assert '# Ddo-Pulse' in content
assert '暂无' in content
out.unlink()
print('empty ok')
"
- [ ] cmd: python -c "
from tools.publishers.markdown import generate_digest_md
from pathlib import Path
import tempfile
# 测试有文章
articles = [{
    'title': 'Test Article',
    'url': 'https://example.com',
    'score': 8,
    'categories': ['AI'],
    'summary_zh': '测试摘要',
    'reason': '测试原因',
    'deep_analysis': {
        'core_content': '核心内容',
        'key_points': ['要点1', '要点2'],
        'insights': '启发'
    }
}]
out = Path(tempfile.mktemp(suffix='.md'))
generate_digest_md('2026-07-15', articles, out)
content = out.read_text()
assert 'Test Article' in content
assert '核心内容' in content
assert '要点1' in content
out.unlink()
print('article ok')
"
- [ ] human: 打开生成的 digest.md，检查排版是否层次分明、格式清晰，无多余空行或错位

通过标准：自动化测试 exit code 为 0，生成的 digest.md 格式正确、排版清晰。

## G3. 文风优化（AC-4）

- [ ] cmd: python -c "
from prompts.reporter import DEEP_ANALYSIS_PROMPT
# 验证 prompt 已更新
assert '资深技术内容分析师' not in DEEP_ANALYSIS_PROMPT, 'Old role still present'
assert 'AI' in DEEP_ANALYSIS_PROMPT or '套话' in DEEP_ANALYSIS_PROMPT or '自然' in DEEP_ANALYSIS_PROMPT, 'AI style constraint missing'
print('prompt ok')
"
- [ ] human: 运行一次完整报告生成，检查深度解读部分的文风是否更自然，无明显 AI 套话

通过标准：prompt 中不再包含旧的角色设定，且包含文风约束指令。

## G4. 回归测试（AC-5）

- [ ] cmd: cd /Users/djhhh/work_area/Ddo-Pulse-feat-2026-07-15-wechat-cover-digest-style && python -m pytest tests/ -x -q
- [ ] cmd: python -c "
from tools.publishers.html_report import generate_digest_html
from pathlib import Path
import tempfile
# HTML 报告不受影响
articles = [{'title': 'T', 'url': '#', 'score': 5, 'categories': [], 'summary_zh': '', 'reason': '', 'deep_analysis': {}}]
out = Path(tempfile.mktemp(suffix='.html'))
generate_digest_html('2026-07-15', articles, out)
assert out.exists()
out.unlink()
print('html ok')
"

通过标准：所有现有测试通过，HTML 报告生成不受影响。

## TDD 测试文件

| 测试文件 | 关联检查项 | 状态 |
|---|---|---|
| tests/test_cover_merger.py | G1 cmd1, G1 cmd2, G1 cmd3 | Red |
