"""Producer service for publishing messages to RabbitMQ.

Handles connection to RabbitMQ using aio-pika and publishing messages
to the 'export:playlist' queue.
"""

import json
import aio_pika
from app.core.config import settings


class ProducerService:
    """Service for sending messages to RabbitMQ."""

    async def send_message(self, queue_name: str, message: dict) -> bool:
        """Send a JSON message to the specified queue.

        Args:
            queue_name: Name of the target queue.
            message: Dictionary containing the message payload.

        Returns:
            True if successful.

        Raises:
            Exception: If connection or publishing fails.
        """
        connection = await aio_pika.connect_robust(settings.RABBITMQ_SERVER)
        
        async with connection:
            channel = await connection.channel()
            
            # Declare queue (durable=True for persistence)
            queue = await channel.declare_queue(queue_name, durable=True)
            
            # Publish message
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    content_type="application/json"
                ),
                routing_key=queue_name,
            )
            
            return True


# Singleton instance
producer_service = ProducerService()
