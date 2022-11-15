#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
import os
from tqdm import tqdm
tqdm.pandas()


DATA_PATH = './data/'
DB_PATH = './db/'

df_rest = pd.read_json(DATA_PATH+'yelp_restaurants.json')
df_user = pd.read_json(DATA_PATH+'yelp_user.json')
df_review = pd.read_json(DATA_PATH+'yelp_review.json')

# Création des noeuds user

users_csv = df_user[["user_id","name","review_count","friends","fans"]]  
users_csv.to_csv(DB_PATH+'users.csv')

# Création des relations friends

friend_relationships_csv = pd.DataFrame(columns = ["user_id","friend_id"])

for i in tqdm(users_csv.index):
    row = users_csv.iloc[i]
    user_id = row['user_id']
    friends = row["friends"]
    relationships = []
    columns = ["user_id","friend_id"]
    for friend_id in friends:
        relationships.append([user_id,friend_id])
    
    df_to_concat = pd.DataFrame(data=relationships,columns=columns)
    friend_relationships_csv = pd.concat([friend_relationships_csv,df_to_concat])

friend_relationships_csv.to_csv(DB_PATH+'friend_relationships_csv')

# Création des noeuds review

reviews_csv = df_review[["review_id","stars","useful","cool"]]  
reviews_csv.to_csv(DB_PATH+'reviews.csv')

# Création des relations reviewed

reviewed_relationships_csv = pd.DataFrame(columns=["user_id","review_id"])

for i in tqdm(df_review.index):
    row = df_review.iloc[i]
    review_id = row["review_id"]
    user_id = row["user_id"]
    df_to_concat = pd.DataFrame(data=[[user_id, review_id]], columns=["user_id", "review_id"])
    
    reviewed_relationships_csv = pd.concat([reviewed_relationships_csv,df_to_concat])

reviewed_relationships_csv.to_csv(DB_PATH+'reviewed_relationships_csv')


