import logging
import os
import torch

log = logging.getLogger(__name__)

def pick_device(prefer: str = "auto") -> str:
    prefer = (prefer or "auto").lower()
    
    # CUDA (includes ROCm builds that expose torch.cuda)
    if prefer in ("auto", "cuda"):
        try:
            if torch.cuda.is_available():
                # Note: On ROCm builds, torch.version.hip is not None; API still uses "cuda"
                count = torch.cuda.device_count()
                name = torch.cuda.get_device_name(0)
                log.info(f"GPU detected: {name} (count={count})")
                return "cuda"
        except Exception as e:
            log.warning(f"CUDA check failed: {e}")

    # Apple Silicon MPS
    if prefer in ("auto", "mps"):
        try:
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                log.info("MPS detected (Apple Silicon)")
                return "mps"
        except Exception as e:
            log.warning(f"MPS check failed: {e}")

    log.info("Falling back to CPU")
    return "cpu" 