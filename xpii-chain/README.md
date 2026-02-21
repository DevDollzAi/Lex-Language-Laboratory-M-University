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
- **Local Assistant Agent**: An offline, rule-based assistant embedded in the UI to guide users through document submission workflows. No internet connection or external API required.

## Setup

### Prerequisites
- Python 3.10 or later
- `pip`

### Install dependencies
```bash
cd xpii-chain
pip install -r requirements.txt
```

### Run the application
```bash
python main.py
```

## Application Layout

### Document Tab
1. Click **SELECT DOCUMENT (.DOCX)** to load a `.docx` file.
2. Set the **AUTHOR** field (defaults to `XPII-CHAIN-PROVENANCE`).
3. Optionally enter a **SESSION ID** (auto-generated from timestamp if blank).
4. Click **EXECUTE STAPLE** and choose a save location.
5. The log panel shows real-time progress through all three pipeline phases.

### Assistant Tab
The embedded **Local Assistant Agent** is a deterministic, rule-based helper that runs entirely offline. It has knowledge of:
- Document submission steps
- Metadata field explanations (Author, Session ID)
- Unpack-Edit-Pack pipeline details
- Common errors and solutions
- Compliance framework alignment (EU AI Act, FINRA Rule 3110, NIST SP 800-53)

Type `help` in the chat input to see all available topics.

## Programmatic Usage
```python
from core.stapler import XPIIStapler

stapler = XPIIStapler()
stapler.unpack("research_report.docx")
stapler.inject_metadata(author="Axiom Hive", session_id="2025-XPII-001")
stapler.pack("research_report_stapled.docx")
```

## Compliance
XPII CHAIN supports: EU AI Act (Art. 12, 15, 19), FINRA Rule 3110, and NIST SP 800-53 Rev 5 AU-10.
