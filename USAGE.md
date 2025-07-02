# 淘宝首页自动化使用说明

## 快速开始

### 1. 环境准备

确保已安装Python 3.13+和Poetry：

```bash
# 安装项目依赖
poetry install

# 安装Playwright浏览器
poetry run playwright install chromium
```

### 2. 运行程序

```bash
# 激活虚拟环境
poetry shell

# 运行主程序
python main.py

# 或运行测试脚本
python test_taobao.py
```

## 功能说明

### 主要功能
- ✅ 自动启动Chrome浏览器
- ✅ 导航到淘宝首页 (https://www.taobao.com)
- ✅ 等待页面完全加载
- ✅ 验证页面关键元素（Logo、搜索框等）
- ✅ 自动截图保存
- ✅ 完整的错误处理和日志记录

### 执行流程
1. **启动浏览器** - 根据配置启动Chrome浏览器
2. **创建页面** - 创建新的浏览器页面
3. **导航到淘宝** - 访问淘宝首页
4. **等待加载** - 等待页面完全加载
5. **验证页面** - 检查关键元素是否存在
6. **截图保存** - 保存成功截图
7. **资源清理** - 关闭浏览器和页面

### 输出文件
- **日志文件**: `logs/rpa_process.log`
- **截图文件**: `data/screenshots/taobao_homepage_YYYYMMDD_HHMMSS.png`
- **错误截图**: `data/screenshots/error_*.png`

## 配置说明

### 浏览器配置
```yaml
browser_settings:
  headless: false    # 是否无头模式（false=显示浏览器窗口）
  slow_mo: 1000      # 操作延迟（毫秒）
  timeout: 30000     # 超时时间（毫秒）
```

### 页面验证配置
```yaml
selectors:
  taobao_logo: ".site-logo"     # 淘宝Logo选择器
  search_input: "#q"            # 搜索框选择器
```

### 业务规则配置
```yaml
business_rules:
  page_load_timeout: 10        # 页面加载超时时间（秒）
  screenshot_on_success: true  # 成功时是否截图
```

## 故障排除

### 常见问题

1. **浏览器启动失败**
   ```bash
   # 重新安装Playwright浏览器
   poetry run playwright install chromium
   ```

2. **页面加载超时**
   - 检查网络连接
   - 调整config.yml中的timeout设置

3. **元素定位失败**
   - 检查config.yml中的selectors配置
   - 确认淘宝页面结构是否发生变化

### 日志查看
```bash
# 查看最新日志
tail -f logs/rpa_process.log

# 查看错误日志
grep "ERROR" logs/rpa_process.log
```

## 扩展开发

### 添加新功能
1. 在`reusable_modules/taobao_operations.py`中添加新函数
2. 更新`config/config.yml`添加相关配置
3. 在`main.py`中集成新功能
4. 添加相应的测试用例

### 自定义异常处理
```python
class CustomTaobaoError(TaobaoOperationError):
    """自定义淘宝操作异常"""
    pass
```

### 添加新的页面验证
```python
def verify_custom_element(page: Page, config: dict) -> bool:
    """验证自定义元素"""
    try:
        selector = config['selectors']['custom_element']
        element = page.locator(selector)
        return element.is_visible()
    except Exception as e:
        logger.error(f"验证自定义元素失败: {e}")
        return False
```

## 性能优化

### 提高执行速度
1. 设置`headless: true`（无头模式）
2. 减少`slow_mo`值
3. 优化页面等待策略

### 减少资源占用
1. 及时关闭浏览器和页面
2. 定期清理截图文件
3. 配置日志轮转

## 安全注意事项

1. **不要提交敏感信息**
   - 确保.env文件已添加到.gitignore
   - 不要在代码中硬编码密码

2. **网络访问**
   - 确保网络连接稳定
   - 考虑使用代理配置

3. **文件权限**
   - 确保程序有权限创建logs和screenshots目录
   - 定期清理临时文件
