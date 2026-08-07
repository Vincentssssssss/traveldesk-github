# Changelog

All notable changes to this project are documented in this file.

## [1.0.0] - 2026-08-06

### Added
- OpenAI-compatible LLM provider module with centralized environment configuration:
  - `OPENAI_API_KEY`
  - `OPENAI_BASE_URL`
  - `OPENAI_MODEL`
- Azure OpenAI endpoint normalization support for both:
  - `/openai/v1`
  - `/openai/v1/responses`
- Regression tests for LLM content parsing in `backend/tests/test_llm_provider.py`.

### Changed
- Replaced Anthropic-based integration with OpenAI Codex integration across:
  - Supervisor agent
  - Knowledge agent
  - Escalation agent
  - Customer interaction agent
- Switched backend dependency from `langchain-anthropic` to `langchain-openai`.
- Updated app version metadata to `1.0.0`.

### Fixed
- Fixed Azure Responses API compatibility issue where `response.content` could be a list of content blocks instead of a plain string, causing `json.loads(...)` failures in supervisor flow.
