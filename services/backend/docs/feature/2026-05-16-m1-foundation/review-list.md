# M1 功能测试清单

- [ ] `pip install -e .` 成功
- [ ] `ddo-pulse init` 创建 `~/.ddo_pulse/config.yaml` 与 `ddo_pulse.db`
- [ ] `ddo-pulse source add` 添加 rss 源
- [ ] `ddo-pulse source list` 可见新源
- [ ] `ddo-pulse run-once` 返回 new > 0（有效 Feed）
- [ ] 第二次 `run-once` new=0（URL 去重）
- [ ] `ddo-pulse config export` 生成含 sources 的 yaml
