"""
AI模型调用服务 - 阿里云DashScope DeepSeek-V3
采用随机风格生成和GRPO优化
"""
import os
from typing import Dict, List, Optional
import dashscope
from dashscope import Generation
import json
from .style_generator import StyleGenerator, StyleParams


class AIService:
    """AI服务类"""

    def __init__(self):
        """初始化AI服务"""
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY环境变量未设置")

        dashscope.api_key = self.api_key
        self.model = "deepseek-v3"
        self.style_generator = StyleGenerator()

    async def generate_article(
        self,
        description: str,
        style: StyleParams,
        experiences: List[str] = None
    ) -> Dict:
        """
        生成文章

        Args:
            description: 用户输入的写作描述
            style: 风格参数
            experiences: 历史经验列表

        Returns:
            包含文章内容和元数据的字典
        """
        # 构建提示词
        prompt = self._build_prompt(description, style, experiences)

        # 根据风格参数计算temperature
        # 创新度越高，temperature越高
        temperature = 0.6 + style.creativity * 0.4  # 范围 0.6-1.0

        # 调用DeepSeek模型
        try:
            response = Generation.call(
                model=self.model,
                prompt=prompt,
                max_tokens=2000,
                temperature=temperature,
                top_p=0.9,
                result_format='message'
            )

            if response.status_code == 200:
                content = response.output.choices[0].message.content
                return self._parse_response(content, style, temperature)
            else:
                raise Exception(f"AI调用失败: {response.message}")

        except Exception as e:
            raise Exception(f"生成文章时出错: {str(e)}")

    def _build_prompt(
        self,
        description: str,
        style: StyleParams,
        experiences: List[str] = None
    ) -> str:
        """
        构建AI提示词

        Args:
            description: 写作描述
            style: 风格参数
            experiences: 经验列表
        """
        base_prompt = f"""你是一位专业的内容创作者。请根据以下要求创作一篇文章：

**写作要求**：
{description}

"""

        # 添加经验指导
        if experiences and len(experiences) > 0:
            base_prompt += "**用户偏好参考**（根据历史反馈总结）：\n"
            for i, exp in enumerate(experiences, 1):
                base_prompt += f"{i}. {exp}\n"
            base_prompt += "\n"

        # 使用风格生成器构建风格指导
        base_prompt += self.style_generator.build_prompt_from_style(
            style, ""
        ).split("**风格要求**：")[1]

        return base_prompt

    def _parse_response(
        self,
        content: str,
        style: StyleParams,
        temperature: float
    ) -> Dict:
        """
        解析AI响应

        Args:
            content: AI生成的内容
            style: 风格参数
            temperature: 使用的temperature值

        Returns:
            包含文章和元数据的字典
        """
        return {
            "content": content.strip(),
            "style_params": json.dumps({
                **style.to_dict(),
                "temperature": temperature
            }),
            "style_description": style.to_description()
        }

    async def summarize_experience_grpo(
        self,
        selected_articles: List[Dict],
        rejected_articles: List[Dict],
        iteration: int = 0
    ) -> Dict[str, any]:
        """
        使用GRPO方法总结用户偏好经验

        Args:
            selected_articles: 用户选择的文章列表（带风格参数）
            rejected_articles: 用户未选择的文章列表
            iteration: 当前迭代次数

        Returns:
            经验总结字典，包含：
            - preference_summary: 文本总结
            - preferred_params: 偏好的风格参数
            - reward_info: 奖励信息
        """
        if not selected_articles:
            return {
                "preference_summary": "",
                "preferred_params": {},
                "reward_info": {"mean": 0, "std": 1}
            }

        # 1. 分析风格参数分布
        preferred_params = self._analyze_style_preferences(
            selected_articles,
            rejected_articles
        )

        # 2. 使用AI生成自然语言总结
        nl_summary = await self._generate_nl_summary(
            selected_articles,
            rejected_articles,
            preferred_params
        )

        # 3. 计算奖励统计（GRPO核心）
        reward_info = self._calculate_group_rewards(
            selected_articles,
            rejected_articles
        )

        return {
            "preference_summary": nl_summary,
            "preferred_params": preferred_params,
            "reward_info": reward_info,
            "iteration": iteration + 1
        }

    def _analyze_style_preferences(
        self,
        selected: List[Dict],
        rejected: List[Dict]
    ) -> Dict[str, float]:
        """
        分析风格参数偏好

        Returns:
            各维度的偏好值
        """
        # 解析选中文章的风格参数
        selected_params = []
        for article in selected:
            if article.get('style_params'):
                try:
                    params = json.loads(article['style_params'])
                    selected_params.append(params)
                except:
                    pass

        if not selected_params:
            return {}

        # 计算各维度的平均值
        dims = ['formality', 'emotion', 'detail_level', 'creativity', 'technicality', 'narrative']
        preferences = {}

        for dim in dims:
            values = [p.get(dim, 0.5) for p in selected_params if dim in p]
            if values:
                preferences[dim] = sum(values) / len(values)

        return preferences

    async def _generate_nl_summary(
        self,
        selected: List[Dict],
        rejected: List[Dict],
        preferred_params: Dict[str, float]
    ) -> str:
        """
        生成自然语言形式的偏好总结
        """
        # 构建提示词
        prompt = f"""请分析以下数据，总结用户的写作偏好。

**用户偏好的风格参数**（0-1范围）：
"""
        for dim, value in preferred_params.items():
            dim_name = {
                'formality': '正式度',
                'emotion': '情感度',
                'detail_level': '详细度',
                'creativity': '创新度',
                'technicality': '专业度',
                'narrative': '叙事性'
            }.get(dim, dim)
            prompt += f"- {dim_name}: {value:.2f}\n"

        prompt += f"""
**选择次数**: {len(selected)}次

请用1-2句简洁的话总结用户的核心偏好，例如：
"用户偏好正式且专业的写作风格，倾向于详细的论述和适度的创新表达。"
"""

        try:
            response = Generation.call(
                model=self.model,
                prompt=prompt,
                max_tokens=150,
                temperature=0.3,
                result_format='message'
            )

            if response.status_code == 200:
                return response.output.choices[0].message.content.strip()
            else:
                return self._fallback_summary(preferred_params)

        except Exception as e:
            print(f"生成总结时出错: {str(e)}")
            return self._fallback_summary(preferred_params)

    def _fallback_summary(self, params: Dict[str, float]) -> str:
        """备用的规则总结"""
        summary_parts = []

        if params.get('formality', 0.5) > 0.6:
            summary_parts.append("正式专业")
        elif params.get('formality', 0.5) < 0.4:
            summary_parts.append("轻松口语化")

        if params.get('emotion', 0.5) > 0.6:
            summary_parts.append("富有感染力")

        if params.get('detail_level', 0.5) > 0.6:
            summary_parts.append("详尽深入")

        if params.get('creativity', 0.5) > 0.6:
            summary_parts.append("创新新颖")

        if summary_parts:
            return f"用户偏好{' '.join(summary_parts)}的写作风格。"
        return "用户偏好尚在探索中。"

    def _calculate_group_rewards(
        self,
        selected: List[Dict],
        rejected: List[Dict]
    ) -> Dict[str, float]:
        """
        计算组内相对奖励（GRPO核心思想）

        在GRPO中，奖励是相对的，通过对比同一组（任务）中被选择和未被选择的输出来计算
        """
        # 简化版本：被选择的得分为1，未被选择的得分为0
        all_scores = [1.0] * len(selected) + [0.0] * len(rejected)

        if not all_scores:
            return {"mean": 0.0, "std": 1.0}

        mean_reward = sum(all_scores) / len(all_scores)
        variance = sum((x - mean_reward) ** 2 for x in all_scores) / len(all_scores)
        std_reward = variance ** 0.5

        return {
            "mean": mean_reward,
            "std": std_reward if std_reward > 0 else 1.0
        }
