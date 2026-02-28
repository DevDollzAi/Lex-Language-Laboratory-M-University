"""
XPII CHAIN Governance Module
Implements the Operator Control Mandate First Principles as executable code.

Principle 6: Governance Must Be Codified, Not Documented.
Principle 4: Identity is the Foundation of Trust.
Principle 7: Observability is Mandatory, Not Optional.
Principle 1: Human Authority is Non-Negotiable.
"""

import hashlib
import json
import threading
import uuid
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Principle 4 — Identity is the Foundation of Trust
# ---------------------------------------------------------------------------

class AgentIdentity:
    """
    Cryptographic, unique identity for an XPII CHAIN agent session.

    Every agent instance receives a globally unique identifier derived from
    a UUID4 seed.  The identity is prefixed with 'AGENT:' so it is always
    distinguishable from human-user identifiers.
    """

    AGENT_PREFIX = "AGENT"

    def __init__(self, name: str = "XPII-STAPLER"):
        self._name = name
        self._seed = str(uuid.uuid4())
        self._identity_hash = hashlib.sha256(
            f"{self.AGENT_PREFIX}:{name}:{self._seed}".encode("utf-8")
        ).hexdigest()
        self._created_at = datetime.now(timezone.utc).isoformat()
        self._revoked = False

    @property
    def identity_id(self) -> str:
        """Globally unique, cryptographic agent identity string."""
        return f"{self.AGENT_PREFIX}:{self._identity_hash[:16]}"

    @property
    def is_revoked(self) -> bool:
        return self._revoked

    def revoke(self) -> None:
        """Revoke this identity.  Revoked identities must not be trusted."""
        self._revoked = True

    def verify(self) -> bool:
        """
        Verify identity integrity.  Returns False if revoked or tampered.
        Deterministic check — no probabilistic inference (Principle 3).
        """
        if self._revoked:
            return False
        expected = hashlib.sha256(
            f"{self.AGENT_PREFIX}:{self._name}:{self._seed}".encode("utf-8")
        ).hexdigest()
        return self._identity_hash == expected

    def to_dict(self) -> dict:
        return {
            "identity_id": self.identity_id,
            "name": self._name,
            "created_at": self._created_at,
            "revoked": self._revoked,
        }


# ---------------------------------------------------------------------------
# Principle 7 — Observability is Mandatory, Not Optional
# ---------------------------------------------------------------------------

class AuditLog:
    """
    Append-only, in-process audit log.

    Once an entry is written it cannot be removed or modified (immutability
    is enforced by storing a running chain hash — each entry includes the
    SHA-256 of the previous entry, producing a tamper-evident chain).

    Principle 7 requirements addressed:
      - All agent actions logged with context.
      - Chain of Thought captured via the 'context' field.
      - Forensic analysis possible via export().
    """

    def __init__(self, agent_identity: AgentIdentity):
        self._agent_identity = agent_identity
        self._entries: list[dict] = []
        self._chain_hash = "GENESIS"
        self._lock = threading.Lock()

    def record(self, action: str, context: dict | None = None, outcome: str = "OK") -> dict:
        """
        Append an immutable entry to the audit log.

        Parameters
        ----------
        action:  Short action label (e.g. 'unpack', 'inject_metadata', 'pack').
        context: Dict of relevant context data for forensic purposes.
        outcome: 'OK' or a failure description.
        """
        with self._lock:
            entry = {
                "seq": len(self._entries),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_id": self._agent_identity.identity_id,
                "action": action,
                "context": context or {},
                "outcome": outcome,
                "prev_hash": self._chain_hash,
            }
            entry_bytes = json.dumps(entry, sort_keys=True).encode("utf-8")
            entry["entry_hash"] = hashlib.sha256(entry_bytes).hexdigest()
            self._chain_hash = entry["entry_hash"]
            self._entries.append(entry)
            return entry

    def verify_chain(self) -> bool:
        """
        Verify the integrity of the audit chain.
        Returns True only if no entries have been tampered with.
        """
        prev_hash = "GENESIS"
        for entry in self._entries:
            stored_entry_hash = entry["entry_hash"]
            entry_copy = {k: v for k, v in entry.items() if k != "entry_hash"}
            entry_bytes = json.dumps(entry_copy, sort_keys=True).encode("utf-8")
            computed = hashlib.sha256(entry_bytes).hexdigest()
            if computed != stored_entry_hash:
                return False
            if entry_copy["prev_hash"] != prev_hash:
                return False
            prev_hash = stored_entry_hash
        return True

    def export(self) -> list[dict]:
        """Return a snapshot of all audit entries (read-only copy)."""
        with self._lock:
            return list(self._entries)


# ---------------------------------------------------------------------------
# Principle 6 — Governance Must Be Codified, Not Documented
# Principle 3 — Probabilistic Systems Require Deterministic Guardrails
# ---------------------------------------------------------------------------

