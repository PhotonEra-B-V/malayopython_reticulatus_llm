# Changelog

## 1.16.0b1 (2026-09-08)

### Added

- **GLM-OCR document layout parsing** via z.ai. New `pyllym.parse_layout(file)`
  façade extracts Markdown text and positional layout elements from images and
  PDFs. z.ai serves `glm-ocr` from a dedicated `layout_parsing` endpoint rather
  than `chat/completions`, so this adds a `parse_layout` concern to the protocol
  layer (`Protocol.parse_layout` raises `NotImplementedError` by default) and a
  `ZhipuLayout` protocol implementing it. Returns a `LayoutParsing` with
  `.markdown`, `.elements` (each a `LayoutElement` carrying `label`, `bbox`,
  `content`), `.page_count` and token usage. Accepts URLs, `data:` URIs, and
  local paths (read and base64-encoded automatically). Configurable via
  `config.default_layout_parsing_model` (default `glm-ocr`).
- **GLM-5.3 and GLM-5.3-Flash** registered for the `zhipu` provider with real
  context/pricing metadata, so cost tracking and context-limit checks work
  rather than falling back to the assumed-model defaults. Both carry a
  1,048,576-token context window and 131,072 max output tokens. Aliases map
  `glm-5.3` / `glm-5.3-flash` across the `zhipu` and `openrouter` providers.

### Fixed

- **`models_schema.json` was not valid JSON Schema.** Four properties
  (`created_at`, `context_window`, `max_output_tokens`, `knowledge_cutoff`)
  declared `"type": ["null", {…}]`, but a `type` array may only contain type-name
  strings. Any attempt to validate the registry failed on the schema itself
  before reaching the data. Rewritten as `anyOf`, preserving the intent; the
  packaged registry now validates cleanly.

## 1.16.0a2 (2026-07-18)

### Added

- **MCP client support** (`mcp` extra). `pyllym.MCPServer.stdio(...)` /
  `.http(...)` connect to Model Context Protocol servers and adapt their tools
  into ordinary pyllym `Tool` objects (`MCPTool`) usable in the same agentic
  loop; `tools_from_session` adapts any live session. See the README's
  "MCP tools" section.

### Fixed

- **Transport errors are now always pyllym errors.** `Connection` no longer
  re-raises raw `aiohttp` / `TimeoutError` exceptions after retries are
  exhausted (or on non-retryable transport failures). They are wrapped in the
  new `pyllym.ConnectionFailedError` (a subclass of `pyllym.Error`), with the
  original exception preserved as `__cause__`. The same guarantee now covers
  streaming (`Connection.stream`), multipart uploads, and image/video URL
  downloads (`Image.ato_blob` / `Video.ato_blob`, which also map HTTP error
  statuses through the standard error hierarchy instead of raising
  `aiohttp.ClientResponseError`). Callers only ever need
  `except pyllym.Error`.

### Changed (wire payloads)

- **Gemini: system messages are sent as `systemInstruction`.** Previously
  system prompts were folded into `contents` as a `user` turn. They are now
  emitted via the API's first-class `systemInstruction` field (multiple system
  messages are concatenated); `contents` carries only user/assistant/tool
  turns.
- **OpenAI-compatible providers send the classic `system` role again.** The
  `developer` role is now only used for the OpenAI API itself (overridable
  back to `system` via `config.openai_use_system_role`). All other providers
  speaking the Chat Completions protocol — DeepSeek, Mistral, Ollama,
  OpenRouter, vLLM, GPUStack, `openai_compatible`, etc. — send `system`, which
  local/self-hosted servers actually accept. Custom providers can opt in via
  the `Provider.uses_developer_role()` classmethod.