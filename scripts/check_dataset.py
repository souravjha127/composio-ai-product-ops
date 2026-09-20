import pandas as pd

df = pd.read_csv("data/apps.csv")

print("Number of apps:", len(df))
print()

print("Columns:")
print(df.columns.tolist())
print()

print("Categories:")
print(df["category"].value_counts())
print()

print("Duplicate IDs:", df["id"].duplicated().sum())
print("Duplicate apps:", df["app"].duplicated().sum())
print()

print("Missing websites:", df["website"].isna().sum())
print("Missing docs:", df["docs_hint"].isna().sum())