"""Handler mixin package for WebAppService.

M70/M77/M78 decomposition trilogy:
  aggregate.py (937 lines) → candidates + corrections + reviewed_memory
"""
from app.handlers.candidates import CandidateHandlerMixin
from app.handlers.chat import ChatHandlerMixin
from app.handlers.corrections import CorrectionHandlerMixin
from app.handlers.feedback import FeedbackHandlerMixin
from app.handlers.preferences import PreferenceHandlerMixin
from app.handlers.reviewed_memory import ReviewedMemoryHandlerMixin

__all__ = [
    "CandidateHandlerMixin",
    "ChatHandlerMixin",
    "CorrectionHandlerMixin",
    "FeedbackHandlerMixin",
    "PreferenceHandlerMixin",
    "ReviewedMemoryHandlerMixin",
]
