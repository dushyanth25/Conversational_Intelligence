import logging
from typing import Any, Dict, List

import torch

from .exceptions import VADInferenceError, VADModelLoadError

logger = logging.getLogger(__name__)


class SileroVADModel:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SileroVADModel, cls).__new__(cls)
            cls._instance._model = None
            cls._instance._utils = None
        return cls._instance

    def load(
        self, model_repo: str = "snakers4/silero-vad", force_reload: bool = False
    ):
        """Load the Silero VAD model into memory."""
        if self._model is not None and not force_reload:
            return

        logger.info(
            f"Loading VAD model from {model_repo}...",
            extra={"pipeline_module": "vad"},
        )
        try:
            # We use force_reload=False, torch hub caches it locally.
            self._model, utils = torch.hub.load(
                repo_or_dir=model_repo,
                model="silero_vad",
                force_reload=force_reload,
                trust_repo=True,
            )
            self._utils = utils
        except Exception as e:
            raise VADModelLoadError(f"Failed to load VAD model: {e}") from e

    def get_speech_timestamps(
        self, audio: torch.Tensor, sampling_rate: int = 16000, **kwargs
    ) -> List[Dict[str, Any]]:
        """Run inference and return raw timestamps in dict format."""
        if self._model is None or self._utils is None:
            raise VADModelLoadError("Model is not loaded. Call load() first.")

        try:
            (get_speech_timestamps, _, _, _, _) = self._utils
            # The get_speech_timestamps utility returns
            # [{'start': int, 'end': int}] (in samples)
            timestamps = get_speech_timestamps(
                audio, self._model, sampling_rate=sampling_rate, **kwargs
            )
            return timestamps
        except Exception as e:
            raise VADInferenceError(f"Inference failed: {e}") from e
