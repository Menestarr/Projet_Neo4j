import pandas as pd
import numpy as np
import os
from tqdm import tqdm
tqdm.pandas()

DATA_PATH = './data/'
DB_PATH = './db/'

########## Import ##########
print("------- Import des fichiers -------\n")
yelp_restaurants = pd.read_json(DATA_PATH+'yelp_restaurants.json')
yelp_user = pd.read_json(DATA_PATH+'yelp_user.json')
yelp_review = pd.read_json(DATA_PATH+'yelp_review.json')

########## Preprocessing ##########
yelp_restaurants["city"] = yelp_restaurants["city"].apply(lambda x : x.lower().replace(" ","")) # les villes en minuscule et sans espace pour éviter les doublons
yelp_restaurants["categories"] = yelp_restaurants["categories"].apply(lambda x : [y.replace(" ","").lower() for y in x.split(',')]) # de même pour les catégories

########## users.csv ##########
print("------- Création de users.csv -------\n")
users = yelp_user[["user_id","name","review_count","fans"]]  
users = users.set_index("user_id")
users.index.name = "user_id:ID(users)"
users.to_csv(DB_PATH+'users.csv')

########## reviews.csv ##########
print("------- Création de reviews.csv -------\n")
reviews = yelp_review[["review_id","stars","useful","cool"]]
reviews['stars'].apply(lambda x : int(x))
reviews = reviews.set_index("review_id")
reviews.index.name = "review_id:ID(reviews)"  
reviews.to_csv(DB_PATH+'reviews.csv')

########## restaurant.csv ##########
print("------- Création de restaurant.csv -------\n")
df_rest = yelp_restaurants.copy()
df_rest = df_rest[["business_id", "name", "review_count"]]
price_range = []

for index, item in yelp_restaurants.iterrows():
    try:
        p = item['attributes'].get('RestaurantsPriceRange2')
        if p == None:
            price_range.append(None) # on laisse None aux restaurants qui n'ont pas de price_range
        else:
            price_range.append(int(p))
    except:
        price_range.append(None)
        
df_rest['price_range'] = price_range  
df_rest = df_rest.set_index("business_id")
df_rest.index.name = "restaurant_id:ID(restaurants)"
df_rest.to_csv(DB_PATH+'restaurants.csv')

########## cities.csv ##########
print("------- Création de cities.csv -------\n")
cities = []
for city in yelp_restaurants['city']:
    if city not in cities:
        cities.append(city)

df_city = pd.DataFrame(cities, columns=['city'])
df_city.index.name = "city_id:ID(cities)"
df_city.to_csv(DB_PATH+'cities.csv')

########## ambiences.csv ##########
print("------- Création de ambiences.csv -------\n")
list_amb = []
for attr in yelp_restaurants['attributes']:
    try:
        ambs = attr["Ambience"]
        ambs = ambs.replace("{","")
        ambs = ambs.replace("}","")
        ambs = ambs.replace("u'","")
        ambs = ambs.replace("'","")
        ambs = ambs.replace(" ","")
        ambs = ambs.split(",")
        for amb in ambs:
            amb, val = amb.split(":")
            if amb not in list_amb:
                list_amb.append(amb)
    except:
        pass
        
df_ambience = pd.DataFrame(list_amb, columns=['ambience'])
df_ambience.index.name = "ambience_id:ID(ambiences)"
df_ambience.to_csv(DB_PATH+'ambiences.csv')

########## category.csv ##########
print("------- Création de category.csv -------\n")
list_cat = []
for cats in yelp_restaurants['categories']:
    for cat in cats:
        if cat not in list_cat:
            list_cat.append(cat)

df_category = pd.DataFrame(list_cat, columns=['category'])
df_category.index.name = "category_id:ID(categories)"
df_category.to_csv(DB_PATH+'categories.csv')



########## RELATIONS ##########

