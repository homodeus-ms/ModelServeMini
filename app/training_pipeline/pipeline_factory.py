import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

def create_training_pipeline(features: pd.DataFrame, estimator) -> Pipeline:

    numeric_columns = list(features.select_dtypes(include="number").columns)
    categorical_columns = list(features.select_dtypes(include=["object", "category"]).columns)

    # impute : 결측값 처리, scaler : 값 표준화(평균 0, 표준편차 1)
    numeric_pipeline = Pipeline(
        steps=[("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])

    # encoder : 범주형 데이터를 숫자벡터로 변환
    categorical_pipeline = Pipeline(
        steps=[("imputer", SimpleImputer(strategy="most_frequent")), ("encoder", OneHotEncoder(handle_unknown="ignore"))])

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                numeric_columns
            ),
            (
                "categorical",
                categorical_pipeline,
                categorical_columns
            ),
        ],
        # 위에서 지정하지 않은 칼럼은 버림
        remainder="drop"
    )

    return Pipeline(steps=[("preprocessor", preprocessor), ("estimator", estimator)])

