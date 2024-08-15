import signal
import argparse
import curses
import os
from PIL import Image
from random import randint
import math

class ColorPicker:
    def __init__(self):
        self.color = (0, 0, 0)
        self.screen = curses.initscr()
        curses.start_color()
        curses.curs_set(0)
        self.screen.keypad(True)

        # Initialize all 256 colors
        for i in range(0, 256):
            curses.init_pair(i, i, 0)

    def hex_prompt(self):
        max_y, max_x = self.screen.getmaxyx()
        rows = 16  # Number of rows in the color grid
        cols = 16  # Number of columns in the color grid

        def draw_color_grid(selected_y, selected_x):
            for y in range(rows):
                for x in range(cols):
                    color_index = y * cols + x
                    if color_index < 256:
                        if y == selected_y and x == selected_x:
                            self.screen.addstr(y, x * 3, "  ", curses.color_pair(color_index) | curses.A_REVERSE)
                        else:
                            self.screen.addstr(y, x * 3, "  ", curses.color_pair(color_index))
            self.screen.refresh()

        selected_y, selected_x = 0, 0
        draw_color_grid(selected_y, selected_x)

        while True:
            key = self.screen.getch()
            if key == curses.KEY_UP:
                selected_y = (selected_y - 1) % rows
            elif key == curses.KEY_DOWN:
                selected_y = (selected_y + 1) % rows
            elif key == curses.KEY_LEFT:
                selected_x = (selected_x - 1) % cols
            elif key == curses.KEY_RIGHT:
                selected_x = (selected_x + 1) % cols
            elif key == ord('q'):  # Press 'q' to quit
                break
            elif key == ord('\n'):  # Press 'Enter' to select color
                color_index = selected_y * cols + selected_x
                self.color = curses.color_content(color_index)
                break

            draw_color_grid(selected_y, selected_x)

        curses.endwin()

class Drawing:
    def __init__(self, stdscr, width=64, height=64, view_size=64, filename=None, background=0):
        self.stdscr = stdscr
        self.rect_pen = False
        self.x1 = self.x2 = self.y1 = self.y2 = -1
        self.background_color = background
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

        self.colors = self.init_colors()

        self.color_pairs = {}
        self.initialize_colors()
        self.pen_down = False  # Initialize pen state
        self.set_color(1)

        if filename:
            self.load_image(filename)

    def init_colors(self):
        """Initialize and return the color palette."""
        colors = [
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

        # Add random unique colors until we reach 254 total colors
        while len(colors) < 254:
            random_color = (randint(0, 255), randint(0, 255), randint(0, 255))
            if random_color not in colors:
                colors.append(random_color)

        return colors

    def update_cursor(self):
        self.stdscr.clear()
        self.display_view()
                                        
        if (self.pen_down):
            char='•'
        else:
            char='◘'

        if self.color_pair != 1: # if black turn to white (cause black on black ain't visible)
            color = curses.color_pair(self.color_pair) # set to active color
        else:
            color = curses.color_pair(2) # set to white
            char='X'

    def hex_to_rgb(self, hex_color):
        """Convert a hex color to an RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def load_rgb_from_file(self, filename):
        """Load hex colors from a file and convert them to RGB."""
        with open(filename, 'r') as file:
            for i, line in enumerate(file):
                hex_color = line.strip()
                rgb_tuple = self.hex_to_rgb(hex_color)
                self.colors[i+1] = rgb_tuple

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
        if int(color_key) <= 1:
            self.set_color(color_key)
        else:
            index = int(len(self.colors) - 10) + int(color_key)
            self.color = self.colors[index]
            self.color_pair = self.color_pairs[index]

    def increase_color(self):
        if self.color_pair < len(self.colors):
            self.set_color(self.color_pair)
            self.color_pair += 1
        else:
            self.color_pair = 1
            self.set_color(self.color_pair)

    def decrease_color(self):
        if self.color_pair > 1:
            self.color_pair -= 1
            self.set_color(self.color_pair - 1)
        else:
            self.color_pair = len(self.colors)

    def draw_pixel(self):
        self.image.putpixel((self.cursor_x, self.cursor_y), self.color)
        if self.mirror_h:
            self.image.putpixel((self.width - 1 - self.cursor_x, self.cursor_y), self.color)
        if self.mirror_v:
            self.image.putpixel((self.cursor_x, self.height - 1 - self.cursor_y), self.color)
        if self.mirror_h and self.mirror_v:
            self.image.putpixel((self.width - 1 - self.cursor_x, self.height - 1 - self.cursor_y), self.color)

    def set_pixel(self, x, y, color=-1):
        if color == -1:
            color = self.color
        self.image.putpixel((x, y), color)
        if self.mirror_h:
            self.image.putpixel((self.width - 1 - x, y), color)
        if self.mirror_v:
            self.image.putpixel((x, self.height - 1 - y), color)
        if self.mirror_h and self.mirror_v:
            self.image.putpixel((self.width - 1 - x, self.height - 1 - y), color)

    def draw_rect(self):
        if self.rect_pen:
            self.x2, self.y2 = self.cursor_x, self.cursor_y
            x1, x2 = sorted([self.x1, self.x2])
            y1, y2 = sorted([self.y1, self.y2])
            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    self.set_pixel(x, y)
            self.reset_rect()
        else:
            self.x1, self.y1 = self.cursor_x, self.cursor_y
            self.rect_pen = True

    def reset_rect(self):
        self.rect_pen = False
        self.x1 = self.x2 = self.y1 = self.y2 = -1

    def take_screenshot(self):
        return self.image.copy()

    def load_image(self, filename):
        self.image = Image.open(filename).resize((self.width, self.height))

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
    if key == ord(' '):
        drawing.pen_down = not drawing.pen_down
        if drawing.pen_down:
            drawing.save_image('pix.save.0.png', confirm="y")
            drawing.take_screenshot() # save current image to variable screenshot
    if key == ord('\n'):
        drawing.pen_down = False
        drawing.save_image('pix.save.0.png', confirm="y")
        drawing.take_screenshot() # save current image to variable screenshot
        drawing.draw_pixel()
    if key == ord('l'):
        drawing.pen_down = False
        drawing.save_image('pix.save.0.png', confirm="y")
        drawing.take_screenshot() # save current image to variable screenshot
        drawing.draw_rect()            
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
    if drawing.pen_down:
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
