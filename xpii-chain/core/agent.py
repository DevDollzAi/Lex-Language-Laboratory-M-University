"""
XPII CHAIN — Local Assistant Agent
A deterministic, rule-based assistant that runs entirely offline.
Provides guidance on document submission, metadata configuration,
and the Unpack-Edit-Pack provenance pipeline.

Grounding statement:
  All responses from this agent are derived from structured, static knowledge
  embedded at design time. This module does not use a stochastic language model,
  does not access the network, and produces no probabilistic outputs. Any topic
  outside the defined knowledge base is explicitly declared as out-of-scope.
"""

from __future__ import annotations

import re
from datetime import datetime


# ---------------------------------------------------------------------------
# Knowledge Base — grounded, structured, offline
# ---------------------------------------------------------------------------

_KB: list[tuple[list[str], str]] = [
    # --- Greetings ---
    (
        ["hello", "hi", "hey", "greetings", "good morning", "good afternoon"],
        "Hello! I am the XPII CHAIN Local Assistant. I can help you with:\n"
        "  • Selecting and submitting documents\n"
        "  • Configuring provenance metadata (Author, Session ID)\n"
        "  • Understanding the Unpack-Edit-Pack pipeline\n"
        "  • Troubleshooting stapler errors\n\n"
        "Type a question to get started.",
    ),
    # --- What is XPII CHAIN ---
    (
        ["what is xpii", "what does xpii", "explain xpii", "about xpii", "xpii chain"],
        "XPII CHAIN is a deterministic provenance stapler for OOXML documents (.docx).\n\n"
        "It embeds authorship, session identifiers, and forensic markers directly\n"
        "into the XML structure of a document — without relying on any probabilistic\n"
        "AI model. Every output is mathematically reproducible given the same inputs.\n\n"
        "Use cases: legal record-keeping, compliance (EU AI Act Art. 12/15/19,\n"
        "FINRA Rule 3110, NIST SP 800-53 Rev 5 AU-10), and zero-trust environments.",
    ),
    # --- How to submit a document ---
    (
        ["how to submit", "submit document", "how do i submit", "upload", "select file",
         "select document", "open file", "choose file"],
        "To submit a document for provenance stapling:\n\n"
        "  1. Click  [ SELECT DOCUMENT (.DOCX) ]  in the 'Document' tab.\n"
        "  2. Browse to your .docx file and confirm the selection.\n"
        "     The filename will turn GREEN when a valid file is loaded.\n"
        "  3. Fill in the AUTHOR field (defaults to 'XPII-CHAIN-PROVENANCE').\n"
        "  4. Optionally enter a SESSION ID — if left blank, one is auto-generated\n"
        "     from the current timestamp (YYYYMMDDHHMMSS).\n"
        "  5. Click  [ EXECUTE STAPLE ]  and choose a save location.\n"
        "     The log panel will show each phase in real time.",
    ),
    # --- Author field ---
    (
        ["author", "what is author", "author field"],
        "The AUTHOR field embeds your identity into the document's core.xml metadata\n"
        "(dc:creator element). It serves as the forensic record of who processed\n"
        "the document through the XPII CHAIN pipeline.\n\n"
        "Best practice: use a consistent, unique identifier such as your organisation\n"
        "name, a user handle, or an employee ID. Example: 'Axiom-Hive-Legal-QA'.",
    ),
    # --- Session ID ---
    (
        ["session id", "session", "what is session"],
        "The SESSION ID is a unique token embedded into the dc:description element\n"
        "of core.xml. It ties a specific document to a specific processing session,\n"
        "enabling audit trails and chain-of-custody verification.\n\n"
        "Format recommendation: <YEAR>-<PROJECT>-<SEQ>, e.g. '2026-XPII-001'.\n"
        "If left blank, the system generates a timestamp-based ID automatically.",
    ),
    # --- Pipeline / phases ---
    (
        ["pipeline", "phases", "unpack", "edit", "pack", "staple", "how does it work",
         "how it works", "process"],
        "The Unpack-Edit-Pack pipeline has three phases:\n\n"
        "  Phase 1 — UNPACK\n"
        "    The .docx file (a ZIP archive) is decompressed into a temporary\n"
        "    directory, exposing the underlying XML components.\n\n"
        "  Phase 2 — EDIT (XML DOM injection)\n"
        "    Targeted edits are made to:\n"
        "      • docProps/core.xml  — author and session identifier\n"
        "      • word/document.xml  — structural markers (w:ins/w:del)\n"
        "      • word/settings.xml  — Revision Save IDs (RSIDs)\n\n"
        "  Phase 3 — PACK (auto-repair)\n"
        "    The modified XML is recompressed into a new .docx archive with\n"
        "    schema-compliant ZIP_DEFLATED compression. The temp directory is\n"
        "    then removed.",
    ),
    # --- Output file ---
    (
        ["output", "where is", "save", "saved file", "find the file"],
        "When you click EXECUTE STAPLE, a save dialog appears. You choose the\n"
        "location and filename for the output. The default name is:\n\n"
        "    stapled_<original_filename>.docx\n\n"
        "The stapled file is a fully valid .docx that can be opened in Microsoft\n"
        "Word, LibreOffice, or any OOXML-compatible application.",
    ),
    # --- Errors ---
    (
        ["error", "failed", "not working", "crash", "problem", "issue", "bug"],
        "Common errors and solutions:\n\n"
        "  • 'No such file' — The source file was moved or deleted after selection.\n"
        "    Re-select the document.\n\n"
        "  • 'Permission denied' — The output directory is read-only.\n"
        "    Choose a writable location (e.g. your Desktop or Documents folder).\n\n"
        "  • 'Bad ZIP file' — The .docx is corrupted. Open and re-save it in Word\n"
        "    or LibreOffice first, then retry.\n\n"
        "  • XML parse error — The document contains non-standard markup. The\n"
        "    auto-repair phase will attempt recovery; if it fails, re-export the\n"
        "    document from its source application.",
    ),
    # --- Compliance ---
    (
        ["compliance", "regulation", "legal", "eu ai act", "finra", "nist", "audit",
         "zero trust", "zta"],
        "XPII CHAIN is designed to support the following compliance frameworks\n"
        "(source: official regulatory texts — no unverified claims are made):\n\n"
        "  • EU AI Act (2024/1689) — Articles 12, 15, 19\n"
        "    Traceability, accuracy, and transparency obligations for AI systems.\n\n"
        "  • FINRA Rule 3110 — Supervision and record-keeping requirements.\n\n"
        "  • NIST SP 800-53 Rev 5 — Control AU-10 (Non-repudiation).\n\n"
        "The embedded metadata provides the forensic trail required by these\n"
        "frameworks without altering the visible content of the document.",
    ),
    # --- Help / commands ---
    (
        ["help", "commands", "what can you do", "options", "topics"],
        "I can answer questions on these topics:\n\n"
        "  • 'what is xpii chain'    — overview of the system\n"
        "  • 'how to submit'         — document submission steps\n"
        "  • 'author'                — the Author metadata field\n"
        "  • 'session id'            — the Session ID field\n"
        "  • 'pipeline' or 'phases'  — Unpack-Edit-Pack details\n"
        "  • 'output'                — where the stapled file is saved\n"
        "  • 'error'                 — common errors and solutions\n"
        "  • 'compliance'            — regulatory alignment\n\n"
        "Type any of the above keywords to get started.",
    ),
]

