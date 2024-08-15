# Pixel-art Independent of X11 or P.I.X for short
import signal
import argparse
import curses
import os
from PIL import Image
from random import randint
import math
from collections import Counter

class Drawing:
    def __init__(self, stdscr, width=64, height=64, view_size=64, filename=None, background=0):
        self.stdscr = stdscr
        # for line pen:
        self.rect_pen=False
        self.tool_id=0
        self.tool_count=3
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

        self.tools = ["Pen","Pixel","Rect","Pick"]
        
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

        # NOTE: Add some random colors to the default pallet
        suported_colors=24
        while len(self.colors) < suported_colors:
            random_color = (randint(0, 255), randint(0, 255), randint(0, 255))
            if random_color not in self.colors:
                self.colors.append(random_color)
 
        self.load_rgb_from_file("pix.hex")
        self.color_pairs = {}
        self.initialize_colors()
        self.pen_down = False  # Initialize pen state
        self.set_color(1)

        if filename:
            self.load_image(filename)

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
            self.image.putpixel((self.width - 1 - self.cursor_x, self.cursor_y), self.color)
        if self.mirror_v:
            self.image.putpixel((self.cursor_x, self.height - 1 - self.cursor_y), self.color)
        if self.mirror_h and self.mirror_v:
            self.image.putpixel((self.width - 1 - self.cursor_x, self.height - 1 - self.cursor_y), self.color)

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
            self.x2, self.y2 = self.cursor_x, self.cursor_y
            x1, x2 = sorted([self.x1, self.x2])
            y1, y2 = sorted([self.y1, self.y2])
            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    self.set_pixel(x, y)
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
#            if self.tool_id == 0: # Line tool
#                char='•'
#            elif self.tool_id == 1: # Rect tool
#                char="🖍"
#            elif self.tool_id == 2: # Picker tool
#                char="🖋"
#            elif self.tool_id == 3: # Pixel tool
#                char="🖌"             
#            else:
            char=str(self.tool_id)

        if self.color_pair != 1: # if black turn to white (cause black on black ain't visible)
            color = curses.color_pair(self.color_pair) # set to active color
        else:
            color = curses.color_pair(2) | curses.A_REVERSE # set to white
