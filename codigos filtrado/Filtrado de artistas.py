#%%
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from unicodedata import normalize
import pickle 
import textdistance as td
from scipy.spatial.distance import pdist, squareform
import networkx as nx
#%%

def normalizar(string):
    trans_tab = dict.fromkeys(map(ord, u'\u0301\u0308'), None)
    string_normalizado = normalize('NFKC', normalize('NFKD', string).translate(trans_tab)).lower().replace(" ", "")
    return string_normalizado

with open(f"red_filtrada/red_filtrada.gpickle", "rb") as f:
    G = pickle.load(f)
# %%
lista_artistas = list(G.nodes())

# %%
# Creamos una lista con los artistas repetidos
artistas_repetidos = []
# Creamos una lista con los artistas repetidos pero los strings normalizados
artistas_normalizados = []

for artista_i in lista_artistas["nombre"]:
    nombre_normalizado_i = normalizar(artista_i)
    for artista_j in lista_artistas["nombre"]:
        nombre_normalizado_j = normalizar(artista_j)
        if nombre_normalizado_j in nombre_normalizado_i and artista_i != artista_j and (nombre_normalizado_i, nombre_normalizado_j) not in artistas_normalizados:
            artistas_repetidos.append((artista_i, artista_j)) 
            artistas_normalizados.append((nombre_normalizado_i, nombre_normalizado_j))

#%% Sacamos palabras de artistas que no queremos combinar/eliminar de la red
artistas_repetidos_filtrados = []

palabras_filtro = ["UN","Fernando","Rodrigo","Axel","Emilia","TINI","Rei","Wen","Árbol",'Cacho Lafalce, Bernardo Baraj, Cacho Arce, Domingo Cura & Chino Rossi',
                   'David Lebón Jr',"Vandera",'Jairo',"Julio Martinez","Karina Cohen",'Lalo Schifrin',
                   'Lagartijeando',"MYA","Juanse","MAX","ACRU","Oscar Alem",'Sandro',"Carca"
                   ,"La Mississippi","Roberto Diaz Velado"]

for i in artistas_repetidos:
    filtro = True
    j = 0
    while filtro and j < len(palabras_filtro):
        
        if palabras_filtro[j] in i:
            filtro = False
        j+= 1

    if filtro:
        artistas_repetidos_filtrados.append(i)
#%%
for i in artistas_repetidos_filtrados:
    print(i)
#%%
i = 1496
with open(f"red_final_generos.gpickle", "rb") as f:
    G = pickle.load(f)

G_copia = G.copy()

nodos_para_remover = ['David Lebón Jr',"Julio Martinez Oyanguren",'Lalo Schifrin Conducts Stravinsky, Schifrin, And Ravel',
                      "Lagartijeando, Sajra", 'Mya feat. Spice','Mya feat. Stacie & Lacie','Mya feat. Trina'
                      ,'KR3TURE', 'Feral Fauna', "MAX"]

G_copia.remove_nodes_from(nodos_para_remover)

# %%
# enlaces = list(G.edges(data= True))
artistas_repetidos_filtrados = sorted(artistas_repetidos_filtrados)

artistas_a_matar = []

for i,j in artistas_repetidos_filtrados:
    if len(i) <= len(j):
        enlaces = list(G.edges(j,data=True))
        for data_enlace in enlaces:
            if i not in list(G_copia.nodes()):
                print(f"agregue a {i}")
            G_copia.add_edge(i,data_enlace[1],nombre = data_enlace[2]["nombre"],fecha = data_enlace[2]["fecha"])

        artistas_a_matar.append(j)
    else:
        enlaces = list(G.edges(i,data=True))
        for data_enlace in enlaces:
            if j not in list(G_copia.nodes()):
                print(f"agregue a {j}")
            G_copia.add_edge(j,data_enlace[1],nombre = data_enlace[2]["nombre"],fecha = data_enlace[2]["fecha"])

        artistas_a_matar.append(i)
#print(artistas_a_matar)

G_copia.remove_nodes_from(artistas_a_matar)

#%%--------------------Para guardar la red--------------------

nx.write_gpickle(G, f"red_filtrada/red_filtrada.gpickle")

#%% Lo siguiente es para comprobar que no hayan quedado artistas por filtrar

datos = set(G.nodes()) ^ set(G_copia.nodes()) 

#%%
for i in datos:
    if i not in artistas_repetidos_filtrados:
        print(i)
#%%
lista = [i for i,j in artistas_repetidos_filtrados] + [j for i,j in artistas_repetidos_filtrados]
lista = list(np.unique(lista))

no_interseccion = datos ^ set(lista)

print(no_interseccion)

# %%
lista_artistas_copia = pd.DataFrame(list(G_copia.nodes()), columns = ["nombre"])

lista_artistas_copia.to_csv("artistas copia.csv")
# %%
