"""z.ai layout parsing (``glm-ocr``).

z.ai serves document OCR from a dedicated ``layout_parsing`` endpoint rather
than ``chat/completions``, returning Markdown text plus positional layout
elements. Everything else on this protocol is plain Chat Completions.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from .. import utils
from ..layout_parsing import LayoutElement, LayoutParsing
from .chat_completions import ChatCompletions

# Extensions the endpoint accepts as inline base64 input.
_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


class ZhipuLayout(ChatCompletions):
    def layout_parsing_url(self) -> str:
        return "layout_parsing"

    async def parse_layout(self, file: str, *, model: str, **options: Any) -> Any:
        payload = self.render_layout_payload(file, model=model, **options)
        response = await self.connection.post(self.layout_parsing_url(), payload)
        return self.parse_layout_response(response, model=model)

    def render_layout_payload(self, file: str, *, model: str, **options: Any) -> dict[str, Any]:
        return utils.compact(
            {
                "model": model,
                "file": self._encode_file(file),
                "return_crop_images": options.get("return_crop_images"),
                "need_layout_visualization": options.get("need_layout_visualization"),
                "start_page_id": options.get("start_page_id"),
                "end_page_id": options.get("end_page_id"),
                "request_id": options.get("request_id"),
                "user_id": options.get("user_id"),
            }
        )

    def parse_layout_response(self, response: Any, *, model: str) -> LayoutParsing:
        body = response.body or {}
        usage = body.get("usage") or {}
        details = usage.get("prompt_tokens_details") or {}
        data_info = body.get("data_info") or {}
        return LayoutParsing(
            text=body.get("md_results") or "",
            model=body.get("model") or model,
            id=body.get("id"),
            created=body.get("created"),
            elements=[LayoutElement(e) for e in body.get("layout_details") or []],
            visualization=body.get("layout_visualization"),
            page_count=data_info.get("num_pages"),
            pages=data_info.get("pages"),
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            cached_tokens=details.get("cached_tokens"),
        )

    @staticmethod
    def _encode_file(file: str) -> str:
        """Pass URLs and pre-encoded data through; read local paths as base64."""
        if file.startswith(("http://", "https://", "data:")):
            return file
        path = Path(file).expanduser()
        if not path.exists():
            return file
        mime = _MIME_TYPES.get(path.suffix.lower(), "application/octet-stream")
        encoded = base64.b64encode(path.read_bytes()).decode()
        return f"data:{mime};base64,{encoded}"
