import csv
import random
from pathlib import Path

OUTPUT_FILE = Path("../test_data/churn_dataset.csv")
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

LINE_SIZE = 200

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    writer.writerow([
        "age",
        "income",
        "experience_years",
        "churn"
    ])

    for _ in range(LINE_SIZE):
        age = random.randint(20, 60)

        experience = max(
            0,
            age - 22 + random.randint(-3, 3)
        )

        income = (
            2500
            + experience * 350
            + random.randint(-500, 500)
        )

        churn = 1 if income < 4500 else 0

        writer.writerow([
            age,
            income,
            experience,
            churn
        ])

print(f"Created: {OUTPUT_FILE}")