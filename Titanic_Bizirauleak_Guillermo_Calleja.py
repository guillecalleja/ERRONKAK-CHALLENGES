# -*- coding: utf-8 -*-
"""Untitled2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1knWmv_i70PuXja6hmWHnh-IumpwlA6wn

## ERRONKA: TITANIC
"""

import pandas as pd
pd.options.display.float_format = '{:.2f}'.format
pd.set_option('display.max_columns', None)
import numpy as np
np.set_printoptions(precision=3, suppress=True)
import seaborn as sns
from scipy import stats
from sklearn.preprocessing import StandardScaler
import random
from numpy.random import seed
np.random.seed(123)
seed(123)
import warnings
warnings.filterwarnings('ignore')
from keras.models import Sequential
from keras.layers import Dense
import tensorflow as tf
import os
import sklearn
from tensorflow.keras import layers

train = pd.read_csv('/content/Titanic/train.csv')
print(train)

"""Conozcamos nuestros datos"""

train.dtypes

#pip install sweetviz

import sweetviz as sv

sweet_config = sv.FeatureConfig(skip=['PassengerId','Ticket','Name'], force_cat=['Sex','Survived','Embarked'])
eda_titanic_survived = sv.analyze(train,target_feat ='Survived')
eda_titanic_survived.show_html('Titanic-survived.html')
eda_titanic_survived.show_notebook(layout='vertical')

"""Hay variables con muy poca información útil a la hora de realizar análisis. Son, básicamente, identificadores únicos como PassengerId, Name, Nº de Ticket).De hecho, ya los hemos ignorado en nuestro EDA por esta razón. Procedemos a eliminar estas columnas para ir ligeros de cargar y computar ágilmente.

Asimismo, vemos que hay un montón de valores perdidos (20% en la variable Age, 77% en la variable Cabin y 2 en la variable Embarked). No podemos tener en cuenta la variable Cabin, debemos despreciarla junto a las que mencionábamos anteriormente. En cuanto a Age, haremos un análisis de la tabla ANOVA para ver si se trata de una variable relevante.
"""

NAs = train.isnull().sum()
print(NAs)

train = train.drop(columns=['PassengerId', 'Name', 'Ticket', 'Cabin'])
print(train)

"""Realizamos ANOVA para la variable Age, hemos de valorar su significancia dada la gran proporción de valores perdidos que contiene. Aprovechamos para valorar la importancia de cada un ade las demás variables enfrentándolas con a variable a predecir (Survived).
La tabla ANOVA sólo acepta valores numéricos, hacemos dummies de todas nuestras variables categóricas antes de pasar la prueba. También deberemos imputar datos en los valores perdidos, con la fx fancyimpute.
"""

train = pd.get_dummies(train, columns=['Sex', 'Embarked'],drop_first = True)

"""Al hacer Drop First con la binaerización de las variables categóricas, nos hemos deshecho de la columns Embarked-C, en ella se encontraban los 2 valores perdidos de la variable Embarked. No necesitamos, por esto, imputar estos 2 valores. Nuestro EDA nos mostraba, por otro lado, cierta influencia del embarque en Cherburgo a la hora de sobrevivir ddel naufragio"""

print(train)

#pip install fancyimpute

import fancyimpute
from fancyimpute import IterativeImputer

train.isnull().sum()

columnas = train.columns
mice_imputer = IterativeImputer()
train = mice_imputer.fit_transform(train)
train = pd.DataFrame(train)
train.columns = columnas
train.isnull().any().any()

train

resultado_ANOVA = []
significativa = []
for a in train.columns[:-1]:
    tmp = stats.f_oneway(train.loc[:,a], train.Survived)

    alpha = 0.05  # nivel de significancia
    if tmp.pvalue < alpha:
    # Hay diferencias significativas entre los grupos
      tmp2 = 1
    else:
    # No hay diferencias significativas entre los grupos
      tmp2 = 0

    # Mostramos resultados
    print('Columna: ', a)
    print('Estadístico F: ', tmp.statistic)
    print('P-Valor: ', tmp.pvalue)
    print('Significatividad: ', tmp2)
    resultado_ANOVA.append(tmp)
    significativa.append(tmp2)

"""Los valores de significatividad son muy claros: todas las variables son importantes, salvo Parch. Estando definidas las relaciones familiares de cada pasajero de una manera mucho más eficaz e informativa en la variable SibsP, la despreciaremos en un principio. Tal vez la tengamos en cuenta posteriormente si nos vemos en la necesidad de comparar y mejorar nuestros resultados.

NOTA> Efectivamente, tras modelar nuestra red neuronal hemos comprobado que al tener la variable Parch en cuenta, los resultados mejoran (ver comentario después)
"""

#train = train.drop(columns=['Parch'])
train

X = train.copy()
y = X.pop('Survived')

type(X)

"""Normalizamos los datos"""

from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()

