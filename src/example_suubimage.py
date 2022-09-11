#!/usr/bin/env python3

#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

# Example script showing how to tile a larger image across multiple buttons, by
# first generating an image suitable for the entire deck, then cropping out and
# applying key-sized tiles to individual keys of a StreamDeck.

import os
import threading

from PIL import Image, ImageDraw, ImageOps, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

# Folder location of image assets used by this example.
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "Assets")

#typos = 'HalvarEng-Bd.ttf', 'HalvarEng-Bd.ttf'

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
    image = PILHelper.create_scaled_image(deck, icon, margins=[0, 0, 0, 0])


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
    image = PILHelper.create_scaled_image(deck, icon)

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

# Returns styling information for a key based on its position and state.
def get_key_style(deck, key, state, font = "HalvarEng-Bd.ttf"):


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
    
    elif key == down_key_left_index:
        name = "down_left"
        icon = "{}.png".format("Down_filled")
        icon_path = os.path.join(ASSETS_PATH, icon)
        label = "Downed" if state else "Down"
        if state:
            print('Call_other_objects')
    
    elif key == call_to_action_key_left_index:
        name = "call_to_action"
        icon = "{}.png".format("Alternator_real_squared")
        icon_path = os.path.join(ASSETS_PATH, icon)
        label = "Down" if state else "Down"
        
    elif key in tile_0_keys_index:
        name = "first_option"
        icon = "switch_blue"
        icon_path = "draw_switch_blue"
        label = "Down" if state else "Down"
    
    elif key in tile_1_keys_index:
        name = "second_option"
        icon = "switch_blue"
        icon_path = "draw_switch_blue"
        label = "Down" if state else "Down"
    
    elif key in tile_2_keys_index:
        name = "third_option"
        icon = "switch_blue"
        icon_path = "draw_switch_blue"
        label = "Down" if state else "Down"
        
    elif key in tile_3_keys_index:
        name = "fourth_option"
        icon = "switch_blue"
        icon_path = "draw_switch_blue"
        label = "Down" if state else "Down"
    
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
        "label": label
    }

def update_key_image(deck, key, state):
    # Determine what icon and label to use on the generated key.
    key_style = get_key_style(deck, key, state)
    print(key_style)
    
    # Generate the custom key with the requested image and label.
    image = render_key_image(deck, key_style["icon"], key_style["font"], key_style["label"])
    image = PILHelper.to_native_format(deck, image)
    # Use a scoped-with on the deck to ensure we're the only thread using it
    # right now.
    with deck:
        # Update requested key with the generated image.
        deck.set_key_image(key, image)

# Closes the StreamDeck device on key state change.
def key_change_callback(deck, key, state):
    # Print new key state
    print("Deck {} Key {} = {}".format(deck.id(), key, state), flush=True)
    
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


