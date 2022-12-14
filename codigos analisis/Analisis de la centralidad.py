#%%
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt 
from scipy.optimize import curve_fit
import random
import time
import pickle 
from tqdm import tqdm
import seaborn 
plt.style.use("seaborn")
#%%-----------------------Cargamos el multigrafo---------------------------

with open(f"../red_filtrada/red_filtrada.gpickle", "rb") as f:
    G = pickle.load(f)

#%%-------Calculamos las distintas centralidades y las metemos en un dataframe--------
def centralidades(Red):
    df= pd.DataFrame(dict(
    Grado = dict(Red.degree),
    #Autovalores= nx.eigenvector_centrality(Red, max_iter=1000, tol=1e-06, nstart=None, weight='weight'),
    Intermediatez = nx.betweenness_centrality(Red,k=None, normalized=True, weight=None, endpoints=False, seed=None),
    Cercania = nx.closeness_centrality(Red, u=None, distance=None, wf_improved=True),
    Popularidad = {nodo: G.nodes()[nodo]["popularidad"] for nodo in G.nodes()}))
    return df

df_centralidad = centralidades(G)
#%%-------------Para agregar las centralidades como atributos de los nodos---------------
df_nodos = pd.read_csv("../red_filtrada/tabla_nodos.csv")

# Le ponemos el mismo nombre a los índices
df_nodos = df_nodos.set_index("Id")
df_centralidad.index.name = "Id"
# Saco las columnas que no quiero mergear
df_centralidad = df_centralidad.drop(["Popularidad"], axis = 1)
# Uno los dos dataframes
df_nodos = pd.concat([df_nodos,df_centralidad], axis = 1)
#%%-------------------Para guardar el dataframe-----------------------------
df_nodos.to_csv("../red_filtrada/tabla_nodos.csv")
#%%
def armar_componente_gigante(Red):
    Conjunto_nodos_en_gigante = max(nx.connected_components(Red), key=len)
    Componente_Gigante = Red.subgraph(Conjunto_nodos_en_gigante).copy()
    return Componente_Gigante

def long_segunda_comp_gigante(Red):
    lista_componentes=[Red.subgraph(componente) for componente in sorted(nx.connected_components(Red), key=len, reverse=True)]
    segunda_comp_gigante =  lista_componentes[1]
    return len(segunda_comp_gigante)


def desarmar_red(red,lista_sacar):
    componente_gigante = armar_componente_gigante(red)
    tamano_inicial = len(componente_gigante.nodes())
    tamano_componente = tamano_inicial
    fraccion_en_gigante = [1] # Defino que empiece en 1 para tener el valor inicial
    fraccion_quitados = [0] # Defino que empiece en 0 para tener el valor inicial
    
    i = 0

    while tamano_inicial/2 < tamano_componente and i < len(lista_sacar):
        # Tomamos el nodo a sacar usando la funcion pasada
        nodo_sacar = lista_sacar[i]
        # Lo sacamos
        if nodo_sacar in componente_gigante.nodes():
            componente_gigante.remove_node(nodo_sacar)
        # Nos quedamos con la nueva componente gigante
        componente_gigante = armar_componente_gigante(componente_gigante)
        # Calculamos el tamaño de la componente gigante
        tamano_componente = len(componente_gigante.nodes())
        # Guardamos la fracción que queda
        fraccion_restante = (tamano_componente)/tamano_inicial
        fraccion_en_gigante.append(fraccion_restante)
        # Guardamos la fracción que ya sacamos
        fraccion_quitados.append(i/tamano_inicial)
        i +=1
    return fraccion_quitados, fraccion_en_gigante


#%%---------------------Paso la red a pesada para analizarla-------------------

G2 = nx.Graph()# Lo escribo así a cambio de perder la información de los enlaces
G2.add_nodes_from(G.nodes())
G2.add_edges_from(G.edges())

#%%--------------------Calculamos la ruptura por aleatoriedad-----------------------
lista_frac_quit_random_iterada = []
lista_frac_en_gig_random_iterada = []

cant_iteraciones = 100
for i in tqdm(range(cant_iteraciones)):

    lista_random = list(G2.nodes())
    random.shuffle(lista_random)
    frac_quit_random, frac_en_gig_random = desarmar_red(G2,lista_random) 
    lista_frac_quit_random_iterada.append(np.array(frac_quit_random))
    lista_frac_en_gig_random_iterada.append(np.array(frac_en_gig_random))

#Redefino la lista para q todos tengan el minimo de longitud(sino no puedo sumar los array):

minimo_quit = min([len(i) for i in lista_frac_quit_random_iterada])

frac_quit_random = [i[0:minimo_quit] for i in lista_frac_quit_random_iterada]
frac_en_gig_random = [i[0:minimo_quit] for i in lista_frac_en_gig_random_iterada]

#Creo mis listas para plotear: promedio sobre todas las random

