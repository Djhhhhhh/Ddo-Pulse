# 变更日志

**提交信息**: fix(scheduler): 修复 cron 表达式时区问题，使用 Asia/Shanghai 替代 UTC
**分支**: fix/2026-07-14-cron-expression-timezone-fix
**日期**: 2026-07-14
**作者**: Djhhh

## 变更文件
- services/backend/api/ddo_pulse_api/scheduler.py (modified)
- tests/test_scheduler_timezone.py (added)

## 统计
- 新增文件: 1
- 修改文件: 1
- 删除文件: 0
- 代码行数: +106 / -2

## 描述
修复定时任务 cron 表达式解析时区不正确的问题。CronTrigger.from_crontab() 默认使用 UTC，导致设置 9 点的任务在北京时间 17 点才执行。修复后显式传入 timezone=APP_TZ（Asia/Shanghai），确保按北京时间调度。
