#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进程守护脚本 - guardian.py

功能：
- 监控主进程状态
- 自动重启异常进程
- 日志记录
- 健康检查

作者：创薪前沿&淞哥
版本：v1.0
日期：2026-06-29
"""

import os
import sys
import time
import json
import logging
import subprocess
import signal
import psutil
from datetime import datetime
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/guardian.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ProcessGuardian:
    """进程守护器"""
    
    def __init__(self, config_path: str = 'config/guardian.json'):
        """
        初始化守护器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.monitored_processes = self.config.get('processes', [])
        self.check_interval = self.config.get('check_interval', 60)
        self.restart_delay = self.config.get('restart_delay', 5)
        self.max_restart_attempts = self.config.get('max_restart_attempts', 3)
        
        logger.info("进程守护器初始化完成")
        logger.info(f"监控进程数: {len(self.monitored_processes)}")
        logger.info(f"检查间隔: {self.check_interval}秒")
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        default_config = {
            'processes': [
                {
                    'name': 'btc_eth_monitor_v5',
                    'script': 'src/monitors/btc_eth_monitor_v5.py',
                    'restart_on_crash': True,
                    'max_restart_attempts': 3
                }
            ],
            'check_interval': 60,
            'restart_delay': 5,
            'max_restart_attempts': 3
        }
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"✅ 配置文件加载成功: {config_path}")
                return config
        except FileNotFoundError:
            logger.warning(f"⚠️ 配置文件未找到: {config_path}，创建默认配置")
            self._save_config(config_path, default_config)
            return default_config
        except Exception as e:
            logger.error(f"❌ 加载配置文件失败: {e}，使用默认配置")
            return default_config
    
    def _save_config(self, config_path: str, config: Dict):
        """保存配置文件"""
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 配置文件保存成功: {config_path}")
        except Exception as e:
            logger.error(f"❌ 保存配置文件失败: {e}")
    
    def is_process_running(self, process_name: str) -> bool:
        """
        检查进程是否在运行
        
        Args:
            process_name: 进程名称
            
        Returns:
            bool: 是否运行中
        """
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and process_name in ' '.join(cmdline):
                        logger.debug(f"进程 {process_name} 正在运行 (PID: {proc.info['pid']})")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            logger.warning(f"⚠️ 进程 {process_name} 未运行")
            return False
            
        except Exception as e:
            logger.error(f"❌ 检查进程 {process_name} 状态失败: {e}")
            return False
    
    def start_process(self, process_config: Dict) -> Optional[subprocess.Popen]:
        """
        启动进程
        
        Args:
            process_config: 进程配置
            
        Returns:
            Optional[subprocess.Popen]: 进程对象
        """
        try:
            script_path = process_config.get('script', '')
            process_name = process_config.get('name', '')
            
            if not os.path.exists(script_path):
                logger.error(f"❌ 脚本文件不存在: {script_path}")
                return None
            
            logger.info(f"🚀 启动进程: {process_name}")
            logger.info(f"   脚本: {script_path}")
            
            # 启动进程
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            logger.info(f"✅ 进程 {process_name} 启动成功 (PID: {process.pid})")
            return process
            
        except Exception as e:
            logger.error(f"❌ 启动进程 {process_name} 失败: {e}")
            return None
    
    def stop_process(self, pid: int):
        """
        停止进程
        
        Args:
            pid: 进程ID
        """
        try:
            logger.info(f"🛑 停止进程 (PID: {pid})...")
            os.kill(pid, signal.SIGTERM)
            logger.info(f"✅ 进程 (PID: {pid}) 已停止")
        except Exception as e:
            logger.error(f"❌ 停止进程 (PID: {pid}) 失败: {e}")
    
    def restart_process(self, process_config: Dict) -> Optional[subprocess.Popen]:
        """
        重启进程
        
        Args:
            process_config: 进程配置
            
        Returns:
            Optional[subprocess.Popen]: 新的进程对象
        """
        process_name = process_config.get('name', '')
        
        logger.info(f"🔄 重启进程: {process_name}")
        
        # 等待重启延迟
        time.sleep(self.restart_delay)
        
        # 启动新进程
        return self.start_process(process_config)
    
    def check_and_restart(self, process_config: Dict, restart_counts: Dict) -> Dict:
        """
        检查并重启进程
        
        Args:
            process_config: 进程配置
            restart_counts: 重启计数
            
        Returns:
            Dict: 更新后的重启计数
        """
        process_name = process_config.get('name', '')
        script_path = process_config.get('script', '')
        
        # 检查进程是否在运行
        if not self.is_process_running(process_name):
            logger.warning(f"⚠️ 检测到进程 {process_name} 未运行")
            
            # 检查是否需要重启
            if not process_config.get('restart_on_crash', True):
                logger.info(f"ℹ️ 进程 {process_name} 配置为不自动重启")
                return restart_counts
            
            # 检查重启次数
            if process_name not in restart_counts:
                restart_counts[process_name] = 0
            
            if restart_counts[process_name] >= self.max_restart_attempts:
                logger.error(f"❌ 进程 {process_name} 重启次数达到上限 ({self.max_restart_attempts})")
                return restart_counts
            
            # 重启进程
            restart_counts[process_name] += 1
            logger.info(f"🔄 重启进程 {process_name} (第 {restart_counts[process_name]} 次)")
            
            process = self.restart_process(process_config)
            if process:
                logger.info(f"✅ 进程 {process_name} 重启成功")
            else:
                logger.error(f"❌ 进程 {process_name} 重启失败")
        else:
            # 进程正常运行，重置重启计数
            if process_name in restart_counts:
                logger.info(f"✨ 进程 {process_name} 恢复正常，重置重启计数")
                restart_counts[process_name] = 0
        
        return restart_counts
    
    def run(self):
        """运行守护器（主循环）"""
        logger.info("🛡️ 进程守护器启动...")
        
        restart_counts = {}  # 重启计数
        
        try:
            while True:
                logger.debug(f"🔍 开始第 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 次检查...")
                
                # 检查所有监控的进程
                for process_config in self.monitored_processes:
                    restart_counts = self.check_and_restart(process_config, restart_counts)
                
                # 等待下次检查
                logger.debug(f"😴 等待 {self.check_interval} 秒后进行下次检查...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("⏹️ 进程守护器手动停止")
        except Exception as e:
            logger.error(f"❌ 进程守护器运行异常: {e}")
            raise


def main():
    """主函数"""
    # 创建必要的目录
    os.makedirs('logs', exist_ok=True)
    os.makedirs('config', exist_ok=True)
    os.makedirs('src/utils', exist_ok=True)
    
    # 启动守护器
    guardian = ProcessGuardian()
    guardian.run()


if __name__ == '__main__':
    main()