########## located_relationships.csv ##########
print("------- Création de located_relationships.csv -------\n")
df_located = df_city.reset_index().merge(yelp_restaurants, how="right", on='city')[["business_id","city_id:ID(cities)"]]
df_located = df_located.rename(columns={"business_id": ":START_ID(restaurants)", "city_id:ID(cities)":":END_ID(cities)"})
df_located = df_located.set_index(":START_ID(restaurants)")
df_located.to_csv(DB_PATH+'located_relationships.csv')

########## restCat_relationships.csv ##########
print("------- Création de restCat_relationships.csv -------\n")
list_cat = []
list_rest = []

for val in yelp_restaurants[['business_id','categories']].values:
    for cat in val[1]:
        cat = df_category.index[df_category['category']==cat].to_list()[0]
        list_cat.append(cat)
        list_rest.append(val[0])

df_restCat = pd.DataFrame({":START_ID(restaurants)": list_rest, ":END_ID(categories)":list_cat})
df_restCat.to_csv(DB_PATH+'restCat_relationships.csv', index=False)

########## friends_relationships.csv ##########
print("------- Création de friends_relationships.csv -------\n")
relationships = []
columns = [":START_ID(users)",":END_ID(users)"]
for _, user in tqdm(yelp_user.iterrows(), total=yelp_user.shape[0]):
    user_id = user["user_id"]
    friends = user["friends"]
    for friend_id in friends:
        relationships.append([user_id,friend_id])

friends_relationships = pd.DataFrame(data=relationships,columns=columns)
friends_relationships.to_csv(DB_PATH+'friends_relationships.csv', index=False)

########## reviewed_relationships.csv ##########
print("------- Création de reviewed_relationships.csv -------\n")

data = []
for i in tqdm(yelp_review.index):
    row = yelp_review.iloc[i]
    review_id = row["review_id"]
    user_id = row["user_id"]
    data.append([user_id, review_id])

reviewed_relationships = pd.DataFrame(data=data, columns=[":START_ID(users)",":END_ID(reviews)"])
reviewed_relationships.to_csv(DB_PATH+'reviewed_relationships.csv', index=False)

########## revRest_relationships.csv ##########
print("------- Création de revRest_relationships.csv -------\n")

data = []
for i in tqdm(yelp_review.index):
    row = yelp_review.iloc[i]
    review_id = row["review_id"]
    restaurant_id = row["business_id"]
    data.append([review_id, restaurant_id])

revRest_relationships = pd.DataFrame(data=data, columns = [":START_ID(reviews)",":END_ID(restaurants)"])
revRest_relationships.to_csv(DB_PATH+'revRest_relationships.csv', index=False)

########## revAmb_relationships.csv ##########
print("------- Création de revAmb_relationships.csv -------\n")

def ambs_to_dict(ambs):
    # création d'un dictionnaire pour les ambiances
    # nécessaire car les ambiances sont dans un dictionnaire mais sous forme de string (i.e. de la forme : "{k:v,k1:v1, ...}")
    try:
        d = {}
        ambs = ambs.replace("{","")
        ambs = ambs.replace("}","")
        ambs = ambs.replace("u'","")
        ambs = ambs.replace("'","")
        ambs = ambs.replace(" ","")
        ambs = ambs.split(",")
        for amb in ambs:
            amb, val = amb.split(":")
            d[amb] = val
        return d
    
    except:
        return {}

ambiences_id = {}
for i in df_ambience.index:
    row = df_ambience.iloc[i]
    ambiences_id[row["ambience"]] = i

data=[]
for i in tqdm(yelp_restaurants.index):
    row = yelp_restaurants.iloc[i]
    restaurant_id = row["business_id"]
    try:
        ambs = ambs_to_dict(row["attributes"]["Ambience"])
        for amb, b in ambs.items():
            if b == "True":
                data.append([restaurant_id, ambiences_id[amb]])       
    except:
        pass

restAmb = pd.DataFrame(data=data, columns=[":START_ID(restaurants)", ":END_ID(ambiences)"])
restAmb.to_csv(DB_PATH+"restAmb_relationships.csv", index=False)