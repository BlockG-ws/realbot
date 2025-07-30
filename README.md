# realbot
又一个 vibe coding 产物

demo: @BlockG_bot

致力于替代 kmuav2bot，但是很明显还差点距离
# 功能
- /打 \打 这样的指令
- 清理链接
- 复读机
- 消息统计
- 按照条件解除频道消息在群组的置顶

# 运行
安装好依赖之后
```bash
BOT_TOKEN="12345678:<your token>" uv run main.py
```
默认全部功能关闭，你可以把 config.example.yaml 复制到 config.yaml 自己改一下

# TODO
我想做 matrix bot，不过这两天先不做了

# 特别感谢
- ➗ Actually Legitimate URL Shortener Tool 规则提供了一些链接清理的特性，他们的许可证在这里：
    https://github.com/DandelionSprout/adfilt/blob/master/LICENSE.md

# 许可证
GNU General Public License v3.0