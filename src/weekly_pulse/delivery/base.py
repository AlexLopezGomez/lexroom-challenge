from abc import ABC, abstractmethod


class DeliveryChannel(ABC):
    """Abstract base for all delivery channels."""

    @abstractmethod
    def deliver(self, message: str) -> None:
        """Deliver a formatted message to its destination."""
