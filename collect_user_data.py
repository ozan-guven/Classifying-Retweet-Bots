import csv
from io import TextIOWrapper
from typing import Generator
import twarc
import config
import pandas as pd
import numpy as np

#twarc2 = twarc.Twarc2(bearer_token=config.BEARER_TOKEN, metadata=False)
twarc2 = twarc.Twarc2(consumer_key=config.CONSUMER_KEY, consumer_secret=config.CONSUMER_SECRET, access_token=config.ACCESS_TOKEN, access_token_secret=config.ACCESS_SECRET, metadata=False)

def write_user(author_ids: list[int], f: TextIOWrapper, counter: list[int], csv_writer) -> None:
    gen: Generator[dict] = twarc2.user_lookup(author_ids)
    for data in gen:
        if 'data' in data:
            for profile in data['data']:
                print(counter[0], 'success')
                counter[0] += 1
                f.write(f"{profile}\n")
                csv_writer.writerow([profile['id'], 1])
        if 'errors' in data:
            for error in data['errors']:
                print(counter[0], 'error')
                counter[0] += 1
                csv_writer.writerow([error['resource_id'], 0])
            
with open('outputs/users.jsonl', 'w', encoding='UTF-8') as f, open('outputs/contains_profile_info.csv', 'w', newline='') as p:
    csv_writer = csv.writer(p)
    csv_writer.writerow(['author_id', 'has_profile_info'])

    counter = [0]
    while_called = [0]
    df = pd.read_csv("outputs/done3.csv")
    authors = df['author_id'].to_numpy()

    write_user(authors, f, counter, csv_writer)
# got user data from done3.csv up to line 7895, i.e. user 7894