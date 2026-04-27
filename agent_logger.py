import json
import logging
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")


class AgentLogger:
    def __init__(self):
        self.steps = []
        self._ensure_log_dir()
        self._file_logger = self._setup_file_logger()

    def _ensure_log_dir(self):
        os.makedirs(LOG_DIR, exist_ok=True)

    def _setup_file_logger(self):
        logger = logging.getLogger("agent_workflow")
        logger.setLevel(logging.DEBUG)
        if not logger.handlers:
            fh = logging.FileHandler(
                os.path.join(LOG_DIR, "agent_steps.log"), encoding="utf-8"
            )
            fh.setLevel(logging.DEBUG)
            fmt = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            fh.setFormatter(fmt)
            logger.addHandler(fh)
        return logger

    def log_step(self, step_name, agent_phase, details, decision_rationale=None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step_name,
            "phase": agent_phase,
            "details": details,
            "decision_rationale": decision_rationale,
        }
        self.steps.append(entry)
        self._file_logger.info(
            f"[{agent_phase}] {step_name}: {json.dumps(details, default=str)[:200]}"
        )
        if decision_rationale:
            self._file_logger.debug(f"  Rationale: {decision_rationale}")
        return entry

    def get_steps(self):
        return list(self.steps)

    def get_steps_for_display(self):
        display = []
        for entry in self.steps:
            phase_labels = {
                "PLAN": "1. Plan",
                "ACT": "2. Act",
                "CHECK": "3. Check",
                "REFLECT": "4. Reflect",
            }
            display.append(
                {
                    "phase": phase_labels.get(entry["phase"], entry["phase"]),
                    "step": entry["step"],
                    "summary": json.dumps(entry["details"], default=str)[:120],
                    "rationale": entry.get("decision_rationale"),
                }
            )
        return display

    def clear(self):
        self.steps = []


_agent_logger = None


def get_agent_logger():
    global _agent_logger
    if _agent_logger is None:
        _agent_logger = AgentLogger()
    return _agent_logger
