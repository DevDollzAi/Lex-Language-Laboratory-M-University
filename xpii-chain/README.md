# XPII CHAIN: Deterministic Provenance Stapler

## Overview
XPII CHAIN is a lightweight, non-model-based post-processing system designed to embed deterministic provenance, cryptographic hashes, and authorship markers directly into the structural layers of digital documents (OOXML).

## The Stapler Paradigm
This component implements the **Unpack-Edit-Pack** pipeline:
1. **Unpack**: Decompresses `.docx` files to access the underlying XML DOM.
2. **Edit**: Injects metadata, RSIDs, and authorship tags into `core.xml` and `document.xml`.
3. **Pack**: Recompresses the archive with auto-repair protocols to ensure schema compliance.

## Key Features
- **Hardware-Agnostic**: Pure Python implementation with minimal dependencies.
- **Deterministic**: Bypasses probabilistic LLM generation for metadata embedding.
- **Zero Trust Ready**: Provides the forensic trail required for ZTA policy enforcement.

## Usage
```python
from core.stapler import XPIIStapler

stapler = XPIIStapler()
stapler.unpack("research_report.docx")
stapler.inject_metadata(author="Axiom Hive", session_id="2025-XPII-001")
stapler.pack("research_report_stapled.docx")
```
