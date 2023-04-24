#!/usr/bin/env python3

#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

# Stream Deck XL has key size of 144 x 144 pixel
# spacing between keys is considered as 36 pixel
# a 3 x 2 image has (144 * 3) + (2 * 36) = 504
#  (144 * 2) + (1 * 36) = 324

import time
import os
import numpy
import threading
import json
import requests
from pickle import load

import argparse

from PIL import Image, ImageDraw, ImageOps, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

# Folder location of image assets used by this example.
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "Assets")
#typos = 'HalvarEng-Bd.ttf', 'HalvarEng-Bd.ttf'

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
       #message =  "threading.current_thread().getName()".encode()
        self.wfile.write(json_message)
        return
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return super(Handler, self).end_headers()

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

class MyServer(threading.Thread):
    def run(self):
        self.server = ThreadedHTTPServer(('localhost', 8000), Handler)
        self.server.serve_forever()
    def stop(self):
        self.server.shutdown()

# Generates an image that is correctly sized to fit across all keys of a given
# StreamDeck.
def create_partial_deck_sized_image(deck, key_spacing, image_filename, key_rows_man = 2, key_cols_man = 3 ):
    #key_rows, key_cols = deck.key_layout()
    
    key_rows = key_rows_man
    key_cols = key_cols_man
    
    key_width, key_height = deck.key_image_format()['size']   
    
    spacing_x, spacing_y = key_spacing

    # Compute total size of the full StreamDeck image, based on the number of
    # buttons along each axis. This doesn't take into account the spaces between
    # the buttons that are hidden by the bezel.
    key_width *= key_cols
    key_height *= key_rows

    # Compute the total number of extra non-visible pixels that are obscured by
    # the bezel of the StreamDeck.
    spacing_x *= key_cols - 1
    spacing_y *= key_rows - 1
    
    # Compute final full deck image size, based on the number of buttons and
    # obscured pixels.
    full_deck_image_size = (key_width + spacing_x, key_height + spacing_y)

    # Resize the image to suit the StreamDeck's full image size. We use the
    # helper function in Pillow's ImageOps module so that the image's aspect
    # ratio is preserved.
    image = Image.open(os.path.join(ASSETS_PATH, image_filename)).convert("RGBA")
    image = ImageOps.fit(image, full_deck_image_size, Image.LANCZOS)

    return image


# Crops out a key-sized image from a larger deck-sized image, at the location
# occupied by the given key index.
def crop_key_image_from_deck_sized_image(deck, 
                                         image, 
                                         key_spacing,
                                         key,
                                         delta_row = 0,
                                         delta_col = 0):
    
    key_rows, key_cols = deck.key_layout()
    
    key_width, key_height = deck.key_image_format()['size']
    
    
    spacing_x, spacing_y = key_spacing

    # Determine which row and column the requested key is located on.
    row = key // key_cols - delta_row
    col = key % key_cols - delta_col
    
    # Compute the starting X and Y offsets into the full size image that the
    # requested key should display.
    start_x = col * (key_width + spacing_x)
    start_y = row * (key_height + spacing_y)

    # Compute the region of the larger deck image that is occupied by the given
    # key, and crop out that segment of the full image.
    region = (start_x, start_y, start_x + key_width, start_y + key_height)
    segment = image.crop(region)

    # Create a new key-sized image, and paste in the cropped section of the
    # larger image.
    key_image = PILHelper.create_image(deck)
    key_image.paste(segment)

   # return PILHelper.to_native_format(deck, key_image)
    return key_image


# Generates a custom tile with run-time generated text and custom image via the
# PIL module.
def render_key_image(deck,
                     icon_filename = "{}.png".format("Exit"),
                     font_filename = 'HalvarEng-Bd.ttf', 
                     label_text = 'DEFAULT'
                     ):
    # Resize the source image asset to best-fit the dimensions of a single key,
    # leaving a margin at the bottom so that we can draw the key title
    # afterwards.
    
    icon_filename = os.path.join(ASSETS_PATH, icon_filename)

    icon = Image.open(icon_filename)
    image = PILHelper.create_scaled_image(deck, icon, margins=[0,0, 0,0])


    return image


# Generates a custom tile with run-time generated text and custom image via the
# PIL module.
def render_key_text(deck,
                    icon_filename = "{}.png".format("Solid_black"),  
                    font_filename = 'HalvarEng-Bd.ttf', 
                    label_text = 'DEFAULT',
                    fill = 'white',
                    font_size = 28):
    # Resize the source image asset to best-fit the dimensions of a single key,
    # leaving a margin at the bottom so that we can draw the key title
    # afterwards.
    
    icon_filename = os.path.join(ASSETS_PATH, icon_filename)
    font_filename = os.path.join(ASSETS_PATH, font_filename)
    
    icon = Image.open(icon_filename)
    image = PILHelper.create_scaled_image(deck, icon, margins=[0, 0, 0, 0])

    # Load a custom TrueType font and use it to overlay the key index, draw key
    # label onto the image a few pixels from the bottom of the key.
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_filename, font_size)
    draw.text((3, image.height / 2 ), 
              text=label_text, 
              font=font,
              anchor="lm",
              fill=fill)
   # return PILHelper.to_native_format(deck, image)
    return image


