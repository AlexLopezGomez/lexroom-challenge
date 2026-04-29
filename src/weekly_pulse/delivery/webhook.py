import httpx

from weekly_pulse.delivery.base import DeliveryChannel


class WebhookDelivery(DeliveryChannel):
    """Posts the formatted message as JSON to a Slack-compatible webhook."""

    def __init__(self, webhook_url: str, timeout: float) -> None:
        self._webhook_url = webhook_url
        self._timeout = timeout

    def deliver(self, message: str) -> None:
        """POST message to the webhook URL."""
        response = httpx.post(
            self._webhook_url, json={"text": message}, timeout=self._timeout
        )
        if not (200 <= response.status_code < 300):
            raise RuntimeError(
                f"Webhook delivery failed with status {response.status_code}"
            )
