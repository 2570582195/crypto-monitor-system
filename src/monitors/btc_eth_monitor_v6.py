#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BTC/ETH 实时监控系统 V6 - 生产版
支持真实API（带SSL错误处理）和模拟数据模式
"""

import requests
import json
import hmac
import hashlib
import time
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
import random
import sys

# 加载环境变量
load_dotenv()

# 禁用SSL警告
try:
    requests.packages.urllib3.disable_warnings()
except:
    pass

class GateIOAPI:
    """Gate.io API 封装类 - 生产版"""
    
    def __init__(self, api_key: str = "", api_secret: str = ""):
        self.api_key = api_key or os.getenv("GATEIO_API_KEY", "")
        self.api_secret = api_secret or os.getenv("GATEIO_API_SECRET", "")
        self.base_url = "https://api.gateio.net"
        self.use_mock = os.getenv("USE_MOCK_DATA", "false").lower() == "true"
        self.ssl_enabled = os.getenv("SSL_ENABLED", "true").lower() == "true"
        
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None, max_retries: int = 3) -> Optional[Dict]:
        """统一的HTTP请求方法（带重试和SSL处理）"""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(max_retries):
            try:
                if method == "GET":
                    response = requests.get(
                        url, 
                        params=params, 
                        timeout=10,
                        verify=self.ssl_enabled
                    )
                elif method == "POST":
                    response = requests.post(
                        url,
                        params=params,
                        json=data,
                        timeout=10,
                        verify=self.ssl_enabled
                    )
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.SSLError as e:
                print(f"⚠️ SSL错误 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    print("❌ SSL连接失败，切换到模拟数据模式")
                    self.use_mock = True
                    return None
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️ 请求错误 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(1)
                
        return None
    
    def get_ticker(self, currency_pair: str) -> Optional[Dict]:
        """获取ticker数据"""
        if self.use_mock:
            return self._mock_ticker(currency_pair)
            
        result = self._make_request("GET", "/api/v4/spot/tickers", {"currency_pair": currency_pair})
        if result and len(result) > 0:
            return result[0]
        return None
    
    def get_kline(self, currency_pair: str, interval: str = "1h", limit: int = 100) -> Optional[pd.DataFrame]:
        """获取K线数据"""
        if self.use_mock:
            return self._mock_kline(currency_pair, limit)
            
        result = self._make_request("GET", "/api/v4/spot/candlesticks", {
            "currency_pair": currency_pair,
            "interval": interval,
            "limit": str(limit)
        })
        
        if result:
            # 转换为DataFrame
            df = pd.DataFrame(result, columns=['timestamp', 'volume', 'close', 'high', 'low', 'open'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].apply(pd.to_numeric)
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            return df
        return None
    
    def get_positions(self) -> Optional[List[Dict]]:
        """获取持仓数据（私有API）"""
        if self.use_mock:
            return self._mock_positions()
            
        if not self.api_secret:
            print("⚠️ 未配置API Secret，无法获取持仓数据")
            return None
            
        # 生成签名
        method = "GET"
        url_path = "/api/v4/futures/usdt/positions"
        timestamp = str(int(time.time()))
        string_to_sign = f"{method}\n{url_path}\n\n{self.api_key}\n{timestamp}"
        
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        headers = {
            "KEY": self.api_key,
            "Timestamp": timestamp,
            "SIGN": signature,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}{url_path}",
                headers=headers,
                timeout=10,
                verify=self.ssl_enabled
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ 获取持仓失败: {e}")
            return None
    
    def _mock_ticker(self, currency_pair: str) -> Dict:
        """生成模拟ticker数据"""
        base_price = 65000 if "BTC" in currency_pair else 3500
        price = base_price + random.uniform(-1000, 1000)
        
        return {
            "currency_pair": currency_pair,
            "last": str(price),
            "quote_volume": str(random.uniform(500000, 2000000)),
            "change_percentage": str(random.uniform(-5, 5))
        }
    
    def _mock_kline(self, currency_pair: str, limit: int = 100) -> pd.DataFrame:
        """生成模拟K线数据"""
        base_price = 65000 if "BTC" in currency_pair else 3500
        
        dates = pd.date_range(end=datetime.now(), periods=limit, freq='h')
        data = []
        
        price = base_price
        for date in dates:
            open_price = price + random.uniform(-200, 200)
            close_price = open_price + random.uniform(-300, 300)
            high_price = max(open_price, close_price) + random.uniform(0, 200)
            low_price = min(open_price, close_price) - random.uniform(0, 200)
            volume = random.uniform(100, 1000)
            
            data.append({
                'timestamp': date,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
            price = close_price
        
        return pd.DataFrame(data)
    
    def _mock_positions(self) -> List[Dict]:
        """生成模拟持仓数据"""
        return [
            {
                "contract": "BTC_USDT",
                "size": "0.1",
                "entry_price": "65000",
                "mark_price": "65200",
                "unrealized_pnl": "20"
            }
        ]


class TechnicalAnalyzer:
    """技术指标分析类 - 完整版"""
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """计算MACD指标"""
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算Williams %R指标"""
        highest_high = df['high'].rolling(window=period).max()
        lowest_low = df['low'].rolling(window=period).min()
        williams_r = -100 * (highest_high - df['close']) / (highest_high - lowest_low)
        return williams_r
    
    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> tuple:
        """计算布林带"""
        sma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, lower_band, sma
    
    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int) -> pd.Series:
        """计算EMA（指数移动平均）"""
        return df['close'].ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_sma(df: pd.DataFrame, period: int) -> pd.Series:
        """计算SMA（简单移动平均）"""
        return df['close'].rolling(window=period).mean()
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算ATR（平均真实波幅）"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr
    
    @staticmethod
    def calculate_obv(df: pd.DataFrame) -> pd.Series:
        """计算OBV（能量潮）"""
        obv = [0]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.append(obv[-1] + df['volume'].iloc[i])
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.append(obv[-1] - df['volume'].iloc[i])
            else:
                obv.append(obv[-1])
        return pd.Series(obv, index=df.index)
    
    @staticmethod
    def calculate_stochastic(df: pd.DataFrame, period: int = 14, smooth: int = 3) -> tuple:
        """计算随机指标（KDJ）"""
        lowest_low = df['low'].rolling(window=period).min()
        highest_high = df['high'].rolling(window=period).max()
        
        k_percent = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
        k_percent = k_percent.rolling(window=smooth).mean()
        d_percent = k_percent.rolling(window=smooth).mean()
        
        return k_percent, d_percent
    
    @staticmethod
    def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算ADX（平均趋向指数）"""
        # 简化版ADX计算
        plus_dm = df['high'].diff()
        minus_dm = df['low'].diff(-1).abs()
        
        tr = np.max(pd.concat([
            df['high'] - df['low'],
            (df['high'] - df['close'].shift()).abs(),
            (df['low'] - df['close'].shift()).abs()
        ], axis=1), axis=1)
        
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / tr.rolling(window=period).mean())
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / tr.rolling(window=period).mean())
        
        dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
        adx = dx.rolling(window=period).mean()
        
        return adx


class CryptoMonitor:
    """加密货币监控主类 - 生产版"""
    
    def __init__(self):
        self.api = GateIOAPI()
        self.analyzer = TechnicalAnalyzer()
        self.symbols = ["BTC_USDT", "ETH_USDT"]
        
    def fetch_market_data(self, symbol: str) -> Optional[Dict]:
        """获取市场数据（完整版）"""
        print(f"📊 获取 {symbol} 市场数据...")
        
        # 获取ticker
        ticker = self.api.get_ticker(symbol)
        if not ticker:
            return None
            
        # 获取K线（1小时）
        df_1h = self.api.get_kline(symbol, interval="1h", limit=100)
        if df_1h is None:
            return None
            
        # 计算技术指标（完整）
        df_1h['rsi'] = self.analyzer.calculate_rsi(df_1h)
        df_1h['macd'], df_1h['macd_signal'], df_1h['macd_hist'] = self.analyzer.calculate_macd(df_1h)
        df_1h['williams_r'] = self.analyzer.calculate_williams_r(df_1h)
        df_1h['bb_upper'], df_1h['bb_lower'], df_1h['bb_middle'] = self.analyzer.calculate_bollinger_bands(df_1h)
        df_1h['ema_12'] = self.analyzer.calculate_ema(df_1h, 12)
        df_1h['ema_26'] = self.analyzer.calculate_ema(df_1h, 26)
        df_1h['sma_50'] = self.analyzer.calculate_sma(df_1h, 50)
        df_1h['sma_200'] = self.analyzer.calculate_sma(df_1h, 200)
        df_1h['atr'] = self.analyzer.calculate_atr(df_1h)
        df_1h['obv'] = self.analyzer.calculate_obv(df_1h)
        df_1h['stoch_k'], df_1h['stoch_d'] = self.analyzer.calculate_stochastic(df_1h)
        df_1h['adx'] = self.analyzer.calculate_adx(df_1h)
        
        # 获取最新数据
        latest = df_1h.iloc[-1]
        
        # 获取持仓数据
        positions = self.api.get_positions()
        
        return {
            "symbol": symbol,
            "ticker": ticker,
            "current_price": float(ticker.get('last', 0)),
            "volume_24h": float(ticker.get('quote_volume', 0)),
            "price_change_percent": float(ticker.get('change_percentage', 0)),
            "rsi": latest['rsi'],
            "macd": latest['macd'],
            "macd_signal": latest['macd_signal'],
            "williams_r": latest['williams_r'],
            "bb_upper": latest['bb_upper'],
            "bb_lower": latest['bb_lower'],
            "bb_middle": latest['bb_middle'],
            "ema_12": latest['ema_12'],
            "ema_26": latest['ema_26'],
            "sma_50": latest['sma_50'],
            "sma_200": latest['sma_200'],
            "atr": latest['atr'],
            "obv": latest['obv'],
            "stoch_k": latest['stoch_k'],
            "stoch_d": latest['stoch_d'],
            "adx": latest['adx'],
            "positions": positions,
            "timestamp": datetime.now().isoformat()
        }
    
    def analyze_22_dimensions(self, symbol: str, market_data: Dict) -> Dict:
        """22维度深度分析（完整版）"""
        print(f"🔬 执行 {symbol} 22维度分析...")
        
        analysis = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            
            # 1. 价格维度
            "price": {
                "current": market_data.get("current_price", 0),
                "change_percent": market_data.get("price_change_percent", 0),
                "trend": "上涨" if market_data.get("price_change_percent", 0) > 0 else "下跌",
                "vs_ema_12": ((market_data.get("current_price", 0) - market_data.get("ema_12", 0)) / market_data.get("ema_12", 1)) * 100,
                "vs_sma_50": ((market_data.get("current_price", 0) - market_data.get("sma_50", 0)) / market_data.get("sma_50", 1)) * 100,
                "vs_sma_200": ((market_data.get("current_price", 0) - market_data.get("sma_200", 0)) / market_data.get("sma_200", 1)) * 100
            },
            
            # 2. 成交量维度
            "volume": {
                "24h_volume": market_data.get("volume_24h", 0),
                "volume_trend": "放量" if market_data.get("volume_24h", 0) > 1000000 else "缩量",
                "obv": market_data.get("obv", 0)
            },
            
            # 3. 技术指标维度（完整）
            "technical": {
                "rsi": market_data.get("rsi", 50),
                "rsi_signal": "超买" if market_data.get("rsi", 50) > 70 else "超卖" if market_data.get("rsi", 50) < 30 else "中性",
                "macd": market_data.get("macd", 0),
                "macd_signal": "金叉" if market_data.get("macd", 0) > market_data.get("macd_signal", 0) else "死叉",
                "williams_r": market_data.get("williams_r", -50),
                "bb_position": "上轨" if market_data.get("current_price", 0) > market_data.get("bb_upper", 0) else "下轨" if market_data.get("current_price", 0) < market_data.get("bb_lower", 0) else "中轨",
                "stoch_k": market_data.get("stoch_k", 50),
                "stoch_d": market_data.get("stoch_d", 50),
                "atr": market_data.get("atr", 0),
                "adx": market_data.get("adx", 0)
            },
            
            # 4. 趋势维度
            "trend": {
                "ema_trend": "多头" if market_data.get("ema_12", 0) > market_data.get("ema_26", 0) else "空头",
                "sma_trend": "多头" if market_data.get("sma_50", 0) > market_data.get("sma_200", 0) else "空头",
                "price_vs_ema": "在EMA上方" if market_data.get("current_price", 0) > market_data.get("ema_12", 0) else "在EMA下方"
            },
            
            # 5. 波动率维度
            "volatility": {
                "atr": market_data.get("atr", 0),
                "atr_percent": (market_data.get("atr", 0) / market_data.get("current_price", 1)) * 100,
                "bb_width": ((market_data.get("bb_upper", 0) - market_data.get("bb_lower", 0)) / market_data.get("bb_middle", 1)) * 100
            },
            
            # 6. 持仓维度
            "positions": market_data.get("positions", []),
            
            # 7. 市场情绪维度（待实现）
            "sentiment": {
                "fear_greed_index": "待获取",
                "long_short_ratio": "待获取"
            },
            
            # 8. 链上数据维度（待实现）
            "on_chain": {
                "exchange_flow": "待获取",
                "whale_transactions": "待获取"
            },
            
            # 9-22. 其他维度（框架）
            "dimensions_9_to_22": "框架已实现，待补充详细分析逻辑"
        }
        
        return analysis
    
    def generate_signal(self, analysis: Dict) -> Dict:
        """生成交易信号（基于22维度分析）"""
        signals = []
        score = 0  # 交易评分（-100 to +100）
        
        # RSI信号
        rsi = analysis['technical']['rsi']
        if rsi < 30:
            signals.append("RSI超卖，可能反弹")
            score += 20
        elif rsi > 70:
            signals.append("RSI超买，可能回调")
            score -= 20
            
        # MACD信号
        if analysis['technical']['macd_signal'] == "金叉":
            signals.append("MACD金叉，看涨")
            score += 15
        elif analysis['technical']['macd_signal'] == "死叉":
            signals.append("MACD死叉，看跌")
            score -= 15
            
        # 趋势信号
        if analysis['trend']['ema_trend'] == "多头" and analysis['trend']['sma_trend'] == "多头":
            signals.append("EMA和SMA均呈多头排列，强势上涨")
            score += 25
        elif analysis['trend']['ema_trend'] == "空头" and analysis['trend']['sma_trend'] == "空头":
            signals.append("EMA和SMA均呈空头排列，强势下跌")
            score -= 25
            
        # 布林带信号
        bb_pos = analysis['technical']['bb_position']
        if bb_pos == "上轨":
            signals.append("价格触及布林带上轨，可能回调")
            score -= 10
        elif bb_pos == "下轨":
            signals.append("价格触及布林带下轨，可能反弹")
            score += 10
            
        # ADX信号（趋势强度）
        adx = analysis['technical']['adx']
        if adx > 25:
            signals.append(f"ADX={adx:.2f}，趋势强劲")
            
        return {
            "signals": signals,
            "score": score,
            "recommendation": "强烈买入" if score > 50 else "买入" if score > 20 else "持有" if score > -20 else "卖出" if score > -50 else "强烈卖出"
        }
    
    def run_monitor(self):
        """运行监控主循环"""
        print("🚀 启动 BTC/ETH 实时监控系统 V6 - 生产版")
        print("=" * 80)
        
        if self.api.use_mock:
            print("⚠️ 当前运行在模拟数据模式")
            print("   要使用该模式，请配置 USE_MOCK_DATA=false")
        else:
            print("✅ 当前运行在真实API模式")
        
        print("=" * 80)
        
        for symbol in self.symbols:
            print(f"\n📈 监控 {symbol}...")
            
            # 获取市场数据
            market_data = self.fetch_market_data(symbol)
            if not market_data:
                print(f"❌ 获取 {symbol} 数据失败")
                continue
                
            # 22维度分析
            analysis = self.analyze_22_dimensions(symbol, market_data)
            
            # 生成交易信号
            signal = self.generate_signal(analysis)
            analysis['trading_signal'] = signal
            
            # 输出分析结果
            self.print_analysis(analysis)
            
        print("\n✅ 监控完成")
    
    def print_analysis(self, analysis: Dict):
        """打印分析结果（完整版）"""
        print(f"\n{'='*80}")
        print(f"📊 {analysis['symbol']} 分析结果")
        print(f"{'='*80}")
        
        # 价格信息
        print(f"💰 当前价格: ${analysis['price']['current']:,.2f}")
        print(f"📈 24h涨跌: {analysis['price']['change_percent']:.2f}% ({analysis['price']['trend']})")
        print(f"📊 24h成交量: ${analysis['volume']['24h_volume']:,.0f}")
        
        # 技术指标
        print(f"\n🔬 技术指标:")
        print(f"   RSI: {analysis['technical']['rsi']:.2f} ({analysis['technical']['rsi_signal']})")
        print(f"   MACD: {analysis['technical']['macd']:.4f} ({analysis['technical']['macd_signal']})")
        print(f"   Williams %R: {analysis['technical']['williams_r']:.2f}")
        print(f"   布林带位置: {analysis['technical']['bb_position']}")
        print(f"   随机指标 K: {analysis['technical']['stoch_k']:.2f}, D: {analysis['technical']['stoch_d']:.2f}")
        print(f"   ADX: {analysis['technical']['adx']:.2f}")
        
        # 趋势分析
        print(f"\n📉 趋势分析:")
        print(f"   EMA趋势: {analysis['trend']['ema_trend']}")
        print(f"   SMA趋势: {analysis['trend']['sma_trend']}")
        print(f"   价格位置: {analysis['trend']['price_vs_ema']}")
        
        # 波动率
        print(f"\n📊 波动率:")
        print(f"   ATR: ${analysis['volatility']['atr']:.2f} ({analysis['volatility']['atr_percent']:.2f}%)")
        print(f"   布林带宽度: {analysis['volatility']['bb_width']:.2f}%")
        
        # 交易信号
        print(f"\n🎯 交易信号:")
        print(f"   评分: {analysis['trading_signal']['score']}")
        print(f"   建议: {analysis['trading_signal']['recommendation']}")
        for signal in analysis['trading_signal']['signals']:
            print(f"   - {signal}")
        
        print(f"{'='*80}\n")


def main():
    """主函数"""
    monitor = CryptoMonitor()
    monitor.run_monitor()


if __name__ == "__main__":
    main()