# Takes an exisiting key and adds run-time generated text via the
# PIL module.
def render_text_over_image(deck,
                           existing_key_image,  
                           font_filename = 'HalvarEng-Bd.ttf', 
                           label_text = 'DEFAULT',
                           fill = 'white',
                           font_size = 28):
    # Resize the source image asset to best-fit the dimensions of a single key,
    # leaving a margin at the bottom so that we can draw the key title
    # afterwards.
    
    font_filename = os.path.join(ASSETS_PATH, font_filename)
    
    #image = PILHelper.create_scaled_image(deck, existing_key_image)

    # Load a custom TrueType font and use it to overlay the key index, draw key
    # label onto the image a few pixels from the bottom of the key.
    draw = ImageDraw.Draw(existing_key_image)
    font = ImageFont.truetype(font_filename, font_size)
    draw.text((3, existing_key_image.height / 2 ), 
              text=label_text, 
              font=font,
              anchor="lm",
              fill=fill)

    #return PILHelper.to_native_format(deck, image)
    return existing_key_image

# Returns style information about display of certain product groups
def get_product_group_info(response, iterator = 0, product_group = 'Alternator'):
    
    product_group = response['product_group_prediction_list']['predictions'][iterator]['product_group']
    
    print(product_group)
    
    # ID
    if product_group == 'Alternator': # aka 'Alternator'
        image_file_name = "Alternator_real_squared.png"
        label_text = "ALTER\nNATOR"
        fill = 'black'
    
    # ID  
    elif product_group == 'Starter': #'Starter':
        image_file_name = "Starter_StreamDeck_XL.png"
        label_text = "STARTER"
        fill = 'black'
    
    # ID
    elif product_group == 'CommonRailInjector': #'CommonRailInjector':
        image_file_name = "CommonRailInjector_StreamDeck_XL.png"
        label_text = "COMMON\nRAIL\nINJECTOR"
        fill = 'black'
    
    # ID
    elif product_group == 'DieselInjector': #'DieselInjector':
        image_file_name = "DieselInjector_StreamDeck_XL.png"
        label_text = "DIESEL\nINJECTOR"
        fill = 'black'
    
    elif product_group == 'CommonRailHighPressurePump': #'CommonRailHighPressurePump':
        image_file_name = "CommonRailHighPressurePump_StreamDeck_XL.png"
        label_text = "COMMON\nRAIL\nHIGH\nPRESSURE\nPUMP"
        fill = 'black'
    
    elif product_group == 'BrakeCaliper': #'BrakeCaliper':
        image_file_name = "brake-caliper.png"
        label_text = "BRAKE\nCALIPER"
        fill = 'black'
    
    elif product_group == 'ClutchDisc': #'ClutchDisc':
        image_file_name = "clutch-disc.png"
        label_text = "CLUTCH\nDISC"
        fill = 'black'
    
    elif product_group == 'UnitInjector': #'UnitInjector':
        image_file_name = "diesel-injector.jpg"
        label_text = "UNIT\nINJECTOR"
        fill = 'black'
    
    elif product_group == 'Compressor': #'Compressor':
        image_file_name = "Alternator_right_white_small.png"
        label_text = "COM\nPRESSOR"
        fill = 'black'
    
    elif product_group == 'Injectionpump': #'InjectionPump':
        image_file_name = "InjectionPump_StreamDeck_XL.png"
        label_text = "INJECT\nION\nPUMP"
        fill = 'black'
        
    elif product_group == 'PSG5-Set': #'PSG5-Set':
        image_file_name = "PSG5-Set_StreamDeck_XL.png"
        label_text = "PSG5\nSET"
        fill = 'black'
        
    elif product_group == 'steeringCV': #'PSG5-Set':
        image_file_name = "SteeringCV_StreamDeck_XL.png"
        label_text = "STEERING\nCV"
        fill = 'black'
    
    elif product_group == 'Ignitiondistributor': #'PSG5-Set':
        image_file_name = "Ignitiondistributor_StreamDeck_XL.png"
        label_text = "IGNITION\nDISTRIBUTOR"
        fill = 'black'
    
    elif product_group == 'Steeringpump': #'PSG5-Set':
        image_file_name = "Steeringpump_StreamDeck_XL.png"
        label_text = "STEERING\nPUMP"
        fill = 'black'

    elif product_group == 'hydraulicsteering': #'PSG5-Set':
        image_file_name = "Hydraulicsteering_StreamDeck_XL.png"
        label_text = "HYDRAULIC\nSTEERING"
        fill = 'black'
    
    elif product_group == 'UnitPump': #'PSG5-Set':
        image_file_name = "Unitpump_StreamDeck_XL.png"
        label_text = "UNIT\nPUMP"
        fill = 'black'
    
    elif product_group == 'electronicsteering': #'PSG5-Set':
        image_file_name = "Electronicsteering_StreamDeck_XL.png"
        label_text = "ELECTRONIC\nSTEERING"
        fill = 'black'
        
    elif product_group == 'ECU': #'PSG5-Set':
        image_file_name = "ECU_StreamDeck_XL.png"
        label_text = "ECU"
        fill = 'black'
               
    elif product_group == 'Electricpump': #'PSG5-Set':
        image_file_name = "Electricpump_StreamDeck_XL.png"
        label_text = "ELECTRIC\nPUMP"
        fill = 'black'
        
    elif product_group == 'DNOX2': #'PSG5-Set':
        image_file_name = "DNOX2_StreamDeck_XL.png"
        label_text = "DNOX2"
        fill = 'black'
            
    elif product_group == 'OtherProduct': #'OtherProduct':
        image_file_name = "Alternator.png"
        label_text = "OTHER\nPRODUCT"
        fill = 'white'
            
    else:
        image_file_name = "Alternator.png"
        label_text = "FALSE"
        fill = 'white'
        
    return {
        "label_text": label_text,
        "fill": fill,
        "image_file": os.path.join(ASSETS_PATH, image_file_name),
        "image_file_name": image_file_name
        }

