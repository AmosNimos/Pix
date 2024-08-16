import signal
import argparse
import curses
import os
from PIL import Image
from random import randint

class Drawing:
    def __init__(self, stdscr, width=64, height=64, view_size=64, filename=None, background=-1):

        # for line pen:
        self.pen_down=False
        self.color_id=1 # default white
        self.color = (255, 255, 255)  # Default color white
        self.colors = []  # empty color palette
        self.tool_id=0 #( concept: to add more tools later on, and toggle between them, each tool could later have their own character for the cursor to diferentiate them)
        self.x1 = self.x2 = self.y1 = self.y2 = -1
        self.tty_mode = False
        self.background_color=background
        self.filename = filename
        self.stdscr = stdscr
        self.width = width
        self.height = height
        self.view_size = view_size
        self.image = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        self.cursor_x = width // 2
        self.cursor_y = height // 2
        self.mirror_h = self.mirror_v = False
        self.undo_stack = []
        self.redo_stack = []
        self.screenshots = []  # Change to a list to store multiple screenshots
        self.current_state = self.take_screenshot()

    def init_color(self):
        curses.start_color()        
        for i in range(256):
            # All combination of RGB colors
            curses.init_color(i, i * 1000 // 255, i * 1000 // 255, i * 1000 // 255)
            curses.init_pair(i + 1, curses.COLOR_BLACK, i)

    def set_color(self, color_key):
        self.color = self.colors[int(color_key)]
        
                
    def move_cursor(self, direction):
        if direction == 'UP':
            self.cursor_y = (self.cursor_y - 1) % self.height
        elif direction == 'DOWN':
            self.cursor_y = (self.cursor_y + 1) % self.height
        elif direction == 'LEFT':
            self.cursor_x = (self.cursor_x - 1) % self.width
        elif direction == 'RIGHT':
            self.cursor_x = (self.cursor_x + 1) % self.width


    def increase_color(self):
        colors_count=int(len(self.colors))
        if self.color_id < colors_count:
            self.color = self.colors[int(self.color_id)]
            self.color_id+=1
        else:
            self.color_id=1
            self.color = self.colors[int(self.color_id)]
            
    def decrease_color(self):
        colors_count=int(len(self.colors))
        if self.color_id > 1:
            self.color_id-=1
            self.color = self.colors[str(self.color_id-1)]
        else:
            self.color_id=colors_count

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

    def draw_rect(self):

        if (self.pen_down):
            self.x2=self.cursor_x
            self.y2=self.cursor_y

            # Make work in all directions
            if self.x1 > self.x2:
                xx=self.x1
                self.x1=self.x2
                self.x2=xx
            if self.y1 > self.y2:
                yy=self.y1
                self.y1=self.y2
                self.y2=yy

            self.x2+=1
            self.y2+=1
            for x in range(self.x1,self.x2):
                for y in range(self.y1,self.y2):
                    self.set_pixel(x,y)
                    
            self.pen_down=False
            self.x1=-1
            self.x2=-1
            self.y1=-1
            self.y2=-1
        else:
            self.x1=self.cursor_x 
            self.y1=self.cursor_y
            self.rect_pen=True


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
            self.stdscr.addch(self.view_size // 2, self.view_size // 2, '•', curses.color_pair(self.color_id) | curses.A_REVERSE)
        else:
            self.stdscr.addch(self.view_size // 2, self.view_size // 2, '◘', curses.color_pair(self.color_id) | curses.A_REVERSE)
        self.stdscr.move(self.view_size // 2, self.view_size // 2)

    def display_view(self):
        # Example setup
        self.stdscr.clear()
        start_x = self.cursor_x - self.view_size // 2
        start_y = self.cursor_y - self.view_size // 2
        for y in range(-1,self.view_size):
            for x in range(-1,self.view_size):
                img_x = start_x + x
                img_y = start_y + y
                char=" "
                char_color_id=-1
                if 0 <= img_x < self.width and 0 <= img_y < self.height:
                    # get the rgb value for the current selected pixel
                    r, g, b = self.image.getpixel((img_x, img_y))
                    rgb_color = (r,g,b)

                    # set the color id to black if blank
                    if (r + g + b == 0):
                        char_color_id = -1
                    else:
                        char_color_id = self.get_closest_color_id(r, g, b)

                    # Assigning the char
                    if img_y == 0 or img_y == self.height-1 or img_x == 0 or img_x == self.width-1:
                        # border limit
                        if (r + g + b == 0):
                            char = '.'
                        else:
                            char = '█'
                    elif (img_x == int(self.width / 2) and self.mirror_h):
                        # Vertical guideline for mirror mode
                        char = '|'
                    elif (img_y == int(self.height / 2) and self.mirror_v):
                        # Horizontal guideline for mirror mode
                        char = '-'
                        if (r + g + b == 0):
                            char_color_id = -1
                    else:
                        # pixel color
                        char = '█'
                        char_color_id = self.get_closest_color_id(r, g, b)
                        # for drawing rectangles
                        if self.rect_pen: 
                            if img_x >= self.x1 and img_y >= self.y1 and img_x <= self.cursor_x and img_y <= self.cursor_y or img_x <= self.x1 and img_y <= self.y1 and img_x >= self.cursor_x and img_y >= self.cursor_y or img_x >= self.x1 and img_y <= self.y1 and img_x <= self.cursor_x and img_y >= self.cursor_y or img_x <= self.x1 and img_y >= self.y1 and img_x >= self.cursor_x and img_y <= self.cursor_y:
                                char = 'x'
                                char_color_id=self.char_color_id
                elif img_x > 0 and img_x < self.width:
                        # represent the color on the oposite side horizontally
                        char_color_id=-1
                        if (img_y == -1):
                            r, g, b = self.image.getpixel((img_x, self.height-1))
                            char_color_id = self.get_closest_color_id(r, g, b)
                            char = '▲'
                        elif (img_y == self.height):
                            r, g, b = self.image.getpixel((img_x, 0))
                            char_color_id = self.get_closest_color_id(r, g, b)
                            char = '▼'
                        else:
                            char = ' '
                elif img_y > 0 and img_y < self.height:
                        # represent the color on the oposite side vertically
                        char_color_id=-1
                        if (img_x == -1):
                            r, g, b = self.image.getpixel((self.width-1, img_y))
                            char_color_id = self.get_closest_color_id(r, g, b)
                            char = '◀'
                        elif (img_x == self.width):
                            r, g, b = self.image.getpixel((0, img_y))
                            char_color_id = self.get_closest_color_id(r, g, b)
                            char = '▶'
                        else:
                            char = ' '
                else:
                    # default alpha, no pixel color value
                    char = ' '
                    char_color_id = -1

                # Ensure char_color_id is an integer and falls back to a default if None
                if char_color_id is None or not isinstance(char_color_id, int):
                    char_color_id = 1  # or any valid default color ID
                
                self.stdscr.addch(y, x, char, curses.color_pair(1))
                self.stdscr.refresh()

                try:
                    if char_color_id != -1:
                        # Color character only
                        self.stdscr.addch(y, x, char, curses.color_pair(1))
                    else:
                        # Default color
                        self.stdscr.addch(y, x, char)
                except curses.error:
                    pass

    def get_closest_color_id(self, r, g, b):
        closest_color_id = None
        closest_distance = float('inf')
        
        for i, color in enumerate(self.colors):
            distance = ((r - color[0]) ** 2 + (g - color[1]) ** 2 + (b - color[2]) ** 2) ** 0.5
            if distance < closest_distance:
                closest_distance = distance
                closest_color_id = i

        return closest_color_id


    def load_image(self, filename):
        with Image.open(filename) as img:
            self.image = img.convert('RGB')
            self.width, self.height = self.image.size
            self.cursor_x = self.width // 2
            self.cursor_y = self.height // 2

    def hex_picker(self):
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

        self.color = (r, g, b)
        color_id = self.get_closest_color_id(r, g, b)

        curses.setupterm()

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
        drawing.set_color(chr(key))
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
    elif key == ord('b'):  # Bucket fill
        drawing.take_screenshot() # save current image to variable screenshot
        drawing.save_image('pix.save.0.png', confirm="y")
        drawing.bucket_fill(drawing.cursor_x, drawing.cursor_y, drawing.color)
    elif key == ord('h'):
        drawing.toggle_horizontal_mirroring()
    elif key == ord('v'):
        drawing.toggle_vertical_mirroring()
    elif key == ord('c'):
        drawing.hex_picker()
    if key == ord('='):
        drawing.increase_color()

    if key == ord('-'):
        drawing.decrease_color()
        
    # Drawing logic if pen is down
    if drawing.pen_down:
        if drawing.tool_id==0:
            drawing.draw_pixel()
        elif drawing.tool_id==1: 
            drawing.draw_rect()            

    drawing.update_cursor()

    return True    
        
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
    drawing.init_color
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
# note (and if only one argument is given without flag use it as file name)a
parser.add_argument('-W','--width', type=int, default=64, help='Width of the image.')
parser.add_argument('-H','--height', type=int, default=64, help='Height of the image.')
parser.add_argument('-f','--file', type=str, help='File to load.')
parser.add_argument('-b','--background', type=int, default=-1, help="Canvas background color")
args = parser.parse_args()



curses.wrapper(main)

if os.path.exists('pix.save.0.png'):
    os.remove('pix.save.0.png')
