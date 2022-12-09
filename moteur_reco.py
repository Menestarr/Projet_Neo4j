from py2neo import Graph
from operator import itemgetter
# input : ville, [ambiances], [categories], cat_tarif

class MoteurReco:

    def __init__(self, alpha, beta, gamma, delta):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta

        self.graph = Graph("bolt://localhost:11006", auth=("neo4j","1234"))

        q = "match (u:users) return u.user_id"
        # Liste des tous les user_id
        self.users_id = [id[0] for id in self.graph.run(q).to_table()]

        # dictionnaire des scores des utilsateurs
        self.score = {id:0 for id in self.users_id}

        q = "match (u:users)-[:friends]->(v:users) with u,count(v) as c return u.user_id,c"
        # Dictionnaire entre user_id et son nombre d'ami associé
        self.n_friends = {id:0 for id in self.users_id}
        for v in self.graph.run(q).to_table():
            self.n_friends[v[0]] = v[1]
        
        # Nombre maximal d'ami
        self.max_friends = max(self.n_friends.values())

        q = "match (u:users)-[:friends]->(v:users) with u,v return u.user_id,v.user_id"
        aux = self.graph.run(q).to_table()
        # Dictionnaire entre user_id et les id de ses amis
        self.id_friends = {id:[] for id in self.users_id}
        for (user, friend) in aux:
            self.id_friends[user].append(friend)
        
        # Dictionnaire entre user_id et les id des amis de ses amis
        self.id_friends_of_friends = self.id_friends.copy()
        # Dictionnaire entre user_id et son nombre d'amis de ses amis
        self.n_friends_of_friends = {id:0 for id in self.users_id}
        for key, friends in self.id_friends_of_friends.items():
            id_list = []
            for friend in friends:
                id_list += self.id_friends[friend]
            self.id_friends_of_friends[key] = set(id_list)
            self.n_friends_of_friends[key] = len(id_list)

        # Nombre maximal d'amis d'amis
        self.max_friends_of_friends = max(self.n_friends_of_friends.values())

        q = "match (u:users) return u.user_id,u.fans"
        # Dictionnaire entre user_id et son nombre de fans
        self.n_fans = {v[0]:int(v[1]) for v in self.graph.run(q).to_table()}
        
        # Nombre maximal de fan
        self.max_fans = max(self.n_fans.values())

        q="match (u:users) return u.user_id,u.review_count"
        # Nombre de review par utilisateur
        res=self.graph.run(q).to_table()
        self.n_reviews = {v[0]:int(v[1]) for v in res}
        
        q="match (u:users)-[:reviewed]->(r:reviews) with u,r where toInteger(r.useful)>0 return u.user_id,count(r)"
        res= self.graph.run(q).to_table()
        # Dictionnaire entre user_id et le nombre de review au moins une fois useful
        self.n_useful_reviews = {id:0 for id in self.users_id}
        for user, count in res:
            self.n_useful_reviews[user] = count

        q="match (u:users)-[:reviewed]->(r:reviews) with u,r where toInteger(r.cool)>0 return u.user_id,count(r)"
        res= self.graph.run(q).to_table()
        # Dictionnaire entre user_id et le nombre de review au moins une fois useful
        self.n_cool_reviews = {id:0 for id in self.users_id}
        for user, count in res:
            self.n_cool_reviews[user] = count


    ##### S1 : Score Social Immédiat #####
    def score_social_imm(self, u):
        return self.n_friends[u]/self.max_friends

    ##### S2 : Score Social de Second Niveau #####
    def score_social_2(self, u):
        return self.n_friends_of_friends[u]/self.max_friends_of_friends

    ##### S3 : Score Social Intrinsèque #####
    def score_social_intr(self, u):
        return self.n_fans[u]/self.max_fans

    ##### Facteur de centralité #####
    def f_centralite(self, u):
        return (self.score_social_imm(u) + self.score_social_2(u) + self.score_social_intr(u))/3

    ##### S4 : Score de Validité des Commentaires #####
    def score_val_comm(self,u):
        return self.n_useful_reviews[u]/self.n_reviews[u]

    ##### S5 : Score de Coolitude #####
    def score_cool(self,u):
        return self.n_cool_reviews[u]/self.n_reviews[u]

    ##### Facteur de Validité des Commentaires #####
    def f_val_comm(self,u):
        return (self.score_val_comm(u) + self.score_cool(u))/2

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

    ##### Score Utilisateur #####
    def score_user(self, id_user):
        return self.alpha*self.f_centralite(id_user) + self.beta*self.f_val_comm(id_user) #+ gamma*f_adeq_rest() + delta*f_geographique()

    
    ##### Mise à jour des scores de tous les utilisateurs #####
    def update_scores(self):
        for id in self.score.keys():
            self.score[id] = self.score_user(id)

    ##### Récupération des 10 meilleurs utilisateurs #####
    def get_best_users(self):
        return dict(sorted(self.score.items(), key=itemgetter(1), reverse=True)[:10])



if __name__=="__main__":
    alpha, beta, gamma, delta = 0.3, 0.3, 0.3, 0.1

    mot = MoteurReco(alpha, beta, gamma, delta)
    mot.update_scores()
    print(mot.get_best_users())
    