# Returns style information about display of certain product groups
def get_oen_info(response, iterator = 0):
    
    product_group = response['oen_prediction_list']['predictions'][iterator]['oen']
    
    print(product_group)

    if product_group == '0445110369': # aka 'Alternator'
        image_file_name = "Alternator.png"
        label_text = "ALTER\nNATOR"
        fill = 'black'
    
    elif product_group == '0445115007': #'Starter':
        image_file_name = "Alternator_right_white_small.png"
        label_text = "STARTER"
        fill = 'white'
    
    elif product_group == '0445110351': #'CommonRailInjector':
        image_file_name = "Alternator_real_squared.png"
        label_text = "COMMON\nRAIL\nINJECTOR"
        fill = 'black'
    
    elif product_group == '0445115077': #'DieselInjector':
        image_file_name = "Alternator_icon_black.png"
        label_text = "DIESEL\nINJECTOR"
        fill = 'black'
    
    elif product_group == '0445110183': #'CommonRailHighPressurePump':
        image_file_name = "high-pressure-pump.jpg"
        label_text = "COMMON\nRAIL\nHIGH\nPRESSURE\nPUMP"
        fill = 'black'
    
    elif product_group == '0445110647': #'BrakeCaliper':
        image_file_name = "brake-caliper.png"
        label_text = "BRAKE\nCALIPER"
        fill = 'black'
    
    elif product_group == '0445110297': #'ClutchDisc':
        image_file_name = "clutch-disc.png"
        label_text = "CLUTCH\nDISC"
        fill = 'black'
    
    elif product_group == '0445115050': #'UnitInjector':
        image_file_name = "diesel-injector.jpg"
        label_text = "UNIT\nINJECTOR"
        fill = 'black'
    
    elif product_group == '0445115084': #'Compressor':
        image_file_name = "Alternator_right_white_small.png"
        label_text = "COM\nPRESSOR"
        fill = 'black'
    
    elif product_group == '0445116030': #'InjectionPump':
        image_file_name = "Alternator.png"
        label_text = "INJECT\nION\nPUMP"
        fill = 'white'
        
    elif product_group == '0445110110': #'OtherProduct':
        image_file_name = "Alternator.png"
        label_text = "OTHER\nPRODUCT"
        fill = 'white'
        
    else:
        image_file_name = "Alternator.png"
        label_text = "FALSE"
        fill = 'white'
    
    return {
        "label_text": label_text,
        "fill": fill,
        "image_file": os.path.join(ASSETS_PATH, image_file_name),
        "image_file_name": image_file_name
        }


# Returns styling information for a key based on its position and state.
def get_key_style(deck, key, state, font = "HalvarEng-Bd.ttf", action = "None"):


    # LEFT MENU

    if key == back_key_index:
        name = "back"
        icon = "{}.png".format("Back_filled")
        icon_path = os.path.join(ASSETS_PATH, icon)
        label = "Bye" if state else "Back"
        
    elif key == up_key_left_index:
        name = "up_left"
        icon = "{}.png".format("Up_filled")
        icon_path = os.path.join(ASSETS_PATH, icon)
        label = "Uped" if state else "Up"
        if state:
            action = "scroll_up" 
    
    elif key == down_key_left_index:
        name = "down_left"
        icon = "{}.png".format("Down_filled")
        icon_path = os.path.join(ASSETS_PATH, icon)
        label = "Downed" if state else "Down"
        if state:
            action = "scroll_down"
    
    elif key == call_to_action_key_left_index:
        name = "call_to_action"
        icon = "{}.png".format("Alternator_real_squared")
        icon_path = os.path.join(ASSETS_PATH, icon)
        label = "Down" if state else "Down"
        
    elif key in tile_0_keys_index:
        name = "first_option"
        icon = "switch_blue"
        icon_path = "draw_switch_blue"
        label = "Downed" if state else "Down"
        action = "call_option_0"
    
    elif key in tile_1_keys_index:
        name = "second_option"
        icon = "switch_blue"
        icon_path = "draw_switch_blue"
        label = "Downed" if state else "Down"
        action = "call_option_1"
    
    elif key in tile_2_keys_index:
        name = "third_option"
        icon = "switch_blue"
        icon_path = "draw_switch_blue"
        label = "Downed" if state else "Down"
        action = "call_option_2"
        
    elif key in tile_3_keys_index:
        name = "fourth_option"
        icon = "switch_blue"
        icon_path = "draw_switch_blue"
        label = "Downed" if state else "Down"
        action = "call_option_3"
    
    elif key == exit_key_index:
        name = "exit"
        icon = "{}.png".format("Exit")
        icon_path = os.path.join(ASSETS_PATH, icon)
        label = "Bye" if state else "Exit"
        
    else:
        name = "emoji"                                                      
        icon = "{}.png".format("Pressed" if state else "Released")
        icon_path = os.path.join(ASSETS_PATH, icon)
        font = "HalvarEng-Bd.ttf"
        label = "Outch!" if state else "Key {}".format(key)

    return {
        "name": name,
        "icon": icon_path,
        "font": os.path.join(ASSETS_PATH, font),
        "label": label,
        "action": action
    }

