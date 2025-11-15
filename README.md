# realbot
又一个 vibe coding 产物

demo: @BlockG_bot

致力于替代 kmuav2bot，但是很明显还差点距离
# 功能
- /打 \打 这样的指令
- 清理链接
- 复读机
- 抽奖
- 消息转发到联邦宇宙
- 消息统计
- 按照条件解除频道消息在群组的置顶

# 运行
## 直接运行
安装好依赖之后
```bash
uv sync
BOT_TOKEN="12345678:<your token>" uv run main.py
```
默认开启全部功能，你可以把 config.example.yaml 复制到 config.yaml 自己改一下

## 使用 Docker
```bash
docker build -t realbot .
docker run -e BOT_TOKEN="12345678:<your token>" realbot
```

另外有 Docker 镜像发布在 `ghcr.io/blockg-ws/realbot:latest`，可以直接拉取使用
```bash
docker run -e BOT_TOKEN="12345678:<your token>" ghcr.io/blockg-ws/realbot:latest
```
# TODO
我想做 matrix bot，不过这两天先不做了

# 特别感谢
- 链接清理的特性使用了 ClearURLs 插件提供的规则，他们的许可证在这里：
    https://github.com/ClearURLs/Rules/blob/master/LICENSE

# 许可证
GNU General Public License v3.0