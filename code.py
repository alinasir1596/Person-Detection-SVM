# Imports
import cv2
import os
import pandas as pd
import numpy as np
import sklearn

# %matplotlib inline
import matplotlib.pyplot as plt

# from google.colab.patches import cv2_imshow

# Loading Data

#Helper Function to Load data
def load_images_from_folder(folder, label):
  images = []
  for filename in os.listdir(folder):
    # i=i+1
    # print(i)
    img = cv2.imread(os.path.join(folder,filename),0)
    if img is not None:
      resized = cv2.resize(img, (150,150))
      # plt.imshow(img1)
      images.append(resized)
  labelLength = len(images)
  labelList = [label] * labelLength
  return (images, labelList)

# Getting Train Data
train_data_pos, train_label_pos = load_images_from_folder("INRIAPerson/Train/pos", "human")
train_data_neg, train_label_neg = load_images_from_folder("INRIAPerson/Train/neg", "non-human")

#Getting Test Data
test_data_pos, test_label_pos = load_images_from_folder("INRIAPerson/Test/pos", "human")
test_data_neg, test_label_neg = load_images_from_folder("INRIAPerson/Test/neg", "non-human")

# Pre-Processing Data

# cv2_imshow(test_data_pos[81])

# Calling DataFrame constructor after zipping 
# both lists, with columns specified 
pos_train = pd.DataFrame(list(zip(train_data_pos, train_label_pos)), 
               columns =['Train_img', 'Train_label']) 
neg_train = pd.DataFrame(list(zip(train_data_neg, train_label_neg)), 
               columns =['Train_img', 'Train_label']) 

pos_test = pd.DataFrame(list(zip(test_data_pos, test_label_pos)), 
               columns =['Test_img', 'Test_label']) 
neg_test = pd.DataFrame(list(zip(test_data_neg, test_label_neg)), 
               columns =['Test_img', 'Test_label']) 

train = pos_train.append(neg_train, ignore_index=True)

test = pos_test.append(neg_test, ignore_index=True)

train_shuffled = train.sample(frac=1).reset_index(drop=True)

test_shuffled = test.sample(frac=1).reset_index(drop=True)

# Computing HoG

# HoG for Training Data

#Imports plus Initializing
from skimage import feature
from skimage import exposure
from tqdm.notebook import tqdm

#initialize list that contains training images
train_data = []
train_hog_img = []
# count of all training images to use in loop
train_img_count = len(train_shuffled)
train_img_count

def compute_HOG(image):
  (H1, hogImage1) = feature.hog(image, orientations = 3,
                                pixels_per_cell  = (2, 2), cells_per_block  = (2, 2), transform_sqrt=True,
                                block_norm  = 'L1' , visualize=True)
  return (H1, hogImage1)

# loop over the images
for i in tqdm(range(0,train_img_count)):
  # pre-process image here if needed
  # Computing the HOG features. Also Keep and eye on the parameters used in this function call.
  (h_vector, h_image) = compute_HOG(train_shuffled.Train_img[i])
  #append computed HOGs in train data
  train_data.append(h_vector)
  train_hog_img.append(h_image)

#get train labels
train_label = train_shuffled.Train_label[0:train_img_count]

train_shuffled['HoG_vector'] = train_data
train_shuffled['HoG_img'] = train_hog_img
#train_shuffled.to_csv('TrainData.csv')

# Visualize an example of computed HOG

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4), sharex=True, sharey=True)

ax1.axis('off')
ax1.imshow(train_shuffled.Train_img[i], cmap=plt.cm.gray) #i==499
ax1.set_title('Input image')

# Rescale histogram for better display
hog_image_rescaled = exposure.rescale_intensity(h_image, in_range=(0, 255))

ax2.axis('off')
ax2.imshow(hog_image_rescaled)
ax2.set_title('Histogram of Oriented Gradients')
plt.show()

