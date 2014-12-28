__author__ = 'Michael'

import Pyramids
import numpy as np
import Helper
from skimage.filter import hsobel, vsobel,canny
from skimage.io import imread
from skimage.viewer import ImageViewer
from skimage import color
from sys import maxint
import math
'''
Feature extraction:
'''
def gradient_map(image):
    h = hsobel(image)
    v = vsobel(image)
    return np.dstack((h,v))

def gradient_orientation_map(image):
    h = hsobel(image)
    v = vsobel(image)
    return np.arctan2(h,v)

def edge_map(image):
    return canny(image)

'''
Matching algorithm:
'''

def match(left_edges, left_gradients, right_edges, right_gradients, search_radius):
    #Pad the edge images:
    padded_left_edges = np.pad(left_edges, (search_radius,search_radius), 'constant', constant_values=(0,0))
    padded_right_edges = np.pad(right_edges, (search_radius,search_radius), 'constant', constant_values=(0,0))

    points = np.zeros_like(left_edges)
    values = np.zeros_like(left_edges, dtype=np.float)

    #Iterate through the image:
    for x in xrange(search_radius, len(padded_left_edges)-search_radius):
        for y in xrange(search_radius, len(padded_left_edges[0])-search_radius):

            #Check if there is an edge:
            if padded_left_edges[x,y]:
                best_similarity = -1
                #Iterate through the window to see if there are other edges:
                for i in xrange(-search_radius, search_radius):
                    for j in xrange(-search_radius, search_radius):
                        if padded_right_edges[x+i,y+j]:
                            g1 = left_gradients[x-search_radius,y-search_radius]
                            g2 = right_gradients[x-search_radius+i,y-search_radius+j]

                            #Calculate cosine distance:
                            n1 = np.linalg.norm(g1)
                            n2 = np.linalg.norm(g2)

                            #We dont like zero gradients:
                            if n1 != 0 and n2 != 0:
                                #Compare it:
                                similarity = np.dot(g1, g2)/n1/n2

                                if similarity > best_similarity:
                                    points[x-search_radius,y-search_radius] = 1
                                    values[x-search_radius,y-search_radius] = math.sqrt(i**2 + j**2)
                                    best_similarity = similarity


    return points, values

'''
Stereoanalysis:
'''

#Define a stereoanalysis program function using the submodules:
def analyse(left_image, right_image, pyramid_levels=4, search_radius = 10, maxitt=100, l=0.01):
    print "pyramids"
    #Calculate pyramids:
    left_pyramid = Pyramids.down_pyramid(left_image, levels=pyramid_levels)
    right_pyramid = Pyramids.down_pyramid(right_image, levels=pyramid_levels)

    #Define some arrays to hold edges and gradients:
    left_edges = [None]*pyramid_levels
    left_gradients = [None]*pyramid_levels
    right_edges = [None]*pyramid_levels
    right_gradients = [None]*pyramid_levels

    print "edges and gradients"

    #Do the calculation:
    for i in xrange(pyramid_levels):
        viewer = ImageViewer(left_pyramid[i])
        left_edges[i] = edge_map(left_pyramid[i])
        right_edges[i] = edge_map(right_pyramid[i])
        left_gradients[i] = gradient_map(left_pyramid[i])
        right_gradients[i] = gradient_map(left_pyramid[i])

    result_matrices = [None]*pyramid_levels

    #TODO: What are we supposed to do with the first layer?
    print left_image.shape
    result_matrices[-1] = np.zeros_like(left_edges[-1], dtype=np.float)
    print result_matrices

    print [x.shape for x in left_edges]

    #set first prior
    print "start stuff"
    #Run through the layers, interpolating from the previous:
    for i in reversed(xrange(pyramid_levels)):
        print "level",i
        (points, values) = match(left_edges[i], left_gradients[i], right_edges[i], right_gradients[i], search_radius)
        print "done matching"
        print result_matrices[i].shape
        print points.shape
        print values.shape
        result_matrices[i] = Helper.interp(result_matrices[i], points, values, maxitt, l)
        viewer = ImageViewer(result_matrices[i])
        viewer.show()
        print "done interp"
        if i > 0:
            result_matrices[i-1] = np.multiply(Pyramids.upsample(result_matrices[i],desired_corrected_size=left_edges[i-1].shape),2)

    #Return the interpolation at the top level:
    return result_matrices[0]

def show_disparity_map(disparity_map):
    #Scale to zero:
    image = np.subtract(disparity_map, np.min(disparity_map))

    if np.max(image) != 0:
        #Normalize and invert:
        image = np.multiply(image, -255.0/float(np.max(image)))
        image = np.add(image, 255)


    #Show the stuff:
    viewer = ImageViewer(image.astype(np.uint8))
    viewer.show()

'''
Testing:
'''

if __name__ == "__main__":
    limg = imread('pentagonL.jpg')
    limg2 = color.rgb2gray(limg)
    rimg = imread('pentagonR.jpg')
    rimg2 = color.rgb2gray(rimg)

    print "done loading"

    img3 = analyse(limg2, rimg2, pyramid_levels=4,maxitt=100)

    show_disparity_map(img3)
