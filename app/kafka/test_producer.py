from app.kafka.producer import publish_training_job

for job_id in range(1, 31):
    publish_training_job(job_id)