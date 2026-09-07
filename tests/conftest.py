import sys
from unittest.mock import MagicMock

try:
    import torch  # noqa: F401
except ImportError:
    class FakeTensor:
        def __init__(self, *shape):
            self._shape = shape
            
        def size(self, dim):
            return self._shape[dim]
            
        def __getitem__(self, idx):
            return self

    mock_torch = MagicMock()
    mock_torch.zeros = lambda *shape: FakeTensor(*shape)
    mock_torch.Tensor = FakeTensor
    mock_torch.__version__ = "mocked"
    mock_torch.hub = MagicMock()
    mock_torch.hub.load.return_value = (MagicMock(), MagicMock())
    sys.modules["torch"] = mock_torch
    sys.modules["torchaudio"] = MagicMock()

try:
    import pyannote.audio  # noqa: F401
except ImportError:
    mock_pyannote = MagicMock()
    sys.modules["pyannote"] = mock_pyannote
    sys.modules["pyannote.audio"] = mock_pyannote