frac_quit_random = sum(np.array(frac_quit_random))/len(frac_quit_random)
frac_en_gig_random = sum(np.array(frac_en_gig_random))/len(frac_en_gig_random)

#%%---------------------------Celda para guardar los datos---------------------
pickle.dump(frac_quit_random, open(f'../datos analisis/frac_quit_random_100.pickle', 'wb'))
pickle.dump(frac_en_gig_random, open(f'../datos analisis/frac_en_gig_random_100.pickle', 'wb'))
#%%-------------------------Celda para cargar los datos--------------------
with open(f"../datos analisis/frac_quit_random_100.pickle", "rb") as f:
    frac_quit_random = pickle.load(f)
with open(f"../datos analisis/frac_en_gig_random_100.pickle", "rb") as f:
    frac_en_gig_random = pickle.load(f)    
#%%---------Celda para graficar y romper la red con el resto de centralidades---------
fig, axs = plt.subplots(figsize = (12, 8))
for columna in tqdm(df_centralidad.columns):
    lista_centralidad = df_centralidad.sort_values(by = columna, ascending = False).index

    frac_quitados, frac_en_gigante = desarmar_red(G2, lista_centralidad)
    
    axs.plot(frac_quitados, frac_en_gigante, label = columna)


axs.plot(frac_quit_random, frac_en_gig_random,label = "Aleatorio",c = "k")
axs.grid(True)
axs.set_xlabel("Fracción de nodos quitados",fontsize = 16)
axs.set_ylabel("Fracción de nodos en la componente gigante", fontsize = 16)
axs.legend(fontsize = 20)
axs.tick_params(axis = "both", labelsize = 16)
#axs.xaxis.label.set_color('white')
#axs.yaxis.label.set_color('white')
axs.set_ylim(0.5,1)
#plt.savefig(f"../imagenes del analisis/centralidad multienlace.png", bbox_inches = 'tight')
plt.show()

#%%--------------------Rompo la red por género musical-----------------------

generos_representativos = ["Trap","Jazz", "Pop", "HipHop", "Clasico", "Indie",
                           "R&B", "Tango", "Cumbia",
                           "Chamame", "Electronica", "Folklore", "Rock", "Punk", "Rap", "Metal",
                           "Reggae","Alternative"]

min_artistas_en_comunidad = 54
cant_iteraciones = 100
generos_a_analizar = []
lista_frac_quit_iterada_por_genero = []
lista_frac_en_gig_iterada_por_genero = []

for genero in tqdm(generos_representativos):
    lista_artistas_por_genero = [nodo for nodo in G.nodes() 
                            if genero in G.nodes()[nodo]["generos_musicales"]]
    
    if len(lista_artistas_por_genero) >= min_artistas_en_comunidad:
        lista_frac_quit_iterada = []
        lista_frac_en_gig_iterada = []
        generos_a_analizar.append(genero)
        for i in (range(cant_iteraciones)):
            lista_random = list(lista_artistas_por_genero)
            random.shuffle(lista_random)
            frac_quit, frac_en_gig = desarmar_red(G2,lista_random) 
            lista_frac_quit_iterada.append(np.array(frac_quit))
            lista_frac_en_gig_iterada.append(np.array(frac_en_gig))

        #Redefino la lista para q todos tengan el minimo de longitud(sino no puedo sumar los array):

        minimo_quit = min([len(i) for i in lista_frac_quit_iterada])
        frac_quit_random_genero = [i[0:minimo_quit] for i in lista_frac_quit_iterada]
        frac_en_gig_random_genero = [i[0:minimo_quit] for i in lista_frac_en_gig_iterada]

        #Creo mis listas para plotear: promedio sobre todas las random
        frac_quit_random_genero = sum(np.array(frac_quit_random_genero))/len(frac_quit_random_genero)
        frac_en_gig_random_genero = sum(np.array(frac_en_gig_random_genero))/len(frac_en_gig_random_genero)
        
        lista_frac_quit_iterada_por_genero.append(frac_quit_random_genero)
        lista_frac_en_gig_iterada_por_genero.append(frac_en_gig_random_genero)


#%%--------------------------------Grafico-----------------------------------

fig, axs = plt.subplots(figsize = (8, 5))
cmap = plt.get_cmap("Dark2")#Dark2
for i, genero in enumerate(generos_a_analizar):
    frac_quit_random_genero = lista_frac_quit_iterada_por_genero[i]
    frac_en_gig_random_genero = lista_frac_en_gig_iterada_por_genero[i]

    axs.plot(frac_quit_random_genero, frac_en_gig_random_genero,label = genero, c = cmap(i))