# length of computed feature vector
print("Length of computed vector\n",len(h_vector))

# HoG for Testing Data

test_data = []
test_hog_img = []
test_img_count = len(test_shuffled)

# loop over the images
for i in tqdm(range(test_img_count)):
  # pre-process image here if needed
  # Computing the HOG features. Also Keep and eye on the parameters used in this function call.
  (h_vector, h_image) = compute_HOG(test_shuffled.Test_img[i])
  #append computed HOGs in train data
  test_data.append(h_vector)
  test_hog_img.append(h_image)

#get labels
test_labels = test_shuffled.Test_label[0:test_img_count]

test_shuffled['HoG_vector'] = test_data
test_shuffled['HoG_img'] = test_hog_img
#test_shuffled.to_csv('TestData.csv')


# train_data = train_shuffled.HoG_vector
# train_label = train_shuffled.Train_label
# test_data = test_shuffled.HoG_vector
# test_labels = test_shuffled.Test_label
# df.infer_objects().dtypes

# SVM

# Training

#train_data --> contains vector histogram of train images
#train_label --> contains labels of train images
#test_data --> contains histogram of test images
#test_labels --> contains labels of test

from sklearn.svm import LinearSVC

# load linear SVM
modelSVC = LinearSVC(max_iter=3000)
modelSVC.fit(train_data, train_label)
print("SVC training completed")

# Saving Model

from joblib import dump, load

dump(modelSVC, 'modelSVM.joblib')

# Loading Model

modelSVC = load('modelSVM.joblib')

# Testing

# Create predictions
predicted_labels = modelSVC.predict(test_data)
print("Prediction completed")
print("Comparing predicted and actual labels")
print(predicted_labels[0:10])
print(test_labels[0:10])

# Performance Report with SVM

# Computing performance measures


mask = predicted_labels==test_labels
correct = np.count_nonzero(mask)
print (correct*100.0/predicted_labels.size)

# Confusion Matrix

act = pd.Series(test_labels,name='Actual')
pred = pd.Series(predicted_labels,name='Predicted')
confusion_matrix = pd.crosstab(act, pred,margins=True)
print("Confusion matrix:\n%s" % confusion_matrix)

#Plotting Above Confusion Matrix
def plot_confusion_matrix(df_confusion, title='Confusion matrix', cmap=plt.cm.YlOrRd):
  plt.matshow(df_confusion, cmap=cmap) # imshow
  plt.colorbar()
  tick_marks = np.arange(len(df_confusion.columns))
  plt.xticks(tick_marks, df_confusion.columns, rotation=45)
  plt.yticks(tick_marks, df_confusion.index)
  plt.ylabel(df_confusion.index.name)
  plt.xlabel(df_confusion.columns.name)

  
#call function
plot_confusion_matrix(confusion_matrix)

#confusion_matrix.to_csv('SVM_ConfusionMatrix.csv')

# Classification Report

from sklearn.metrics import classification_report
print(classification_report(test_labels, predicted_labels, target_names=["human","non-human"]))

# Classifying Few correctly classified images

# set index out of 10000 test images
index = 5
#get image
image = test_shuffled.Test_img[index]

#compute hog feature vector for above image
(h_vector, h_image) = compute_HOG(image)
obtained_label = modelSVC.predict([h_vector])

#comparison
print("Actual Label =")
print(test_labels[index])
print("Predicted Label =")
print(obtained_label[0])

#visualize
figr, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4), sharex=True, sharey=True)
ax1.axis('off')
ax1.imshow(image, cmap="gray")
ax1.set_title('Input image')
ax2.axis('off')
ax2.imshow(h_image,cmap=plt.cm.gray)
ax2.set_title('Histogram of Oriented Gradients')
plt.show()

# set index out of 10000 test images
index = 157
#get image
image = test_shuffled.Test_img[index]

#compute hog feature vector for above image
(h_vector, h_image) = compute_HOG(image)
obtained_label = modelSVC.predict([h_vector])

