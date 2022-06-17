import pandas as pd

df = pd.read_csv("outputs/done.csv")
print(type(df[df['num_tweet'] == 200]), "VS.", len(df))
df[df['num_tweet'] == 200].to_csv("outputs/done3.csv", index=False)
