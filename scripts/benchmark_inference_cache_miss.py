import time
import statistics
import httpx
import numpy as np


URL = "http://localhost:8000/inference/models/2/predict"
DELETE_CACHE_URL = "http://localhost:8001/inference/model_versions/model_cache"

REQUEST_BODY = {
    "input": {
                "gender": "Female",
                "study_time_hours": 4.0,
                "attendance_percent": 90.0,
                "sleep_hours": 8.5,
                "parental_education": "Masters",
                "internet_access": "Yes",
                "extracurricular_activities": "Yes",
                "part_time_job": "No",
                "previous_grade": 85.0
            }
}

TEST_COUNT = 20

def main():
    latencies = []

    with httpx.Client(timeout=30.0) as client:

        # 실제 측정
        print("benchmark start...")

        for i in range(TEST_COUNT):
            response  = client.delete(DELETE_CACHE_URL)
            response.raise_for_status()

            started_at = time.perf_counter()
            response = client.post(URL, json=REQUEST_BODY)
            elapsed_ms = (time.perf_counter() - started_at) * 1000

            response.raise_for_status()

            latencies.append(elapsed_ms)

            print(f"{i + 1:02d}: "f"{elapsed_ms:.2f} ms")

    print()
    print("=== Benchmark Result ===")
    print(f"count : {len(latencies)}")
    print(f"mean  : {statistics.mean(latencies):.2f} ms")
    print(f"p50   : {statistics.median(latencies):.2f} ms")
    print(f"p95   : {np.percentile(latencies, 95):.2f} ms")
    print(f"min   : {min(latencies):.2f} ms")
    print(f"max   : {max(latencies):.2f} ms")

if __name__ == "__main__":
    main()