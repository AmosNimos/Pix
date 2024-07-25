import argparse
import curses
from PIL import Image

class Drawing:
    def __init__(self, stdscr, width=64, height=64, view_size=64, filename=None):
        self.tty_mode = False
        self.filename = filename
        self.stdscr = stdscr
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
        self.colors = {
            '0': (0, 0, 0),
            '1': (255, 255, 255),
            '2': (255, 0, 0),
            '3': (0, 255, 0),
            '4': (0, 0, 255),
            '5': (255, 255, 0),
            '6': (0, 255, 255),
            '7': (255, 0, 255),
            '8': (192, 192, 192),
            '9': (128, 128, 128),
            '9': (128, 128, 128),
        }
        # Add 216 colors in a 6x6x6 color cube
        for i in range(6):
            for j in range(6):
                for k in range(6):
                    index = 16 + (i * 36) + (j * 6) + k
                    r = i * 51
                    g = j * 51
                    b = k * 51
                    self.colors[str(index)] = (r, g, b)

        # Add 24 grayscale colors
        for i in range(24):
            gray = i * 10 + 8
            index = 232 + i
            self.colors[str(index)] = (gray, gray, gray)
        
        self.set_tty_mode()
        self.color_pairs = {}
        self.initialize_colors()
        self.pen_down = False  # Initialize pen state
        self.set_color("1")

        if filename:
            self.load_image(filename)

