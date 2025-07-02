# 自动选择器功能使用说明

## 概述

自动选择器功能是一个智能的选择器生成和管理系统，能够自动分析网页元素并生成稳定的选择器，当选择器失效时自动更新。

## 主要功能

### 1. 智能选择器生成
- **多种生成方法**: 支持基于ID、属性、文本内容、位置等多种方式生成选择器
- **置信度评估**: 为每个生成的选择器分配置信度分数
- **自动验证**: 生成后自动验证选择器是否有效

### 2. 选择器生命周期管理
- **版本控制**: 记录选择器的版本历史
- **使用统计**: 跟踪选择器的成功/失败次数
- **自动更新**: 当选择器失效时自动生成新的选择器

### 3. 缓存机制
- **智能缓存**: 缓存生成的选择器以提高性能
- **缓存管理**: 支持清除缓存和查看缓存统计

## 配置说明

在 `config/config.yml` 中添加自动选择器配置：

```yaml
auto_selector:
  enabled: true                    # 启用自动选择器功能
  methods:                         # 选择器生成方法
    - smart_algorithm             # 智能算法
    - text_based                  # 基于文本
    - attribute_based             # 基于属性
    - position_based              # 基于位置
  fallback_selectors: true        # 启用备用选择器
  validation_timeout: 5           # 验证超时时间（秒）
  confidence_threshold: 0.8       # 置信度阈值
  max_candidates: 10              # 最大候选数量
  cache_enabled: true             # 启用缓存
  cache_duration: 3600            # 缓存持续时间（秒）
```

## 使用方法

### 1. 基本使用

```python
from reusable_modules.taobao_operations import open_taobao_homepage, get_selector_manager

# 加载配置
config = load_config()

# 打开淘宝首页（自动使用智能选择器）
browser, page, screenshot_path = open_taobao_homepage(config)

# 获取选择器管理器
selector_manager = get_selector_manager(config)

# 智能获取选择器
search_selector = selector_manager.get_selector(
    page=page,
    selector_name="search_input",
    target_description="搜索输入框",
    target_attributes={'type': 'text'}
)

# 使用选择器
page.fill(search_selector, "测试商品")
```

### 2. 直接使用自动生成器

```python
from reusable_modules.auto_selector import AutoSelectorGenerator

# 创建自动生成器
auto_generator = AutoSelectorGenerator(config)

# 生成选择器
selector = auto_generator.generate_selector(
    page=page,
    target_description="登录按钮",
    target_text="登录",
    target_attributes={'type': 'button'}
)
```

### 3. 使用选择器管理器

```python
from reusable_modules.selector_manager import SelectorManager

# 创建选择器管理器
selector_manager = SelectorManager(config)

# 添加选择器
selector_manager.add_selector(
    name="my_button",
    selector="#my-button",
    description="我的按钮",
    confidence=0.9
)

# 获取选择器
selector = selector_manager.get_selector(page, "my_button")

# 查看统计
stats = selector_manager.get_selector_stats("my_button")
```

## 命令行工具

使用 `selector_tools.py` 进行选择器管理：

### 列出所有选择器
```bash
python selector_tools.py list
```

### 添加选择器
```bash
python selector_tools.py add "search_input" "#q" --description "搜索输入框" --confidence 0.9
```

### 更新选择器
```bash
python selector_tools.py update "search_input" "#new-search" --confidence 0.8
```

### 移除选择器
```bash
python selector_tools.py remove "search_input"
```

### 显示选择器详情
```bash
python selector_tools.py show "search_input"
```

### 导出选择器
```bash
python selector_tools.py export "selectors_backup.json"
```

### 导入选择器
```bash
python selector_tools.py import "selectors_backup.json" --overwrite
```

### 缓存管理
```bash
# 清除缓存
python selector_tools.py cache clear

# 显示缓存统计
python selector_tools.py cache stats
```

## 测试功能

运行测试脚本验证功能：

```bash
python test_auto_selector.py
```

测试包括：
- 自动选择器生成功能
- 选择器管理器功能
- 集成的淘宝操作功能

## 选择器生成方法

### 1. 智能算法 (smart_algorithm)
- 分析页面所有元素
- 基于ID、data属性、aria属性等生成选择器
- 计算置信度分数

### 2. 基于文本 (text_based)
- 根据元素文本内容生成选择器
- 支持精确匹配和包含匹配
- 使用XPath和Playwright text选择器

### 3. 基于属性 (attribute_based)
- 根据元素属性生成选择器
- 支持type、placeholder、class等属性
- 优先使用稳定属性

### 4. 基于位置 (position_based)
- 根据元素在页面中的位置生成选择器
- 适用于布局相对稳定的页面
- 置信度相对较低

## 置信度说明

- **0.9-1.0**: 非常稳定（如ID选择器）
- **0.8-0.9**: 比较稳定（如data属性）
- **0.7-0.8**: 一般稳定（如aria属性）
- **0.6-0.7**: 相对稳定（如文本内容）
- **0.4-0.6**: 不太稳定（如位置相关）

## 最佳实践

### 1. 选择器命名
- 使用描述性的名称
- 遵循一致的命名规范
- 避免使用特殊字符

### 2. 配置优化
- 根据网站特点调整生成方法
- 设置合适的置信度阈值
- 合理配置缓存参数

### 3. 监控和维护
- 定期查看选择器统计
- 及时清理失效的选择器
- 备份重要的选择器配置

### 4. 错误处理
- 实现选择器失效的回退机制
- 记录选择器使用日志
- 设置告警机制

## 故障排除

### 1. 选择器生成失败
- 检查页面是否正确加载
- 确认目标元素存在且可见
- 调整生成方法配置

### 2. 选择器验证失败
- 检查元素是否被动态修改
- 确认页面结构是否变化
- 尝试使用不同的生成方法

### 3. 性能问题
- 调整缓存配置
- 减少候选选择器数量
- 优化验证超时时间

## 扩展功能

### 1. 自定义生成方法
可以继承 `AutoSelectorGenerator` 类并添加自定义的生成方法：

```python
class CustomAutoSelectorGenerator(AutoSelectorGenerator):
    def _custom_method_candidates(self, page, target_description):
        # 实现自定义生成逻辑
        pass
```

### 2. 集成AI模型
可以集成AI模型来提高选择器生成的准确性：

```python
def generate_ai_selector(self, page_content, target_description):
    # 调用AI API生成选择器
    pass
```

### 3. 视觉识别
可以集成计算机视觉技术来识别页面元素：

```python
def generate_visual_selector(self, screenshot, target_element):
    # 使用图像识别技术
    pass
```

## 总结

自动选择器功能大大简化了RPA项目中选择器的管理，提供了智能、稳定、可维护的选择器解决方案。通过合理配置和使用，可以显著提高自动化脚本的稳定性和维护效率。
