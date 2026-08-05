import pandas as pd

df = pd.read_csv("../test_data/Teen_Mental_Health_Dataset.csv")

print(df["anxiety_level"].value_counts())
print(df["stress_level"].value_counts())
print(df["social_interaction_level"].value_counts())
print(df["addiction_level"].value_counts())
print(df["depression_label"].value_counts())