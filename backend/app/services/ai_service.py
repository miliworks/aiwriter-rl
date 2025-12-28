"""
AI模型调用服务 - 阿里云DashScope DeepSeek-V3
"""
import os
from typing import Dict, List
import dashscope
from dashscope import Generation
import json


class AIService:
    """AI服务类"""

    def __init__(self):
        """初始化AI服务"""
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY环境变量未设置")

        dashscope.api_key = self.api_key
        self.model = "deepseek-v3"  # 阿里云上的DeepSeek-V3模型

    async def generate_article(
        self,
        description: str,
        variant: str,
        experiences: List[str] = None
    ) -> Dict[str, str]:
        """
        生成文章

        Args:
            description: 用户输入的写作描述
            variant: 变体类型 ("A" 或 "B")
            experiences: 历史经验列表

        Returns:
            包含文章内容和元数据的字典
        """
        # 构建提示词
        prompt = self._build_prompt(description, variant, experiences)

        # 调用DeepSeek模型
        try:
            response = Generation.call(
                model=self.model,
                prompt=prompt,
                max_tokens=2000,
                temperature=0.7 if variant == "A" else 0.85,  # B版本更多样化
                top_p=0.9,
                result_format='message'
            )

            if response.status_code == 200:
                content = response.output.choices[0].message.content
                return self._parse_response(content, variant)
            else:
                raise Exception(f"AI调用失败: {response.message}")

        except Exception as e:
            raise Exception(f"生成文章时出错: {str(e)}")

    def _build_prompt(
        self,
        description: str,
        variant: str,
        experiences: List[str] = None
    ) -> str:
        """
        构建AI提示词

        Args:
            description: 写作描述
            variant: 变体类型
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

        # 根据变体类型调整风格
        if variant == "A":
            base_prompt += """**风格指导**：
- 采用正式、专业的语言风格
- 结构清晰，逻辑严谨
- 使用经典的总分总结构
- 语言简洁精炼

请直接输出文章内容。"""
        else:  # variant == "B"
            base_prompt += """**风格指导**：
- 采用亲切、生动的语言风格
- 结构灵活，可以使用故事化叙述
- 适当使用修辞手法和比喻
- 语言富有感染力

请直接输出文章内容。"""

        return base_prompt

    def _parse_response(self, content: str, variant: str) -> Dict[str, str]:
        """
        解析AI响应

        Args:
            content: AI生成的内容
            variant: 变体类型

        Returns:
            包含文章和元数据的字典
        """
        # 分析文章特征
        structure_type = "formal" if variant == "A" else "narrative"
        tone = "professional" if variant == "A" else "conversational"

        return {
            "content": content.strip(),
            "variant_type": variant,
            "structure_type": structure_type,
            "tone": tone,
            "style_params": json.dumps({
                "temperature": 0.7 if variant == "A" else 0.85,
                "formality": "high" if variant == "A" else "medium"
            })
        }

    async def summarize_experience(
        self,
        selected_articles: List[Dict],
        rejected_articles: List[Dict]
    ) -> str:
        """
        使用AI总结用户偏好经验

        Args:
            selected_articles: 用户选择的文章列表
            rejected_articles: 用户未选择的文章列表

        Returns:
            经验总结文本
        """
        if not selected_articles:
            return ""

        # 构建总结提示词
        prompt = """请分析以下用户选择的文章特征，总结用户的写作偏好。

**用户选择的文章特征**：
"""
        for i, article in enumerate(selected_articles[-5:], 1):  # 只看最近5次
            prompt += f"\n{i}. 结构类型: {article.get('structure_type', 'unknown')}, "
            prompt += f"语气: {article.get('tone', 'unknown')}"

        if rejected_articles:
            prompt += "\n\n**用户未选择的文章特征**：\n"
            for i, article in enumerate(rejected_articles[-5:], 1):
                prompt += f"\n{i}. 结构类型: {article.get('structure_type', 'unknown')}, "
                prompt += f"语气: {article.get('tone', 'unknown')}"

        prompt += """

请用1-2句话总结用户的偏好特点。格式如下：
用户倾向于选择[特征]的文章，偏好[风格]。"""

        try:
            response = Generation.call(
                model=self.model,
                prompt=prompt,
                max_tokens=200,
                temperature=0.3,
                result_format='message'
            )

            if response.status_code == 200:
                return response.output.choices[0].message.content.strip()
            else:
                return "无法生成经验总结"

        except Exception as e:
            print(f"总结经验时出错: {str(e)}")
            return ""