#            if (self.pen_down):
#                char='X'
#            else:
#                char='x'


        self.stdscr.addch(self.view_size // 2, self.view_size // 2, char, color)
        self.stdscr.move(self.view_size // 2, self.view_size // 2)

    # Get the closest even if not exact match
#    def get_closest_color_id(self, rr, gg, bb):
#        for i, (r, g, b) in enumerate(self.colors):
#            if (r, g, b) == (rr, gg, bb):
#                return self.color_pairs[i+1]
#
#        closest_index = None
#        min_distance = float('inf')
#
#        for i, (r, g, b) in enumerate(self.colors):
#            # Calculate the Euclidean distance between the colors
#            distance = math.sqrt((rr - r) ** 2 + (gg - g) ** 2 + (bb - b) ** 2)
#            
#            if distance < min_distance:
#                min_distance = distance
#                closest_index = i
#
#        # Return the closest color pair if found, otherwise return -1
#        return self.color_pairs[closest_index+1] if closest_index is not None else -1

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
                    elif (img_x == int(self.width / 2) and self.mirror_h):
                        # Vertical guideline for mirror mode
                        char = '|'
                        if (r + g + b == 0):
                            color_id = 3
                        else:
                            color_id = closest
                    elif (img_y == int(self.height / 2) and self.mirror_v):
                        # Horizontal guideline for mirror mode
                        char = '-'
                        if (r + g + b == 0):
                            color_id = 3
                        else:
                            color_id = closest
                    else:
                        char = '█'
                        color_id = closest
                        # rect pen selection
                        if self.tool_id==2 and self.pen_down: 
                            if img_x >= self.x1 and img_y >= self.y1 and img_x <= self.cursor_x and img_y <= self.cursor_y or img_x <= self.x1 and img_y <= self.y1 and img_x >= self.cursor_x and img_y >= self.cursor_y or img_x >= self.x1 and img_y <= self.y1 and img_x <= self.cursor_x and img_y >= self.cursor_y or img_x <= self.x1 and img_y >= self.y1 and img_x >= self.cursor_x and img_y <= self.cursor_y:
                                char = 'x'
                                color_id=self.color_pair+1
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

                # pbar Draw pallet bar
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
                    

                # default black and white
                #self.stdscr.addch(5, 5, char, curses.color_pair(0))
                #self.stdscr.addch(13, 5, char, curses.color_pair(1))
                # Use addstr to add a string at position (5, 5)
                # Debugs:
                self.stdscr.addstr(1, 1, str(self.tools[self.tool_id]), curses.color_pair(2))
#                self.stdscr.addstr(20, 7, "Color: "+str(self.color), curses.color_pair(0))
#                self.stdscr.addstr(22, 7, "Index: "+str(self.color_pair), curses.color_pair(0))
#                self.stdscr.addstr(24, 7, "pos: "+str(self.cursor_x)+", "+str(self.cursor_y), curses.color_pair(0))
                
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
        if self.color_pair-1>1: # don't overwrite the default (black and white)
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
        

    # use the color wheel from the color picker class

    def save_image(self, filename=None, confirm="n"):
        if filename is None:
            curses.endwin()  # End curses mode to allow normal input
            filename = input("Enter filename (default 'out.png'): ").strip()
            if not filename:
                filename = "out.png"
            if not filename.endswith('.png'):
                filename += '.png'
            # Replace spaces with underscores and convert to lowercase
            filename = filename.replace(' ', '_').lower()
            #curses.setupterm()  # Restart curses mode
            confirm="y"

        if str(confirm.lower()) == "n":
            curses.endwin()  # End curses mode to allow normal input
            confirm = input("Save changes to "+str(filename)+"? (y/N): ").strip()            

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

def handle_input(key, drawing):
    if key == 'KEY_UP' or key == 'KEY_DOWN' or key == 'KEY_LEFT' or key == 'KEY_RIGHT' or key == ' ' or key == 'b' or key == 'x':
        drawing.perform_action()
        drawing.undo_stack.append(drawing.take_screenshot())
        if len(drawing.undo_stack) > drawing.max_history_steps:
            drawing.undo_stack.pop(0)
        drawing.redo_stack.clear()

    if key == ord('q'):
        drawing.save_image('pix.save.png')
        return False  # Quit on 'q'
    if key == ord('Q'):
        drawing.save_image('pix.save.png', confirm="y")
        return False  # Quit on 'q'
    if key in map(ord, '0123456789'):
        drawing.set_color(int(chr(key)))
    elif key == ord('e'):  # 'e' to save and quit
        drawing.save_image(filename=drawing.filename)  # Save with default or user-provided filename
        return False
    elif key == ord('e'):  # 'e' to save and quit
        drawing.save_image(filename=drawing.filename)  # Save with default or user-provided filename
        return False
    elif key == ord('u'):  # 'e' to save and quit
        drawing.load_screenshot() # load variable screenshot to current image
    elif key == curses.KEY_UP or key == ord('w'):
        drawing.move_cursor('UP')
    elif key == curses.KEY_DOWN or key == ord('s'):
        drawing.move_cursor('DOWN')
    elif key == curses.KEY_LEFT or key == ord('a'):
        drawing.move_cursor('LEFT')
    elif key == curses.KEY_RIGHT or key == ord('d'):
        drawing.move_cursor('RIGHT')
    if key == ord(' ') or key == ord('\n'):
        if not drawing.pen_down:
            drawing.save_image('pix.save.0.png', confirm="y")
            drawing.take_screenshot() # save current image to variable screenshot
        # Tools actions
        if drawing.tool_id==0:
            drawing.pen_down = not drawing.pen_down
        elif drawing.tool_id==1:
            drawing.pen_down = False
            drawing.draw_pixel()                        
        elif drawing.tool_id==2:
            drawing.draw_rect()            
        elif drawing.tool_id==3:
            drawing.pick_pixel()    
            drawing.tool_id=0
            drawing.pen_down = False

    if key == ord('t'):
        drawing.pen_down = False
        if drawing.tool_id<drawing.tool_count:
            drawing.tool_id+=1
        else:
            drawing.tool_id=0
    elif key == ord('b'):  # Bucket fill
        drawing.take_screenshot() # save current image to variable screenshot
        drawing.save_image('pix.save.0.png', confirm="y")
        drawing.bucket_fill(drawing.cursor_x, drawing.cursor_y, drawing.color)
    elif key == ord('h'):
        drawing.toggle_horizontal_mirroring()
    elif key == ord('v'):
        drawing.toggle_vertical_mirroring()
    elif key == ord('c'):
        # Right now this is for entering custom hex values
        drawing.hex_prompt()
    elif key == ord('n'):
        drawing.noise_texture()
    # Once I nail the color selection these could be use to swap tools
    if key == ord('='):
        drawing.increase_color()
    if key == ord('-'):
        drawing.decrease_color()
        
    # Drawing logic if pen is down
    if drawing.pen_down and drawing.tool_id==0:
        drawing.draw_pixel()

    drawing.update_cursor()

    return True

def parse_arguments():
    parser = argparse.ArgumentParser(description='Pix - Minimalistic CLI Pixel Art Tool')
    parser.add_argument('-f', '--file', type=str, help="Path to the image file to load.")
    parser.add_argument('-W', '--width', type=int, default=64, help="Width of the canvas")
    parser.add_argument('-H','--height', type=int, default=64, help="Height of the canvas")
    parser.add_argument('--help', action='store_true', help='Show help message and exit.')
#    parser.add_argument('-v', '--view', type=int, default=64, help="View size of the canvas")
    args = parser.parse_args()
    return args
    
        
def main(stdscr):
    #args = parse_arguments()
    
    filename = args.file if args.file else None

    #curses.curs_set(1)  # Make cursor visible

    # Hide the cursor
    curses.curs_set(0)
    
    stdscr.clear()

    # so if args.width is passed make drawing.width equal to args.width if not argument passed use 64 as the default
    canvas_width = args.width if args.width else 64
    canvas_height = args.height if args.height else 64

    drawing = Drawing(stdscr, filename=filename, width=canvas_width, background=args.background )
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
        if not handle_input(key, drawing):
            break



parser = argparse.ArgumentParser(description='CLI drawing program.')
parser = argparse.ArgumentParser(usage='(w,a,s,d) keys to move the cursor, (e) to export, (0 - 9) change the color, (b) bucket fill, (h,v) mirror pen, (r) reset canvas, (l) color wheel, (space) toggle pen, (enter) place single pixel, (U,F) Undo & Redo')
parser.add_argument('-W','--width', type=int, default=64, help='Width of the image.')
parser.add_argument('-H','--height', type=int, default=64, help='Height of the image.')
parser.add_argument('-F','--file', type=str, help='File to load.')
parser.add_argument('-B','--background', type=int, default=-1, help="Canvas background color")
args = parser.parse_args()



curses.wrapper(main)

if os.path.exists('pix.save.0.png'):
    os.remove('pix.save.0.png')
