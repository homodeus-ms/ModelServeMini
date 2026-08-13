import json
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.training_batch import repository as training_batch_repository
from app.domain.training_batch.exceptions import TrainingBatchNotFound
from app.sse import event_store

router = APIRouter(
    prefix="/training-batches",
    tags=["SSE"],
)

@router.get("/{training_batch_id}/events")
async def training_events(training_batch_id: UUID, db: Session = Depends(get_db)):

    training_batch = training_batch_repository.find_by_id(db, training_batch_id)
    if training_batch is None:
        raise TrainingBatchNotFound(training_batch_id)

    async def event_generator():
        try:
            if training_batch.status in { "SUCCEEDED", "FAILED", "CANCELLED"}:
                event = {
                    "training_batch_id": str(training_batch.id),
                    "status": training_batch.status,
                    "recommendation": training_batch.recommendation,
                }
                yield f"data: {json.dumps(event)}\n\n"

                return

            queue = event_store.subscribe(training_batch_id)

            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
                if event["status"] in {"SUCCEEDED", "FAILED", "CANCELLED"}:
                    break

        finally:
            event_store.unsubscribe(training_batch_id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