def change_page(change=0):
    
    global page
    page = page + change
    
    if page < 0:
        page = 0
    
    return page

def messagetosent(string):
    
    global json_message
    message = {'product_group' : string }
#   message = string.encode()
    json_message = json.dumps(message).encode()
    


def set_page_zero():
    
    global page
    page = 0
    
    return page

def key_updater(deck):
    display_order = [x + page*4 for x in order]   #display_order = change_order(-4)
    print(display_order)
    
    for k in tile_keys:
        # key_images[k] = get_key_image_for_pane(k, response, display_order)
        key_images[k] = get_key_image_for_pane_new(k, response, display_order, PG_images, PG_dict)

        with deck:
            #key_images[k] = PILHelper.to_native_format(deck, key_images[k])    
            deck.set_key_image(k, key_images[k])
    
    with deck:
        deck.set_brightness(100)

def update_key_image(deck, key, state):
    # Determine what icon and label to use on the generated key.
    key_style = get_key_style(deck, key, state)    
    
    print(key_style['action'])
    
    if (key_style['action'] == 'call_option_0'):
        print('send option left up')
 
        #get Name of PG
        PG_dict_inv = {v: k for k, v in PG_dict.items()}

        messagetosent( str(
            NametoPGIDDict[PG_dict_inv[display_order[0]]])
            )
        s = MyServer()
        
        start_and_stop_server(s)
        
        del s
        
        
    elif (key_style['action'] == 'call_option_1'):
        print('send option right up')
        
        #get Name of PG
        PG_dict_inv = {v: k for k, v in PG_dict.items()}

        messagetosent( str(
            NametoPGIDDict[PG_dict_inv[display_order[1]]])
            )
        s = MyServer()
        
        start_and_stop_server(s)
        
        del s

    elif (key_style['action'] == 'call_option_2'):
        print('send option left down')
        
        #get Name of PG
        PG_dict_inv = {v: k for k, v in PG_dict.items()}

        messagetosent( str(
            NametoPGIDDict[PG_dict_inv[display_order[2]]])
            )
        s = MyServer()
        
        start_and_stop_server(s)
        
        del s


    elif (key_style['action'] == 'call_option_3'):
        print('send option right down')
        
        #get Name of PG
        PG_dict_inv = {v: k for k, v in PG_dict.items()}

        messagetosent( str(
            NametoPGIDDict[PG_dict_inv[display_order[3]]])
            )
        s = MyServer()
        
        start_and_stop_server(s)
        
        del s

    else:
    
        # Generate the custom key with the requested image and label.
        image = render_key_image(deck, key_style["icon"], key_style["font"], key_style["label"])
        image = PILHelper.to_native_format(deck, image)
    
    # Use a scoped-with on the deck to ensure we're the only thread using it
    # right now.
    
    
        if (key_style['action'] == 'scroll_down') or (key_style['action'] == 'scroll_up'):    
            if key_style['action'] == 'scroll_down':
                #display_order = get_random_display_order(4)    
                change_page(1)
        
            elif key_style['action'] == 'scroll_up':
                #display_order = get_random_display_order(4)
                change_page(-1)
                
            key_updater(deck)
        
    
    
      #      display_order = [x + page*4 for x in order]   #display_order = change_order(-4)
    #        print(display_order)
      #      
      #      for k in tile_keys:
      #          key_images[k] = get_key_image_for_pane_new(k, response, display_order, PG_images, PG_dict)
    #
      #          with deck:
       #             #key_images[k] = PILHelper.to_native_format(deck, key_images[k])    
       #             deck.set_key_image(k, key_images[k])
     #             
        with deck:
            # Update requested key with the generated image.
            deck.set_key_image(key, image)


# Closes the StreamDeck device on key state change.
def key_change_callback(deck, key, state):
    # Print new key state
    #print("Deck {} Key {} = {}".format(deck.id(), key, state), flush=True)
    
    # Update the key image based on the new key state.
    update_key_image(deck, key, state)
        
    #with deck:
        # Update requested key with the generated image.
        #deck.set_key_image(key, image)

    # Use a scoped-with on the deck to ensure we're the only thread using it
    # right now.
#    with deck:
        # Reset deck, clearing all button images.
