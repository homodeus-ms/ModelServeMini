import json
from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.sse import event_store

router = APIRouter(
    prefix="/training-batches",
    tags=["SSE"],
)

@router.get("/{training_batch_id}/events")
async def training_events(training_batch_id: UUID):

    queue = event_store.subscribe(training_batch_id)

    async def event_generator():
        try:
            while True:
                event = await queue.get()

                # yield - 청크단위로 실시간 전송
                yield (f"data: {json.dumps(event)}\n\n")

                if event["status"] in {
                    "SUCCEEDED",
                    "FAILED",
                    "CANCELLED",
                }:
                    break

        finally:
            event_store.unsubscribe(training_batch_id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