#    def initialize_colors(self):

        
    def set_tty_mode(self):
        curses.setupterm()
        colors = curses.tigetnum("colors")
        if (colors is not None and colors < 256):
            self.tty_mode = True

    def initialize_colors(self):
        if self.tty_mode:
            curses.start_color()
            curses.use_default_colors()
            
            # Define standard 8-color palette
            palette = {
                '0': curses.COLOR_WHITE,
                '1': curses.COLOR_RED,
                '2': curses.COLOR_GREEN,
                '3': curses.COLOR_BLUE,
                '4': curses.COLOR_YELLOW,
                '5': curses.COLOR_CYAN,
                '6': curses.COLOR_MAGENTA,
                '7': curses.COLOR_BLACK,
                '8': curses.COLOR_BLACK,   # Gray
                '9': curses.COLOR_BLACK    # Black
            }
            
            # Initialize color pairs
            color_id = 1
            for key, color_code in palette.items():
                curses.init_pair(color_id, color_code, curses.COLOR_BLACK)  # Use black as background
                self.color_pairs[key] = color_id
                color_id += 1
        else:
            curses.start_color()
            curses.use_default_colors()
            color_id = 1
            for i, (r, g, b) in self.colors.items():
                curses.init_color(color_id, int(r * 1000 / 255), int(g * 1000 / 255), int(b * 1000 / 255))
                curses.init_pair(color_id, color_id, -1)  # Use -1 for the background color
                self.color_pairs[i] = color_id
                color_id += 1
         

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
        self.color = self.colors[color_key]
        self.color_pair = self.color_pairs[color_key]

    def draw_pixel(self):
        self.image.putpixel((self.cursor_x, self.cursor_y), self.color)
        if self.mirror_h:
            self.image.putpixel((self.width - 1 - self.cursor_x, self.cursor_y), adjusted_color)
        if self.mirror_v:
            self.image.putpixel((self.cursor_x, self.height - 1 - self.cursor_y), adjusted_color)
        if self.mirror_h and self.mirror_v:
            self.image.putpixel((self.width - 1 - self.cursor_x, self.height - 1 - self.cursor_y), adjusted_color)

    def bucket_fill(self, x, y, new_color):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        old_color = self.image.getpixel((x, y))
        if old_color == new_color:
            return
        self._bucket_fill(x, y, old_color, new_color)

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
        # ◯
        if (self.pen_down):
            self.stdscr.addch(self.view_size // 2, self.view_size // 2, '•', curses.color_pair(self.color_pair) | curses.A_REVERSE)
        else:
            self.stdscr.addch(self.view_size // 2, self.view_size // 2, '◘', curses.color_pair(self.color_pair) | curses.A_REVERSE)
        self.stdscr.move(self.view_size // 2, self.view_size // 2)

    def display_view(self):
        start_x = self.cursor_x - self.view_size // 2
        start_y = self.cursor_y - self.view_size // 2
        for y in range(self.view_size):
            for x in range(self.view_size):
                img_x = start_x + x
                img_y = start_y + y
                if 0 <= img_x < self.width and 0 <= img_y < self.height:
                    r, g, b = self.image.getpixel((img_x, img_y))
                    if (r + g + b == 0):
                        color_id = -1
                    else:
                        color_id = self.get_closest_color_id(r, g, b)

                    if img_x < 1 or img_x >= self.width-1 or img_y < 1 or img_y >= self.height-1:
                            char = '.'
                    elif (img_x == int(self.width / 2) and self.mirror_h):
                        # Vertical guideline
                        char = '|'
                    elif (img_y == int(self.height / 2) and self.mirror_v):
                        # Horizontal guideline
                        char = '-'
                        if (r + g + b == 0):
                            color_id = -1
                        else:
                            color_id = self.get_closest_color_id(r, g, b)
                    else:
                        char = '█'
                        color_id = self.get_closest_color_id(r, g, b)
                #elif img_x == -1 or img_x == self.width or img_y == -1 or img_y == self.height:
                else:
                    char = ' '
                    color_id = -1

                try:
                    if color_id != -1:
                        # Color character only
                        self.stdscr.addch(y, x, char, curses.color_pair(color_id))
                    else:
                        # Default color
                        self.stdscr.addch(y, x, char)
                except curses.error:
                    pass


    def get_closest_color_id(self, r, g, b):
        for key, color in self.colors.items():
            if color == (r, g, b):
                return self.color_pairs[key]
        return -1

    def load_image(self, filename):
        with Image.open(filename) as img:
            self.image = img.convert('RGB')
            self.width, self.height = self.image.size
            self.cursor_x = self.width // 2
            self.cursor_y = self.height // 2


    def color_wheel(self):
        curses.endwin()  # End curses mode to allow normal input
        # Could be a single input taking hex value instead
        r=input("R: ")
        g=input("G: ")
        b=input("B: ")
        self.color= (int(r),int(g),int(b))
        #curses.initscr()
        curses.setupterm()
        

    def save_image(self, filename=None):
        curses.endwin()  # End curses mode to allow normal input
        if filename is None:
            filename = input("Enter filename (default 'out.png'): ").strip()
            if not filename:
                filename = "out.png"
            if not filename.endswith('.png'):
                filename += '.png'
            # Replace spaces with underscores and convert to lowercase
            filename = filename.replace(' ', '_').lower()
            #curses.setupterm()  # Restart curses mode
            confirm="y"
        else: 
            confirm = input("Save changes to "+str(filename)+"? (y/N): ").strip()            

        if confirm.lower() == "y":
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



def handle_input(key, drawing):
    if key == ord('q'):
        return False  # Quit on 'q'
    elif key == ord('e'):  # 'e' to save and quit
        drawing.save_image(filename=drawing.filename)  # Save with default or user-provided filename
        return False
    elif key == ord('r'):  # 'e' to save and quit
        drawing.reset_image()  # Reset canvas
    elif key == curses.KEY_UP or key == ord('w'):
        drawing.move_cursor('UP')
    elif key == curses.KEY_DOWN or key == ord('s'):
        drawing.move_cursor('DOWN')
    elif key == curses.KEY_LEFT or key == ord('a'):
        drawing.move_cursor('LEFT')
    elif key == curses.KEY_RIGHT or key == ord('d'):
        drawing.move_cursor('RIGHT')
    elif key in map(ord, '0123456789'):
        drawing.set_color(chr(key))
    elif key == ord(' '):
        drawing.pen_down = not drawing.pen_down
        #drawing.draw_pixel()
    elif key == ord('b'):  # Bucket fill
        drawing.bucket_fill(drawing.cursor_x, drawing.cursor_y, drawing.color)
    elif key == ord('h'):
        drawing.toggle_horizontal_mirroring()
    elif key == ord('v'):
        drawing.toggle_vertical_mirroring()
    elif key == ord('l'):
        drawing.color_wheel()
    elif key == ord('-'):  # Decrease brightness
        r, g, b = drawing.color
        drawing.color = (
            max(0, r - 25),
            max(0, g - 25),
            max(0, b - 25)
        )
        
    elif key == ord('+'):  # Increase brightness
        r, g, b = drawing.color
        drawing.color = (
            min(255, r + 25),
            min(255, g + 25),
            min(255, b + 25)
        )    
        
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
    drawing = Drawing(stdscr, filename=filename, width=canvas_width)
    drawing.update_cursor()  # Initial cursor update

    while True:
        stdscr.refresh()
        key = stdscr.getch()
        if not handle_input(key, drawing):
            break


parser = argparse.ArgumentParser(description='CLI drawing program.')
parser.add_argument('-W','--width', type=int, default=64, help='Width of the image.')
parser.add_argument('-H','--height', type=int, default=64, help='Height of the image.')
parser.add_argument('-F','--file', type=str, help='File to load.')
args = parser.parse_args()


curses.wrapper(main)


