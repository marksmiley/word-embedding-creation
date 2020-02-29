import itertools
import pandas as pd
import numpy as np
import re
import os
from tqdm import tqdm

# Deep learning: 
from keras.models import Input, Model
from keras.layers import Dense

from scipy import sparse

# Reading the text from the input folder
texts = pd.read_csv('input/spam_text.csv')
texts = texts[texts['Category']=='spam']
texts = [x for x in texts['Message']]

# Defining the window for context
window = 3

# Creating a placeholder for the scanning of the word list
word_lists = []
all_text = []

for text in texts:

    # Removing punctuations
    punctuations = r'''!()-[]{};:'"\,<>./?@#$%^&*_“~'''
    for x in text.lower(): 
        if x in punctuations: 
            text = text.replace(x, "")

    # Removing words that have numbers in them
    text = re.sub(r'\w*\d\w*', '', text)

    # Removing digits
    text = re.sub(r'[0-9]+', '', text)

    # Cleaning the whitespaces
    text = re.sub(r'\s+', ' ', text).strip()

    # Setting every word to lower
    text = text.lower()

    # Converting all our text to a list 
    text = text.split(' ')
    all_text += text

    # Creating a context dictionary
    for i, word in enumerate(text):
        if i + 1 + window <= len(text): 
            context = text[(i + 1):(i + 1 + window)]
            word_lists.append([word] + context)

# Getting all the unique words from our text 
words = set(all_text)

# Defining the number of features (unique words)
n_words = len(words)

# Creating the dictionary for the unique words
unique_word_dict = {}
for i, word in enumerate(words):
    unique_word_dict.update({
        word: i
    })

# Creating the X and Y matrices using one hot encoding
X = []
Y = []

for i, word_list in tqdm(enumerate(word_lists)):
    for w in range(window):
        # Creating the placeholders   
        X_row = np.zeros(n_words)
        Y_row = np.zeros(n_words)

        # One hot encoding the main word
        X_row[unique_word_dict.get(word_list[0])] = 1

        # One hot encoding the Y matrix words 
        Y_row[unique_word_dict.get(word_list[w + 1])] = 1

        # Appending to the main matrices
        X.append(X_row)
        Y.append(Y_row)

# Converting the matrices into a sparse format because the vast majority of the data are 0s
X = sparse.csr_matrix(X)
Y = sparse.csr_matrix(Y)

# Defining the size of the embedding
embed_size = 100

# Defining the neural network
inp = Input(shape=(n_words,))
x = Dense(units=embed_size)(inp)
x = Dense(units=n_words, activation='softmax')(x)
model = Model(inputs=inp, outputs=x)
model.compile(loss = 'categorical_crossentropy', optimizer = 'adam')

# Optimizing the network weights
model.fit(
    x=X, 
    y=Y, 
    batch_size=256,
    epochs=100
    )

# Obtaining the weights from the neural network. 
# These are the so called word embeddings

# The input layer 
weights = model.get_weights()[0]

# Creating a dictionary to store the embeddings in. The key is a unique word and 
# the value is the numeric vector
embedding_dict = {}
for word in words: 
    embedding_dict.update({
        word: weights[unique_word_dict.get(word)]
        })

# Saving the embedding vector to a txt file
try:
    os.mkdir(f'{os.getcwd()}\\output')        
except Exception as e:
    print(f'Cannot create output folder: {e}')

with open(f'{os.getcwd()}\\output\\embedding.txt', 'w') as f:
    for key, value in embedding_dict.items():
        try:
            f.write(f'{key}: {value}\n')   
        except Exception as e:
            print(f'Cannot write word {key} to dict: {e}')     

# Functions to find the most similar word 
def euclidean(vec1:np.array, vec2:np.array) -> float:
    """
    A function to calculate the euclidean distance between two vectors
    """
    return np.sqrt(np.sum((vec1 - vec2)**2))

def find_similar(word:str, embedding_dict:dict, top_n=10)->list:
    """
    A method to find the most similar word based on the learnt embeddings
    """
    dist_dict = {}
    word_vector = embedding_dict.get(word, [])
    if len(word_vector) > 0:
        for key, value in embedding_dict.items():
            if key!=word:
                dist = euclidean(word_vector, value)
                dist_dict.update({
                    key: dist
                })

        return sorted(dist_dict.items(), key=lambda x: x[1])[0:top_n]          