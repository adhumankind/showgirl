# ShowGirl 插件

一个简单的美女图片获取插件，可通过关键词或语义理解来触发，从网络API获取美女图片。

## 功能特点

- 关键词触发：当消息中包含"美女"或"妹子"等关键词时自动触发
- 语义触发：通过简单NLU识别用户请求图片的意图（如"发个好看的"）
- 安全性保障：验证图片URL是否使用HTTPS
- 频率限制：同一用户6秒内仅允许请求一次
- 异常处理：当API请求失败时提供友好提示

## 安装方法

1. 将本插件目录放置于 `plugins/` 目录下
2. 重启程序或使用 `#scanp` 命令扫描插件
3. 使用 `#enablep ShowGirl` 启用插件

## 配置说明

配置文件位于 `plugins/showgirl/config.json`，可配置以下参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| api_url | string | https://api.317ak.com/API/tp/mntp.php | 图片API地址 |
| timeout | number | 10 | API请求超时时间(秒) |
| frequency_limit | number | 6 | 用户请求频率限制(秒) |
| enable_nlu | boolean | true | 是否启用语义触发 |

## 使用方法

向机器人发送以下类型的消息即可触发：

1. 包含关键词：
   - "发张美女图片"
   - "来个妹子看看"

2. 语义理解（如启用）：
   - "发个好看的"
   - "来张图片"
   - "想要看照片"

## 注意事项

- 本插件仅转发第三方API，不存储任何图片
- 使用的API来源：https://api.317ak.com/?action=doc&id=52
- 图片内容仅供个人娱乐使用
- 微信仅支持HTTPS图片链接
- 图片格式需为PNG、JPG或JPEG

## 调试建议

如果遇到图片未显示的问题，请检查：

1. 日志中的`[ShowGirl] API响应URL`是否能在浏览器中正常打开
2. URL是否使用HTTPS协议（非HTTPS链接会被拒绝）
3. 图片格式是否为PNG、JPG或JPEG
4. 微信服务器能否访问该URL（公网可访问）

## 日志

错误日志保存在 `logs/showgirl_error.log` 文件中。 