# Si dividimos el fit_transform en 2 podemos luego
# des-estandarizar fácil

X_n = scaler.fit_transform(X)
X_n = pd.DataFrame(X_n, columns=X.columns)
X_n

"""## RNA - Creamos una red neuronal para los siguientes escenarios: • Datos normalizados y una capa oculta con 4 neuronas. • Datos normalizados y una capa oculta con 8 neuronas."""

#Dividimos nuestros registros para entrenamiento y prueba
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
                                        X,
                                        y,
                                        train_size   = 0.7,
                                        random_state = 123,
                                        shuffle      = True
                                    )

"""Definimos el modelo Keras (keras.io/api)"""

#Añadimos una semilla
tf.random.set_seed(123)
np.random.seed(123)
random.seed(123)
seed(123)

# Definiremos el modelo como una secuencia de capas.
# Usaremos el modelo secuencial de manera que podamos ir añadiendo capas hasta estar contentos con la arquitectura desarrollada.
model1 = Sequential()

# Partimos de un sistema con 8 variables por lo que nuestra primera capa acomodará dichas variables
# En la primera capa oculta usaremos 12 neuronas y una función de activación ReLU
# En la segunda capa oculta usaremos 8 neuronas y una función de activación ReLU
# Finalmente en la de salida una neurona y función de activación sigmoide
model1.add(Dense(12, input_dim=8, activation='relu'))
model1.add(Dense(8, activation='tanh'))
model1.add(Dense(4, activation='relu'))
model1.add(Dense(1, activation='sigmoid'))

"""Compilamos el modelo:
Usamos Binary Cross Entropy puesto que funciona bien para problemas binarios de clasificación.Como métrica ,al ser clasificación, usaremos la precisión.
Como optimizador, usaremos el algoritmo "adam" ya que ofrece buenos resultados en un amplio abanico de problemas y además de manera rápida



"""

model1.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
              #loss="binary_crossentropy",
              loss=tf.keras.losses.BinaryCrossentropy(from_logits=False, # usar cuando valores de predicción sean [0,1]
                                                      label_smoothing=0.0,
                                                      axis=-1,
                                                      reduction="auto",
                                                      name="binary_crossentropy"),
              metrics=['accuracy'])

"""Entrenamos el modelo"""

model1.fit(X_train, y_train, epochs=150, batch_size=10)

"""Evaluamos el modelo"""

_, accuracy = model1.evaluate(X_train, y_train)
print('Accuracy: %.2f' % (accuracy*100))

"""Me gusta llegar al test con una accuracy mayor, voy a probar a reintroducir la variable Parch. Pese a lo que anunciaba la tabla ANOVA, creo que el hecho de viajar sólo(o con doncella) debería ser relevante a la hora de poder ser evacuado con mayor faciidad que en el caso de las familias completas.
Comento la línea en la que eliminaba la columna Parch para ver qué ocurre. Hemos pasado de una accuracy de 84.75 a 85.71
Vamos a por las predicciones

##Predicciones:
"""

predicciones = model1.predict(X_test)

# La función sigmoide nos devueve los resultados en formato probabilidad.
# Convertimos los mismos a casos, tomando como umbral 0.5
y_pred = (predicciones > 0.5).astype(int)
y_pred

from sklearn.metrics import confusion_matrix
confusion_matrix(y_test, y_pred)

from sklearn.metrics import precision_recall_fscore_support as score
precision, recall, fscore, support = score(y_test, y_pred.round())
print('precision: {}'.format(precision))
print('recall: {}'.format(recall))
print('fscore: {}'.format(fscore))
print('support: {}'.format(support))
print("############################")
print(sklearn.metrics.classification_report(y_test,y_pred.round()))

"""Estos resultados podrían parecer estadísticamente satisfactorios, pero podría espeerarse algún margen de mejora (al menos, desde la perspectiva de los familiares de los pasajeros a la espera de noticias sobre la supervivencia de sus allegados).
Vamos a tratar de mejorar los datos agrupando valores en las variables, extrayendo información de valor de laguna de las despreciadas y enriqueciendo la tabla mediante una clusterización. Revisamos nuestro EDA para definir estrategias:

Empezamos por crear nuevas variables. Si nos fijamos en Parch y SibsP nos pueden dar el número de componentes de cada unidas familiar. Con este datos podemos averiguar el precio del billete unitario de cada tripulante, pues la columna Fare nos da el dato del coste de cada billete por unidad familiar.

Vuelvo a cargar train para repetir el proceso de preporcesamiento con mejoras.


### (*) En una segunda revisión del primer modelo, nos quedamos con el. Saltamos hasta abajo para mostrar los resultados



"""

#train['tamanio_familia']=train['SibSp']+train['Parch']

#train['tarifa_unit']=train['Fare']/(train['tamanio_familia']+1)

#train

"""Vamos a diferenciar entre solteros y casados a partir del título, que se puede extraer del nombre"""

