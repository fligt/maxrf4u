"""The amazing possibilities of Jupyter ipywidgets and cloud storage"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../notebooks/80_interactive-plotting.ipynb.

# %% auto 0
__all__ = ['UploadDir', 'make_filenames', 'make_gridbox_widget', 'export_element_maps']

# %% ../notebooks/80_interactive-plotting.ipynb 25
import maxrf4u as mx

import skimage.exposure as ske

import json 
import os 

import IPython 

from IPython.display import display
from IPython.display import Image
from IPython.display import HTML


from ipywidgets.embed import embed_minimal_html, embed_data 
from ipywidgets import Layout, HBox, VBox, GridBox, jslink, HTML 
from ipywidgets import Widget 

from ipyleaflet import (Map, projections, ImageOverlay, Rectangle, ZoomControl, FullScreenControl, 
                        DrawControl, WKTLayer, Popup)
import os 

import PIL
import urllib 
import numpy as np 
import matplotlib.pyplot as plt

# %% ../notebooks/80_interactive-plotting.ipynb 26
class UploadDir(): 
    
    def __init__(self, mount_dir, objnr, bucket_url, subdir='images'):
        '''Creates a standard upload (image) directory object. '''
        
        self._mount_dir = mount_dir
        self._objnr = objnr 
        self._subdir = subdir 
        self._bucket_url = bucket_url 
        
        # check mount 
        assert os.path.isdir(mount_dir), f'Directory {mount_dir} was not found. Forgot to mount?' 

        # create subdirectory if needed  
        self._img_dir = os.path.join(mount_dir, objnr, subdir) 
        os.makedirs(self._img_dir, exist_ok=True)
        
        self._images_url = os.path.join(bucket_url, objnr, subdir)
        
        print(f'Created online images folder: {self._images_url}')

        
    def imsave(self, img_list, filename_list, verbose=True): 
        '''Save image arrays `img_list` as `filename_list` in cloud storage.  

        Returns: img_url_list 
        ''' 
        
        print(f'Saving {len(img_list)} images to folder: {self._images_url}')
        
        img_url_list = []
        for img, filename in zip(img_list, filename_list):   
            filepath = os.path.join(self._img_dir, filename) 
            
            # save to rclone mounted image folder 
            plt.imsave(filepath, img) 
            
            img_url = os.path.join(self._bucket_url, self._objnr, self._subdir, filename)
            img_url_list.append(img_url)
            
        if verbose: 
            print('\n')
            for img_url in img_url_list: 
                print(img_url)

        return img_url_list 
    
    
    def listdir(self, filepath=True): 
        '''List local (mounted) file paths for images subfolder. '''
        
        filenames = os.listdir(self._img_dir)
        
        # prefix filepath 
        if filepath:  
            filenames = [os.path.join(self._img_dir, fn) for fn in filenames] 
            
        return filenames 
    
    def listurls(self): 
        '''Construct image urls'''
        
        filename_list = os.listdir(self._img_dir)
        
        img_url_list = []
        for filenames in filename_list: 
            img_url = os.path.join(self._bucket_url, self._objnr, self._subdir, filename)
            img_url_list.append(img_url)
            
        return img_url_list 
    
    def export_interactive_html(self, widget, viztype): 
        '''Save `widget` as interactive html page in cloud storage.
        
        Returns: html_url'''
        
        # create html subdirectory if needed  
        html_dir = os.path.join(self._mount_dir, self._objnr, 'html') 
        os.makedirs(html_dir, exist_ok=True)
        
        html_filename = f'{self._objnr}_{viztype}.html' 
        html_filepath = os.path.join(html_dir, html_filename)
        html_url = os.path.join(self._bucket_url, self._objnr, 'html', html_filename)

        print(f'Saving interactive html to cloud storage...')
        embed_minimal_html(html_filepath, widget)
        print('Click link to load the interactive visualization (opens a separate page).\n')

        print(html_url)
        
        return html_url 
        
    
    
def make_filenames(objnr, viztype, titles, ext): 
    '''Creates standard filenames. 
    
    Returns: filenames
    '''
    
    filenames = []
    for t in titles: 
        fname = f'{objnr}_{viztype}_{t}.{ext}'
        filenames.append(fname)
    
    return filenames




def make_gridbox_widget(img_urls, titles, shape=None): 
    '''Creates multi-image interactive synchronized viewer. '''
    
    # close all widgets to avoid ever growing html export file size  
    Widget.close_all()
    
    # if shape is not specified 
    # assume all images map onto shape of first image 
    if shape is None: 
        shape = np.array(PIL.Image.open(urllib.request.urlopen(img_urls[0]))).shape[0:2] # height, width 
        h, w = shape  

    map_layout = Layout(width='20vw', height='20vw')
    vbox_layout = Layout(width='20.5vw', height='20vw')
    grid_layout = Layout(grid_template_columns="repeat(5, 20.2vw)") 
    
    # make map widgets  
    
    map_widgets = [] 
    for url in img_urls:

        m = Map(center=[h/2, w/2], zoom=-4, crs=projections['Simple'], layout=map_layout, 
                    scroll_wheel_zoom=True, min_zoom=-5)#, interpolation='nearest')
        L
        imo = ImageOverlay(url=url, bounds=[[0, 0], [h, w]]) # bounds= SW NE corners
        fsc = FullScreenControl()
        
        m.add(imo)
        m.add(fsc)
        m.remove(m.layers[0]) # hack to remove world map 
        
        map_widgets.append(m)
        
    # sync map widgets centers and zoom levels via browser javascript 
    first, rest = map_widgets[0], map_widgets[1:]
    for r in rest: 
        jslink([first, 'center'],[r, 'center'])
        jslink([first, 'zoom'],[r, 'zoom'])
    
    # titles 
    
    title_widgets = []
    for t in titles: 
        
        tw = HTML(f'<center><bf>{t}</bf></center>') # ? 
        title_widgets.append(tw)
    
    # combine titles and maps 
    vboxes = []
    for title_widget, map_widget in zip(title_widgets, map_widgets): 
        
        vbox = VBox([title_widget, map_widget], layout=vbox_layout)
        vboxes.append(vbox)
    
    gridbox = GridBox(vboxes, layout=grid_layout)
    
    return gridbox 

def export_element_maps(datastack_file, output_dir=None, histeq=True): 
    '''Save element maps as separate png images.
    '''
    
    ds = mx.DataStack(datastack_file)

    if not output_dir:
        output_dir = ""
        
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
        
    file_name = os.path.basename(datastack_file).removesuffix(mx.DATASTACK_EXT)
    
    element_maps = ds.read('nmf_elementmaps')
    element_nums = ds.read('nmf_atomnums')
    elements = mx.elems_from_atomnums(element_nums)
    
    if histeq:   
        element_maps = [ske.equalize_hist(m) for m in element_maps]
        
    for im, elem in zip(element_maps, elements):

        plt.imsave(f'{output_dir}{file_name}_{elem}.png', im)
        print(f'{output_dir}{file_name}_{elem}.png saved')