#        deck.reset()
#
#        # Close deck handle, terminating internal worker threads.
#        deck.close()

# Closes the StreamDeck device on key state change.
def key_change_rest(deck, key, state):
    # Print new key state
    print('Stream deck is idle')
    
    deck.close()
    #print("Deck {} Key {} = {}".format(deck.id(), key, state), flush=True)
    
    # Update the key image based on the new key state.
    # update_key_image(deck, key, state)
        
    #with deck:
        # Update requested key with the generated image.
        #deck.set_key_image(key, image)

    # Use a scoped-with on the deck to ensure we're the only thread using it
    # right now.
#    with deck:
        # Reset deck, clearing all button images.
#        deck.reset()
#
#        # Close deck handle, terminating internal worker threads.
#        deck.close()

def get_random_display_order(end = 3, start = 0):
    import random
    l = list(range(start,end))
    #print(l)
    # [0, 1, 2, 3]
    
    lr = random.sample(l, len(l))
    #print(lr)
    # [0, 3, 1, 2]
    global order
    order = lr

    return lr

def get_key_image_for_pane(k, response, display_order_loc):

    if k in tile_0_keys_index:
                
        product_group_info = get_product_group_info(response, display_order_loc[0])
        image_0 = create_partial_deck_sized_image(deck, key_spacing, product_group_info['image_file_name'])
        key_image = crop_key_image_from_deck_sized_image(deck, image_0, key_spacing, k, 0, 1)
        
        if k == 0:
            # Generate the custom key with the requested image and label.
            key_image = render_text_over_image(deck, 
                                                   key_image,
                                                   label_text = product_group_info['label_text'],
                                                   fill = product_group_info['fill'])  
          

    elif k in tile_1_keys_index:
        product_group_info = get_product_group_info(response, display_order_loc[1])
        image_1 = create_partial_deck_sized_image(deck, key_spacing, product_group_info['image_file_name'])
        key_image = crop_key_image_from_deck_sized_image(deck, image_1, key_spacing, k, 0, 4)
        
        if k == 3:
            # Generate the custom key with the requested image and label.
            key_image = render_text_over_image(deck, 
                                                   key_image,
                                                   label_text = product_group_info['label_text'],
                                                   fill = product_group_info['fill'])
        elif k == 11:
            # Generate the custom key with the requested image and label.
            key_image = render_text_over_image(deck, 
                                                   key_image, 
                                                   label_text = '',
                                                   fill = 'white')

        
    elif k in tile_2_keys_index:
        
        product_group_info = get_product_group_info(response, display_order_loc[2])
        image_2 = create_partial_deck_sized_image(deck, key_spacing, product_group_info['image_file_name'])
        key_image = crop_key_image_from_deck_sized_image(deck, image_2, key_spacing, k, 2, 1)
        
        if k == 16:
            # Generate the custom key with the requested image and label.
            key_image = render_text_over_image(deck, 
                                                   key_image,
                                                   label_text = product_group_info['label_text'],
                                                   fill = product_group_info['fill'])
        elif k == 24:
            # Generate the custom key with the requested image and label.
            key_image = render_text_over_image(deck, 
                                                   key_image, 
                                                   label_text = '',
                                                   fill = 'black')

    elif k in tile_3_keys_index:
        product_group_info = get_product_group_info(response, display_order_loc[3])
        image_3 = create_partial_deck_sized_image(deck, key_spacing, product_group_info['image_file_name'])
        key_image = crop_key_image_from_deck_sized_image(deck, image_3, key_spacing, k, 2, 4)
        
        if k == 19:
            # Generate the custom key with the requested image and label.
            key_image = render_text_over_image(deck, 
                                                key_image,
                                                label_text = product_group_info['label_text'],
                                                fill = product_group_info['fill'])
        elif k == 27:
            # Generate the custom key with the requested image and label.
            key_image = render_text_over_image(deck, 
                                                   key_image, 
                                                   label_text = '',
                                                   fill = 'white')
            

    return key_image

def get_key_image_for_pane_new(k, response, display_order_loc, PG_key_images, PG_iterator_dict):
    
    if k in tile_0_keys_index:
        product_group = response['product_group_prediction_list']['predictions'][display_order_loc[0]]['product_group']
         
    elif k in tile_1_keys_index:
        product_group = response['product_group_prediction_list']['predictions'][display_order_loc[1]]['product_group']
        
    elif k in tile_2_keys_index:   
        product_group = response['product_group_prediction_list']['predictions'][display_order_loc[2]]['product_group']

    elif k in tile_3_keys_index:   
        product_group = response['product_group_prediction_list']['predictions'][display_order_loc[3]]['product_group']

    key_image = PG_key_images[PG_iterator_dict[product_group]][k]
           
    return key_image

