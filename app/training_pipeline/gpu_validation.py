
import cudf
import numpy as np

def validate_gpu_features(features: cudf.DataFrame) -> None:

    if features.empty:
        raise ValueError("Dataset has no feature columns")

    unsupported_columns = []

    for column in features.columns:

        dtype = features[column].dtype

        if isinstance(dtype, cudf.CategoricalDtype):
            continue

        try:
            if np.issubdtype(dtype, np.number):
                continue
        except TypeError:
            pass

        if str(dtype) == "str":
            continue

        unsupported_columns.append(column)

    if unsupported_columns:
        raise ValueError(
            f"Unsupported feature columns: {unsupported_columns}"
        )