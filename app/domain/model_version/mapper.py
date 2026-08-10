
from app.domain.model_version.schema import ModelVersionCache


def model_version_to_cache_dto(model_version) -> ModelVersionCache:

    return ModelVersionCache(
        id=model_version.id,
        model_id=model_version.model_id,
        algorithm=model_version.algorithm,
        artifact_uri=model_version.artifact_uri,
        input_schema=model_version.input_schema,
    )