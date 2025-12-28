"""
风格生成器 - 随机生成多维度风格参数
"""
import random
from typing import Dict
from dataclasses import dataclass


@dataclass
class StyleParams:
    """风格参数"""
    formality: float       # 正式度 0-1
    emotion: float         # 情感度 0-1
    detail_level: float    # 详细度 0-1
    creativity: float      # 创新度 0-1
    technicality: float    # 专业度 0-1
    narrative: float       # 叙事性 0-1

    def to_dict(self) -> Dict[str, float]:
        """转换为字典"""
        return {
            "formality": self.formality,
            "emotion": self.emotion,
            "detail_level": self.detail_level,
            "creativity": self.creativity,
            "technicality": self.technicality,
            "narrative": self.narrative,
        }

    def to_description(self) -> str:
        """转换为文本描述"""
        desc = []

        # 正式度
        if self.formality > 0.7:
            desc.append("正式、专业")
        elif self.formality < 0.3:
            desc.append("轻松、口语化")
        else:
            desc.append("适度正式")

        # 情感度
        if self.emotion > 0.7:
            desc.append("富有感染力")
        elif self.emotion < 0.3:
            desc.append("客观、理性")

        # 详细度
        if self.detail_level > 0.7:
            desc.append("详尽、深入")
        elif self.detail_level < 0.3:
            desc.append("简洁、概括")

        # 创新度
        if self.creativity > 0.7:
            desc.append("新颖、创意")
        elif self.creativity < 0.3:
            desc.append("稳健、传统")

        # 专业度
        if self.technicality > 0.7:
            desc.append("专业术语丰富")

        # 叙事性
        if self.narrative > 0.7:
            desc.append("故事化叙述")
        elif self.narrative < 0.3:
            desc.append("论述性结构")

        return "、".join(desc)


class StyleGenerator:
    """风格生成器"""

    def __init__(self, seed: int = None):
        """初始化"""
        if seed is not None:
            random.seed(seed)

    def generate_random_style(self) -> StyleParams:
        """生成完全随机的风格参数"""
        return StyleParams(
            formality=random.uniform(0, 1),
            emotion=random.uniform(0, 1),
            detail_level=random.uniform(0, 1),
            creativity=random.uniform(0, 1),
            technicality=random.uniform(0, 1),
            narrative=random.uniform(0, 1),
        )

    def generate_diverse_pair(self) -> tuple[StyleParams, StyleParams]:
        """
        生成两个差异较大的风格参数
        确保充分探索风格空间
        """
        style_a = self.generate_random_style()

        # 生成与A差异较大的B
        # 通过在某些维度上取反向值来增加多样性
        style_b = StyleParams(
            formality=self._diversify(style_a.formality),
            emotion=self._diversify(style_a.emotion),
            detail_level=self._diversify(style_a.detail_level),
            creativity=self._diversify(style_a.creativity),
            technicality=random.uniform(0, 1),  # 部分维度保持随机
            narrative=self._diversify(style_a.narrative),
        )

        return style_a, style_b

    def _diversify(self, value: float) -> float:
        """
        生成与给定值差异较大的值
        """
        # 如果值在0-0.5，倾向于生成0.5-1的值
        # 如果值在0.5-1，倾向于生成0-0.5的值
        if value < 0.5:
            return random.uniform(0.5, 1.0)
        else:
            return random.uniform(0.0, 0.5)

    def generate_from_preferences(
        self,
        preferences: Dict[str, float],
        exploration_rate: float = 0.3
    ) -> StyleParams:
        """
        基于偏好生成风格，同时保持一定探索性

        Args:
            preferences: 偏好参数字典
            exploration_rate: 探索率 (0-1)，越高越随机
        """
        style = StyleParams(
            formality=self._blend(
                preferences.get("formality", 0.5),
                random.uniform(0, 1),
                exploration_rate
            ),
            emotion=self._blend(
                preferences.get("emotion", 0.5),
                random.uniform(0, 1),
                exploration_rate
            ),
            detail_level=self._blend(
                preferences.get("detail_level", 0.5),
                random.uniform(0, 1),
                exploration_rate
            ),
            creativity=self._blend(
                preferences.get("creativity", 0.5),
                random.uniform(0, 1),
                exploration_rate
            ),
            technicality=self._blend(
                preferences.get("technicality", 0.5),
                random.uniform(0, 1),
                exploration_rate
            ),
            narrative=self._blend(
                preferences.get("narrative", 0.5),
                random.uniform(0, 1),
                exploration_rate
            ),
        )

        return style

    def _blend(self, preferred: float, random_val: float, rate: float) -> float:
        """
        混合偏好值和随机值

        Args:
            preferred: 偏好值
            random_val: 随机值
            rate: 随机值的权重
        """
        return preferred * (1 - rate) + random_val * rate

    def build_prompt_from_style(
        self,
        style: StyleParams,
        base_description: str
    ) -> str:
        """
        根据风格参数构建提示词

        Args:
            style: 风格参数
            base_description: 基础写作要求
        """
        prompt = f"""你是一位专业的内容创作者。请根据以下要求创作一篇文章：

**写作要求**：
{base_description}

**风格要求**：
- 正式度: {"高（正式、专业）" if style.formality > 0.6 else "低（轻松、口语化）" if style.formality < 0.4 else "中等"}
- 情感表达: {"丰富（富有感染力）" if style.emotion > 0.6 else "克制（客观、理性）" if style.emotion < 0.4 else "适度"}
- 详细程度: {"详尽（深入分析）" if style.detail_level > 0.6 else "简洁（提纲挈领）" if style.detail_level < 0.4 else "适中"}
- 创新性: {"高（新颖观点、创意表达）" if style.creativity > 0.6 else "稳健（传统可靠）" if style.creativity < 0.4 else "平衡"}
- 专业性: {"专业术语丰富" if style.technicality > 0.6 else "通俗易懂" if style.technicality < 0.4 else "专业与通俗结合"}
- 叙述方式: {"故事化叙述" if style.narrative > 0.6 else "论述性结构" if style.narrative < 0.4 else "叙议结合"}

请直接输出文章内容，不需要额外说明。"""

        return prompt
