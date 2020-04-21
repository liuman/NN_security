from Data_loader import Data_loader
import numpy as np
import random
from antialliasing import rotated_stripe, calc_dist
import yaml
import math
from math import cos, sin
import os
from os.path import join

class Data_loader_lines(Data_loader):
    """
This experiment is creating tilted lines and checking how humans and AI compare in both
accuracy and confidence estimate. 
----------
number_of_samples (int): Number of images generated for the test
grid_size (int): Size of images (grid_size x grid_size)

Methods
-------
load_data(): Loads the training data.
"""
    def __init__(self, arguments):
        super(Data_loader_lines, self).__init__(arguments)
        required_keys = ['number_of_samples', 'grid_size', 'side_length', 'width','save','images','labels']

        self._check_for_valid_arguments(required_keys, arguments)
        self.number_of_samples = arguments['number_of_samples']
        self.grid_size = arguments['grid_size']
        self.side_length = arguments['side_length']
        self.width= arguments['width']
        self.save = arguments['save']
        self.images = arguments['images']
        self.labels = arguments['labels']
        self.shift = arguments['shift']
        self.epsilon = arguments['epsilon']
    def load_data(self):
        data, label = self._generate_set()
        
        return data, label 

    def load_data2(self):
        data, label = self._generate_set2()

        return data, label

    def load_data3(self):
        data, label = self._generate_set3()

        return data, label

    def _generate_set(self, shuffle= True):
        
        n = self.number_of_samples
        L = self.grid_size
        a = self.side_length
        w = self.width
        shift = self.shift
        epsilon = self.epsilon

        data = np.ones([n,L,L])
        label = np.zeros([n,1])
        angle = np.zeros(n)

        for i in range(n):
            
            sensible = 0
            while sensible==0:
                i1 = np.random.randint(L-a-7) +2
                j1 = np.random.randint(L-a-7) +2
                angle[i] = np.random.normal(45,18)
                if angle[i]<0:
                    angle[i] = 0
                    sensible = 1
                elif angle[i] > 90:
                    angle[i] = 90
                    sensible = 1
                elif (abs(int(round(a*cos(angle[i]*math.pi/180)))) == abs(int(round(a*sin(angle[i]*math.pi/180))))):
                    sensible = 0 
                else:
                    sensible = 1
            data[i,:,:] = rotated_stripe(i1,j1, a, w, angle[i], L)
            
            if angle[i]<45:
                label[i] = 1
            '''
                if shift == True:
                    data[i,:,:] += epsilon     
            elif shift == True:
                    data[i,:,:] -= epsilon
            '''
        data = np.expand_dims(data, axis =3)
        image_link = join("data",self.images)
        label_link = join("data",self.images)
        if self.save == True :
            np.save(image_link,data)
            np.save(label_link,label)

        return data, label

    def _generate_set2(self):

        n = self.number_of_samples
        L = self.grid_size
        a = self.side_length
        w = self.width

        data = np.zeros((n,L,L))
        label = np.zeros([n,1])
        angle = np.zeros(n)

        for i in range(n):
            
            sensible = 0
            while sensible==0:
                i1 = np.random.randint(L-a-7) + 2
                j1 = np.random.randint(L-a-7) + 2 
                angle[i] = np.random.normal(45,18)
                if angle[i]<0:
                    angle[i] = 0
                    sensible = 1
                elif angle[i] > 90:
                    angle[i] = 90
                    sensible = 1
                elif (abs(int(round(a*cos(angle[i]*math.pi/180)))) == abs(int(round(a*sin(angle[i]*math.pi/180))))):
                    sensible = 0 
                else:
                    sensible = 1
            data[i,:,:] += rotated_stripe(i1,j1, a, w, angle[i], L) 
            
            if angle[i]<45:
                label[i] = 1

        data = np.expand_dims(data, axis =3)
        image_link = join("data",self.images)
        label_link = join("data",self.images)
        if self.save == True :
            np.save(image_link,data)
            np.save(label_link,label)

        return data, label

    def _generate_set3(self):
        
        n = self.number_of_samples
        L = self.grid_size
        a = self.side_length
        w = self.width
        shift = self.shift
        epsilon = self.epsilon
        ep = np.ones([L,L])*epsilon
        data = np.ones([n,L,L])
        label = np.zeros([n,1])
        angle = np.zeros(n)

        for i in range(n):
            
            i1 = np.random.randint(L-a-7) +2
            j1 = np.random.randint(L-a-7) +2
            angle[i] = 90*np.random.binomial(1,0.5)
            data[i,:,:] = rotated_stripe(i1,j1, a, w, angle[i], L)
        
            if angle[i]<45:
                label[i] = 1
           
                if shift == True:
                    data[i] += ep
                '''
                    if epsilon > 0:
                        data[i] = data[i]*(1-epsilon)
                    else:
                        data[i] = data[i]*(1+epsilon) - epsilon 
                '''
            elif shift == True:
                data[i] -= ep
                '''
                if epsilon > 0 :
                    data[i] = epsilon + data[i]*(1-epsilon)
                else:
                    data[i] = data[i]*(1+epsilon)
                '''
        data = np.expand_dims(data, axis =3)
        image_link = join("data",self.images)
        label_link = join("data",self.images)

        if self.save == True :
            np.save(image_link,data)
            np.save(label_link,label)

        return data, label


if __name__ =="__main__":

    with open("config_lines.yml") as ymlfile:
        cgf = yaml.load(ymlfile, Loader=yaml.SafeLoader)
    dataset = Data_loader_lines(cgf["DATASET_TRAIN"]["arguments"])
    data,label = dataset.load_data()

