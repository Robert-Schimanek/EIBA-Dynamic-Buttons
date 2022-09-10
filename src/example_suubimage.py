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
    #key_image.show()

    return PILHelper.to_native_format(deck, key_image)

# Generates a custom tile with run-time generated text and custom image via the
# PIL module.
def render_key_image(deck,
                     icon_filename = "{}.png".format("Exit"),
                     font_filename = 'Roboto-Regular.ttf', 
                     label_text = 'DEFAULT'):
    # Resize the source image asset to best-fit the dimensions of a single key,
    # leaving a margin at the bottom so that we can draw the key title
    # afterwards.
    
    icon_filename = os.path.join(ASSETS_PATH, icon_filename)
    font_filename = os.path.join(ASSETS_PATH, font_filename)
    
    icon = Image.open(icon_filename)
    image = PILHelper.create_scaled_image(deck, icon, margins=[0, 0, 20, 0])

    # Load a custom TrueType font and use it to overlay the key index, draw key
    # label onto the image a few pixels from the bottom of the key.
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_filename, 14)
    draw.text((image.width / 2, image.height - 5), text=label_text, font=font, anchor="ms", fill="white")

    return PILHelper.to_native_format(deck, image)

# Generates a custom tile with run-time generated text and custom image via the
# PIL module.
def render_key_text(deck,
                    icon_filename = "{}.png".format("Solid_black"),  
                    font_filename = 'Roboto-Regular.ttf', 
                    label_text = 'DEFAULT'):
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
    font = ImageFont.truetype(font_filename, 15)
    draw.text((image.width / 2, image.width / 2), text=label_text, font=font, anchor="ms", fill="white")

    return PILHelper.to_native_format(deck, image)

# Generates a custom tile with run-time generated text and custom image via the
# PIL module.
def render_text_over_image(deck,
                           existing_key_image,  
                           font_filename = 'Roboto-Regular.ttf', 
                           label_text = 'DEFAULT'):
    # Resize the source image asset to best-fit the dimensions of a single key,
    # leaving a margin at the bottom so that we can draw the key title
    # afterwards.
    
    font_filename = os.path.join(ASSETS_PATH, font_filename)
    
    image = PILHelper.create_scaled_image(deck, existing_key_image)

    # Load a custom TrueType font and use it to overlay the key index, draw key
    # label onto the image a few pixels from the bottom of the key.
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_filename, 15)
    draw.text((existing_key_image.width / 2, existing_key_image.width / 2), text=label_text, font=font, anchor="ms", fill="white")

    return PILHelper.to_native_format(deck, image)

# Closes the StreamDeck device on key state change.
def key_change_callback(deck, key, state):
    # Use a scoped-with on the deck to ensure we're the only thread using it
    # right now.
    with deck:
        # Reset deck, clearing all button images.
        deck.reset()

        # Close deck handle, terminating internal worker threads.
        deck.close()


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
        image_2 = create_partial_deck_sized_image(deck, key_spacing, "Alternator_square_white.png")
        image_3 = create_partial_deck_sized_image(deck, key_spacing, "Alternator_square_white_small.png")

        #print("Created sub image in size of {}x{} pixels.".format(image.width, image.height))

        # Extract out the section of the image that is occupied by each key.
        key_images = dict()
        
        key_count = range(deck.key_count())
        #key_count = [0,1,2,3,8,9,10,11]
        #key_count = [1,2,3,4,9,10,11,12]
        #key_count = [0,1,2,3,4,8,9,10,11,12]
        
        
        for k in key_count:
            
            # LEFT MENU
            if k == 0:
                # Generate the custom key with the requested image and label.
                key_images[k] = render_key_image(deck, "{}.png".format("Back_white"))
            if k == 8:
                # Generate the custom key with the requested image and label.
                key_images[k] = render_key_image(deck, 
                                                 "{}.png".format("Up_filled"), 
                                                 label_text = 'UP')
            if k == 16:
                # Generate the custom key with the requested image and label.
                key_images[k] = render_key_image(deck, "{}.png".format("Down"))
            if k == 24:
                # Generate the custom key with the requested image and label.
                key_images[k] = render_key_text(deck)
            
            # OPTIONS PANE
            
            if k == 1 or k == 2 or k == 3 or k == 9 or k == 10 or k == 11:
                key_images[k] = crop_key_image_from_deck_sized_image(deck, image_0, key_spacing, k, 0, 1)
                
                if k == 1:
                    # Generate the custom key with the requested image and label.
                    key_images[k] = render_text_over_image(deck, key_images[k], label_text = 'ALTERNATOR')
                    

            if k == 4 or k == 5 or k == 6 or k == 12 or k == 13 or k == 14:
                key_images[k] = crop_key_image_from_deck_sized_image(deck, image_1, key_spacing, k, 0, 4)
                
            if k == 17 or k == 18 or k == 19 or k == 25 or k == 26 or k == 27:
                key_images[k] = crop_key_image_from_deck_sized_image(deck, image_2, key_spacing, k, 2, 1)

            if k == 20 or k == 21 or k == 22 or k == 28 or k == 29 or k == 30:
                key_images[k] = crop_key_image_from_deck_sized_image(deck, image_3, key_spacing, k, 2, 4)
                
                
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
