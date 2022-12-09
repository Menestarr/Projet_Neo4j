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

##### S4 : Score de Validité des Commentaires #####
def score_val_comm():
    return None

##### S5 : Score de Coolitude #####
def score_cool():
    return None

##### Facteur de Validité des Commentaires #####
def f_val_comm():
    return (score_val_comm() + score_cool())/2

##### S6 : Score d'Adéquation aux Ambiances #####
def score_adeq_amb():
    return None

##### S7 : Score d'Adéquation aux Catégories #####
def score_adeq_cat():
    return None

##### S8 : Score d'Adéquation aux Tarifs Pratiqués #####
def score_adeq_tarifs():
    return None

##### Facteur d'Adéquation au Restaurant #####
def f_adeq_rest():
    return (score_adeq_amb() + score_adeq_cat() + score_adeq_tarifs())/3

##### Facteur d'Adéquation Géographique #####
def f_geographique():
    return None

def score_user(alpha, beta, gamma, delta):
    return alpha*f_centralite() + beta*f_val_comm() + gamma*f_adeq_rest() + delta*f_geographique()