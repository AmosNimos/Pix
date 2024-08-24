# Pixel-art Independent of X11 or P.I.X for short

import signal
import argparse
import curses
import os
import sys
import re
from PIL import Image
from random import randint
import math
from collections import Counter

# [TODO] :
# - Fix the ellipse tool sometime not being pixel accurate.
# - Add customizable keymapping options

# Default key bindings
default_keymap = {
    "move_up": [curses.KEY_UP, ord('w')],
    "move_down": [curses.KEY_DOWN, ord('s')],
    "move_left": [curses.KEY_LEFT, ord('a')],
    "move_right": [curses.KEY_RIGHT, ord('d')],
    "perform_action": [ord(' '), ord('\n'), ord('x')],
    "save_and_quit": [ord('q')],
    "save_with_confirm": [ord('Q')],
    "toggle_info_bar": [ord('g')],
    "increase_color": [ord('=')],
    "decrease_color": [ord('-')],
    "next_tool": [ord('+')],
    "previous_tool": [ord('_')],
    "select_tool_0": [ord('!')],
    "select_tool_1": [ord('@')],
    "select_tool_2": [ord('#')],
    "select_tool_3": [ord('$')],
    "select_tool_4": [ord('%')],
    "select_tool_5": [ord('^')],
    "select_tool_6": [ord('&')],
    "bucket_fill": [ord('b')],
    "toggle_horizontal_mirroring": [ord('h')],
    "toggle_vertical_mirroring": [ord('v')],
    "move_horizontal_mirroring": [ord('M')],
    "move_vertical_mirroring": [ord('m')],
    "hex_prompt": [ord('H')],
    "hex_export": [ord('E')],
}

def load_keymap(filename, keymap):
    key_aliases = {
        "space": ord(' '),
        "enter": ord('\n'),
        ";": ord(';'),
        "dot": ord('.'),
        "comma": ord(','),
        ">": ord('>'),
        "<": ord('<'),
        # Add more aliases if needed
    }

    try:
        with open(filename, 'r') as file:
            for line in file:
                if '::' in line:
                    action, keys = line.strip().split('::')
                    keys = keys.split(',')
                    key_list = []
                    for key in keys:
                        key = key.strip()
                        if len(key) == 1:  # Single character
                            key_list.append(ord(key))
                        elif key in key_aliases:
                            key_list.append(key_aliases[key])
                        else:
                            raise ValueError(f"Unknown key alias: {key}")

                    if action in keymap:
                        keymap[action] = key_list
    except FileNotFoundError:
        print(f"Keymap file '{filename}' not found. Using default key bindings.")
    except ValueError as e:
        print(f"Error in keymap file: {e}")

    return keymap
    

class Drawing:
    def __init__(self, stdscr, width=64, height=64, view_size=64, filename=None, background=1, palette="palette.hex"):

        self.palette=palette
        self.stdscr = stdscr
        # for line pen:
        self.info_bar=True
        self.rect_pen=False
        self.tool_id=0
        self.tool_count=6
        self.mirror_x_offset=0
        self.mirror_y_offset=0
        # for x2 and y2 you could use cursor_x and cursor_y I think.
        self.x1=self.x2=self.y1=self.y2=-1     
        self.background_color=background
        self.filename = filename
        self.width = width
        self.height = height
        self.view_size = view_size
        self.image = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        self.cursor_x = width // 2
        self.cursor_y = height // 2
        self.color = (255, 255, 255)  # Default color white
        self.color_pair = 1
        self.mirror_h = False
        self.mirror_v = False
        self.undo_stack = []
        self.redo_stack = []
        self.screenshots = []  # Change to a list to store multiple screenshots
        self.current_state = self.take_screenshot()

        self.tools = ["Dot","Pen","Bucket","Line","Rect","Ellipse","Copy"]
        
        self.colors = [
            (0, 0, 0),       # Black
            (255, 255, 255), # White
            (255, 0, 0),     # Red
            (0, 255, 0),     # Green
            (0, 0, 255),     # Blue
            (255, 255, 0),   # Yellow
            (255, 165, 0),   # Orange
            (128, 0, 128),   # Purple
            (0, 255, 255),   # Cyan
            (255, 192, 203)  # Pink
        ]

        #NOTE: too slow to run
        # Add random unique colors until we reach 254 total colors