if __name__ == "__main__":
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
        key_spacing = (36, 36)

        # Load and resize a source image so that it will fill the given
        # StreamDeck.
        image_0 = create_partial_deck_sized_image(deck, key_spacing, "Alternator.png")
        image_1 = create_partial_deck_sized_image(deck, key_spacing, "Alternator_right_white_small.png")
        image_2 = create_partial_deck_sized_image(deck, key_spacing, "Alternator_real_squared.png")
        image_3 = create_partial_deck_sized_image(deck, key_spacing, "Alternator_icon_black.png")



        product_options = range()

        # Extract out the section of the image that is occupied by each key.
        key_images = dict()
        
        key_count = range(deck.key_count())
        
        #LEFT MENU
        
        #First button in the application is the back button
        back_key_index = 0
        #8th button in the application is the up button left
        up_key_left_index = 8 
        #16th button in the application is the down button left
        down_key_left_index = 16 
        #16th button in the application is the up button left
        call_to_action_key_left_index = 24 
        
        #FIRST TILE
        tile_0_keys_index = [1,2,3,9,10,11]
        
        #SECOND TILE
        tile_1_keys_index = [4,5,6,12,13,14]
        
        #THIRD TILE
        tile_2_keys_index = [17,18,19,25,26,27]

        #FOURTH TILE
        tile_3_keys_index = [20,21,22,28,29,30]
        
        # Last button in the example application is the exit button.
        exit_key_index = deck.key_count() - 1
        
        
        for k in key_count:
            
            # LEFT MENU
            if k == back_key_index:
                # Generate the custom key with the requested image and label.
                key_images[k] = render_key_image(deck, 
                                                 "{}.png".format("Back_filled"))
            if k == up_key_left_index:
                # Generate the custom key with the requested image and label.
                key_images[k] = render_key_image(deck, 
                                                 "{}.png".format("Up_filled"))
            if k == down_key_left_index:
                # Generate the custom key with the requested image and label.
                key_images[k] = render_key_image(deck,
                                                 "{}.png".format("Down_filled"))
            if k == call_to_action_key_left_index:
                # Generate the custom key with the requested image and label.
                key_images[k] = render_key_text(deck,
                                                label_text = 'PICK\nPRODUCT\nGROUP')
                
            # RIGHT MENU
            if k == 7:
                # Generate the custom key with the requested image and label.
                key_images[k] = render_key_image(deck, 
                                                 "{}.png".format("Forward_filled"))
            if k == 15:
                # Generate the custom key with the requested image and label.
                key_images[k] = render_key_image(deck, 
                                                 "{}.png".format("Up_filled"))
            if k == 23:
                # Generate the custom key with the requested image and label.
                key_images[k] = render_key_image(deck, 
                                                 "{}.png".format("Down_filled"))
            if k == 31:
                # Generate the custom key with the requested image and label.
                key_images[k] = render_key_text(deck,label_text = 'EIBA')
            
            # OPTIONS PANE
            
            if k in tile_0_keys_index:
                key_images[k] = crop_key_image_from_deck_sized_image(deck, image_0, key_spacing, k, 0, 1)
                
                if k == 1:
                    # Generate the custom key with the requested image and label.
                    key_images[k] = render_text_over_image(deck, 
                                                           key_images[k],
                                                           label_text = 'ALTER\nNATOR',
                                                           fill = 'black')  
                  

            if k in tile_1_keys_index:
                key_images[k] = crop_key_image_from_deck_sized_image(deck, image_1, key_spacing, k, 0, 4)
                
                if k == 4:
                    # Generate the custom key with the requested image and label.
                    key_images[k] = render_text_over_image(deck, 
                                                           key_images[k],
                                                           label_text = 'ALTER\nNATOR',
                                                           fill = 'white')
                if k == 12:
                    # Generate the custom key with the requested image and label.
                    key_images[k] = render_text_over_image(deck, 
                                                           key_images[k], 
                                                           label_text = '',
                                                           fill = 'white')

                
            if k in tile_2_keys_index:
                key_images[k] = crop_key_image_from_deck_sized_image(deck, image_2, key_spacing, k, 2, 1)
                
                if k == 17:
                    # Generate the custom key with the requested image and label.
                    key_images[k] = render_text_over_image(deck, 
                                                           key_images[k],
                                                           label_text = 'ALTER\nNATOR',
                                                           fill = 'black')
                if k == 25:
                    # Generate the custom key with the requested image and label.
                    key_images[k] = render_text_over_image(deck, 
                                                           key_images[k], 
                                                           label_text = '',
                                                           fill = 'black')

            if k in tile_3_keys_index:
                key_images[k] = crop_key_image_from_deck_sized_image(deck, image_3, key_spacing, k, 2, 4)
                
                if k == 20:
                    # Generate the custom key with the requested image and label.
                    key_images[k] = render_text_over_image(deck, 
                                                           key_images[k], 
                                                           label_text = 'ALTER\nNATOR',
                                                           fill = 'black')
                if k == 28:
                    # Generate the custom key with the requested image and label.
                    key_images[k] = render_text_over_image(deck, 
                                                           key_images[k], 
                                                           label_text = '',
                                                           fill = 'white')
                
            
            key_images[k] = PILHelper.to_native_format(deck, key_images[k])
        # Use a scoped-with on the deck to ensure we're the only thread
        # using it right now.
        with deck:
            # Draw the individual key images to each of the keys.
            for k in key_count:
                
                # LEFT MENU
                if k == 0:
                    key_image = key_images[k]
                
                    # Show the section of the main image onto the key.
                    deck.set_key_image(k, key_image)
                if k == 8:
                    key_image = key_images[k]
                
                    # Show the section of the main image onto the key.
                    deck.set_key_image(k, key_image)                
                if k == 16:
                    key_image = key_images[k]
                
                    # Show the section of the main image onto the key.
                    deck.set_key_image(k, key_image)
                if k == 24:
                    key_image = key_images[k]
                
                    # Show the section of the main image onto the key.
                    deck.set_key_image(k, key_image)
                
                # LEFT MENU
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
                
                
                if k == 1 or k == 2 or k == 3 or k == 9 or k == 10 or k == 11:
                    key_image = key_images[k]
                
                    # Show the section of the main image onto the key.
                    deck.set_key_image(k, key_image)
                    
                if k == 4 or k == 5 or k == 6 or k == 12 or k == 13 or k == 14:
                    key_image = key_images[k]
                
                    # Show the section of the main image onto the key.
                    deck.set_key_image(k, key_image)

                if k == 17 or k == 18 or k == 19 or k == 25 or k == 26 or k == 27:
                    key_image = key_images[k]
                
                    # Show the section of the main image onto the key.
                    deck.set_key_image(k, key_image)
                    
                if k == 20 or k == 21 or k == 22 or k == 28 or k == 29 or k == 30:
                    key_image = key_images[k]
                
                    # Show the section of the main image onto the key.
                    deck.set_key_image(k, key_image)
                    

        # Register callback function for when a key state changes.
        deck.set_key_callback(key_change_callback)

        # Wait until all application threads have terminated (for this example,
        # this is when all deck handles are closed).
        for t in threading.enumerate():
            try:
                t.join()
            except RuntimeError:
                pass
