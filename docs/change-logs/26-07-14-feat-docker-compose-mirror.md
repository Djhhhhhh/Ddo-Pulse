# 变更日志

**提交信息**: feat(docker): 添加 docker-compose 配置，优化国内镜像源和启动脚本
**分支**: main
**日期**: 2026-07-14
**作者**: Djhhh

## 变更文件
- docker-compose.yml (added)
- scripts/Dockerfile (modified)
- scripts/docker-start.sh (modified)

## 统计
- 新增文件: 1
- 修改文件: 2
- 删除文件: 0
- 代码行数: +27 / -5

## 描述
新增 docker-compose.yml 支持一键容器化部署；Dockerfile 配置 npm/pip 国内镜像源加速构建，修复 Windows 换行符问题；docker-start.sh 增加错误捕获和窗口保持功能。
