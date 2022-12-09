from py2neo import Graph

graph = Graph("bolt://localhost:7687", auth=("neo4j","1234"))

q = "match (u:users) return u.name as username"
res = graph.run(q).to_table()

for record in res:
    print(record[0])

# input : ville, [ambiances], [categories], cat_tarif


##### S1 : Score Social Immédiat #####
def score_social_imm():
    return None

##### S2 : Score Social de Second Niveau #####
def score_social_2():
    return None

##### S3 : Score Social Intrinsèque #####
def score_social_intr():
    return None

##### Facteur de centralité #####
def f_centralite():
    return (score_social_imm() + score_social_2() + score_social_intr())/3

##### S4 : Score Social Intrinsèque #####
def score_val_comm()

##### Facteur de Validité des Commentaires #####
def f_val_comm():
    return None


