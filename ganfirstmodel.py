# -*- coding: utf-8 -*-
"""GANFirstModel.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/165AH-ZwTOTatA2m7DvWdlFOeAXANwi8-
"""

!pip install torchvision jupyter tensorboardx pillow

import torch 
from torch import nn, optim
from torch.autograd.variable import Variable
from torchvision import transforms, datasets

"""Importing logger to keep a track of training progress"""

from utils import Logger

"""##Importing MNIST Data
Using the MNIST Dataset
Training the Generative network :[link text](https://github.com/soumith/ganhacks)
"""

def mnist_data():
  #transforms.Compose makes multiple transformations at once.
  #transforms.Normalize((mean1,mean2. . . mean n), (std1, std2. . . std n)) normalized n dimensional data with respective means and standard deviations
  compose=transforms.Compose([transforms.ToTensor(),transforms.Normalize((0.5,0.5,0.5),(0.5,0.5,0.5))])
  out_dir='./dataset' #Directory where mnist needs to be downladed
  #download the mnist dataset in output directory 'out_dir' and applies transformations 'compose'
  # here the dataset is returned as a tensor
  return datasets.MNIST(root=out_dir,train=True,transform=compose, download=True)

data=mnist_data()

data_loader=torch.utils.data.DataLoader(data, batch_size=100,shuffle=True)
num_batches=len(data_loader)

"""## Discriminative Netwrok
Defining Discriminator function first. Input will be an image(flattened, one dimensinal) and ouput would be probability(1: real image, 0: fake image)
3 hidden layers using Leaky Relu
Dropout layer use at the end to prevent overfitting.
A sigmoid function is applied to get the output between 0 and 1.
"""

class DiscriminatorGan(torch.nn.Module):
  def __init__(self):
    #super ?? 
    super(DiscriminatorGan,self).__init__()
    n_features = 784
    n_out=1
    
    #Making the model
    #Sequential hidden layer: input nodes: n_features, output nodes: 1024, activation function: LeakyuRelu
    self.hidden0= nn.Sequential(nn.Linear(n_features,1024),nn.LeakyReLU(0.2),nn.Dropout(0.3))
    # nn.Dropout(probability) introduces random zeros to prevent overfitting, i.e. regularizing and preventing the coadapting of neurals.
    #probability is the probability than an element becomees 0
    
    #nn.LeakyRelU(negative_slope) leakyrelu(x)=max(0,x)+negative_slopt*min(0,x)
    self.hidden1=nn.Sequential(nn.Linear(1024,512),nn.LeakyReLU(0.2),nn.Dropout(0.3))
    self.hidden2=nn.Sequential(nn.Linear(512,256),nn.LeakyReLU(0.2),nn.Dropout(0.3)) 
    self.out=nn.Sequential(torch.nn.Linear(256,n_out),torch.nn.Sigmoid()) #Sigmoid at the end to get thevaues between 0 and 1
  
  #one forward pass for input x
  def forward(self,x):
    x=self.hidden0(x)
    x=self.hidden1(x)
    x=self.hidden2(x)
    x=self.out(x)
    return x
  
discriminator=DiscriminatorGan()

"""Adding funcionality to flatten an image and vice versa. 
Flattening means to convert a multidimensional matrix to one dimensional
"""

def images_to_vectors(images):
  return images.view(images.size(0),784) #parameters: (size to flatten(28 here, row size), no. of images to be flattened)

def vectors_to_images(vectors):
  return vectors.view(vectors.size(0),1,28,28) # to convert each row of vectors to 28x28 pixels images 
# parameteres: (initial flattened dim, no. of sub vectors to be converted to 2d, 2d dimensions of output )

"""## Generative Network
Constructing the Generative network
Here the input is an latent valued image and th eoutput is a flattened image.
3 hidden layers, each followed by leakyrelu.
The output layer has TanH activation Function which maps resulting values to -1 to 1. like out normalized mnist images are bound.
"""

class GeneratorGan(torch.nn.Module):
  def __init__(self):
    super(GeneratorGan,self).__init__() # Why is a super constructor created?
    n_features=100 # Can n_features be any random no.
    n_out=784 # flattened output image
    # Why no. of nodes in reverse order as compared to discriminator?
    self.hidden0=nn.Sequential(nn.Linear(n_features,256),nn.LeakyReLU(0.2)) 
    self.hidden1=nn.Sequential(nn.Linear(256,512),nn.LeakyReLU(0.2))
    self.hidden2=nn.Sequential(nn.Linear(512,1024),nn.LeakyReLU(0.2))# how does leaky rely work? and what is its significance?
    self.out=nn.Sequential(nn.Linear(1024,n_out),nn.Tanh())   
  def forward(self,x):
    x=self.hidden0(x)
    x=self.hidden1(x)
    x=self.hidden2(x)
    x=self.out(x)
    return x
  
generator=GeneratorGan()

"""##Noise generation function
Function to generate random noise for generator. The noise is noramlized with mean 0 and standard devi 1. Why?
"""

def noise(size):
  n=Variable(torch.randn(size,100))
  return n