axs.plot(frac_quit_random, frac_en_gig_random,label = "Aleatorio",c = "k", linestyle = "--")
axs.grid(True)
axs.set_xlabel("Fracción de nodos quitados",fontsize = 16)
axs.set_ylabel("Fracción de nodos en la componente gigante", fontsize = 16)
axs.legend(fontsize = 16, labelcolor='k', loc = "lower left")
axs.set_xlim(0, max(lista_frac_quit_iterada_por_genero[generos_a_analizar.index("Tango")]))
axs.set_ylim(min(lista_frac_en_gig_iterada_por_genero[generos_a_analizar.index("Tango")]),1)
axs.tick_params(axis = "both", labelsize = 16)
#axs.xaxis.label.set_color('white')
#axs.yaxis.label.set_color('white')

#Para graficar mas de cerca

# for i, genero in enumerate(generos_a_analizar):
#     frac_quit_random_genero = lista_frac_quit_iterada_por_genero[i]
#     frac_en_gig_random_genero = lista_frac_en_gig_iterada_por_genero[i]

#     axs[1].plot(frac_quit_random_genero, frac_en_gig_random_genero,label = genero, c = cmap(i))

# axs[1].plot(frac_quit_random, frac_en_gig_random,label = "Aleatorio",c = "k")
# axs[1].grid(True)
# axs[1].set_xlabel("Fracción de nodos quitados",fontsize = 16)
# axs[1].set_ylabel("Fracción de nodos en la componente gigante", fontsize = 16)
# #axs[1].legend(fontsize = 16, labelcolor='k')
# axs[1].set_xlim(0,0.1)
# axs[1].set_ylim(0.8,1)
# axs[1].tick_params(axis = "both", labelsize = 14, colors = "k")
# axs[1].xaxis.label.set_color('k')
# axs[1].yaxis.label.set_color('k')


plt.savefig(f"../imagenes del analisis/centralidad por genero.png", bbox_inches = 'tight')
plt.show()

#%%----------------Grafico de manera relativa a la curva aleatoria-----------------------------------

# Esto lo hicimos para comparar la ruptura respecto a la curva random pero no nos convenció

fig, axs = plt.subplots(figsize = (8, 5))
cmap = plt.get_cmap("Dark2")#Dark2
for i, genero in enumerate(generos_a_analizar):
    frac_quit_random_genero = lista_frac_quit_iterada_por_genero[i]
    frac_en_gig_random_genero = lista_frac_en_gig_iterada_por_genero[i]
    
    frac_relativa = frac_en_gig_random_genero-frac_en_gig_random[:len(frac_en_gig_random_genero)]
    
    axs.plot(frac_quit_random_genero, frac_relativa,label = genero, c = cmap(i))


axs.grid(True)
axs.set_xlabel("Fracción de nodos quitados",fontsize = 16)
axs.set_ylabel("Ruptura respecto a la curva aleatoria", fontsize = 16)
axs.legend(fontsize = 16, labelcolor='k')
axs.tick_params(axis = "both", labelsize = 16)
plt.show()

#%% Artistas más centrales según el criterio
cant_artistas = 30

dict_centralidad = {columna: df_centralidad.sort_values(by = columna, ascending = False).index[0:cant_artistas] for columna in df_centralidad.columns}
cmap = plt.get_cmap("plasma")#Dark2
def color(artista):
    cant_apariciones = 0

    for columna in dict_centralidad.values():
        for artista_central in columna:
            if artista == artista_central:
                cant_apariciones += 1

    # No hay artistas que aparezcan más de 3 veces
    color = "white"
    if cant_apariciones >= 2:
        color = "yellow" 
    if cant_apariciones >= 3:
        color = "cyan"
    return 'color: % s' % color

df_artistas_centrales = pd.DataFrame(dict_centralidad)

df_artistas_centrales.style.applymap(color)

# %%
n = 4
umbral = 30
matriz_info_mutua = np.zeros((n, n))
fig, axs = plt.subplots(nrows = 1, ncols = 1, figsize = (8, 8))
for i in range(4):
    for j in range(4):
        conjunto_1 = set(df_artistas_centrales[df_artistas_centrales.columns[i]].values[0:umbral])
        total = len(conjunto_1)
        conjunto_2 = set(df_artistas_centrales[df_artistas_centrales.columns[j]].values[0:umbral])
        z = len(conjunto_1.intersection(conjunto_2)) / total
        matriz_info_mutua[i][j] = z 
        axs.text(j, i, round(z,2), ha='center', va='center')
img = axs.imshow(matriz_info_mutua,cmap='GnBu', vmin= 0, vmax=1)
axs.set_xticks(range(0,n)) # pongo los ticks de los ejes
axs.set_yticks(range(0,n))
axs.grid('on', linestyle = 'dashed', alpha = 0)
axs.set_title('ISolapamiento de centralidades',fontsize = 16)
axs.set_yticklabels(df_artistas_centrales.columns.values) 
axs.set_xticklabels(df_artistas_centrales.columns.values)
fig.colorbar(img, orientation="vertical", pad=0.1,fraction=0.04,extend='min') # la barra de colores
plt.show()