#        while len(self.colors) < 254:
#            random_color = (randint(0, 255), randint(0, 255), randint(0, 255))
#            if random_color not in self.colors:
#                self.colors.append(random_color)

        # NOTE: Add some random colors to the default pallet to expend it a little
        suported_colors=24
        while len(self.colors) < suported_colors:
            random_color = (randint(0, 255), randint(0, 255), randint(0, 255))
            if random_color not in self.colors:
                self.colors.append(random_color)

        if self.valid_palette(self.palette):
            self.load_rgb_from_file(self.palette)
        self.color_pairs = {}
        self.initialize_colors()
        self.pen_down = False  # Initialize pen state
        self.set_color(1)

        if filename:
            self.load_image(filename)

    def valid_palette(self,palette_file):
        # Check if file exists
        if not os.path.isfile(palette_file):
            print(f"File '{palette_file}' does not exist.")
            return False

        valid_hex_pattern = re.compile(r'^#?[0-9a-fA-F]{6}$')
        valid_hex_count = 0

        # Open and read the file line by line
        with open(palette_file, 'r') as file:
            for line in file:
                line = line.strip()
                if valid_hex_pattern.match(line):
                    valid_hex_count += 1

        # Check if there are at least 8 valid hex color values
        if valid_hex_count >= 8:
            return True
        else:
            curses.endwin()  # End curses mode to allow normal input
            print(f"File '{palette_file}' does not have enough valid hex color values.")
            exit()
            return False

    def hex_to_rgb(self,hex_color):
        """Convert a hex color to an RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def load_rgb_from_file(self,filename):
        # init default colors

        """Load hex colors from a file and convert them to RGB."""
        # Replace the 8 last color of the colors array with those in the file
        with open(filename, 'r') as file:
            for i, line in enumerate(file):
                hex_color = line.strip()
                rgb_tuple = self.hex_to_rgb(hex_color)
                self.colors[i+2] = rgb_tuple

    def initialize_colors(self):
        curses.start_color()
        curses.use_default_colors()
        for i, (r, g, b) in enumerate(self.colors):
            curses.init_color(i + 1, int(r * 1000 / 255), int(g * 1000 / 255), int(b * 1000 / 255))
            curses.init_pair(i + 1, i + 1, self.background_color)
            self.color_pairs[i] = i + 1

    def move_cursor(self, direction):
        if direction == 'UP':
            self.cursor_y = (self.cursor_y - 1) % self.height
        elif direction == 'DOWN':
            self.cursor_y = (self.cursor_y + 1) % self.height
        elif direction == 'LEFT':
            self.cursor_x = (self.cursor_x - 1) % self.width
        elif direction == 'RIGHT':
            self.cursor_x = (self.cursor_x + 1) % self.width

    def set_color(self, color_key):
        self.color = self.colors[int(color_key)]
        self.color_pair = self.color_pairs[int(color_key)]

    def set_palette(self, color_key):
        if (int(color_key) <= 1):
            self.color = self.colors[int(color_key)]
            self.color_pair = self.color_pairs[int(color_key)]
        else :
            index=int(len(self.colors)-10)+int(color_key)
            self.color = self.colors[index]
            self.color_pair = self.color_pairs[index]
        

    def increase_color(self):
        colors_count=int(len(self.colors))
        if self.color_pair < colors_count:
            self.color = self.colors[self.color_pair]
            self.color_pair+=1
        else:
            self.color_pair=1
            self.color = self.colors[self.color_pair]
            
    def decrease_color(self):
        colors_count=int(len(self.colors))
        if self.color_pair > 1:
            self.color_pair-=1
            self.color = self.colors[self.color_pair-1]
        else:
            self.color_pair=colors_count

    def draw_pixel(self):
        self.image.putpixel((self.cursor_x, self.cursor_y), self.color)
        if self.mirror_h:
            mx=self.width + self.mirror_x_offset - 1 - self.cursor_x
            if (mx<self.width):
                self.image.putpixel((mx , self.cursor_y), self.color)
        if self.mirror_v:
            my=self.height +self.mirror_y_offset - 1 - self.cursor_y
            if (my<self.height):
                self.image.putpixel((self.cursor_x, my), self.color)
        if self.mirror_h and self.mirror_v:
            my=self.height +self.mirror_y_offset - 1 - self.cursor_y
            mx=self.width + self.mirror_x_offset - 1 - self.cursor_x
            if (mx<self.width) and (my<self.height):
                self.image.putpixel((mx, my), self.color)

    def set_pixel(self,x,y,color=-1):
        if color == -1:
            color=self.color
        self.image.putpixel((x, y), color)
        if self.mirror_h:
            self.image.putpixel((self.width - 1 - x, y), color)
        if self.mirror_v:
            self.image.putpixel((x, self.height - 1 - y), color)
        if self.mirror_h and self.mirror_v:
            self.image.putpixel((self.width - 1 - x, self.height - 1 - y), color)

    def get_pixel(self,x,y):
        r, g, b = self.image.getpixel((x, y))
        color=(r,g,b)
        return color

    def pick_pixel(self):
        r, g, b = self.image.getpixel((self.cursor_x, self.cursor_y))
        color_key=self.get_closest_color_id(r,g,b)        
        color=(r,g,b)
        self.color = color
        self.color_pair = self.color_pairs[int(color_key-2)]

    def draw_rect(self):
        if self.pen_down:
            #self.x2, self.y2 = self.cursor_x, self.cursor_y
            x1, x2 = sorted([self.x1, self.cursor_x])
            y1, y2 = sorted([self.y1, self.cursor_y])
            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    self.set_pixel(x, y)
            self.reset_rect()
        else:
            self.x1, self.y1 = self.cursor_x, self.cursor_y
            self.pen_down = True


    def draw_ellipse(self, filled=False):
        if self.pen_down:
            # Swap coordinates if needed
            if self.x1 > self.cursor_x:
                x1, x2 = self.cursor_x, self.x1
            else:
                x1, x2 = self.x1, self.cursor_x

            if self.y1 > self.cursor_y:
                y1, y2 = self.cursor_y, self.y1
            else:
                y1, y2 = self.y1, self.cursor_y

            # If any of the values are <= 2, draw a rectangle instead
            if (x2 - x1) < 2 or (y2 - y1) < 2:
                self.draw_rect()
                return

            # Ellipse drawing using Bresenham's algorithm
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            radius_x = (x2 - x1) // 2
            radius_y = (y2 - y1) // 2

            # Bresenham's ellipse algorithm variables
            a2 = radius_x * radius_x
            b2 = radius_y * radius_y
            two_a2 = 2 * a2
            two_b2 = 2 * b2
            x = 0
            y = radius_y
            dx = two_b2 * x
            dy = two_a2 * y
            err = a2 * (1 - 2 * radius_y)
            crit1 = -b2 * radius_x
            crit2 = a2 * (1 - 2 * radius_x)
            crit3 = crit1 - a2 * radius_y

            while y >= 0 and x <= radius_x:
                # Draw the ellipse in all four quadrants
                if filled:
                    for xi in range(center_x - x, center_x + x + 1):
                        self.set_pixel(xi, center_y + y)
                        self.set_pixel(xi, center_y - y)
                else:
                    # Outline with 1-pixel thickness
                    self.set_pixel(center_x + x, center_y + y)
                    self.set_pixel(center_x - x, center_y - y)
                    self.set_pixel(center_x + x, center_y - y)
                    self.set_pixel(center_x - x, center_y + y)

                if err <= 0:
                    x += 1
                    dx += two_b2
                    err += dx + b2
                if err > 0:
                    y -= 1
                    dy -= two_a2
                    err += a2 - dy

            self.reset_rect()
        else:
            self.x1, self.y1 = self.cursor_x, self.cursor_y
            self.pen_down = True

        
    def draw_line(self):
        if self.pen_down:
            x1, y1 = self.x1, self.y1
            x2, y2 = self.cursor_x, self.cursor_y

            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            sx = 1 if x1 < x2 else -1
            sy = 1 if y1 < y2 else -1
            err = dx - dy

            while True:
                self.set_pixel(x1, y1)
                if x1 == x2 and y1 == y2:
                    break
                e2 = err * 2
                if e2 > -dy:
                    err -= dy
                    x1 += sx
                if e2 < dx:
                    err += dx
                    y1 += sy

            self.reset_rect()
        else:
            self.x1, self.y1 = self.cursor_x, self.cursor_y
            self.pen_down = True

    def reset_rect(self):
        self.pen_down = False
        self.x1 = self.x2 = self.y1 = self.y2 = 0


    def bucket_fill(self, x, y, new_color):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        old_color = self.image.getpixel((x, y))
        if old_color == new_color:
            return
        self._bucket_fill(x, y, old_color, new_color)
        if self.mirror_h:
            self._bucket_fill(self.width - 1 - self.cursor_x, self.cursor_y, old_color, new_color)
        if self.mirror_v:
            self._bucket_fill(self.cursor_x, self.height - 1 - self.cursor_y, old_color, new_color)
        if self.mirror_h and self.mirror_v:
            self._bucket_fill(self.width - 1 - self.cursor_x, self.height - 1 - self.cursor_y, old_color, new_color)

    def _bucket_fill(self, x, y, old_color, new_color):
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if not (0 <= cx < self.width and 0 <= cy < self.height):
                continue
            if self.image.getpixel((cx, cy)) != old_color:
                continue
            self.image.putpixel((cx, cy), new_color)
            stack.append((cx + 1, cy))
            stack.append((cx - 1, cy))
            stack.append((cx, cy + 1))
            stack.append((cx, cy - 1))

    def update_cursor(self):
        self.stdscr.clear()
        self.display_view()
                                        
        if (self.pen_down):
            char='◘'
        else:
            char="•"

        if self.color_pair != 1: # if black turn to white (cause black on black ain't visible)
            color = curses.color_pair(self.color_pair) # set to active color
        else:
            color = curses.color_pair(2) | curses.A_REVERSE # set to white


        self.stdscr.addch(self.view_size // 2, self.view_size // 2, char, color)
        self.stdscr.move(self.view_size // 2, self.view_size // 2)

    def get_closest_color_id(self, rr, gg, bb, threshold=30):
        for i, (r, g, b) in enumerate(self.colors):
            if (r, g, b) == (rr, gg, bb):
                # Ensure that the index exists in self.color_pairs
                if i+1 in self.color_pairs:
                    return self.color_pairs[i+1]
                else:
                    return -1

            distance = math.sqrt((rr - r) ** 2 + (gg - g) ** 2 + (bb - b) ** 2)
            if distance <= threshold:
                if i+1 in self.color_pairs:
                    return self.color_pairs[i+1]
                else:
                    return -1

        closest_index = None
        min_distance = float('inf')

        for i, (r, g, b) in enumerate(self.colors):
            distance = math.sqrt((rr - r) ** 2 + (gg - g) ** 2 + (bb - b) ** 2)
            if distance < min_distance:
                min_distance = distance
                closest_index = i
                if distance <= threshold:
                    break

        # Ensure that closest_index+1 is valid before accessing self.color_pairs
        if closest_index is not None and closest_index+1 in self.color_pairs:
            return self.color_pairs[closest_index+1]
        else:
            return -1

    def display_view(self):
        # Example setup
        start_x = self.cursor_x - self.view_size // 2
        start_y = self.cursor_y - self.view_size // 2
        for y in range(-1,self.view_size):
            for x in range(-1,self.view_size):
                img_x = start_x + x
                img_y = start_y + y
                color_id=0
                char=" "
                closest=color_id

                # check if within the image canvas
                if 0 <= img_x < self.width and 0 <= img_y < self.height:
                    # get the rgb value for the current selected pixel
                    r, g, b = self.image.getpixel((img_x, img_y))
                    closest = self.get_closest_color_id(r,g,b)
                    rgb_color = (r,g,b)

                    # set the color id to black if blank
                    if (r + g + b == 0):
                        color_id = 3
                    else:
                        color_id = closest

                    # Assigning the char
                    if img_y == 0 or img_y == self.height-1 or img_x == 0 or img_x == self.width-1:
                        # borders
                        if (r + g + b == 0):
                            char = '.'
                        else:
                            char = '█'
                    elif (img_x == int(self.width / 2)+int(self.mirror_x_offset/2) and self.mirror_h):
                        # Vertical guideline for mirror mode
                        char = '|'
                        if (r + g + b == 0):
                            color_id = 3
                        else:
                            color_id = closest
                    elif (img_y == int(self.height / 2)+int(self.mirror_y_offset/2) and self.mirror_v):
                        # Horizontal guideline for mirror mode
                        char = '-'
                        if (r + g + b == 0):
                            color_id = 3
                        else:
                            color_id = closest
                    else:
                        # PREVIEW TOOL

                        char = '█'
                        color_id = closest
                        # Rect pen selection
                        if ( self.tool_id==4 or self.tool_id==5 ) and self.pen_down: 
                            if img_x >= self.x1 and img_y >= self.y1 and img_x <= self.cursor_x and img_y <= self.cursor_y or img_x <= self.x1 and img_y <= self.y1 and img_x >= self.cursor_x and img_y >= self.cursor_y or img_x >= self.x1 and img_y <= self.y1 and img_x <= self.cursor_x and img_y >= self.cursor_y or img_x <= self.x1 and img_y >= self.y1 and img_x >= self.cursor_x and img_y <= self.cursor_y:
                                char = 'x'
                                color_id=self.color_pair+1

                                # make black visible as white
                                if color_id==2:
                                    color_id=3
                                    
                        # Line tool preview
                        if self.tool_id == 3 and self.pen_down:
                            # Bresenham's line algorithm to determine line pixels
                            x1, y1 = self.x1, self.y1
                            x2, y2 = self.cursor_x, self.cursor_y

                            dx = abs(x2 - x1)
                            dy = abs(y2 - y1)
                            sx = 1 if x1 < x2 else -1
                            sy = 1 if y1 < y2 else -1
                            err = dx - dy

                            while True:
                                if img_x == x1 and img_y == y1:
                                    char = 'x'
                                    color_id = self.color_pair + 1

                                    # Make black visible as white
                                    if color_id == 2:
                                        color_id = 3

                                if x1 == x2 and y1 == y2:
                                    break

                                e2 = err * 2
                                if e2 > -dy:
                                    err -= dy
                                    x1 += sx
                                if e2 < dx:
                                    err += dx
                                    y1 += sy                         



                elif img_x > 0 and img_x < self.width:
                        if len(self.colors) < 64:
                            color_id=3
                            char = ' '
                            if (img_y == -1):
                                r, g, b = self.image.getpixel((img_x, self.height-1))
                                closest = self.get_closest_color_id(r,g,b)
                                color_id = closest
                                char = '▲'
                            if (img_y == self.height):
                                r, g, b = self.image.getpixel((img_x, 0))
                                closest = self.get_closest_color_id(r,g,b)
                                color_id = closest
                                char = '▼'
                elif img_y > 0 and img_y < self.height:
                        if len(self.colors) < 64:
                            color_id=3
                            char = ' '
                            if (img_x == -1):
                                r, g, b = self.image.getpixel((self.width-1, img_y))
                                closest = self.get_closest_color_id(r,g,b)
                                color_id = closest
                                char = '◀'
                            if (img_x == self.width):
                                r, g, b = self.image.getpixel((0, img_y))
                                closest = self.get_closest_color_id(r,g,b)
                                color_id = closest
                                char = '▶'
                else:
                    char = ' '
                    color_id = 3

                color_id = 1 if color_id is None else color_id

                try:
                    if color_id > 1:
                        # Color character only
                        self.stdscr.addch(y, x, char, curses.color_pair(color_id-1))
                        #else:
                        #    self.stdscr.addch(y, x, "z", curses.color_pair(12))
                    else:
                        # Default color
                        self.stdscr.addch(y, x, char, curses.color_pair(1))
                        
                except curses.error:
                    pass

                # TOP GUI INFO
                if self.info_bar==True:
                    offset_y=2
                    offset_x=2
                    for i in range(1,11):
                        index=i
                        if self.color_pair==index:
                            # active color
                            # chars: •█
                            char="•"
                            #self.stdscr.addstr(5+i, 7, str(self.colors[index-1])+", "+str(i-1), curses.color_pair(0))
                        else:
                            char=str(i-1)
                            #self.stdscr.addstr(5+i, 7, str(self.colors[index-1])+", "+str(index)+", "+str(i-1), curses.color_pair(0))

                        # make black visible
                        if index > 1:
                            self.stdscr.addch(offset_y+i, offset_x, char, curses.color_pair(index) | curses.A_REVERSE)
                        else:
                            self.stdscr.addch(offset_y+i, offset_x, char, curses.color_pair(2))
                    self.stdscr.addstr(1, 1, str(self.tools[self.tool_id]), curses.color_pair(2))
                    

                # default black and white
                #self.stdscr.addch(5, 5, char, curses.color_pair(0))
                #self.stdscr.addch(13, 5, char, curses.color_pair(1))
                # Use addstr to add a string at position (5, 5)
                # Debugs:
#                self.stdscr.addstr(20, 7, "Color: "+str(self.color), curses.color_pair(0))
#                self.stdscr.addstr(22, 7, "Index: "+str(self.color_pair), curses.color_pair(0))
#                self.stdscr.addstr(24, 7, "pos: "+str(self.cursor_x)+", "+str(self.cursor_y), curses.color_pair(0))
                
    # Could get less compression with higher resolution but that's good enaugh for pixel art, it's some between 128 and 64
    # If I implement a config file system that's the kind of stuff you could tweek in the pixrc file
    def load_image(self, filename, resolution=96):
        with Image.open(filename) as img:
            img = img.quantize(colors=resolution).convert('RGB')
            self.image = img
            self.width, self.height = self.image.size
            self.cursor_x = self.width // 2
            self.cursor_y = self.height // 2

            # Extract colors and count them
            pixels = list(self.image.getdata())
            color_count = Counter(pixels)
            most_common_colors = color_count.most_common(resolution)

            # Append unique colors to palette
            for color, _ in most_common_colors:
                if color not in self.colors:
                    self.colors.append(color)

                    
        self.initialize_colors()

    def rgb_prompt(self):
        curses.endwin()  # End curses mode to allow normal input
        # Could be a single input taking hex value instead
        r=input("R: ")
        g=input("G: ")
        b=input("B: ")
        self.color= (int(r),int(g),int(b))
        #curses.initscr()
        color_id=self.get_closest_color_id(int(r),int(g),int(b))
        
        #self.set_color(color_id)
        curses.setupterm()


    def hex_prompt(self):
        if self.color_pair<3: # don't overwrite the default (black and white)
            self.color_pair=3
        curses.endwin()  # End curses mode to allow normal input
        hex_color = input("Enter hex color (e.g., #ff5733 or ff5733): ").strip()

        # Remove the '#' if it's present
        if hex_color.startswith("#"):
            hex_color = hex_color[1:]

        # Ensure the input is exactly 6 characters long
        if len(hex_color) != 6:
            raise ValueError("Invalid hex color. Please provide a 6-character hex value.")

        # Convert hex to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # set the color
        self.color = (r, g, b)
        self.colors[self.color_pair-1]=self.color

        # update the color palette
        self.initialize_colors()

        curses.setupterm()




    def export_colors_to_hex(self):
        import curses
        curses.endwin()  # End curses mode to allow normal input

        # Prompt the user for the output file name
        print("Exporting current color pallet to .hex file.")
        filename = input("Enter the name for the output file (no extension): ")
        
        # Define colors to ignore
        colors_to_ignore = [(0, 0, 0), (255, 255, 255)]  # Black and White

        # Filter out the colors we want to ignore
        filtered_colors = [color for color in self.colors if color not in colors_to_ignore]

        # Ensure we only export up to 8 colors, even after filtering
        colors_to_export = filtered_colors[:8]
    
        # Prepare the file name with .hex extension
        hex_filename = f"{filename}.hex"

        try:
            with open(hex_filename, 'w') as file:
                for color in colors_to_export:
                    # Convert RGB to hexadecimal format
                    hex_color = "#{:02X}{:02X}{:02X}".format(color[0], color[1], color[2])
                    file.write(f"{hex_color}\n")
            print(f"Colors exported successfully to {hex_filename}")
        except IOError as e:
            print(f"Error writing file {hex_filename}: {e}")

        

    # use the color wheel from the color picker class
    def save_image(self, filename=None, confirm="n"):
        new_filename=""
        if filename is None:
            curses.endwin()  # End curses mode to allow normal input
            filename = input("Enter filename (default 'out.png'): ").strip()
            if not filename:
                filename = "out.png"
            #curses.setupterm()  # Restart curses mode
            confirm="y"

        if str(confirm.lower()) == "n":
            curses.endwin()  # End curses mode to allow normal input
            confirm = input("Save changes to "+str(filename)+"? (y/N): ").strip()
            if str(confirm.lower()) != "y":
                return 0            
            new_filename = input("Enter filename (default '"+str(filename)+"'): ").strip()
            
        if new_filename != "":
            filename=new_filename

        # Replace spaces with underscores and convert to lowercase
        filename = filename.replace(' ', '_').lower()

        if not filename.endswith('.png'):
            filename += '.png'
            
        if str(confirm.lower()) == "y":
            self.image.save(filename)


    def reset_image(self):
        curses.endwin()  # End curses mode to allow normal input
        confirm = input("Reset image? (y/N): ").strip()
        if confirm.lower() == "y":
            self.image = Image.new('RGB', (self.width, self.height), (0, 0, 0))  # Reset canvas to blank state
            self.pen_down = False
            self.cursor_x = self.width // 2
            self.cursor_y = self.height // 2
        curses.initscr()  # Restart curses mode

    def toggle_horizontal_mirroring(self):
        self.mirror_h = not self.mirror_h

    def toggle_vertical_mirroring(self):
        self.mirror_v = not self.mirror_v

    def take_screenshot(self):
        self.screenshots.append(self.image.copy())
        max_screenshots=25
        if len(self.screenshots) > max_screenshots:
            self.screenshots.pop(0)  # Keep only the last `max_history_steps` screenshots

    def load_screenshot(self):
        if self.screenshots:
            self.image = self.screenshots.pop()

def handle_input(key, drawing, keymap):
    if key in map(ord, '0123456789'):
        drawing.set_color(int(chr(key)))
        
    elif key in keymap['move_horizontal_mirroring']:
        if (drawing.mirror_x_offset < int(drawing.width-6)):
            drawing.mirror_x_offset+=2
        else:
            drawing.mirror_x_offset=-int(drawing.width-4)

    elif key in keymap['move_vertical_mirroring']:
        if (drawing.mirror_y_offset < int(drawing.height-6)):
            drawing.mirror_y_offset+=2
        else:
            drawing.mirror_y_offset=-int(drawing.height-4)

    elif key in keymap['move_up']:
        drawing.move_cursor('UP')
    elif key in keymap['move_down']:
        drawing.move_cursor('DOWN')
    elif key in keymap['move_left']:
        drawing.move_cursor('LEFT')
    elif key in keymap['move_right']:
        drawing.move_cursor('RIGHT')
    elif key in keymap['perform_action']:
        # NOTE!: ALL OF THIS COULD BE IN THE PERFORM ACTION FUNCTION OF THE DRAWING CLASS
        #drawing.perform_action()

        if not drawing.pen_down:
            drawing.save_image('pix.save.0.png', confirm="y")
            drawing.take_screenshot() # save current image to variable scre>

        # Tools actions
        if drawing.tool_id==0: # DOT
            drawing.pen_down = False
            drawing.draw_pixel()                        
        elif drawing.tool_id==1: # PEN
            drawing.pen_down = not drawing.pen_down
        elif drawing.tool_id==2: # BUCKET
            drawing.bucket_fill(drawing.cursor_x, drawing.cursor_y, drawing.color)
        elif drawing.tool_id==3: # LINE
            drawing.draw_line()            
        elif drawing.tool_id==4: # RECT
            drawing.draw_rect()            
        elif drawing.tool_id==5: # ELLIPSE
            drawing.draw_ellipse()            
        elif drawing.tool_id==6: # COPY
            drawing.pick_pixel()    
            drawing.tool_id=0
            drawing.pen_down = False

    elif key in keymap['save_and_quit']:
        drawing.save_image('pix.save.png')
        return False  # Quit

    elif key in keymap['save_with_confirm']:
        drawing.save_image('pix.save.png', confirm="y")
        return False  # Quit

    elif key in keymap['toggle_info_bar']:
        drawing.info_bar = not drawing.info_bar

    elif key in keymap['increase_color']:
        drawing.increase_color()

    elif key in keymap['decrease_color']:
        drawing.decrease_color()

    elif key in keymap['next_tool']:
        drawing.pen_down = False
        if drawing.tool_id < drawing.tool_count:
            drawing.tool_id += 1
        else:
            drawing.tool_id = 0

    elif key in keymap['previous_tool']:
        drawing.pen_down = False
        if drawing.tool_id > 0:
            drawing.tool_id -= 1
        else:
            drawing.tool_id = drawing.tool_count

    elif key in keymap['select_tool_0']: # DOT TOOL
        drawing.tool_id = 0
    elif key in keymap['select_tool_1']: # PEN TOOL
        drawing.tool_id = 1
    elif key in keymap['select_tool_2']: # BUCKET TOOL
        drawing.tool_id = 2
    elif key in keymap['select_tool_3']: # LINE TOOL
        drawing.tool_id = 3
    elif key in keymap['select_tool_4']: # RECT TOOL 
        drawing.tool_id = 4
    elif key in keymap['select_tool_5']: # ELLIPSE TOOL
        drawing.tool_id = 5
    elif key in keymap['select_tool_6']: # COPY TOOL
        drawing.pick_pixel()    
        drawing.tool_id = 6

    elif key in keymap['bucket_fill']:
        drawing.take_screenshot()  # Save current image to variable screenshot
        drawing.save_image('pix.save.0.png', confirm="y")
        drawing.bucket_fill(drawing.cursor_x, drawing.cursor_y, drawing.color)
    
    elif key in keymap['toggle_horizontal_mirroring']:
        drawing.toggle_horizontal_mirroring()

    elif key in keymap['toggle_vertical_mirroring']:
        drawing.toggle_vertical_mirroring()

    if key in keymap['hex_prompt']:
        drawing.hex_prompt()

    if key in keymap['hex_export']:
        drawing.export_colors_to_hex()

    # Check for pen down and specific tools
    if drawing.pen_down and drawing.tool_id == 1:
        drawing.draw_pixel()

    drawing.update_cursor()
    return True

        
def main(stdscr):
    #args = parse_arguments()
#    args = sys.argv[1:]
#    filename = single_argument(args)

#    if (sys.argv[1:]):
#        filename = str(sys.argv[1:])
    #else:
    filename = args.file if args.file else None
    palette = args.palette if args.palette else "palette.hex"

    #curses.curs_set(1)  # Make cursor visible

    # Hide the cursor
    curses.curs_set(0)
    
    stdscr.clear()

    # so if args.width is passed make drawing.width equal to args.width if not argument passed use 64 as the default
    canvas_width = args.width if args.width else 64
    canvas_height = args.height if args.height else 64

    #background=args.background
    drawing = Drawing(stdscr, filename=filename, width=canvas_width, background=-1, palette=palette)
    drawing.update_cursor()  # Initial cursor update
    
    def signal_handler(sig, frame):
        if not os.path.exists("pix.save."+str(sig)+".png"):
            drawing.save_image("pix.save."+str(sig)+".png", "y")
        curses.endwin()
        exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    while True:
        stdscr.refresh()
        key = stdscr.getch()
        if not handle_input(key, drawing,keymap):
            break



def is_valid_img(file_name):
    if not os.path.isfile(file_name):
        return False
    
    try:
        with Image.open(file_name) as img:
            img.verify()  # Verify the file is an image
        return True
    except (IOError, SyntaxError):
        return False

        
parser = argparse.ArgumentParser(description='CLI drawing program.')
parser = argparse.ArgumentParser(usage='(w,a,s,d) keys to move the cursor, (e) to export, (0 - 9) change the color, (b) bucket fill, (h,v) mirror pen, (space) toggle pen, (enter) place single pixel, (u) Undo')
parser.add_argument('-W','--width', type=int, default=64, help='Width of the image. (default: 64)')
parser.add_argument('-H','--height', type=int, default=64, help='Height of the image (default; 64).')
parser.add_argument('-f','--file', type=str, help='File to load.')
parser.add_argument('-p','--palette', type=str, help='palette file (default; palette.hex).')
parser.add_argument('-k','--keymap', type=str, default="default.key", help='Keymap file (default: default.key).')
#args = parser.parse_args()
args, unknown_args = parser.parse_known_args()


# Load keymap from a file
keymap = load_keymap(args.keymap, default_keymap)


# Handle the case where a single argument is passed
if len(unknown_args) == 1:
    potential_file = unknown_args[0]
    # check if the file exist and is an image
    if is_valid_img(potential_file):
        args.file = potential_file
    else:
        print(f"Error: '{potential_file}' is not a valid file.")
        exit(1)

curses.wrapper(main)

if os.path.exists('pix.save.0.png'):
    os.remove('pix.save.0.png')
