import argparse
import curses
from PIL import Image

class Drawing:
    def __init__(self, stdscr, width=64, height=64, view_size=64, filename=None):
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
        self.brightness = 0  # Start with no brightness adjustment
        self.colors = {
            '0': (255, 255, 255),
            '1': (255, 0, 0),
            '2': (0, 255, 0),
            '3': (0, 0, 255),
            '4': (255, 255, 0),
            '5': (0, 255, 255),
            '6': (255, 0, 255),
            '7': (192, 192, 192),
            '8': (128, 128, 128),
            '9': (0, 0, 0),
        }
        self.color_pairs = {}
        self.initialize_colors()

        if filename:
            self.load_image(filename)

    def initialize_colors(self):
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

    def adjust_brightness(self, color):
        r, g, b = color
        brightness = self.brightness
        r = max(0, min(255, r - brightness))
        g = max(0, min(255, g - brightness))
        b = max(0, min(255, b - brightness))
        return (r, g, b)

    def set_color(self, color_key):
        self.color = self.adjust_brightness(self.colors[color_key])
        #self.color = self.colors[color_key]
        self.color_pair = self.color_pairs[color_key]

    def draw_pixel(self):
        adjusted_color = self.adjust_brightness(self.color)
        self.image.putpixel((self.cursor_x, self.cursor_y), adjusted_color)
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
        self.stdscr.addch(self.view_size // 2, self.view_size // 2, '#', curses.color_pair(self.color_pair) | curses.A_REVERSE)
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
                    if (img_x == int(self.width/2) and self.mirror_h):
                        # Vertical guideline
                        char = '|'
                        if (r + g + b == 0):
                            color_id = -1
                        else:
                            color_id = self.get_closest_color_id(r, g, b)
                    elif (img_y == int(self.height/2) and self.mirror_v):
                        # Horizontal guideline
                        char = '-'
                        if (r + g + b == 0):
                            color_id = -1
                        else:
                            color_id = self.get_closest_color_id(r, g, b)
                    else:
                        char = ' '
                        color_id = self.get_closest_color_id(r, g, b)
                else:
                    char = '.'
                    color_id = -1

                try:
                    if color_id != -1:
                        # Background color
                        self.stdscr.addch(y, x, char, curses.color_pair(color_id) | curses.A_REVERSE)
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
            curses.setupterm()  # Restart curses mode
            confirm="y"
        else: 
            confirm = input("Save changes to "+str(filename)+"? (y/N): ").strip()            

        if confirm.lower() == "y":
            self.image.save(filename)
    
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
        drawing.draw_pixel()
    elif key == ord('b'):  # Bucket fill
        drawing.bucket_fill(drawing.cursor_x, drawing.cursor_y, drawing.color)
    elif key == ord('h'):
        drawing.toggle_horizontal_mirroring()
    elif key == ord('v'):
        drawing.toggle_vertical_mirroring()
    elif key == ord('l'):  # Adjust brightness
        drawing.brightness = (drawing.brightness + 25) % 225
        
    drawing.update_cursor()
    return True

def parse_arguments():
    parser = argparse.ArgumentParser(description="Drawing application.")
    parser.add_argument('-f', '--file', type=str, help="Path to the image file to load.")
    return parser.parse_args()
    
def main(stdscr):
    args = parse_arguments()
    
    filename = args.file if args.file else None

    #curses.curs_set(1)  # Make cursor visible
    stdscr.clear()

    drawing = Drawing(stdscr, filename=filename)
    drawing.update_cursor()  # Initial cursor update

    while True:
        stdscr.refresh()
        key = stdscr.getch()
        if not handle_input(key, drawing):
            break

curses.wrapper(main)


