"""
Government Contracting Processors Package (Branch #072)

Multimodal processing is now handled by RAGAnything's native library processors:
  TableModalProcessor, ImageModalProcessor, EquationModalProcessor

GovCon domain knowledge is injected via RAGAnything's prompt registry:
  register_prompt_language("govcon", GOVCON_MULTIMODAL_PROMPTS)
  set_prompt_language("govcon")

See prompts/multimodal/govcon_multimodal_prompts.py for all govcon prompt overrides.
See src/server/initialization.py for processor registration.
"""
