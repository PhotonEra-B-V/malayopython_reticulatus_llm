"""Document layout parsing (OCR).

Extracts text and layout structure from images and PDFs via a provider's
dedicated document-parsing endpoint (z.ai's ``glm-ocr``). Unlike vision chat,
the response carries positional layout elements alongside the Markdown text.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from . import models as _models

if TYPE_CHECKING:
    from .context import Context


class LayoutElement:
    """One recognized block on the page."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.index = data.get("index")
        self.label = data.get("label")
        self.bbox = data.get("bbox_2d")
        self.content = data.get("content")
        self.height = data.get("height")
        self.width = data.get("width")

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "label": self.label,
            "bbox_2d": self.bbox,
            "content": self.content,
            "height": self.height,
            "width": self.width,
        }

    def __repr__(self) -> str:
        return f"LayoutElement(index={self.index!r}, label={self.label!r})"


class LayoutParsing:
    def __init__(self, *, text: str, model: str, **attributes: Any) -> None:
        self.text = text
        self.model = model
        self.id = attributes.get("id")
        self.created = attributes.get("created")
        self.elements: list[LayoutElement] = attributes.get("elements") or []
        self.visualization = attributes.get("visualization")
        self.page_count = attributes.get("page_count")
        self.pages = attributes.get("pages")
        self.input_tokens = attributes.get("input_tokens")
        self.output_tokens = attributes.get("output_tokens")
        self.cached_tokens = attributes.get("cached_tokens")

    @property
    def markdown(self) -> str:
        return self.text

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"LayoutParsing(model={self.model!r}, elements={len(self.elements)})"


async def parse_layout(
    file: str,
    *,
    model: str | None = None,
    provider: str | None = None,
    assume_model_exists: bool = False,
    context: Context | None = None,
    **options: Any,
) -> LayoutParsing:
    from . import config as _config

    cfg = context.config if context else _config()
    model = model or cfg.default_layout_parsing_model
    model_info, provider_instance = _models.resolve(
        model, provider=provider, assume_exists=assume_model_exists, config=cfg
    )
    return await provider_instance.parse_layout(file, model=model_info.id, **options)
