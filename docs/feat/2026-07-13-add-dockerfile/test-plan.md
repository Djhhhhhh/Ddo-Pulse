# Ddo-Pulse Dockerfile 测试计划

> 基于已确认的 spec.md 生成的验收测试 checklist。

## G1. Dockerfile 文件规范

- [ ] cmd: test -f scripts/Dockerfile
- [ ] cmd: grep -q "FROM.*python" scripts/Dockerfile
- [ ] cmd: grep -q "FROM.*node" scripts/Dockerfile
- [ ] cmd: grep -q "EXPOSE 8765" scripts/Dockerfile
- [ ] cmd: grep -q "ENTRYPOINT" scripts/Dockerfile
- [ ] cmd: grep -q "VOLUME" scripts/Dockerfile

通过标准：Dockerfile 存在且包含多阶段构建、端口声明、入口点和数据卷声明。

## G2. 构建验证

- [ ] cmd: docker build -f scripts/Dockerfile -t ddo-pulse-test . 2>&1 | tail -5
- [ ] cmd: docker image inspect ddo-pulse-test --format '{{.Size}}' 2>/dev/null && echo "Image exists"

通过标准：`docker build` 成功完成（exit code 0），镜像已生成。

## G3. 运行时验证

- [ ] cmd: docker run -d --name ddo-pulse-verify -p 18765:8765 ddo-pulse-test && sleep 5 && curl -sf http://localhost:18765/api && docker stop ddo-pulse-verify && docker rm ddo-pulse-verify
- [ ] cmd: docker run -d --name ddo-pulse-vol -v /tmp/ddo-pulse-data:/root/.ddo_pulse ddo-pulse-test && sleep 3 && test -d /tmp/ddo-pulse-data && docker stop ddo-pulse-vol && docker rm ddo-pulse-vol && rm -rf /tmp/ddo-pulse-data

通过标准：容器启动后 API 响应正常，数据目录可挂载到宿主机。

## G4. Docker Desktop 兼容性

- [ ] human: 在 Docker Desktop 中选择「Build Image」→ 选择 scripts/Dockerfile → 设置构建上下文为项目根目录 → 构建成功
- [ ] human: 在 Docker Desktop Images 列表中找到构建的镜像 → 点击「Run」→ 配置端口 8765:8765 → 容器启动成功
- [ ] human: 浏览器访问 http://localhost:8765 → 看到 Ddo-Pulse Web UI 页面
- [ ] human: 在 Docker Desktop Containers 中查看容器 → 端口映射和 Volume 挂载信息正确显示

通过标准：Docker Desktop 可完成构建和运行全流程，Web UI 正常访问。
