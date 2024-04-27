#%%
import pandas as pd

# Load csv data
df = pd.read_csv('video_data.csv')

# Create correctedUrl using format and replace username and id
df['correctedUrl'] = "https://www.tiktok.com/@" + df['author'].astype(str) + "/video/" + df['id'].astype(str)

print(df.columns)

#df.drop(columns=['Unnamed: 0'], inplace=True)

df.head()

df.to_csv('video_data.csv', index=False)
# %%
