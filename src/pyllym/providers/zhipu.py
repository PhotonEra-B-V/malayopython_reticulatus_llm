"""Zhipu AI GLM via the z.ai / BigModel API (OpenAI-compatible).

Default base is the international z.ai endpoint; set ``zhipu_api_base`` to
``https://open.bigmodel.cn/api/paas/v4`` for the China region. Serves the GLM
family (glm-5.3, glm-5.1, glm-4.6, ...) plus ``glm-ocr`` document layout
parsing, which z.ai exposes on its own ``layout_parsing`` endpoint.
"""

from __future__ import annotations

from ..protocols.zhipu_layout import ZhipuLayout
from .openai_compatible import OpenAICompatible


class Zhipu(OpenAICompatible):
    protocols = {"chat_completions": ZhipuLayout}
    default_protocol_name = "chat_completions"
    default_api_base = "https://api.z.ai/api/paas/v4"
    assume_models = True
