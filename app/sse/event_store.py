import asyncio
from uuid import UUID

_subscribers: dict[str, list[asyncio.Queue]] = {}

def subscribe(training_batch_id: UUID) -> asyncio.Queue:
    queue = asyncio.Queue()
    key = str(training_batch_id)

    # 키 없으면 빈리스트 추가후 append
    _subscribers.setdefault(key, []).append(queue)
    return queue

def unsubscribe(training_batch_id: UUID, queue: asyncio.Queue) -> None:
    key = str(training_batch_id)
    queues = _subscribers.get(key)

    if queues is None:
        return

    if  queue in queues:
        queues.remove(queue)

    if not queues:
        _subscribers.pop(key, None)

async def publish(event: dict) -> None:
    key = event["training_batch_id"]
    queues =_subscribers.get(key, [])

    for queue in queues:
        await queue.put(event)