class PolicyEngine:
    """
    Deterministic, codified policy enforcement.

    Policies are defined as Python callables — not prose, not checklists.
    Each policy receives an action context dict and returns (allowed: bool,
    reason: str).  All policy decisions are logged to the audit trail.

    Built-in policies enforce the invariants from the First Principles
    document; additional policies can be registered at runtime.
    """

    def __init__(self, audit_log: AuditLog):
        self._audit_log = audit_log
        self._policies: dict[str, callable] = {}
        self._register_builtin_policies()

    # ------------------------------------------------------------------
    # Built-in policies (Principle 3: deterministic, unassailable)
    # ------------------------------------------------------------------

    def _policy_identity_must_be_valid(self, ctx: dict) -> tuple[bool, str]:
        identity: AgentIdentity | None = ctx.get("identity")
        if identity is None:
            return False, "No agent identity present in context."
        if not identity.verify():
            return False, f"Agent identity '{identity.identity_id}' is invalid or revoked."
        return True, "Identity verified."

    def _policy_no_empty_author(self, ctx: dict) -> tuple[bool, str]:
        author = ctx.get("author", "").strip()
        if not author:
            return False, "Author field must not be empty."
        return True, "Author field present."

    def _policy_no_path_traversal(self, ctx: dict) -> tuple[bool, str]:
        for key in ("input_path", "output_path"):
            path = ctx.get(key, "")
            if ".." in path:
                return False, f"Path traversal detected in '{key}': {path!r}."
        return True, "No path traversal detected."

    def _register_builtin_policies(self) -> None:
        self._policies["identity_must_be_valid"] = self._policy_identity_must_be_valid
        self._policies["no_empty_author"] = self._policy_no_empty_author
        self._policies["no_path_traversal"] = self._policy_no_path_traversal

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(self, name: str, policy_fn: callable) -> None:
        """Register an additional deterministic policy."""
        self._policies[name] = policy_fn

    def evaluate(self, action: str, ctx: dict) -> tuple[bool, list[str]]:
        """
        Evaluate all registered policies for the given action context.

        Returns (all_passed: bool, failure_reasons: list[str]).
        Result is logged to the immutable audit trail.
        """
        failures = []
        for name, policy_fn in self._policies.items():
            allowed, reason = policy_fn(ctx)
            if not allowed:
                failures.append(f"[POLICY:{name}] {reason}")

        all_passed = len(failures) == 0
        self._audit_log.record(
            action=f"policy_evaluate:{action}",
            context={"policy_count": len(self._policies), "failures": failures},
            outcome="ALLOWED" if all_passed else "DENIED",
        )
        return all_passed, failures


# ---------------------------------------------------------------------------
# Principle 1 — Human Authority is Non-Negotiable
# ---------------------------------------------------------------------------

class OperatorControl:
    """
    External operator kill-switch and human-in-the-loop gate.

    The kill switch is implemented outside agent logic — this object holds
    a threading.Event that any external caller can set to halt all operations.
    Per Principle 1: 'Kill switches must be external to agent code.'

    Usage:
        control = OperatorControl(audit_log)
        control.halt()          # operator triggers emergency stop
        control.assert_active() # raises RuntimeError if halted
    """

    def __init__(self, audit_log: AuditLog):
        self._audit_log = audit_log
        self._halt_event = threading.Event()

    @property
    def is_halted(self) -> bool:
        return self._halt_event.is_set()

    def halt(self, reason: str = "Operator emergency stop") -> None:
        """Signal all agent operations to cease immediately."""
        self._halt_event.set()
        self._audit_log.record(
            action="operator_halt",
            context={"reason": reason},
            outcome="HALTED",
        )

    def resume(self, reason: str = "Operator resumed operations") -> None:
        """Clear the halt signal (operator re-authorisation required)."""
        self._halt_event.clear()
        self._audit_log.record(
            action="operator_resume",
            context={"reason": reason},
            outcome="RESUMED",
        )

    def assert_active(self) -> None:
        """
        Raise RuntimeError if the operator has halted operations.
        Call this at the start of every agent action.
        """
        if self._halt_event.is_set():
            raise RuntimeError(
                "Operation blocked: operator kill-switch is active. "
                "Human authorization required to resume."
            )


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def create_governance_stack(agent_name: str = "XPII-STAPLER") -> tuple[
    AgentIdentity, AuditLog, PolicyEngine, OperatorControl
]:
    """
    Instantiate a fully-wired governance stack for a single agent session.

    Returns (identity, audit_log, policy_engine, operator_control).
    """
    identity = AgentIdentity(name=agent_name)
    audit_log = AuditLog(agent_identity=identity)
    policy_engine = PolicyEngine(audit_log=audit_log)
    operator_control = OperatorControl(audit_log=audit_log)
    return identity, audit_log, policy_engine, operator_control
