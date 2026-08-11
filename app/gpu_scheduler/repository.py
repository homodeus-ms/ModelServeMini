import json

from app.redis.client import redis_client
from app.gpu_scheduler.schema import GpuTaskType


OWNER_KEY = "gpu:scheduler:owner"
WAITING_KEY = "gpu:scheduler:waiting"
WAITING_IDS_KEY = "gpu:scheduler:waiting:ids"
SEQUENCE_KEY = "gpu:scheduler:sequence"

SCORE_SEQUENCE_RANGE = 1_000_000_000


def get_owner() -> dict | None:
    owner = redis_client.get(OWNER_KEY)

    if owner is None:
        return None

    return json.loads(owner)


def try_set_owner(task_id: str, task_type: GpuTaskType, priority: int) -> bool:

    payload = json.dumps(
        {
            "task_id": task_id,
            "task_type": task_type.value,
            "priority": priority,
        }
    )

    # nx=True : OWNER_KEY에 대해 원자적으로 동작함
    result = redis_client.set(OWNER_KEY, payload, nx=True)

    return bool(result)


def update_owner(task_id: str, task_type: GpuTaskType, priority: int) -> None:

    payload = json.dumps(
        {
            "task_id": task_id,
            "task_type": task_type.value,
            "priority": priority,
        }
    )

    redis_client.set(OWNER_KEY, payload)

def clear_owner() -> None:
    redis_client.delete(OWNER_KEY)

def next_sequence() -> int:
    return redis_client.incr(SEQUENCE_KEY)

def add_waiting_task(task_id: str, task_type: GpuTaskType, priority: int) -> None:
    sequence = next_sequence()

    payload = {
        "task_id": task_id,
        "task_type": task_type.value,
        "priority": priority,
        "sequence": sequence,
    }

    serialized_payload = json.dumps(payload)

    score = priority * SCORE_SEQUENCE_RANGE + sequence

    # Priority Queue
    redis_client.zadd(WAITING_KEY, { serialized_payload: score})

    # task_id 중복 확인용
    redis_client.sadd(WAITING_IDS_KEY, task_id)


def get_waiting_tasks() -> list[dict]:
    members = redis_client.zrange(WAITING_KEY, 0, -1)
    return [ json.loads(member) for member in members ]

def pop_next_waiting_task() -> dict | None:

    result = redis_client.zpopmin(WAITING_KEY, count=1)

    if not result:
        return None

    member, _score = result[0]

    task = json.loads(member)

    # ZSET에서 빠졌으므로 중복확인 SET에서도 제거
    redis_client.srem(WAITING_IDS_KEY, task["task_id"])

    return task


def is_waiting(task_id: str) -> bool:
    return bool(redis_client.sismember(WAITING_IDS_KEY, task_id))

def get_highest_priority_waiting_task() -> dict | None:

    members = redis_client.zrange(WAITING_KEY, 0, 0)
    if not members:
        return None
    return json.loads(members[0])


_RELEASE_SCRIPT = """
local owner = redis.call("GET", KEYS[1])
if not owner then return nil
end

local owner_obj = cjson.decode(owner)
if owner_obj["task_id"] ~= ARGV[1] then return false
end

local next_items = redis.call("ZPOPMIN", KEYS[2], 1)
if #next_items == 0 then redis.call("DEL", KEYS[1]) return ""
end

local next_payload = next_items[1]
local next_task = cjson.decode(next_payload)
redis.call("SREM", KEYS[3], next_task["task_id"])

local next_owner = cjson.encode({
    task_id = next_task["task_id"],
    task_type = next_task["task_type"],
    priority = next_task["priority"]
})

redis.call("SET", KEYS[1], next_owner)

return next_payload
"""


def release_and_assign_next(task_id: str) -> tuple[bool, dict | None]:

    result = redis_client.eval(
        _RELEASE_SCRIPT,
        3,  # 뒤의 key 갯수
        OWNER_KEY,
        WAITING_KEY,
        WAITING_IDS_KEY,
        task_id,
    )

    # owner 없음
    if result is None:
        return False, None

    # task_id가 현재 owner와 다름
    if result is False:
        return False, None

    # 정상 release + 다음 작업 없음
    if result == "":
        return True, None

    # 다음 작업이 owner로 승격됨
    next_task = json.loads(result)
    return True, next_task


_ACQUIRE_SCRIPT = """
local owner = redis.call("GET", KEYS[1])

-- 이미 owner가 있다면
if owner then
    local owner_obj = cjson.decode(owner)

    -- 내가 이미 owner면 그대로 성공
    if owner_obj["task_id"] == ARGV[1] then return "GRANTED"
    end

    -- 이미 waiting queue에 있으면 중복 등록 안 함
    local is_waiting = redis.call("SISMEMBER", KEYS[3], ARGV[1])
    if is_waiting == 1 then return "WAITING"
    end

    -- 새로운 sequence 발급, 대기열로
    local sequence = redis.call("INCR", KEYS[4])
    local priority = tonumber(ARGV[3])

    local payload = cjson.encode({
        task_id = ARGV[1],
        task_type = ARGV[2],
        priority = priority,
        sequence = sequence
    })

    local score = priority * tonumber(ARGV[4]) + sequence

    redis.call("ZADD", KEYS[2], score, payload)
    redis.call("SADD", KEYS[3], ARGV[1])
    return "WAITING"
end

-- owner가 없으면 현재 task가 바로 owner 획득
local new_owner = cjson.encode({task_id = ARGV[1], task_type = ARGV[2], priority = tonumber(ARGV[3])})

redis.call("SET", KEYS[1], new_owner)

return "GRANTED"
"""

def acquire_or_enqueue(task_id: str, task_type: GpuTaskType, priority: int) -> bool:

    result = redis_client.eval(
        _ACQUIRE_SCRIPT,
        4,
        OWNER_KEY,
        WAITING_KEY,
        WAITING_IDS_KEY,
        SEQUENCE_KEY,
        task_id,
        task_type.value,
        priority,
        SCORE_SEQUENCE_RANGE,
    )

    return result == "GRANTED"