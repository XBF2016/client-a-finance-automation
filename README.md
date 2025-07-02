# 多平台订单自动合并工具

## 项目介绍
多平台订单自动合并工具是一个RPA（机器人流程自动化）演示项目，旨在展示如何自动化从多个电商平台获取订单数据，合并处理并导出为统一格式的Excel文件。该工具可以大幅提高订单处理效率，减少人工操作错误。

## 核心特性
- **多平台支持**：目前支持淘宝和京东两个主流电商平台，架构设计支持轻松扩展到更多平台
- **自动登录**：支持自动登录各平台，并可处理常见的登录验证流程
- **智能数据获取**：自动导航到订单页面，获取订单列表及订单详情
- **数据标准化**：将不同平台的订单数据字段统一映射为标准格式
- **格式化导出**：将合并后的订单数据导出为美观的Excel表格
- **健壮性设计**：完善的异常处理和重试机制，确保流程稳定运行
- **智能选择器系统**：具备自动生成和管理UI元素选择器的能力，提高程序健壮性

## 技术栈
- Python 3.8+
- Playwright (用于Web自动化操作)
- Pandas (用于数据处理和Excel导出)
- YAML (用于配置管理)
- 正则表达式 (用于文本解析)

## 系统要求
- Python 3.8 或更高版本
- 支持的操作系统：Windows, macOS, Linux
- 稳定的网络连接
- 可用的淘宝/京东账号

## 安装指南
1. 克隆项目到本地：
   ```bash
   git clone https://github.com/yourusername/client-a-finance-automation.git
   cd client-a-finance-automation
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 初始化Playwright：
   ```bash
   playwright install
   ```

4. 配置账号信息：
   在项目根目录创建`config/.env`文件（不要提交到版本控制系统），内容如下：
   ```
   TAOBAO_USERNAME=你的淘宝账号
   TAOBAO_PASSWORD=你的淘宝密码
   JD_USERNAME=你的京东账号
   JD_PASSWORD=你的京东密码
   ```

## 使用方法
1. 启动程序：
   ```bash
   python main.py
   ```

2. 根据菜单提示选择操作：
   - 获取所有平台订单并合并导出
   - 仅获取淘宝订单并导出
   - 仅获取京东订单并导出

3. 如果出现验证码或其他安全验证，请按照提示在浏览器窗口中手动完成验证。

4. 程序执行完成后，会在`data/output`目录下生成合并后的Excel文件。

## 项目结构
```
client-a-finance-automation/
├── config/                    # 配置文件
│   ├── config.yml            # 主配置文件
│   ├── selectors.json        # UI元素选择器配置
│   └── .env                  # 环境变量文件（存储凭据，不提交到版本控制）
├── data/                      # 数据目录
│   ├── output/               # 输出文件存放目录
│   └── screenshots/          # 截图存放目录
├── logs/                      # 日志文件目录
├── reusable_modules/          # 可复用模块
│   ├── platforms/            # 平台特定实现
│   │   ├── base_platform.py  # 平台基类
│   │   ├── taobao.py         # 淘宝平台实现
│   │   └── jd.py             # 京东平台实现
│   ├── auto_selector.py      # 自动选择器生成器
│   ├── order_processor.py    # 订单处理器
│   ├── platform_factory.py   # 平台工厂
│   ├── selector_manager.py   # 选择器管理器
│   ├── taobao_operations.py  # 淘宝操作封装
│   └── utils.py              # 通用工具函数
├── docs/                      # 项目文档
├── main.py                    # 主程序（支持多平台）
├── pyproject.toml             # 项目元数据和依赖定义
└── README.md                  # 项目说明
```

## 注意事项
- 此工具仅用于演示和技术验证，请勿用于任何违反电商平台使用条款的用途
- 程序运行过程中请勿关闭自动打开的浏览器窗口
- 如遇登录失败，程序会自动重试最多2次（间隔5秒）
- 如需详细了解程序运行状态，请查看`logs/`目录下的日志文件

## 贡献指南
欢迎提交问题报告、功能请求和代码贡献。请确保您的代码符合项目的代码风格和测试要求。

## 授权协议
本项目采用MIT许可证。详情请见`LICENSE`文件。
