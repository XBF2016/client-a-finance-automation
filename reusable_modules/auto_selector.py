"""
自动选择器生成模块
提供智能的选择器生成、验证和管理功能
"""

import logging
import time
import hashlib
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from playwright.sync_api import Page, ElementHandle

logger = logging.getLogger("RPA_Logger")


@dataclass
class SelectorCandidate:
    """选择器候选对象"""

    selector: str
    method: str
    confidence: float
    description: str
    attributes: Dict[str, str]
    text_content: str
    position: Dict[str, int]


class AutoSelectorGenerator:
    """自动选择器生成器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.auto_config = config.get("auto_selector", {})
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_enabled = self.auto_config.get("cache_enabled", True)
        self.cache_duration = self.auto_config.get("cache_duration", 3600)

    def generate_selector(
        self,
        page: Page,
        target_description: str,
        target_text: Optional[str] = None,
        target_attributes: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        生成选择器的主方法

        Args:
            page: Playwright页面对象
            target_description: 目标元素描述
            target_text: 目标元素文本内容
            target_attributes: 目标元素属性

        Returns:
            最佳选择器或None
        """
        logger.info(f"开始为 '{target_description}' 生成选择器")

        # 检查缓存
        cache_key = self._generate_cache_key(page.url, target_description, target_text)
        if self.cache_enabled and cache_key in self.cache:
            cached_result = self.cache[cache_key]
            if time.time() - cached_result["timestamp"] < self.cache_duration:
                logger.info(f"使用缓存的选择器: {cached_result['selector']}")
                return cached_result["selector"]

        # 生成候选选择器
        candidates = self._generate_candidates(
            page, target_description, target_text, target_attributes
        )

        if not candidates:
            logger.warning(f"未找到 '{target_description}' 的候选选择器")
            return None

        # 验证和排序选择器
        valid_candidates = self._validate_candidates(page, candidates)
        if not valid_candidates:
            logger.warning("所有候选选择器验证失败")
            return None

        # 选择最佳选择器
        best_selector = self._select_best_selector(valid_candidates)

        # 缓存结果
        if self.cache_enabled:
            self.cache[cache_key] = {
                "selector": best_selector.selector,
                "timestamp": time.time(),
                "confidence": best_selector.confidence,
            }

        logger.info(
            f"生成选择器成功: {best_selector.selector} (置信度: {best_selector.confidence:.2f})"
        )
        return best_selector.selector

    def _generate_candidates(
        self,
        page: Page,
        target_description: str,
        target_text: Optional[str] = None,
        target_attributes: Optional[Dict[str, str]] = None,
    ) -> List[SelectorCandidate]:
        """生成候选选择器"""
        candidates: List[SelectorCandidate] = []
        methods = self.auto_config.get("methods", ["smart_algorithm"])

        for method in methods:
            if method == "smart_algorithm":
                candidates.extend(
                    self._smart_algorithm_candidates(
                        page, target_description, target_text, target_attributes
                    )
                )
            elif method == "text_based":
                candidates.extend(self._text_based_candidates(page, target_text))
            elif method == "attribute_based":
                candidates.extend(
                    self._attribute_based_candidates(page, target_attributes)
                )
            elif method == "position_based":
                candidates.extend(
                    self._position_based_candidates(page, target_description)
                )

        return candidates

    def _smart_algorithm_candidates(
        self,
        page: Page,
        target_description: str,
        target_text: Optional[str] = None,
        target_attributes: Optional[Dict[str, str]] = None,
    ) -> List[SelectorCandidate]:
        """智能算法生成候选选择器"""
        candidates: List[SelectorCandidate] = []

        # 获取页面所有元素
        elements = page.query_selector_all("*")

        for element in elements:
            try:
                # 获取元素信息
                tag_name = element.evaluate("el => el.tagName.toLowerCase()")
                element_id = element.get_attribute("id")
                text_content = (
                    element.text_content().strip() if element.text_content() else ""
                )

                # 计算匹配度
                confidence = 0.0
                selector = ""

                # 基于ID的选择器
                if element_id:
                    selector = f"#{element_id}"
                    confidence = 0.9
                    candidates.append(
                        SelectorCandidate(
                            selector=selector,
                            method="smart_algorithm",
                            confidence=confidence,
                            description=target_description,
                            attributes={"id": element_id},
                            text_content=text_content,
                            position=self._get_element_position(element),
                        )
                    )

                # 基于data属性的选择器
                data_attrs = self._get_data_attributes(element)
                for attr, value in data_attrs.items():
                    if value and len(value) > 2:  # 避免太短的值
                        selector = f"[{attr}='{value}']"
                        confidence = 0.8
                        candidates.append(
                            SelectorCandidate(
                                selector=selector,
                                method="smart_algorithm",
                                confidence=confidence,
                                description=target_description,
                                attributes={attr: value},
                                text_content=text_content,
                                position=self._get_element_position(element),
                            )
                        )

                # 基于文本内容的选择器
                if (
                    target_text
                    and text_content
                    and target_text.lower() in text_content.lower()
                ):
                    # 使用XPath基于文本内容
                    selector = f"//{tag_name}[contains(text(), '{target_text}')]"
                    confidence = 0.7
                    candidates.append(
                        SelectorCandidate(
                            selector=selector,
                            method="smart_algorithm",
                            confidence=confidence,
                            description=target_description,
                            attributes={},
                            text_content=text_content,
                            position=self._get_element_position(element),
                        )
                    )

                # 基于aria属性的选择器
                aria_label = element.get_attribute("aria-label")
                if aria_label:
                    selector = f"[aria-label='{aria_label}']"
                    confidence = 0.75
                    candidates.append(
                        SelectorCandidate(
                            selector=selector,
                            method="smart_algorithm",
                            confidence=confidence,
                            description=target_description,
                            attributes={"aria-label": aria_label},
                            text_content=text_content,
                            position=self._get_element_position(element),
                        )
                    )

            except Exception as e:
                logger.debug(f"处理元素时出错: {e}")
                continue

        return candidates

    def _text_based_candidates(
        self, page: Page, target_text: Optional[str]
    ) -> List[SelectorCandidate]:
        """基于文本内容生成候选选择器"""
        candidates: List[SelectorCandidate] = []

        if not target_text:
            return candidates

        try:
            # 使用Playwright的text选择器
            elements = page.query_selector_all(f"text={target_text}")

            for element in elements:
                try:
                    text_content = element.text_content().strip()
                    tag_name = element.evaluate("el => el.tagName.toLowerCase()")

                    # 生成多种文本相关的选择器
                    selectors = [
                        f"text={target_text}",
                        f"//{tag_name}[contains(text(), '{target_text}')]",
                        f"//{tag_name}[text()='{target_text}']",
                    ]

                    for selector in selectors:
                        candidates.append(
                            SelectorCandidate(
                                selector=selector,
                                method="text_based",
                                confidence=0.6,
                                description=f"文本匹配: {target_text}",
                                attributes={},
                                text_content=text_content,
                                position=self._get_element_position(element),
                            )
                        )

                except Exception as e:
                    logger.debug(f"处理文本元素时出错: {e}")
                    continue

        except Exception as e:
            logger.debug(f"文本搜索出错: {e}")

        return candidates

    def _attribute_based_candidates(
        self, page: Page, target_attributes: Optional[Dict[str, str]]
    ) -> List[SelectorCandidate]:
        """基于属性生成候选选择器"""
        candidates: List[SelectorCandidate] = []

        if not target_attributes:
            return candidates

        for attr, value in target_attributes.items():
            try:
                elements = page.query_selector_all(f"[{attr}='{value}']")

                for element in elements:
                    try:
                        text_content = element.text_content().strip()

                        selector = f"[{attr}='{value}']"
                        confidence = 0.8 if attr in ["id", "data-testid"] else 0.6

                        candidates.append(
                            SelectorCandidate(
                                selector=selector,
                                method="attribute_based",
                                confidence=confidence,
                                description=f"属性匹配: {attr}={value}",
                                attributes={attr: value},
                                text_content=text_content,
                                position=self._get_element_position(element),
                            )
                        )

                    except Exception as e:
                        logger.debug(f"处理属性元素时出错: {e}")
                        continue

            except Exception as e:
                logger.debug(f"属性搜索出错: {e}")

        return candidates

    def _position_based_candidates(
        self, page: Page, target_description: str
    ) -> List[SelectorCandidate]:
        """基于位置生成候选选择器"""
        candidates: List[SelectorCandidate] = []

        try:
            # 获取页面主要元素
            main_elements = page.query_selector_all(
                "main, .main, #main, .container, .content"
            )

            for element in main_elements:
                try:
                    position = self._get_element_position(element)
                    tag_name = element.evaluate("el => el.tagName.toLowerCase()")
                    element_id = element.get_attribute("id")

                    # 生成位置相关的选择器
                    if element_id:
                        selector = f"#{element_id}"
                    else:
                        selector = tag_name

                    candidates.append(
                        SelectorCandidate(
                            selector=selector,
                            method="position_based",
                            confidence=0.4,
                            description=f"位置匹配: {target_description}",
                            attributes={"id": element_id},
                            text_content=element.text_content().strip(),
                            position=position,
                        )
                    )

                except Exception as e:
                    logger.debug(f"处理位置元素时出错: {e}")
                    continue

        except Exception as e:
            logger.debug(f"位置搜索出错: {e}")

        return candidates

    def _validate_candidates(
        self, page: Page, candidates: List[SelectorCandidate]
    ) -> List[SelectorCandidate]:
        """验证候选选择器"""
        valid_candidates = []

        for candidate in candidates:
            try:
                # 尝试查找元素
                element = page.query_selector(candidate.selector)
                if element:
                    # 检查元素是否可见
                    is_visible = element.is_visible()
                    if is_visible:
                        valid_candidates.append(candidate)
                        logger.debug(f"选择器验证成功: {candidate.selector}")
                    else:
                        logger.debug(f"选择器找到元素但不可见: {candidate.selector}")
                else:
                    logger.debug(f"选择器未找到元素: {candidate.selector}")

            except Exception as e:
                logger.debug(f"选择器验证失败: {candidate.selector}, 错误: {e}")
                continue

        return valid_candidates

    def _select_best_selector(
        self, candidates: List[SelectorCandidate]
    ) -> SelectorCandidate:
        """选择最佳选择器"""
        if not candidates:
            raise ValueError("没有有效的候选选择器")

        # 按置信度排序
        sorted_candidates = sorted(candidates, key=lambda x: x.confidence, reverse=True)

        # 返回置信度最高的选择器
        return sorted_candidates[0]

    def _get_data_attributes(self, element: ElementHandle) -> Dict[str, str]:
        """获取元素的data属性"""
        try:
            return element.evaluate(
                """
                (element) => {
                    const dataAttrs = {};
                    for (let attr of element.attributes) {
                        if (attr.name.startsWith('data-')) {
                            dataAttrs[attr.name] = attr.value;
                        }
                    }
                    return dataAttrs;
                }
            """
            )
        except Exception as e:
            logger.debug(f"获取data属性时出错: {e}")
            return {}

    def _get_element_position(self, element: ElementHandle) -> Dict[str, int]:
        """获取元素位置信息"""
        try:
            return element.evaluate(
                """
                (element) => {
                    const rect = element.getBoundingClientRect();
                    return {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    };
                }
            """
            )
        except Exception as e:
            logger.debug(f"获取元素位置时出错: {e}")
            return {"x": 0, "y": 0, "width": 0, "height": 0}

    def _generate_cache_key(
        self, url: str, description: str, text: Optional[str] = None
    ) -> str:
        """生成缓存键"""
        content = f"{url}:{description}:{text or ''}"
        return hashlib.md5(content.encode()).hexdigest()

    def clear_cache(self):
        """清除缓存"""
        self.cache.clear()
        logger.info("选择器缓存已清除")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "cache_size": len(self.cache),
            "cache_enabled": self.cache_enabled,
            "cache_duration": self.cache_duration,
        }
