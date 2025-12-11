"""Consumer worker for processing export requests.

Connects to RabbitMQ, listens for 'export:playlist' messages,
fetches playlist data, and sends it via email.
"""

import asyncio
import json
import logging
import sys
import traceback
from typing import Dict, Any

import aio_pika
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.services.mail_service import mail_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Consumer:
    def __init__(self):
        self.engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
        self.SessionLocal = async_sessionmaker(bind=self.engine)

    async def get_playlist_data(self, playlist_id: str) -> Dict[str, Any]:
        """Fetch playlist and songs data from database directly."""
        async with self.SessionLocal() as session:
            try:
                # Fetch Playlist Name
                query_playlist = text("SELECT id, name, owner FROM playlists WHERE id = :id")
                result_playlist = await session.execute(query_playlist, {"id": playlist_id})
                playlist = result_playlist.mappings().one_or_none()
                
                if not playlist:
                    raise ValueError(f"Playlist with ID {playlist_id} not found")

                # Fetch Songs in Playlist
                query_songs = text("""
                    SELECT s.id, s.title, s.performer
                    FROM songs s
                    JOIN playlist_songs ps ON s.id = ps.song_id
                    WHERE ps.playlist_id = :id
                """)
                result_songs = await session.execute(query_songs, {"id": playlist_id})
                songs = result_songs.mappings().all()

                return {
                    "playlist": {
                        "id": playlist["id"],
                        "name": playlist["name"],
                        "owner": playlist["owner"],  # Include owner for reference
                        "songs": [
                            {
                                "id": song["id"],
                                "title": song["title"],
                                "performer": song["performer"]
                            }
                            for song in songs
                        ]
                    }
                }
            except SQLAlchemyError as e:
                logger.error(f"Database error while fetching playlist {playlist_id}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error while fetching playlist {playlist_id}: {e}")
                raise

    async def process_message(self, message: aio_pika.IncomingMessage):
        """Process incoming RabbitMQ message."""
        # Ack happens via context manager *after* work completes to avoid
        # losing messages if email sending fails mid-flight.
        async with message.process():
            try:
                payload = json.loads(message.body.decode())
                playlist_id = payload["playlistId"]
                target_email = payload["targetEmail"]
                
                logger.info(f"Processing export for playlist {playlist_id} to {target_email}")
                
                # Get Data
                data = await self.get_playlist_data(playlist_id)
                
                # Format content
                content = json.dumps(data, indent=2)
                
                # Send Email
                await mail_service.send_email(
                    target_email=target_email,
                    subject=f"Export Playlist: {data['playlist']['name']}",
                    content=f"<pre>{content}</pre>"
                )
                
                logger.info(f"Successfully exported playlist {playlist_id}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in message: {e}")
            except KeyError as e:
                logger.error(f"Missing required field in message payload: {e}")
            except ValueError as e:
                logger.error(f"Value error in message processing: {e}")
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                # Message is acked by context manager, but logged. 
                # In prod, might want dlx.

    async def run(self):
        """Run the consumer loop."""
        logger.info("Connecting to RabbitMQ...")
        try:
            connection = await aio_pika.connect_robust(settings.RABBITMQ_SERVER)
            
            async with connection:
                channel = await connection.channel()
                queue = await channel.declare_queue("export:playlist", durable=True)
                
                logger.info("Waiting for messages...")
                await queue.consume(self.process_message)
                
                # Keep running
                await asyncio.Future()
        except Exception as e:
            logger.error(f"Error in consumer: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    consumer = Consumer()
    try:
        asyncio.run(consumer.run())
    except KeyboardInterrupt:
        logger.info("Consumer stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error in consumer: {e}", exc_info=True)
        sys.exit(1)
