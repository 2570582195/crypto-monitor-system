# BTC/ETH 加密货币监控系统

**项目描述**: 自动化加密货币监控系统，实时追踪BTC和ETH价格变动，提供22维度深度分析，并通过企微自动推送通知。

**当前版本**: v5.0  
**最后更新**: 2026-06-29

---

## 📋 项目特性

### 核心功能
- ✅ 实时监控 BTC/ETH 价格变动
- ✅ 22维度深度市场分析
- ✅ 自动推送通知（企微Webhook）
- ✅ 技术指标计算（RSI、MACD、Williams %R等）
- ✅ 链上数据分析
- ✅ 多空比、资金费率监控
- ✅ 智能交易建议（TP/SL）

### 技术特性
- 🔄 多数据源混合配置（Gate.io + TradingView + CoinGlass）
- 🛡️ 进程守护机制（guardian.py）
- 📱 移动端优化推送格式
- ⚡ 并行数据获取（加速K线获取 ~30s → ~10s）
- 🔁 自动重启机制

---

## 🏗️ 项目架构

```
crypto-monitor-system/
├── src/
│   ├── monitors/          # 监控脚本
│   │   ├── btc_eth_monitor_v5.py
│   │   ├── gate_listener.py
│   │   └── telegram_listener_v5.py
│   ├── analyzers/         # 分析脚本
│   │   ├── pro_analyzer_v5.py
│   │   └── dual_source_collector.py
│   ├── pushers/          # 推送脚本
│   │   ├── push_ultimate_v3.py
│   │   └── push_all.py
│   └── utils/            # 工具脚本
│       ├── guardian.py
│       ├── service_monitor.py
│       └── gate_final.py
├── config/               # 配置文件
├── docs/                 # 文档
│   └── 项目开发工作记录_完整重建_v1.0.md
├── logs/                 # 日志文件
├── .gitignore
├── README.md
└── LICENSE
```

---

## 🚀 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/2570582195/crypto-monitor-system.git
cd crypto-monitor-system
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置API密钥
创建 `config/api_keys.json`:
```json
{
  "gateio_api_key": "你的API密钥",
  "gateio_api_secret": "你的API密钥",
  "wecom_webhook_url": "你的企微Webhook URL"
}
```

### 4. 运行监控系统
```bash
python src/monitors/btc_eth_monitor_v5.py
```

---

## 📊 功能模块

### 1. 监控系统 (`src/monitors/`)
- **btc_eth_monitor_v5.py**: 主监控脚本，实时追踪BTC/ETH价格
- **gate_listener.py**: 监听Gate平台帖子（竞对监控）
- **telegram_listener_v5.py**: 监听Telegram频道/群组

### 2. 分析系统 (`src/analyzers/`)
- **pro_analyzer_v5.py**: 专业行情分析，TP/SL建议
- **dual_source_collector.py**: 双源数据采集（截图+API）

### 3. 推送系统 (`src/pushers/`)
- **push_ultimate_v3.py**: 终极推送脚本，22维度分析
- **push_all.py**: 自动化报告推送

### 4. 工具脚本 (`src/utils/`)
- **guardian.py**: 进程守护脚本
- **service_monitor.py**: 服务监控
- **gate_final.py**: Dashboard仪表盘

---

## 🔧 配置说明

### API集成
1. **Gate.io API**: 行情、K线、持仓数据
2. **TradingView**: 技术指标（通过WebFetch）
3. **CoinGlass**: 爆仓、资金费率（通过WebFetch）
4. **企微Webhook**: 消息推送

### 用户设置
- **交易所**: Weex、Gate.io
- **账户资金**: ~$500/交易所
- **交易品种**: BTC、ETH
- **杠杆倍数**: 200x
- **目标日盈利**: $200

---

## 📝 开发记录

详细的项目开发记录请查看：
- 📄 [项目开发工作记录_完整重建_v1.0.md](docs/项目开发工作记录_完整重建_v1.0.md)

**注意**: 本文档基于系统重装后的对话历史重建，部分代码细节可能不完整。

---

## 🔄 版本控制策略

### 分支管理
- `main`: 生产稳定版本
- `dev`: 开发分支
- `feature/*`: 功能分支
- `hotfix/*`: 紧急修复分支

### Commit规范
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type类型**:
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**:
```
feat(monitor): 添加ETH大额委托数据监控

- 集成CoinGlass API获取ETH大额委托
- 优化推送格式，防止企微截断
- 更新22维度分析框架

Closes #123
```

---

## 🤖 自动备份策略

### 自动提交配置
本项目配置了自动化备份机制：

1. **Git Hooks**: 使用pre-commit hook自动检查
2. **WorkBuddy自动化任务**: 定时自动提交和推送
3. **多重备份**: 同时备份至GitHub和Gitee

### 备份频率
- **代码变更**: 每次提交后自动推送
- **文档更新**: 每天定时备份
- **配置文件**: 手动备份（防止敏感信息泄露）

---

## 🛡️ 安全注意事项

### ⚠️ 重要提醒
1. **Never commit API密钥**: 使用 `.gitignore` 排除配置文件
2. **使用环境变量**: 敏感信息存储在 `.env` 文件中
3. **定期检查日志**: 防止敏感信息泄露到日志中
4. **使用仓库保护**: 配置分支保护规则，防止意外删除

### 安全清单
- [ ] API密钥已添加到 `.gitignore`
- [ ] `.env` 文件已创建并配置
- [ ] 仓库已设置为私有（如需要）
- [ ] 分支保护规则已配置

---

## 📈 开发路线图

### ✅ 已完成
- [x] BTC/ETH实时监控系统 v5
- [x] 22维度深度分析
- [x] 企微自动推送
- [x] Gate监听器系统
- [x] Telegram监听器系统
- [x] 进程守护机制

### 🔄 进行中
- [ ] 实现沙箱外运行方案
- [ ] 完善ETH大额委托数据
- [ ] 修复Playwright崩溃问题

### 📅 计划中
- [ ] Web Dashboard界面
- [ ] 移动端App
- [ ] 多交易所支持（Binance、OKX等）
- [ ] 机器学习预测模型

---

## 🐛 已知问题

1. **监控进程依赖沙箱运行**
   - 症状：会话重置会中断监控
   - 解决方案：实现沙箱外执行方案（进行中）

2. **Playwright CDP断开问题**
   - 症状：Playwright崩溃导致采集中断
   - 解决方案：深度修复CDP连接逻辑

3. **僵尸进程误判重启**
   - 症状：进程仍在运行但被误判为僵尸进程
   - 解决方案：优化进程状态检测逻辑

---

## 📞 联系方式

- **Issues**: 使用GitHub Issues报告问题
- **Pull Requests**: 欢迎提交PR贡献代码
- **讨论**: 使用GitHub Discussions进行讨论

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

感谢所有为这个项目贡献代码和想法的人。

---

**最后更新**: 2026-06-29  
**维护者**: 创薪前沿&淞哥
