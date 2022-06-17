import ast
import json

counter = 0
with open('outputs/users.jsonl', 'r', encoding='UTF-8') as f:
    for line in f:
        user = ast.literal_eval(line)
        if user['verified']:
            counter += 1
    print(counter)
# current with 7778 users is 11 verified
