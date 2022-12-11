from py2neo import Graph
from operator import itemgetter
import time


class MoteurReco:

    def __init__(self, alpha, beta, gamma, delta, city, ambiences, categories, price_range):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta
        self.city = city.lower()
        self.ambiences = ambiences
        self.categories = [x.lower().replace(" ","") for x in categories]
        self.price_range = price_range

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

        # Dictionnaire entre user_id et le nombre de reviews positives pour chaque ambiance du restaurant
        self.n_pos_reviews_amb = {id : 0 for id in self.users_id}
        for amb in self.ambiences:
            q=f"match (u:users)-[:reviewed]->(r:reviews)-[]->(:restaurants)-[]->(a:ambiences) with u,r,a where toInteger(r.stars)>=4 and a.ambience='{amb}' return u.user_id,count(r)"
            res=self.graph.run(q).to_table()
            for user, count in res:
                self.n_pos_reviews_amb[user] += count

        # Nombre d'ambiances
        self.n_ambiences = len(self.ambiences)

        # Dictionnaire entre user_id et le nombre de reviews positives pour chaque categorie du restaurant
        self.n_pos_reviews_cat = {id : 0 for id in self.users_id}
        for cat in self.categories:
            q=f"match (u:users)-[:reviewed]->(r:reviews)-[]->(:restaurants)-[]->(c:categories) with u,r,c where toInteger(r.stars)>=4 and c.category='{cat}' return u.user_id,count(r)"
            res=self.graph.run(q).to_table()
            for user, count in res:
                self.n_pos_reviews_cat[user] += count

        # Nombre de catégories
        self.n_categories = len(self.categories)

        # Dictionnaire entre user_id et le nombre de reviews positives pour le même price range du restaurant
        self.n_pos_reviews_pr = {id : 0 for id in self.users_id}
        q=f"match (u:users)-[:reviewed]->(r:reviews)-[]->(rest:restaurants) with u,r,rest where toInteger(r.stars)>=4 and toInteger(rest.price_range)={self.price_range} return u.user_id,count(r)"
        res=self.graph.run(q).to_table()
        for user, count in res:
            self.n_pos_reviews_pr[user] += count

        # Dictionnaire entre user_id et le nombre de reviews ecrites par ses amis
        self.n_reviews_friends = {id : 0 for id in self.users_id}
        for user, friends in self.id_friends.items():
            for friend in friends:
                self.n_reviews_friends[user] += self.n_reviews[friend]

        # Dictionnaire entre user_id et le nombre de reviews pour des restaurants dans la ville 'city'
        self.n_reviews_city = {id : 0 for id in self.users_id}
        q=f"match (u:users)-[:reviewed]->(r:reviews)-[:revRest]->(:restaurants)-[:located]->(c:cities) where c.city='{self.city}' return u.user_id, count(r)"
        for user,count in self.graph.run(q).to_table():
            self.n_reviews_city[user]=count
        
        # Dictionnaire entre user_id et le nombre de reviews ecrites par ses amis pour des restaurants dans la ville 'city'
        self.n_reviews_friends_city = {id : 0 for id in self.users_id}
        for user, friends in self.id_friends.items():
            for friend in friends:
                self.n_reviews_friends_city[user] += self.n_reviews_city[friend]



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
    def score_adeq_amb(self, u):
        return self.n_pos_reviews_amb[u]/(self.n_ambiences * self.n_reviews[u])

    ##### S7 : Score d'Adéquation aux Catégories #####
    def score_adeq_cat(self,u):
        return self.n_pos_reviews_cat[u]/(self.n_categories * self.n_reviews[u])

    ##### S8 : Score d'Adéquation aux Tarifs Pratiqués #####
    def score_adeq_tarifs(self,u):
        return self.n_pos_reviews_pr[u]/self.n_reviews[u]

    ##### Facteur d'Adéquation au Restaurant #####
    def f_adeq_rest(self,u):
        return (self.score_adeq_amb(u) + self.score_adeq_cat(u) + self.score_adeq_tarifs(u))/3

    ##### Facteur d'Adéquation Géographique #####
    def f_geographique(self,u):
        n_reviews_friends = self.n_reviews_friends[u]
        if n_reviews_friends==0:
            return 0
        else:
            return self.n_reviews_friends_city[u]/self.n_reviews_friends[u]

    ##### Score Utilisateur #####
    def score_user(self, id_user):
        return self.alpha*self.f_centralite(id_user) + self.beta*self.f_val_comm(id_user) + self.gamma*self.f_adeq_rest(id_user) + self.delta*self.f_geographique(id_user)

    
    ##### Mise à jour des scores de tous les utilisateurs #####
    def update_scores(self):
        for id in self.score.keys():
            self.score[id] = self.score_user(id)

    ##### Récupération des 10 meilleurs utilisateurs #####
    def get_best_users(self):
        self.update_scores()
        best_users = dict(sorted(self.score.items(), key=itemgetter(1), reverse=True)[:10])
        return best_users

    ##### Affichage des utilisateurs à recommander #####
    def print_best_users(self):
        start = time.time()
        best_users = self.get_best_users()
        print(f"Temps d'exécution : {time.time()-start:.3} ms\n")
        print("user_id                 name    score")
        for k,v in best_users.items():
            q=f"match (u:users) where u.user_id='{k}' return u.name"
            print(f"{k}  {self.graph.run(q).to_table()[0][0]}  {v}")



if __name__=="__main__":
    alpha, beta, gamma, delta = 0.3, 0.3, 0.3, 0.1
    
    tests = [
        {'city':'Wilmington', 'ambiences':['casual'], 'categories':['Pizza','Burgers','Italian'],'price_range':1},
        {'city':'Wilmington', 'ambiences':['casual','romantic'],'categories':['Chinese'], 'price_range':2},
        {'city':'Wilmington', 'ambiences':['hipster'], 'categories':['Nightlife','Bars'],'price_range':1},
        {'city':'New Castle', 'ambiences':['casual','classy'], 'categories':['Coffee & Tea'], 'price_range':2},
        {'city':'New Castle', 'ambiences':['classy'], 'categories':['Seafood'],'price_range':1}]

    for i, test in enumerate(tests):
        print(f"\n\n#################### Test n°{i+1} ####################\n")
        city = test['city']
        ambiences = test['ambiences']
        categories = test['categories']
        price_range = test['price_range']
        mot = MoteurReco(alpha, beta, gamma, delta, city, ambiences, categories, price_range)
        mot.print_best_users()
    