def init_key_image_for_all_pgs(response):
    
    responselength = len(response['product_group_prediction_list']['predictions'])
    
    all_PG_images = [None] * responselength
    all_PG_images_Dict = {}
    
    for iterator in range(responselength):
        print(iterator)
        
        product_group, pg_key_images  = init_pg_key_image_for_all_panes(response, iterator)

        print(pg_key_images)
        err
        # Show the section of the main image onto the key.
        all_PG_images[iterator] = pg_key_images.copy()
        all_PG_images_Dict[product_group] = iterator
        

        
    for i,n in enumerate(all_PG_images):
        for k in tile_keys:
            deck.set_key_image(k, all_PG_images[i][k])
        
        time.sleep(1)
        
    print('Length of all PG Images', len(all_PG_images))    
    print('Length of all 0 PG Images', len(all_PG_images[0]))
    return all_PG_images, all_PG_images_Dict

def init_pg_key_image_for_all_panes(response, iterator):

    product_group_info = get_product_group_info(response, iterator)
    
    product_group = response['product_group_prediction_list']['predictions'][iterator]['product_group']
        
    pg_image = create_partial_deck_sized_image(deck, key_spacing, product_group_info['image_file_name'])

    for k in tile_0_keys_index:
                
        key_images[k] = crop_key_image_from_deck_sized_image(deck, pg_image, key_spacing, k, 0, 1)
        
        if k == 0:
            # Generate the custom key with the requested image and label.
            key_images[k] = render_text_over_image(deck, 
                                                   key_images[k],
                                                   label_text = product_group_info['label_text'],
                                                   fill = product_group_info['fill'])  
        elif k == 8:
            # Generate the custom key with the requested image and label.
            key_images[k] = render_text_over_image(deck, 
                                                   key_images[k], 
                                                   label_text = '',
                                                   fill = 'white')

    for k in tile_1_keys_index:
        
        key_images[k] = crop_key_image_from_deck_sized_image(deck, pg_image, key_spacing, k, 0, 4)
        
        if k == 3:
            # Generate the custom key with the requested image and label.
            key_images[k] = render_text_over_image(deck, 
                                                   key_images[k],
                                                   label_text = product_group_info['label_text'],
                                                   fill = product_group_info['fill'])
        elif k == 11:
            # Generate the custom key with the requested image and label.
            key_images[k] = render_text_over_image(deck, 
                                                   key_images[k], 
                                                   label_text = '',
                                                   fill = 'white')

    for k in tile_2_keys_index:
        
        key_images[k] = crop_key_image_from_deck_sized_image(deck, pg_image, key_spacing, k, 2, 1)
        
        if k == 16:
            # Generate the custom key with the requested image and label.
            key_images[k] = render_text_over_image(deck, 
                                                   key_images[k],
                                                   label_text = product_group_info['label_text'],
                                                   fill = product_group_info['fill'])
        elif k == 24:
            # Generate the custom key with the requested image and label.
            key_images[k] = render_text_over_image(deck, 
                                                   key_images[k], 
                                                   label_text = '',
                                                   fill = 'black')

    for k in tile_3_keys_index:
        
        key_images[k] = crop_key_image_from_deck_sized_image(deck, pg_image, key_spacing, k, 2, 4)
        
        if k == 19:
            # Generate the custom key with the requested image and label.
            key_images[k] = render_text_over_image(deck, 
                                                key_images[k],
                                                label_text = product_group_info['label_text'],
                                                fill = product_group_info['fill'])
        elif k == 27:
            # Generate the custom key with the requested image and label.
            key_images[k] = render_text_over_image(deck, 
                                                   key_images[k], 
                                                   label_text = '',
                                                   fill = 'white')
    
    for k in tile_keys:
        key_images[k] = PILHelper.to_native_format(deck, key_images[k])

    return product_group, key_images 

def get_PG_results(session_key):
    x = requests.get('http://localhost:5100/bde/selection/evaluation/status/' + session_key)
    return x

def get_session_key():
    # Check wether FrontEnd is actvie and get current session-key
    x = requests.get('http://localhost:4444/sensors/active')
    if x.json()["scanner"]["session_key"] != "":
        #print( x.json()["scanner"]["session_key"])
        response = x.json()     
        
    # get BDE status to selection from host
    session_key = response["scanner"]["session_key"]
    
    return session_key

def get_front_end_state():
    # Check wether FrontEnd is actvie and get current session-key
    x = requests.get('http://localhost:4444/sensors/active')
    
    front_end_active = False
    try:
        if x.json()["scanner"]["scanner_bool"]:
            if x.json()["scanner"]["session_key"] != "":
                #print( x.json()["scanner"]["session_key"])
                response = x.json() 
                front_end_active = True
    except:
        print("got no result")
        
    # get BDE status to selection from host
    try:
        session_key = response["scanner"]["session_key"]
    
    except:
        session_key = ''
    
    return front_end_active, session_key
    
def start_and_stop_server(s):
   
    
    s.start()
    print('thread alive:', s.is_alive())  # True
    time.sleep(0.5)
    s.stop()
    print('thread alive:', s.is_alive())  # False
    deck.set_brightness(0)
    