_FALLBACK = (
    "I don't have a verified answer for that topic in my current knowledge base.\n\n"
    "Please type 'help' to see what I can assist with, or consult the project\n"
    "documentation in the docs/ directory for detailed technical reference.\n\n"
    "(Note: This assistant is rule-based and offline. It does not generate\n"
    "speculative or probabilistic responses.)"
)


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------

class LocalAssistantAgent:
    """
    Deterministic, rule-based assistant for the XPII CHAIN application.

    All responses are derived from the structured knowledge base defined
    above. No network calls, no probabilistic model, no external APIs.
    """

    def __init__(self) -> None:
        self._history: list[tuple[str, str]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def respond(self, user_input: str) -> str:
        """
        Return a deterministic response for the given user input.

        Parameters
        ----------
        user_input : str
            Raw text from the user.

        Returns
        -------
        str
            A grounded, rule-based response.
        """
        normalised = self._normalise(user_input)
        answer = self._match(normalised)
        timestamp = datetime.now().strftime("%H:%M:%S")
        response = f"[{timestamp}] AGENT > {answer}"
        self._history.append((user_input, response))
        return response

    @property
    def history(self) -> list[tuple[str, str]]:
        """Return the conversation history as (user_input, agent_response) pairs."""
        return list(self._history)

    def clear_history(self) -> None:
        """Reset the conversation history."""
        self._history.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(text: str) -> str:
        """Lowercase, strip punctuation, collapse whitespace."""
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _match(normalised: str) -> str:
        """
        Scan the knowledge base for the best keyword match.
        Returns the fallback message when no match is found.
        """
        best_entry: str | None = None
        best_score = 0

        for keywords, response in _KB:
            score = sum(1 for kw in keywords if kw in normalised)
            if score > best_score:
                best_score = score
                best_entry = response

        return best_entry if best_score > 0 else _FALLBACK
