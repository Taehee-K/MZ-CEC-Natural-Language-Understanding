# -*- coding: utf-8 -*-
"""bert_docker.ipynb의 사본

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1niCSAoazh-6SS55vjBYHyAkD-rllSDj1
"""

# from google.colab import drive
# drive.mount('/content/drive')

"""Data load (경로 입력)"""

import pandas as pd

# test = pd.read_csv('dev.txt', sep='\t', names=['purpose','sentence'], encoding='utf-8')
train = pd.read_csv('train.txt', sep='\t',names=['purpose','sentence'],encoding='utf-8')
test_purpose = pd.read_csv('test_intent.txt', sep='\t', names=['purpose'], encoding='utf-8')
test_sent = pd.read_csv('test_sent.txt', sep='\t', names=['sentence'], encoding='utf-8')

test = pd.concat([test_purpose, test_sent],axis =1, sort=False)

"""Model load (경로 입력)"""

import os
import tensorflow as tf

model_fname = 'saved_model_epoch15'
# my_wd = '/content/drive/MyDrive/STT/STT 의도 분류 해커톤(미디어젠)/코드/model load & print/0104(1)'
# new_model = tf.keras.models.load_model(os.path.join(my_wd, model_fname))
new_model = tf.keras.models.load_model(model_fname)

# 나중에 삭제
new_model.summary()

"""# Install"""

# !pip install tensorflow_hub
# !pip install keras tf-models-official pydot graphviz

import numpy as np

import tensorflow_hub as hub

from keras.utils import np_utils

import official.nlp.bert.bert_models
import official.nlp.bert.configs
import official.nlp.bert.run_classifier
import official.nlp.bert.tokenization as tokenization

from official.modeling import tf_utils
from official import nlp
from official.nlp import bert

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

import matplotlib.pyplot as plt

gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
  try:
    # Currently, memory growth needs to be the same across GPUs
    for gpu in gpus:
      tf.config.experimental.set_memory_growth(gpu, True)
    logical_gpus = tf.config.experimental.list_logical_devices('GPU')
    print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
  except RuntimeError as e:
    # Memory growth must be set before GPUs have been initialized
    print(e)

print("Version: ", tf.__version__)
print("Eager mode: ", tf.executing_eagerly())
print("Hub version: ", hub.__version__)
print("GPU is", "available" if tf.config.list_physical_devices('GPU') else "NOT AVAILABLE")

"""# Data Encoding"""

test1 = test
train1 = train
#test = test.dropna()
train = train.dropna()

#test = test.drop_duplicates(['sentence'], keep='first')
train = train.drop_duplicates(['sentence'], keep='first')

train['purpose'] = train['purpose'].astype('category').cat.codes
test['purpose'] = test['purpose'].astype('category').cat.codes
test1['purpose'] = test1['purpose'].astype('category').cat.codes

x = train.sentence.values

y = train.purpose.values

x_train = train.sentence.values

y_train = train.purpose.values

x_test = test.sentence.values

y_test = test.purpose.values

##Label Encoding

encoder = LabelEncoder()
encoder.fit(y)
encoded_Y_test = encoder.transform(y_test)
encoded_Y_train = encoder.transform(y_train)

# convert integers to dummy variables (i.e. one hot encoded)
dummy_y_test = np_utils.to_categorical(encoded_Y_test)
dummy_y_train = np_utils.to_categorical(encoded_Y_train)

## Tokenization

bert_layer = hub.KerasLayer("https://tfhub.dev/tensorflow/bert_multi_cased_L-12_H-768_A-12/2",
                            trainable=True)

vocab_file = bert_layer.resolved_object.vocab_file.asset_path.numpy()
do_lower_case = bert_layer.resolved_object.do_lower_case.numpy()
tokenizer = tokenization.FullTokenizer(vocab_file, do_lower_case)

tokenizer.convert_tokens_to_ids(['[CLS]', '[SEP]'])

def encode_names(n):
   tokens = list(tokenizer.tokenize(n))
   tokens.append('[SEP]')  # seperation token. Would bemuch more useful if you had a multiple text input.
   return tokenizer.convert_tokens_to_ids(tokens)

sentences = tf.ragged.constant([
    encode_names(n) for n in x_train])

tokenizedSentence = tokenizer.tokenize(x_train[0])

cls = [tokenizer.convert_tokens_to_ids(['[CLS]'])]*sentences.shape[0]
input_word_ids = tf.concat([cls, sentences], axis=-1)
#_ = plt.pcolormesh(input_word_ids[0:10].to_tensor())

input_mask = tf.ones_like(input_word_ids).to_tensor()

type_cls = tf.zeros_like(cls)
type_sentence = tf.ones_like(sentences)
input_type_ids = tf.concat([type_cls, type_sentence], axis=-1).to_tensor()

lens = [len(i) for i in input_word_ids]

max_seq_length = max(lens)
print('Max length is:', max_seq_length)

max_seq_length = int(1.5*max_seq_length)
print('Max length is:', max_seq_length)

def encode_names(n, tokenizer):
   tokens = list(tokenizer.tokenize(n))
   tokens.append('[SEP]')
   return tokenizer.convert_tokens_to_ids(tokens)

def bert_encode(string_list, tokenizer, max_seq_length):
  num_examples = len(string_list)
  
  string_tokens = tf.ragged.constant([
      encode_names(n, tokenizer) for n in np.array(string_list)])

  cls = [tokenizer.convert_tokens_to_ids(['[CLS]'])]*string_tokens.shape[0]
  input_word_ids = tf.concat([cls, string_tokens], axis=-1)

  input_mask = tf.ones_like(input_word_ids).to_tensor(shape=(None, max_seq_length))

  type_cls = tf.zeros_like(cls)
  type_tokens = tf.ones_like(string_tokens)
  input_type_ids = tf.concat(
      [type_cls, type_tokens], axis=-1).to_tensor(shape=(None, max_seq_length))

  inputs = {
      'input_word_ids': input_word_ids.to_tensor(shape=(None, max_seq_length)),
      'input_mask': input_mask,
      'input_type_ids': input_type_ids}

  return inputs

X_train = bert_encode(x_train, tokenizer, max_seq_length)
X_test = bert_encode(x_test, tokenizer, max_seq_length)

"""# Result"""

pred_percnt = new_model.predict(X_test)

pred = []
for i in pred_percnt:  ##추가
      pred.append(int(np.argmax(i))) 
  
real = []
for i in test1['purpose']:
  real.append(int(i))

train1['purpose_cat'] = train1['purpose'].astype('category').cat.codes

cat_pair = train1.drop_duplicates(['purpose']).iloc[:,[0,2]].reset_index(drop = True)

dict_label = {}
for i in range(len(cat_pair)):
  dict_label[str(cat_pair['purpose_cat'][i])] = str(cat_pair['purpose'][i])

print_real = []
for a in real:
  print_real.append(dict_label[str(a)])

print_pred = []
for a in pred:
  print_pred.append(dict_label[str(a)])

# 나중에 삭제
print_list = {"real":print_real, "real_encode":real,"pred":print_pred,"pred_encode":pred}
print_df = pd.DataFrame(print_list)
print_df

print_list = {"pred":print_pred}
result_df = pd.DataFrame(print_list)

result_df.to_csv('result.txt', index=False, header=None, sep="\t")

"""# Test Accuracy"""

loss, accuracy = new_model.evaluate(X_test, dummy_y_test, verbose=False)
print("Testing Accuracy:  {:.4f}".format(accuracy))