"""##Optimization
Adam optimizer used with learning rate = 0.0002
"""

d_optimizer=optim.Adam(discriminator.parameters(),lr=0.0002)
g_optimizer=optim.Adam(generator.parameters(),lr=0.0002)

"""##Loss Function
Using binary cross entropy lss function. then calculating average of loss from each minibatch.
![Loss Function of Gan](https://cdn-images-1.medium.com/max/2000/1*IcuF1_TXjngF2VHQjdwzjg.png)
Here the weights will be 1. Why?
The ouputs yi is 1 and replacing the first input v1 as D(x) and second input vi = D(G(x)). what it (1-y) in the second term?
Since we have to ascent the gradient in Gan. Why? and bce loss function is for gradient 'descent'. we add a negative sign on the loss function
"""

loss=nn.BCELoss()

"""Now since the output for real images is 1 and fake images is zero"""

def ones_target(size):
  #returning tensor variable containing ones, with shape =size
  data=Variable(torch.ones(size,1))
  return data

def zeros_target(size):
  data=Variable(torch.zeros(size,1))
  return data

"""Training the gradients of generator and discriminator separately"""

#Here optimizer is adam optim. created above, as d_optimizer or g_optimizer
def train_discriminator(optimizer, real_data, fake_data):
  N=real_data.size(0)
  #reset gradients
  optimizer.zero_grad()
  
  #training on real_data
  prediction_real=discriminator(real_data)
  #error calculation for back propogation
  error_real=loss(prediction_real,ones_target(N))
  #inbuilt function"backward" in bce loss class 
  error_real.backward()
  
  #training on fake dat
  prediction_fake=discriminator(fake_data)
  error_fake=loss(prediction_fake,zeros_target(N))
  error_fake.backward()
  
  #updating weights and grad
  optimizer.step()
  return error_real+ error_fake, prediction_real, prediction_fake

"""Now training generator, the generator has a different loss function.
![Generator loss funtion](https://cdn-images-1.medium.com/max/1600/1*77HB-XBWpCc-ZIGbyaOisA.png)
"""

def train_generator(optimizer, fake_data):
  N=fake_data.size(0)
  optimizer.zero_grad() #zero out the parameters of optimizer, because there are the no weights.
  #generating fake data by noise
  prediction=discriminator(fake_data)
  
  error=loss(prediction,ones_target(N))
  error.backward()
  optimizer.step()
  return error

num_test_samples=16
#generating test samples
test_noise=noise(num_test_samples)

"""##Training the Gan"""

!pip install --no-cache-dir -I pillow

from PIL import Image
def register_extension(id, extension): Image.EXTENSION[extension.lower()] = id.upper()
Image.register_extension = register_extension
def register_extensions(id, extensions): 
  for extension in extensions: register_extension(id, extension)
Image.register_extensions = register_extensions

from PIL import Image
#creating logger instance
logger=Logger(model_name='VGAN',data_name='MNIST')
num_epochs=50
num_batches = len(data_loader)
for epoch in range(num_epochs):
  for n_batch,(real_batch,_) in enumerate(data_loader):
    N=real_batch.size(0)
    
    #Train discriminator
    real_data=Variable(images_to_vectors(real_batch))
    #generate fake data and detach to avoid further calculation of gradients
    fake_data=generator(noise(N)).detach()
    
    #train
    d_error,d_pred_real,d_pred_fake=train_discriminator(d_optimizer, real_data, fake_data)
    
    #Train Generator
    #generate fake data
    fake_data=generator(noise(N))
    #train 
    g_error=train_generator(g_optimizer, fake_data)
    #Log batch error
    logger.log(d_error, g_error, epoch, n_batch, num_batches)
    if(n_batch)%100==0: #??
      test_images=vectors_to_images(generator(test_noise))
      test_images=test_images.data
#       logger.log_images(test_images, num_test_samples,epoch, n_batch, num_batches);
            
      #display status logs
      logger.display_status(epoch, num_epochs,n_batch,num_batches,d_error,g_error,d_pred_real,d_pred_fake)
      import matplotlib.pyplot as plt
      f, axarr = plt.subplots(2, 2)
      axarr[0, 0].imshow(test_images[0,0])
      axarr[0,1].imshow(test_images[1,0])
      axarr[1, 0].imshow(test_images[2,0])
      axarr[1, 1].imshow(test_images[3,0])
      # Fine-tune figure; make subplots farther from each other.
      f.subplots_adjust(hspace=0.3)

      plt.show()

import matplotlib.pyplot as plt
f, axarr = plt.subplots(2, 2)
axarr[0, 0].imshow(test_images[0,0])
axarr[0,1].imshow(test_images[1,0])
axarr[1, 0].imshow(test_images[2,0])
axarr[1, 1].imshow(test_images[3,0])
# Fine-tune figure; make subplots farther from each other.
f.subplots_adjust(hspace=0.3)

plt.show()

"""https://medium.com/ai-society/gans-from-scratch-1-a-deep-introduction-with-code-in-pytorch-and-tensorflow-cb03cdcdba0f"""