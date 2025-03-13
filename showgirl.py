# encoding:utf-8

import json
import os
import re
import time
import requests
import logging
from datetime import datetime
from typing import Dict, List

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from plugins import *


# 创建日志目录
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 配置日志记录器
error_logger = logging.getLogger("showgirl_error")
error_logger.setLevel(logging.ERROR)
handler = logging.FileHandler(os.path.join(log_dir, "showgirl_error.log"))
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
error_logger.addHandler(handler)


@plugins.register(
    name="ShowGirl",
    desire_priority=5,  # 中等优先级
    hidden=False,
    desc="获取美女图片，通过关键词或语义触发",
    version="1.0",
    author="dify-on-wechat",
)
class ShowGirlPlugin(Plugin):
    def __init__(self):
        super().__init__()
        try:
            # 加载配置
            conf = super().load_config()
            curdir = os.path.dirname(__file__)
            if not conf:
                # 配置不存在则写入默认配置
                config_path = os.path.join(curdir, "config.json")
                if not os.path.exists(config_path):
                    conf = {
                        "api_url": "https://api.317ak.com/API/tp/mntp.php",
                        "timeout": 10,
                        "frequency_limit": 5,  # 同一用户调用间隔时间(秒)
                        "enable_nlu": True,      # 是否启用语义理解触发
                        "enable_image": True      # 是否启用图片发送
                    }
                    with open(config_path, "w", encoding="utf-8") as f:
                        json.dump(conf, f, indent=4, ensure_ascii=False)
            
            # 保存配置
            self.api_url = conf.get("api_url", "https://api.317ak.com/API/tp/mntp.php")
            self.timeout = conf.get("timeout", 10)
            self.frequency_limit = conf.get("frequency_limit", 5)
            self.enable_nlu = conf.get("enable_nlu", True)
            
            # 用户使用记录，用于频率限制
            self.user_records: Dict[str, float] = {}
            
            # 注册消息处理器
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
            logger.info("[ShowGirl] 插件初始化完成")
        except Exception as e:
            logger.warn(f"[ShowGirl] 初始化失败: {e}")
            error_logger.error(f"插件初始化失败: {e}")
            raise e

    def on_handle_context(self, e_context: EventContext):
        """处理接收到的消息"""
        if e_context["context"].type != ContextType.TEXT:
            return
        
        content = e_context["context"].content
        logger.debug(f"[ShowGirl] 收到消息: {content}")
        
        # 获取用户ID，用于频率限制
        user_id = e_context['context'].get('session_id', 'default_user')
        
        # 检查是否触发插件
        if self._should_trigger(content):
            # 检查频率限制
            current_time = time.time()
            if user_id in self.user_records:
                last_time = self.user_records[user_id]
                time_diff = current_time - last_time
                if time_diff < self.frequency_limit:
                    # 触发频率限制
                    remaining_time = int(self.frequency_limit - time_diff)
                    reply = Reply(ReplyType.TEXT, f"您的请求过于频繁，请{remaining_time}秒后再试~")
                    e_context["reply"] = reply
                    e_context.action = EventAction.BREAK_PASS
                    return
            
            # 更新用户使用记录
            self.user_records[user_id] = current_time
            
            # 调用API获取图片
            try:
                # 请求图片API
                response = requests.get(self.api_url, timeout=self.timeout, verify=True)
                
                # 检查API响应是否成功
                if response.status_code == 200:
                    # 检查API返回的URL是否安全
                    image_url = response.url
                    logger.debug(f"[ShowGirl] API响应URL: {image_url}")
                    
                    # 验证URL格式
                    if not image_url.startswith('https://'):
                        logger.warning(f"[ShowGirl] 非HTTPS图片URL，已拒绝: {image_url}")
                        error_logger.error(f"非HTTPS图片URL，已拒绝: {image_url}")
                        reply = Reply(ReplyType.TEXT, "图片源不安全，已拦截")
                    # 验证图片格式是否为PNG
                    elif not image_url.lower().endswith('.png') and not image_url.lower().endswith('.jpg') and not image_url.lower().endswith('.jpeg'):
                        logger.warning(f"[ShowGirl] 不支持的图片格式: {image_url}")
                        error_logger.error(f"不支持的图片格式: {image_url}")
                        reply = Reply(ReplyType.TEXT, "获取的图片格式不支持，请稍后再试")
                    else:
                        # 直接返回图片URL，不要包装成字典
                        reply = Reply(ReplyType.IMAGE_URL, image_url)
                        logger.info(f"[ShowGirl] 成功获取并返回图片: {image_url}")
                else:
                    logger.error(f"[ShowGirl] API异常状态码: {response.status_code}")
                    error_logger.error(f"API异常状态码: {response.status_code}")
                    reply = Reply(ReplyType.TEXT, "哎呀，图库暂时打不开~")
            except requests.exceptions.SSLError as e:
                logger.error(f"[ShowGirl] SSL证书验证失败: {e}")
                error_logger.error(f"SSL证书验证失败: {e}")
                reply = Reply(ReplyType.TEXT, "安全连接异常，请联系管理员")
            except requests.exceptions.Timeout as e:
                logger.error(f"[ShowGirl] 请求超时: {e}")
                error_logger.error(f"请求超时: {e}")
                reply = Reply(ReplyType.TEXT, "图片服务器响应超时，请稍后再试")
            except requests.exceptions.ConnectionError as e:
                logger.error(f"[ShowGirl] 连接错误: {e}")
                error_logger.error(f"连接错误: {e}")
                reply = Reply(ReplyType.TEXT, "无法连接到图片服务器，请检查网络")
            except Exception as e:
                logger.error(f"[ShowGirl] 未预期的异常: {e}")
                error_logger.error(f"未预期的异常: {str(e)}")
                reply = Reply(ReplyType.TEXT, "获取图片时发生未知错误")
            
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            return

    def _should_trigger(self, content):
        """判断是否应该触发插件"""
        # 关键词匹配
        if re.search(r'美女|妹子', content):
            logger.info("[ShowGirl] 关键词触发")
            return True
        
        # 通过NLU识别用户意图（如果启用）
        if self.enable_nlu and self._check_image_intent(content):
            logger.info("[ShowGirl] 语义触发")
            return True
        
        return False
    
    def _check_image_intent(self, content):
        """检查是否包含请求图片的意图"""
        # 简单的意图识别，实际生产中可以接入更复杂的NLU服务
        image_patterns = [
            r'发[张个]\s*[好漂美][看丽]',
            r'[来发]一?[张个]\s*[图照片]',
            r'[想要].*[图照片]'
        ]
        
        for pattern in image_patterns:
            if re.search(pattern, content):
                return True
        
        return False
    
    def get_help_text(self, **kwargs):
        return "发送包含\"美女\"或\"妹子\"的消息，获取美女图片。" 