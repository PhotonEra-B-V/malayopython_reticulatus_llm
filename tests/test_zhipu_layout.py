"""GLM-OCR document layout parsing via z.ai's ``layout_parsing`` endpoint."""

from __future__ import annotations

import base64

import pytest

import pyllym

from .conftest import sent_json, sent_requests

URL = "https://api.z.ai/api/paas/v4/layout_parsing"

PAYLOAD = {
    "id": "task-123",
    "created": 1757000000,
    "model": "glm-ocr",
    "md_results": "# Invoice\n\nTotal: $42.00",
    "layout_details": [
        {
            "index": 0,
            "label": "title",
            "bbox_2d": [10, 10, 200, 40],
            "content": "Invoice",
            "height": 30,
            "width": 190,
        }
    ],
    "data_info": {"num_pages": 2, "pages": [{"page_id": 0}, {"page_id": 1}]},
    "usage": {
        "prompt_tokens": 1200,
        "completion_tokens": 300,
        "prompt_tokens_details": {"cached_tokens": 100},
        "total_tokens": 1500,
    },
}


@pytest.mark.asyncio
async def test_parse_layout_returns_text_and_elements(mock_http):
    mock_http.post(URL, payload=PAYLOAD)

    result = await pyllym.parse_layout("https://cdn.example.com/invoice.pdf", provider="zhipu")

    assert sent_requests(mock_http)
    assert result.text == "# Invoice\n\nTotal: $42.00"
    assert result.markdown == result.text
    assert str(result) == result.text
    assert result.model == "glm-ocr"
    assert result.id == "task-123"
    assert result.page_count == 2

    (element,) = result.elements
    assert element.label == "title"
    assert element.bbox == [10, 10, 200, 40]
    assert element.content == "Invoice"
    assert element.to_dict()["index"] == 0


@pytest.mark.asyncio
async def test_parse_layout_reports_usage(mock_http):
    mock_http.post(URL, payload=PAYLOAD)

    result = await pyllym.parse_layout("https://cdn.example.com/invoice.pdf", provider="zhipu")

    assert result.input_tokens == 1200
    assert result.output_tokens == 300
    assert result.cached_tokens == 100


@pytest.mark.asyncio
async def test_parse_layout_defaults_to_glm_ocr_and_omits_unset_options(mock_http):
    mock_http.post(URL, payload=PAYLOAD)

    await pyllym.parse_layout("https://cdn.example.com/invoice.pdf", provider="zhipu")

    sent = sent_json(mock_http)
    assert '"model": "glm-ocr"' in sent
    # compact() drops unset options rather than sending nulls
    assert "start_page_id" not in sent
    assert "need_layout_visualization" not in sent


@pytest.mark.asyncio
async def test_parse_layout_forwards_page_range_options(mock_http):
    mock_http.post(URL, payload=PAYLOAD)

    await pyllym.parse_layout(
        "https://cdn.example.com/invoice.pdf",
        provider="zhipu",
        start_page_id=2,
        end_page_id=5,
        need_layout_visualization=True,
    )

    sent = sent_json(mock_http)
    assert '"start_page_id": 2' in sent
    assert '"end_page_id": 5' in sent
    assert '"need_layout_visualization": true' in sent


@pytest.mark.asyncio
async def test_parse_layout_encodes_local_file_as_data_uri(mock_http, tmp_path):
    mock_http.post(URL, payload=PAYLOAD)
    document = tmp_path / "scan.png"
    document.write_bytes(b"\x89PNG\r\n\x1a\nFAKE")

    await pyllym.parse_layout(str(document), provider="zhipu")

    expected = base64.b64encode(b"\x89PNG\r\n\x1a\nFAKE").decode()
    sent = sent_json(mock_http)
    assert f"data:image/png;base64,{expected}" in sent


@pytest.mark.asyncio
async def test_parse_layout_passes_urls_through_unchanged(mock_http):
    mock_http.post(URL, payload=PAYLOAD)

    await pyllym.parse_layout("https://cdn.example.com/invoice.pdf", provider="zhipu")

    assert '"file": "https://cdn.example.com/invoice.pdf"' in sent_json(mock_http)


@pytest.mark.asyncio
async def test_parse_layout_unsupported_provider_raises():
    with pytest.raises(NotImplementedError, match="layout parsing"):
        await pyllym.parse_layout("https://x/y.pdf", model="gpt-5.4", provider="openai")


def test_glm_ocr_is_registered_with_pricing():
    info = pyllym.models.find("glm-ocr", "zhipu")
    assert info.name == "GLM-OCR"
    standard = info.pricing.text_tokens.standard
    assert standard.input_per_million == 0.03
    assert standard.output_per_million == 0.03
    assert "pdf" in info.modalities.input
