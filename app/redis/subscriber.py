import asyncio
import json

from app.redis.client import redis_client
from app.redis.consts import TRAINING_BATCH_EVENTS_CHANNEL
from app.sse import event_store

# Redis Pub/Sub 객체 생성 → training-batch-events 채널 구독
def subscribe_training_batch_events():
    pubsub = redis_client.pubsub()
    pubsub.subscribe(TRAINING_BATCH_EVENTS_CHANNEL)

    return pubsub

# 메시지 대기 -> 변환 -> event_store.publish
def run_batch_event_subscriber(loop, stop_event):

    pubsub = subscribe_training_batch_events()

    try:
        while not stop_event.is_set():

            message = pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )

            if message is None:
                continue

            event = json.loads(message["data"])

            asyncio.run_coroutine_threadsafe(
                event_store.publish(event),
                loop,
            )

    finally:
        pubsub.close()