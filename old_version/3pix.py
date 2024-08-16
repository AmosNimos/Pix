import signal
import argparse
import curses
import os
from PIL import Image
from random import randint

class Drawing:
    def __init__(self, stdscr, width=64, height=64, view_size=64, filename=None, background=-1):
        self.pen_down = False
        self.color_id = 1
        self.color = (255, 255, 255)  # Default color white
        self.rect_pen = False
        self.tool_id = 0
        self.x1 = self.x2 = self.y1 = self.y2 = -1
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
        self.mirror_h = self.mirror_v = False
        self.undo_stack = []
        self.redo_stack = []
        self.screenshots = []
        self.current_state = self.take_screenshot()
        self.colors = [(i, i, i) for i in range(256)]  # Simple grayscale palette for example

    def init_color(self):
        curses.start_color()        
        for i in range(256):
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
        colors_count = len(self.colors)
        if self.color_id < colors_count:
            self.color = self.colors[self.color_id]
            self.color_id += 1
        else:
            self.color_id = 1
            self.color = self.colors[self.color_id]

    def decrease_color(self):
        colors_count = len(self.colors)
        if self.color_id > 1:
            self.color_id -= 1
            self.color = self.colors[self.color_id - 1]
        else:
            self.color_id = colors_count
            self.color = self.colors[self.color_id - 1]

    def draw_pixel(self):
        self.image.putpixel((self.cursor_x, self.cursor_y), self.color)
        if self.mirror_h:
            self.image.putpixel((self.width - 1 - self.cursor_x, self.cursor_y), self.color)
        if self.mirror_v:
            self.image.putpixel((self.cursor_x, self.height - 1 - self.cursor_y), self.color)
        if self.mirror_h and self.mirror_v:
            self.image.putpixel((self.width - 1 - self.cursor_x, self.height - 1 - self.cursor_y), self.color)

    def set_pixel(self, x, y, color=None):
        color = color or self.color
        self.image.putpixel((x, y), color)
        if self.mirror_h:
            self.image.putpixel((self.width - 1 - x, y), color)
        if self.mirror_v:
            self.image.putpixel((x, self.height - 1 - y), color)
        if self.mirror_h and self.mirror_v:
            self.image.putpixel((self.width - 1 - x, self.height - 1 - y), color)

    def draw_rect(self):
        if self.rect_pen:
            self.x2 = self.cursor_x
            self.y2 = self.cursor_y

            if self.x1 > self.x2:
                self.x1, self.x2 = self.x2, self.x1
            if self.y1 > self.y2:
                self.y1, self.y2 = self.y2, self.y1

            self.x2 += 1
            self.y2 += 1
            for x in range(self.x1, self.x2):
                for y in range(self.y1, self.y2):
                    self.set_pixel(x, y)
                    
            self.rect_pen = False
            self.x1 = self.x2 = self.y1 = self.y2 = -1
        else:
            self.x1 = self.cursor_x
            self.y1 = self.cursor_y
            self.rect_pen = True

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
            stack.extend([(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)])

    def update_cursor(self):
        self.stdscr.clear()
        self.display_view()
        cursor_char = '•' if self.pen_down else '◘'
        self.stdscr.addch(self.view_size // 2, self.view_size // 2, cursor_char, curses.color_pair(self.color_id) | curses.A_REVERSE)
        self.stdscr.move(self.view_size // 2, self.view_size // 2)
        self.stdscr.refresh()

    def display_view(self):
        self.stdscr.clear()
        start_x = max(0, self.cursor_x - self.view_size // 2)
        start_y = max(0, self.cursor_y - self.view_size // 2)
        end_x = min(self.width, start_x + self.view_size)
        end_y = min(self.height, start_y + self.view_size)

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                display_x = x - start_x
                display_y = y - start_y
                color = self.image.getpixel((x, y))
                color_id = self.get_closest_color_id(color)
                if 0 <= display_x < self.view_size and 0 <= display_y < self.view_size:
                    self.stdscr.addch(display_y, display_x, ' ', curses.color_pair(color_id))
        
        self.stdscr.refresh()

    def get_closest_color_id(self, color):
        closest_id = 0
        min_dist = float('inf')
        for i, c in enumerate(self.colors):
            dist = sum((color[j] - c[j]) ** 2 for j in range(3))
            if dist < min_dist:
                min_dist = dist
                closest_id = i
        return closest_id + 1

    def take_screenshot(self):
        self.screenshots.append(self.image.copy())
        return self.image.copy()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.take_screenshot())
            self.image = self.undo_stack.pop()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.take_screenshot())
            self.image = self.redo_stack.pop()

    def save_image(self):
        if self.filename:
            self.image.save(self.filename)
        else:
            print("No filename specified.")

def main(stdscr):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    curses.curs_set(0)
    curses.start_color()
    
    # Initialize color pairs
    drawing = Drawing(stdscr)
    drawing.init_color()
    
    # Main loop
    while True:
        drawing.update_cursor()
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key == curses.KEY_UP:
            drawing.move_cursor('UP')
        elif key == curses.KEY_DOWN:
            drawing.move_cursor('DOWN')
        elif key == curses.KEY_LEFT:
            drawing.move_cursor('LEFT')
        elif key == curses.KEY_RIGHT:
            drawing.move_cursor('RIGHT')
        elif key == ord('p'):
            drawing.pen_down = not drawing.pen_down
        elif key == ord('c'):
            drawing.set_color(randint(0, len(drawing.colors) - 1))
        elif key == ord('r'):
            drawing.draw_rect()
        elif key == ord('b'):
            drawing.bucket_fill(drawing.cursor_x, drawing.cursor_y, drawing.color)
        elif key == ord('u'):
            drawing.undo()
        elif key == ord('o'):
            drawing.redo()
        elif key == ord('s'):
            drawing.save_image()

if __name__ == '__main__':
    curses.wrapper(main)
