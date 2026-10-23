"""Explicit safety gate for legacy model demos; local product mode never calls it."""
import os

def require_model_opt_in():
    if os.getenv("DOUBLES_CHECK_ALLOW_MODEL_CREDITS") != "I_ACCEPT_POSSIBLE_CHARGES":
        raise RuntimeError(
            "Model requests are disabled to protect your credits. "
            "Use team.py or app.py for the credit-free local version. "
            "Do not enable legacy model requests without checking provider billing first."
        )
