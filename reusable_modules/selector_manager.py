"""
选择器管理器
负责选择器的生命周期管理、版本控制和自动更新
"""

import logging
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from playwright.sync_api import Page
from .auto_selector import AutoSelectorGenerator

logger = logging.getLogger("RPA_Logger")


@dataclass
class SelectorInfo:
    """选择器信息"""

    name: str
    selector: str
    description: str
    method: str
    confidence: float
    created_at: str
    last_used: str
    success_count: int
    failure_count: int
    last_updated: str
    version: int
    is_active: bool
    fallback_selectors: List[str]
    attributes: Dict[str, str]
    text_content: str


class SelectorManager:
    """选择器管理器"""

    def __init__(
        self, config: Dict[str, Any], config_file_path: str = "config/selectors.json"
    ):
        self.config = config
        self.config_file_path = config_file_path
        self.auto_generator = AutoSelectorGenerator(config)
        self.selectors: Dict[str, SelectorInfo] = {}
        self.selector_history: Dict[str, List[SelectorInfo]] = {}

        # 加载现有选择器
        self._load_selectors()

    def get_selector(
        self,
        page: Page,
        selector_name: str,
        target_description: Optional[str] = None,
        target_text: Optional[str] = None,
        target_attributes: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        获取选择器，如果失效则自动更新

        Args:
            page: Playwright页面对象
            selector_name: 选择器名称
            target_description: 目标元素描述
            target_text: 目标元素文本
            target_attributes: 目标元素属性

        Returns:
            有效的选择器或None
        """
        logger.info(f"获取选择器: {selector_name}")

        # 检查是否有现有选择器
        if selector_name in self.selectors:
            selector_info = self.selectors[selector_name]

            # 检查选择器是否仍然有效
            if self._validate_selector(page, selector_info.selector):
                # 更新使用统计
                self._update_usage_stats(selector_name, success=True)
                logger.info(f"使用现有选择器: {selector_info.selector}")
                return selector_info.selector
            else:
                logger.warning(f"选择器已失效: {selector_info.selector}")
                # 标记为失效
                self._mark_selector_failed(selector_name)

        # 尝试使用备用选择器
        if selector_name in self.selectors:
            fallback_selectors = self.selectors[selector_name].fallback_selectors
            for fallback in fallback_selectors:
                if self._validate_selector(page, fallback):
                    logger.info(f"使用备用选择器: {fallback}")
                    return fallback

        # 自动生成新选择器
        if self.config.get("auto_selector", {}).get("enabled", True):
            new_selector = self._generate_new_selector(
                page, selector_name, target_description, target_text, target_attributes
            )
            if new_selector:
                return new_selector

        logger.error(f"无法获取有效的选择器: {selector_name}")
        return None

    def add_selector(
        self,
        name: str,
        selector: str,
        description: str = "",
        method: str = "manual",
        confidence: float = 1.0,
        attributes: Optional[Dict[str, str]] = None,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        添加新选择器

        Args:
            name: 选择器名称
            selector: 选择器字符串
            description: 描述
            method: 生成方法
            confidence: 置信度
            attributes: 元素属性
            text_content: 文本内容

        Returns:
            是否添加成功
        """
        try:
            selector_info = SelectorInfo(
                name=name,
                selector=selector,
                description=description,
                method=method,
                confidence=confidence,
                created_at=datetime.now().isoformat(),
                last_used=datetime.now().isoformat(),
                success_count=0,
                failure_count=0,
                last_updated=datetime.now().isoformat(),
                version=1,
                is_active=True,
                fallback_selectors=[],
                attributes=attributes or {},
                text_content=text_content or "",
            )

            self.selectors[name] = selector_info

            # 保存到文件
            self._save_selectors()

            logger.info(f"添加选择器成功: {name} -> {selector}")
            return True

        except Exception as e:
            logger.error(f"添加选择器失败: {e}")
            return False

    def update_selector(
        self,
        name: str,
        new_selector: str,
        method: str = "auto_update",
        confidence: Optional[float] = None,
    ) -> bool:
        """
        更新选择器

        Args:
            name: 选择器名称
            new_selector: 新选择器
            method: 更新方法
            confidence: 新置信度

        Returns:
            是否更新成功
        """
        try:
            if name not in self.selectors:
                logger.warning(f"选择器不存在: {name}")
                return False

            # 保存历史版本
            old_selector = self.selectors[name]
            if name not in self.selector_history:
                self.selector_history[name] = []
            self.selector_history[name].append(old_selector)

            # 更新选择器
            self.selectors[name].selector = new_selector
            self.selectors[name].method = method
            if confidence is not None:
                self.selectors[name].confidence = confidence
            self.selectors[name].last_updated = datetime.now().isoformat()
            self.selectors[name].version += 1
            self.selectors[name].is_active = True

            # 保存到文件
            self._save_selectors()

            logger.info(f"更新选择器成功: {name} -> {new_selector}")
            return True

        except Exception as e:
            logger.error(f"更新选择器失败: {e}")
            return False

    def remove_selector(self, name: str) -> bool:
        """
        移除选择器

        Args:
            name: 选择器名称

        Returns:
            是否移除成功
        """
        try:
            if name in self.selectors:
                del self.selectors[name]
                self._save_selectors()
                logger.info(f"移除选择器成功: {name}")
                return True
            else:
                logger.warning(f"选择器不存在: {name}")
                return False

        except Exception as e:
            logger.error(f"移除选择器失败: {e}")
            return False

    def get_selector_stats(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取选择器统计信息

        Args:
            name: 选择器名称

        Returns:
            统计信息字典
        """
        if name not in self.selectors:
            return None

        selector = self.selectors[name]
        total_uses = selector.success_count + selector.failure_count
        success_rate = selector.success_count / total_uses if total_uses > 0 else 0

        return {
            "name": name,
            "selector": selector.selector,
            "success_count": selector.success_count,
            "failure_count": selector.failure_count,
            "success_rate": success_rate,
            "confidence": selector.confidence,
            "version": selector.version,
            "last_used": selector.last_used,
            "is_active": selector.is_active,
        }

    def get_all_stats(self) -> Dict[str, Any]:
        """
        获取所有选择器的统计信息

        Returns:
            统计信息字典
        """
        stats: Dict[str, Any] = {
            "total_selectors": len(self.selectors),
            "active_selectors": sum(1 for s in self.selectors.values() if s.is_active),
            "total_uses": sum(
                s.success_count + s.failure_count for s in self.selectors.values()
            ),
            "total_success": sum(s.success_count for s in self.selectors.values()),
            "total_failures": sum(s.failure_count for s in self.selectors.values()),
            "selectors": {},
        }

        for name in self.selectors:
            stats["selectors"][name] = self.get_selector_stats(name)

        return stats

    def _validate_selector(self, page: Page, selector: str) -> bool:
        """
        验证选择器是否有效

        Args:
            page: Playwright页面对象
            selector: 选择器字符串

        Returns:
            是否有效
        """
        try:
            element = page.query_selector(selector)
            return element is not None and element.is_visible()
        except Exception as e:
            logger.debug(f"选择器验证失败: {selector}, 错误: {e}")
            return False

    def _generate_new_selector(
        self,
        page: Page,
        selector_name: str,
        target_description: Optional[str] = None,
        target_text: Optional[str] = None,
        target_attributes: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        生成新选择器

        Args:
            page: Playwright页面对象
            selector_name: 选择器名称
            target_description: 目标描述
            target_text: 目标文本
            target_attributes: 目标属性

        Returns:
            新选择器或None
        """
        try:
            # 使用自动生成器
            new_selector = self.auto_generator.generate_selector(
                page,
                target_description or selector_name,
                target_text,
                target_attributes,
            )

            if new_selector:
                # 添加到管理器
                self.add_selector(
                    name=selector_name,
                    selector=new_selector,
                    description=target_description or selector_name,
                    method="auto_generated",
                    confidence=0.8,
                    attributes=target_attributes,
                    text_content=target_text,
                )

                logger.info(f"自动生成选择器成功: {selector_name} -> {new_selector}")
                return new_selector

        except Exception as e:
            logger.error(f"自动生成选择器失败: {e}")

        return None

    def _update_usage_stats(self, selector_name: str, success: bool = True):
        """
        更新使用统计

        Args:
            selector_name: 选择器名称
            success: 是否成功
        """
        if selector_name in self.selectors:
            selector = self.selectors[selector_name]
            if success:
                selector.success_count += 1
            else:
                selector.failure_count += 1
            selector.last_used = datetime.now().isoformat()

    def _mark_selector_failed(self, selector_name: str):
        """
        标记选择器失败

        Args:
            selector_name: 选择器名称
        """
        if selector_name in self.selectors:
            self.selectors[selector_name].failure_count += 1
            self.selectors[selector_name].last_used = datetime.now().isoformat()

    def _load_selectors(self):
        """从文件加载选择器"""
        try:
            if os.path.exists(self.config_file_path):
                with open(self.config_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for selector_data in data.get("selectors", []):
                    selector_info = SelectorInfo(**selector_data)
                    self.selectors[selector_info.name] = selector_info

                logger.info(f"加载了 {len(self.selectors)} 个选择器")
            else:
                logger.info("选择器配置文件不存在，将创建新文件")

        except Exception as e:
            logger.error(f"加载选择器失败: {e}")

    def _save_selectors(self):
        """保存选择器到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)

            # 转换为可序列化的格式
            data = {
                "selectors": [asdict(selector) for selector in self.selectors.values()],
                "last_updated": datetime.now().isoformat(),
            }

            with open(self.config_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"保存了 {len(self.selectors)} 个选择器")

        except Exception as e:
            logger.error(f"保存选择器失败: {e}")

    def export_selectors(self, file_path: str) -> bool:
        """
        导出选择器到文件

        Args:
            file_path: 导出文件路径

        Returns:
            是否导出成功
        """
        try:
            data = {
                "selectors": [asdict(selector) for selector in self.selectors.values()],
                "export_time": datetime.now().isoformat(),
                "total_count": len(self.selectors),
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"导出选择器成功: {file_path}")
            return True

        except Exception as e:
            logger.error(f"导出选择器失败: {e}")
            return False

    def import_selectors(self, file_path: str, overwrite: bool = False) -> bool:
        """
        从文件导入选择器

        Args:
            file_path: 导入文件路径
            overwrite: 是否覆盖现有选择器

        Returns:
            是否导入成功
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            imported_count = 0
            for selector_data in data.get("selectors", []):
                name = selector_data.get("name")
                if name and (overwrite or name not in self.selectors):
                    selector_info = SelectorInfo(**selector_data)
                    self.selectors[name] = selector_info
                    imported_count += 1

            self._save_selectors()
            logger.info(f"导入选择器成功: {imported_count} 个")
            return True

        except Exception as e:
            logger.error(f"导入选择器失败: {e}")
            return False
