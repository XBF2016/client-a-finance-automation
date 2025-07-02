# 多平台订单自动合并架构说明

## 1. 架构概述

本项目采用了模块化、可扩展的架构设计，通过抽象出平台接口基类，实现了对多个电商平台（如淘宝、京东等）的统一操作和管理。核心设计思想是"一次编写，多平台复用"，使得添加新平台变得简单高效。

## 2. 核心组件

### 2.1 平台接口基类 (`PlatformOperationsBase`)

位于 `reusable_modules/platforms/base_platform.py`，定义了所有平台必须实现的标准接口：

- `login()`: 登录平台
- `is_logged_in()`: 检查登录状态
- `navigate_to_orders_page()`: 导航到订单页面
- `get_orders()`: 获取订单数据
- `standardize_orders()`: 标准化订单数据
- `take_screenshot()`: 截图
- `close()`: 关闭资源

### 2.2 平台实现类

- **淘宝平台** (`TaobaoPlatform`): 位于 `reusable_modules/platforms/taobao.py`
- **京东平台** (`JDPlatform`): 位于 `reusable_modules/platforms/jd.py`

每个平台实现类继承自平台接口基类，并根据各自平台的特点实现具体的操作逻辑。

### 2.3 平台工厂 (`platform_factory`)

位于 `reusable_modules/platform_factory.py`，负责根据配置动态创建平台实例，主要功能：

- `create_platform()`: 创建指定平台的实例
- `get_available_platforms()`: 获取所有可用平台列表
- `create_all_platforms()`: 创建所有配置中的平台实例

### 2.4 订单处理器 (`OrderProcessor`)

位于 `reusable_modules/order_processor.py`，负责多平台订单数据的获取、合并、标准化和导出，主要功能：

- `initialize_platforms()`: 初始化所有平台
- `login_all_platforms()`: 登录所有平台
- `fetch_all_orders()`: 获取所有平台的订单数据
- `standardize_all_orders()`: 标准化所有平台的订单数据
- `export_to_excel()`: 导出到Excel
- `process()`: 执行完整的订单处理流程

## 3. 配置系统

配置文件位于 `config/config.yml`，采用分层结构：

- 全局配置：浏览器设置、路径等
- 平台特定配置：每个平台的URL、选择器、字段映射等
- 凭据配置：通过环境变量或`.env`文件加载，避免硬编码敏感信息

## 4. 使用方法

### 4.1 基本使用

```python
from reusable_modules.utils import load_config
from reusable_modules.order_processor import OrderProcessor

# 加载配置
config = load_config()

# 创建订单处理器
processor = OrderProcessor(config)

# 执行完整流程
excel_path = processor.process(days=7)
print(f"订单数据已导出到: {excel_path}")
```

### 4.2 添加新平台

1. 创建新的平台实现类，继承自 `PlatformOperationsBase`
2. 在 `platform_factory.py` 中注册新平台
3. 在 `config.yml` 中添加新平台的配置

## 5. 测试

- `test_multi_platform.py`: 测试多平台架构
- `main.py`: 多平台订单合并主程序

## 6. 扩展性考虑

本架构设计考虑了以下扩展性需求：

- **新平台支持**: 只需创建新的平台实现类，无需修改核心逻辑
- **新功能添加**: 可以在基类中定义新接口，各平台按需实现
- **配置灵活性**: 通过配置文件控制平台启用/禁用、选择器更新等
- **错误处理**: 统一的错误处理机制，确保一个平台的失败不影响其他平台

## 7. 后续优化方向

- 添加更多平台支持（拼多多、抖音等）
- 实现更复杂的订单数据处理逻辑
- 添加自动化测试用例
- 优化UI和用户交互
- 增加定时任务支持
