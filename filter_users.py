import numpy as np
import pandas as pd
import ast
import json
# new_outputs/users.jsonl
def filter_users(input_file_name: str, output_file_name: str, user_csv: str) -> None:
    users_dict = {}
    with open(input_file_name, "r", encoding="UTF-8") as users:
        for line in users:
            user_dict = ast.literal_eval(line)
            users_dict[str(user_dict["id"])] = user_dict

    df = pd.read_csv(user_csv, usecols=["author_id","rt_ratio"], dtype={"author_id": str, "rt_ratio": float})
    rates = df.to_numpy()
    user_rt_dict = {}
    for line in rates:
        user_rt_dict[line[0]] = line[1]
    
    with open(output_file_name, "w", encoding="UTF-8") as new_users:
        counter = 0
        for id, user in users_dict.items():
            if user_rt_dict[id] >= 0.8:
                new_users.write(json.dumps(user, ensure_ascii=False).encode('utf8').decode('utf8')+"\n")
                counter += 1
        print(f"{counter} written.")

filter_users("new_outputs/users.jsonl", "new_outputs/filtered_users.jsonl", "new_outputs/user_ratio.csv")