#comparison
print("Actual Label =")
print(test_labels[index])
print("Predicted Label =")
print(obtained_label[0])

#visualize
figr, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4), sharex=True, sharey=True)
ax1.axis('off')
ax1.imshow(image, cmap="gray")
ax1.set_title('Input image')
ax2.axis('off')
ax2.imshow(h_image,cmap=plt.cm.gray)
ax2.set_title('Histogram of Oriented Gradients')
plt.show()

# set index out of 10000 test images
index = 927
#get image
image = test_shuffled.Test_img[index]

#compute hog feature vector for above image
(h_vector, h_image) = compute_HOG(image)
obtained_label = modelSVC.predict([h_vector])

#comparison
print("Actual Label =")
print(test_labels[index])
print("Predicted Label =")
print(obtained_label[0])

#visualize
figr, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4), sharex=True, sharey=True)
ax1.axis('off')
ax1.imshow(image, cmap="gray")
ax1.set_title('Input image')
ax2.axis('off')
ax2.imshow(h_image,cmap=plt.cm.gray)
ax2.set_title('Histogram of Oriented Gradients')
plt.show()

# set index out of 10000 test images
index = 741
#get image
image = test_shuffled.Test_img[index]

#compute hog feature vector for above image
(h_vector, h_image) = compute_HOG(image)
obtained_label = modelSVC.predict([h_vector])

#comparison
print("Actual Label =")
print(test_labels[index])
print("Predicted Label =")
print(obtained_label[0])

#visualize
figr, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4), sharex=True, sharey=True)
ax1.axis('off')
ax1.imshow(image, cmap="gray")
ax1.set_title('Input image')
ax2.axis('off')
ax2.imshow(h_image,cmap=plt.cm.gray)
ax2.set_title('Histogram of Oriented Gradients')
plt.show()

# set index out of 10000 test images
index = 139
#get image
image = test_shuffled.Test_img[index]

#compute hog feature vector for above image
(h_vector, h_image) = compute_HOG(image)
obtained_label = modelSVC.predict([h_vector])

#comparison
print("Actual Label =")
print(test_labels[index])
print("Predicted Label =")
print(obtained_label[0])

#visualize
figr, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4), sharex=True, sharey=True)
ax1.axis('off')
ax1.imshow(image, cmap="gray")
ax1.set_title('Input image')
ax2.axis('off')
ax2.imshow(h_image,cmap=plt.cm.gray)
ax2.set_title('Histogram of Oriented Gradients')
plt.show()

# set index out of 10000 test images
index = 789
#get image
image = test_shuffled.Test_img[index]

#compute hog feature vector for above image
(h_vector, h_image) = compute_HOG(image)
obtained_label = modelSVC.predict([h_vector])

#comparison
print("Actual Label =")
print(test_labels[index])
print("Predicted Label =")
print(obtained_label[0])

#visualize
figr, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4), sharex=True, sharey=True)
ax1.axis('off')
ax1.imshow(image, cmap="gray")
ax1.set_title('Input image')
ax2.axis('off')
ax2.imshow(h_image,cmap=plt.cm.gray)
ax2.set_title('Histogram of Oriented Gradients')
plt.show()

# set index out of 10000 test images
index = 456
#get image
image = test_shuffled.Test_img[index]

#compute hog feature vector for above image
(h_vector, h_image) = compute_HOG(image)
obtained_label = modelSVC.predict([h_vector])

#comparison
print("Actual Label =")
print(test_labels[index])
print("Predicted Label =")
print(obtained_label[0])

#visualize
figr, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4), sharex=True, sharey=True)
ax1.axis('off')
ax1.imshow(image, cmap="gray")
ax1.set_title('Input image')
ax2.axis('off')
ax2.imshow(h_image,cmap=plt.cm.gray)
ax2.set_title('Histogram of Oriented Gradients')
plt.show()

