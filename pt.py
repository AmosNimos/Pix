import argparse
import curses
from PIL import Image
import copy

class Drawing:
    def __init__(self, stdscr, width=64, height=64, view_size=64, filename=None, background=-1):
        self.tty_mode = False
        self.background_color = background
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
        self.undo_stack = []
        self.redo_stack = []
        self.max_history_steps = 25  # Limit of 25 steps backward and forward
        self.colors = self.initialize_colors_dict()
        
        self.set_tty_mode()
        self.color_pairs = {}
        self.initialize_colors()
        self.pen_down = False  # Initialize pen state
        self.set_color("1")

        if filename:
            self.load_image(filename)

    def initialize_colors_dict(self):
        colors = {
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
        }
        
        # Add 216 colors in a 6x6x6 color cube
        for i in range(6):
            for j in range(6):
                for k in range(6):
                    index = 16 + (i * 36) + (j * 6) + k
                    r = i * 51
                    g = j * 51
                    b = k * 51
                    colors[str(index)] = (r, g, b)

        # Add 24 grayscale colors
        for i in range(24):
            gray = i * 10 + 8
            index = 232 + i
            colors[str(index)] = (gray, gray, gray)
        
        return colors

    def set_tty_mode(self):
        curses.setupterm()
        colors = curses.tigetnum("colors")
        if colors is not None and colors < 256:
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
            background_color = curses.COLOR_BLACK
            for key, color_code in palette.items():
                curses.init_pair(color_id, color_code, background_color)  # Use black as background
                self.color_pairs[key] = color_id
                color_id += 1
        else:
            curses.start_color()
            curses.use_default_colors()
            color_id = 1
            for i, (r, g, b) in self.colors.items():
                curses.init_color(color_id, int(r * 1000 / 255), int(g * 1000 / 255), int(b * 1000 / 255))
                curses.init_pair(color_id, color_id, self.background_color)  # Use -1 for the background color
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
            self.image.putpixel((self.width - 1 - self.cursor_x, self.cursor_y), self.color)
        if self.mirror_v:
            self.image.putpixel((self.cursor_x, self.height - 1 - self.cursor_y), self.color)
        if self.mirror_h and self.mirror_v:
            self.image.putpixel((self.width - 1 - self.cursor_x, self.height - 1 - self.cursor_y), self.color)

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
        if self.pen_down:
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

                    if img_x < 1 or img_x >= self.width - 1 or img_y < 1 or img_y >= self.height - 1:
                        char = '.'
                    elif (img_x == int(self.width / 2) and self.mirror_h):
                        char = '|'
                    elif (img_y == int(self.height / 2) and self.mirror_v):
                        char = '-'
                        if (r + g + b == 0):
                            color_id = -1
                        else:
                            color_id = self.get_closest_color_id(r, g, b)
                    else:
                        char = '█'
                        color_id = self.get_closest_color_id(r, g, b)
                else:
                    char = ' '
                    color_id = -1

                try:
                    if color_id != -1:
                        self.stdscr.addch(y, x, char, curses.color_pair(color_id))
                    else:
                        self.stdscr.addch(y, x, char)
                except curses.error:
                    pass

    def get_closest_color_id(self, r, g, b):
        closest_color_id = -1
        min_distance = float('inf')
        for key, color in self.colors.items():
            cr, cg, cb = color
            distance = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
            if distance < min_distance:
                min_distance = distance
                closest_color_id = self.color_pairs[key]
        return closest_color_id

    def load_image(self, filename):
        with Image.open(filename) as img:
            img = img.convert('RGB')
            self.image = img.resize((self.width, self.height), Image.NEAREST)

    def save_image(self, filename):
        self.image.save(filename)

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(copy.deepcopy(self.image))
            self.image = self.undo_stack.pop()
            self.update_cursor()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(copy.deepcopy(self.image))
            self.image = self.redo_stack.pop()
            self.update_cursor()

    def save_state(self):
        if len(self.undo_stack) >= self.max_history_steps:
            self.undo_stack.pop(0)
        self.undo_stack.append(copy.deepcopy(self.image))
        self.redo_stack.clear()

    def toggle_pen(self):
        self.pen_down = not self.pen_down
        self.update_cursor()

    def toggle_mirror_h(self):
        self.mirror_h = not self.mirror_h

    def toggle_mirror_v(self):
        self.mirror_v = not self.mirror_v

    def run(self):
        while True:
            self.update_cursor()
            key = self.stdscr.getch()

            if key == ord('q'):
                break
            elif key == ord('w'):
                self.move_cursor('UP')
            elif key == ord('s'):
                self.move_cursor('DOWN')
            elif key == ord('a'):
                self.move_cursor('LEFT')
            elif key == ord('d'):
                self.move_cursor('RIGHT')
            elif key == ord(' '):
                self.save_state()
                if self.pen_down:
                    self.draw_pixel()
                else:
                    self.bucket_fill(self.cursor_x, self.cursor_y, self.color)
                self.update_cursor()
            elif key == ord('c'):
                self.set_color("1")  # Example color change
            elif key == ord('u'):
                self.undo()
                self.update_cursor()
            elif key == ord('r'):
                self.redo()
                self.update_cursor()
            elif key == ord('p'):
                self.toggle_pen()
            elif key == ord('m'):
                self.toggle_mirror_h()
            elif key == ord('n'):
                self.toggle_mirror_v()
            elif key == ord('s'):
                if self.filename:
                    self.save_image(self.filename)
            elif key == ord('l'):
                if self.filename:
                    self.load_image(self.filename)
            elif key == ord('f'):
                self.bucket_fill(self.cursor_x, self.cursor_y, self.color)

def main(stdscr):
    parser = argparse.ArgumentParser(description='Drawing Application')
    parser.add_argument('--file', type=str, help='File to load or save')
    parser.add_argument('--bg', type=int, default=-1, help='Background color')
    args = parser.parse_args()

    drawing = Drawing(stdscr, filename=args.file, background=args.bg)
    drawing.run()

curses.wrapper(main)
