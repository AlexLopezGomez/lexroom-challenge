from weekly_pulse.delivery.base import DeliveryChannel


class ConsoleDelivery(DeliveryChannel):
    """Writes the formatted message to stdout."""

    def deliver(self, message: str) -> None:
        """Print message to stdout."""
        print(message)