if __name__ == "__main__":
    
    path = "PG_IDtoLabelDict.pkl"
    with open(path, "rb") as f:
        PG_IDtoLabelDict = load(f)
        
    path = "PG_LabeltoIDDict.pkl"
    with open(path, "rb") as f:
        PG_LabeltoIDDict = load(f)
        
    path = "PGIDtoNamewSpaceDict.pkl"
    with open(path, "rb") as f:
        PGIDtoNamewSpaceDict = load(f)
        

    NametoPGIDDict = {v: k for k, v in PGIDtoNamewSpaceDict.items()}
    

    streamdecks = DeviceManager().enumerate()

    print("Found {} Stream Deck(s).\n".format(len(streamdecks)))

    for index, deck in enumerate(streamdecks):
        # This example only works with devices that have screens.
        if not deck.is_visual():
            continue

        deck.open()
        deck.reset()

        print("Opened '{}' device (serial number: '{}', fw: '{}')".format(
            deck.deck_type(), deck.get_serial_number(), deck.get_firmware_version()
        ))
        # Set initial screen brightness to 30%.
        deck.set_brightness(100)

        # Approximate number of (non-visible) pixels between each key, so we can
        # take those into account when cutting up the image to show on the keys.
        #key_spacing = (36, 36)
        key_spacing = (0, 0)
            
        # Start Init job to get product groups and names of oen    
        url = 'http://localhost:5100/bde/selection/start'
        myobj = {
                "customer_number": "43016357",
                "bar_code": "unknownbarcode",
                "bar_code_scanable": "Y",
                "box_exists": "Y",
                "program": "IAM gesamt",
                "session_key": "STREAMDECKINIT"
                }

        x = requests.post(url, json = myobj)
        
        # Wait for register
        time.sleep(0.05)
        
        # Start Init job to get product groups and names of oen    
        url = 'http://localhost:5100/bde/selection/evaluation/SSE'
        myobj = {
                  "core_mass": 330,
                  "reman": "nullable string",
                  "product_group_ID": 9999999999,
                  "session_key": "STREAMDECKINIT"
                }
        x = requests.post(url, json = myobj)
        
        # Wait for register
        time.sleep(1)
        
        # import of the BDE Status response for display of results
        session_key = "STREAMDECKINIT"
        
        # get results from stream deck
        x = get_PG_results(session_key)

        # check wether results from stream deck contain pg info
        if x.json()["product_group_prediction_list"]["status"] == 'Product group prediction completed!':
            print( x.json()["product_group_prediction_list"]["predictions"])
            response = x.json()        

        #response_location = os.path.join(ASSETS_PATH, "response.json")
        #f = open(response_location)
        #response = json.load(f)
        

        result_length = len(response['product_group_prediction_list']['predictions']) 
        
        knwon_product_groups_num = result_length
        tile_count = 4
        page = 0
        
        display_order = get_random_display_order(end = tile_count) 

        # Extract out the section of the image that is occupied by each key.
        key_images = dict()
        
        key_count = range(deck.key_count())
        
        #LEFT MENU
        
        #First button in the application is the back button
        #back_key_index = 0
        back_key_index = 6
        #8th button in the application is the up button left
        up_key_left_index = 14 
        #16th button in the application is the down button left
        down_key_left_index = 22 
        #16th button in the application is the up button left
        call_to_action_key_left_index = 30 
        
        #FIRST TILE
        tile_0_keys_index = [0,1,2,8,9,10]
        
        #SECOND TILE
        tile_1_keys_index = [3,4,5,11,12,13]
        
        #THIRD TILE
        tile_2_keys_index = [16,17,18,24,25,26]

        #FOURTH TILE
        tile_3_keys_index = [19,20,21,27,28,29]
        
        global tile_keys
        tile_keys = [0,1,2,8,9,10,3,4,5,11,12,13,16,17,18,24,25,26,19,20,21,27,28,29]
        
        PG_images, PG_dict = init_key_image_for_all_pgs(response)
        
        # Last button in the example application is the exit button.
        exit_key_index = 31
        
        
        for k in key_count:
            
            # LEFT MENU
            if k == back_key_index:
                # Generate the custom key with the requested image and label.
                key_images[k] = render_key_image(deck, 
                                                 "{}.png".format("Back_filled"))
                key_images[k] = PILHelper.to_native_format(deck, key_images[k])

            elif k == up_key_left_index:
                # Generate the custom key with the requested image and label.
                key_images[k] = render_key_image(deck, 
                                                 "{}.png".format("Up_filled"))
                key_images[k] = PILHelper.to_native_format(deck, key_images[k])

            elif k == down_key_left_index:
                # Generate the custom key with the requested image and label.
                key_images[k] = render_key_image(deck,
                                                 "{}.png".format("Down_filled"))
                key_images[k] = PILHelper.to_native_format(deck, key_images[k])

            elif k == call_to_action_key_left_index:
                # Generate the custom key with the requested image and label.
                key_images[k] = render_key_text(deck,
                                                label_text = 'PICK\nPRODUCT\nGROUP')
                key_images[k] = PILHelper.to_native_format(deck, key_images[k])

                
            # RIGHT MENU
            if k == 7:
                # Generate the custom key with the requested image and label.
                key_images[k] = render_key_image(deck, 
                                                 "{}.png".format("Forward_filled"))
                key_images[k] = PILHelper.to_native_format(deck, key_images[k])

            elif k == 15:
                # Generate the custom key with the requested image and label.
                key_images[k] = render_key_image(deck, 
                                                 "{}.png".format("Up_filled"))
                key_images[k] = PILHelper.to_native_format(deck, key_images[k])

            elif k == 23:
                # Generate the custom key with the requested image and label.
                key_images[k] = render_key_image(deck, 
                                                 "{}.png".format("Down_filled"))
                key_images[k] = PILHelper.to_native_format(deck, key_images[k])

            elif k == 31:
                # Generate the custom key with the requested image and label.
                key_images[k] = render_key_text(deck,label_text = 'EIBA')
                key_images[k] = PILHelper.to_native_format(deck, key_images[k])
        
                
            # OPTIONS PANE
                        
            if k in tile_0_keys_index:
                key_images[k] = get_key_image_for_pane_new(k, response, display_order, PG_images, PG_dict)
                
            elif k in tile_1_keys_index:
                key_images[k] = get_key_image_for_pane_new(k, response, display_order, PG_images, PG_dict)
                
            elif k in tile_2_keys_index:
                key_images[k] = get_key_image_for_pane_new(k, response, display_order, PG_images, PG_dict)
                
            elif k in tile_3_keys_index:
                key_images[k] = get_key_image_for_pane_new(k, response, display_order, PG_images, PG_dict)

            
        # Use a scoped-with on the deck to ensure we're the only thread
        # using it right now.
        with deck:
            # Draw the individual key images to each of the keys.
            for k in key_count:
                
                # LEFT MENU
                if k == 6:
                    key_image = key_images[k]
                
                    # Show the section of the main image onto the key.
                    deck.set_key_image(k, key_image)
                if k == 14:
                    key_image = key_images[k]
                
                    # Show the section of the main image onto the key.
                    deck.set_key_image(k, key_image)                
                if k == 22:
                    key_image = key_images[k]
                
                    # Show the section of the main image onto the key.
                    deck.set_key_image(k, key_image)
                if k == 30:
                    key_image = key_images[k]
                
                    # Show the section of the main image onto the key.
                    deck.set_key_image(k, key_image)
                
                # RIGHT MENU
                if k == 7:
                    key_image = key_images[k]
                
                    # Show the section of the main image onto the key.
                    deck.set_key_image(k, key_image)
                if k == 15:
                    key_image = key_images[k]
                
                    # Show the section of the main image onto the key.
                    deck.set_key_image(k, key_image)                
                if k == 23:
                    key_image = key_images[k]
                
                    # Show the section of the main image onto the key.
                    deck.set_key_image(k, key_image)
                if k == 31:
                    key_image = key_images[k]
                
                    # Show the section of the main image onto the key.
                    deck.set_key_image(k, key_image)
                
                
                if k == 0 or k == 1 or k == 2 or k == 8 or k == 9 or k == 10:
                    key_image = key_images[k]
                
                    # Show the section of the main image onto the key.
                    deck.set_key_image(k, key_image)
                    
                if k == 3 or k == 4 or k == 5 or k == 11 or k == 12 or k == 13:
                    key_image = key_images[k]
                
                    # Show the section of the main image onto the key.
                    deck.set_key_image(k, key_image)

                if k == 16 or k == 17 or k == 18 or k == 24 or k == 25 or k == 26:
                    key_image = key_images[k]
                
                    # Show the section of the main image onto the key.
                    deck.set_key_image(k, key_image)
                    
                if k == 19 or k == 20 or k == 21 or k == 27 or k == 28 or k == 29:
                    key_image = key_images[k]
                
                    # Show the section of the main image onto the key.
                    deck.set_key_image(k, key_image)
                    

        active = True
        
        with deck:
           deck.set_brightness(0)
           
        # Register callback function for when a key state changes.
        deck.set_key_callback(key_change_callback)
        set_page_zero()
        old_sessionkey = "veryoldsessionkey"
        
        while active:
                       
            front_end_active, session_key = get_front_end_state()
            
            if front_end_active == True:
            
                #session_key = get_session_key()
                #print("Front End active", front_end_active)
                
                #print("Session key", session_key)
            
                if session_key != '':
                    
                    # get results from backend
                    y = get_PG_results(session_key)
                                          
                    # check wether results from stream deck contain pg info
                    if y.json()["product_group_prediction_list"]["status"] == 'Product group prediction completed!':
                        #print( y.json()["product_group_prediction_list"]["predictions"])
                        response = y.json()
                                            
                            
                        if old_sessionkey != session_key:
                            print('page',page)
                            print('old_sessionkey',old_sessionkey)
                            print('old_sessionkey',session_key)
                            print('page changed')
                        
                            set_page_zero()
                            key_updater(deck)
                            print('page changed')
                            old_sessionkey = session_key
                        

                else:
                    with deck:
                        deck.set_brightness(0)
                    time.sleep(1.050)
                    
                    print(page)
                    if page != 0:                            
                        set_page_zero()
                        print(page)
            
            else:
                with deck:
                    deck.set_brightness(0)
                time.sleep(0.050)
                
                print(page)
                if page != 0:                            
                    set_page_zero()
                    print(page)

        # Wait until all application threads have terminated (for this example,
        # this is when all deck handles are closed).
        for t in threading.enumerate():
            try:
                t.join()
            except RuntimeError:
                pass