# Creamos una nueva variable que contenga unicamente el apellido
#train['Apellido']=train['Name'].str.split(',',expand=True)[0]
# Se puede crear tambien otra variable que contenga el nombre
#train['Nombre']=train['Name'].str.split(',',expand=True)[1]
# Si quisieramos podriamos separar el tratamiento o titulo utilizado para cada persona
#train['Titulo']=train['Nombre'].str.split('.',expand=True)[0]
#train = train.drop(columns=['PassengerId', 'Name', 'Ticket', 'Cabin','Apellido','Nombre', 'SibSp', 'Parch','Fare'])
#print(train)

#train.Titulo.unique()

#def replace_titles(x):
  #  if x in [' Mr', 'the Countess',' Mrs', ' Mme', ' Major', ' Jonkheer',' Lady']:
  #      return '0'
  # elif x in [' Mlle', ' Miss', ' Ms']:
  #      return '1'
  #  elif x in [' Don', ' Capt',' Rev', ' Col',' Master',' Dr', ' Sir']:
  #      return '2'

#x = 'Mme'

#replace_titles(x)

#train['Title']=train.Titulo.apply(replace_titles)

#train

#train = train.drop(columns=['Titulo'])

#train = pd.get_dummies(train, columns=['Sex', 'Embarked', 'Title'],drop_first = True)

#from sklearn.preprocessing import StandardScaler
#scaler = StandardScaler()
#trainn = scaler.fit_transform(train)
#trainn = pd.DataFrame(trainn, columns=train.columns)
#trainn

#import fancyimpute
#from fancyimpute import IterativeImputer
#columnas = trainn.columns
#mice_imputer = IterativeImputer()
#trainn = mice_imputer.fit_transform(trainn)
#trainn = pd.DataFrame(trainn)
#trainn.columns = columnas
#trainn.isnull().any().any()

#X = train.copy()
#y = X.pop('Survived')

#X

#type(X)

#Dividimos nuestros registros para entrenamiento y prueba
#from sklearn.model_selection import train_test_split

#X_train, X_test, y_train, y_test = train_test_split(
#                                        X,
#                                        y,
#                                        train_size   = 0.7,
#                                        random_state = 123,
#                                        shuffle      = True
#                                    )

#Añadimos una semilla
#tf.random.set_seed(123)
#np.random.seed(123)
#random.seed(123)
#seed(123)

#model = Sequential()

# Partimos de un sistema con 9 variables por lo que nuestra primera capa acomodará dichas variables
# En la primera capa oculta usaremos 12 neuronas y una función de activación ReLU
# En la segunda capa oculta usaremos 8 neuronas y una función de activación ReLU
# Finalmente en la de salida una neurona y función de activación sigmoide
#model.add(Dense(12, input_dim=9, activation='relu'))
#model.add(Dense(8, activation='tanh'))
#model.add(Dense(4, activation='relu'))
#model.add(Dense(1, activation='sigmoid'))

#model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
              #loss="binary_crossentropy",
              #loss=tf.keras.losses.BinaryCrossentropy(from_logits=False, # usar cuando valores de predicción sean [0,1]
              #                                       label_smoothing=0.0,
              #                                       axis=-1,
              #                                       reduction="auto",
              #                                       name="binary_crossentropy"),
              #metrics=['accuracy'])

#model.fit(X_train, y_train, epochs=150, batch_size=10)

#_, accuracy = model.evaluate(X_train, y_train)
#print('Accuracy: %.2f' % (accuracy*100))

"""### Los resultados son realmente malos. Debemos quedarnos con el primer model. Tal vez trataremos de realizar una clusterización para ganar una variable de calidad que nos pueda dar juego.
#Volvemos a model1
"""

test = pd.read_csv('/content/Titanic/test.csv')
print(test)

test = test.drop(columns=['PassengerId', 'Name', 'Ticket', 'Cabin'])
print(test)

test = pd.get_dummies(test, columns=['Sex', 'Embarked'],drop_first = True)

columnas = test.columns
mice_imputer = IterativeImputer()
test = mice_imputer.fit_transform(test)
test = pd.DataFrame(test)
test.columns = columnas
test.isnull().any().any()

from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()


test_n = scaler.fit_transform(test)
test_n = pd.DataFrame(test_n, columns=test.columns)
test_n

prediccion = model1.predict(test)

y_pred = (prediccion > 0.5).astype(int)
y_pred

"""Cargamos el archivo geneder_submission para reemplazar la columna de resultados ficticios por nuestro array de resultados obtenido"""

gender_submission = pd.read_csv('/content/Titanic/gender_submission.csv')

gender_submission['Bizirauleak'] = y_pred
gender_submission = gender_submission.drop(columns=['Survived'])
print(gender_submission)

gender_submission.to_csv('Bizirauleak.csv')
# Subimos el archivo a Kopuru y entregamos el examen