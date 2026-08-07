import logging

import cudf

from cuml.compose import ColumnTransformer
from cuml.preprocessing import SimpleImputer, OneHotEncoder, StandardScaler
from cuml.pipeline import Pipeline

logger = logging.getLogger(__name__)

def create_gpu_training_pipeline(features: cudf.DataFrame, estimator) -> Pipeline:

    numeric_columns = list(features.select_dtypes(include="number").columns)
    categorical_columns = list(features.select_dtypes(include=["str", "category"]).columns)

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "encoder",
                OneHotEncoder(handle_unknown="ignore"),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                numeric_columns,
            ),
            (
                "categorical",
                categorical_pipeline,
                categorical_columns,
            ),
        ],
        remainder="drop",
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("estimator", estimator),
        ]
    )