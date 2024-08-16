import curses

class ColorPicker:
    def __init__(self):
        self.stdscr = None
        self.colors = []
        self.cursor_x = 0
        self.cursor_y = 0

    def init_curses(self):
        self.stdscr = curses.initscr()
        curses.start_color()
        curses.curs_set(0)
        curses.use_default_colors()
        self.create_color_pairs()
        self.calculate_grid_size()

    def create_color_pairs(self):
        """Initialize all color pairs supported by curses."""
        color_id = 1
        for r in range(0, 1000, 500):
            for g in range(0, 1000, 500):
                for b in range(0, 1000, 500):
                    if color_id <= curses.COLOR_PAIRS - 1:
                        curses.init_color(color_id, r, g, b)
                        curses.init_pair(color_id, color_id, -1)
                        self.colors.append((r, g, b, color_id))
                        color_id += 1

    def calculate_grid_size(self):
        """Calculate grid size based on the number of color pairs."""
        self.grid_width = max(1, len(self.colors) // 2)
        self.grid_height = max(1, len(self.colors) // self.grid_width)

    def wrap_cursor(self):
        """Wrap cursor around the grid edges."""
        self.cursor_x %= self.grid_width
        self.cursor_y %= self.grid_height

    def draw_viewport(self):
        """Draw the current 16x16 viewport based on cursor position."""
        h, w = 16, 16  # Fixed viewport size of 16x16
        half_h, half_w = h // 2, w // 2
        for i in range(h):
            for j in range(w):
                grid_x = (self.cursor_x - half_w + j) % self.grid_width
                grid_y = (self.cursor_y - half_h + i) % self.grid_height
                _, _, _, color_id = self.colors[grid_y * self.grid_width + grid_x]
                self.stdscr.addstr(i, j * 2, "██" if (i, j) == (half_h, half_w) else "  ", curses.color_pair(color_id))
        self.stdscr.refresh()

    def fill_screen_with_color(self, color_id):
        """Fill the entire screen with the selected color."""
        h, w = self.stdscr.getmaxyx()
        for i in range(h):
            for j in range(w // 2):
                self.stdscr.addstr(i, j * 2, "██", curses.color_pair(color_id))
        self.stdscr.refresh()
        self.stdscr.getch()

    def run(self):
        """Main loop to handle user input and draw the color grid."""
        self.init_curses()
        try:
            while True:
                self.stdscr.clear()
                self.wrap_cursor()
                self.draw_viewport()

                key = self.stdscr.getch()
                if key in (ord('q'), ord('Q')):
                    break
                elif key in (curses.KEY_UP, ord('w'), ord('W')):
                    self.cursor_y -= 1
                elif key in (curses.KEY_DOWN, ord('s'), ord('S')):
                    self.cursor_y += 1
                elif key in (curses.KEY_LEFT, ord('a'), ord('A')):
                    self.cursor_x -= 1
                elif key in (curses.KEY_RIGHT, ord('d'), ord('D')):
                    self.cursor_x += 1
                elif key == curses.KEY_ENTER or key in [10, 13]:
                    _, _, _, color_id = self.colors[self.cursor_y * self.grid_width + self.cursor_x]
                    self.fill_screen_with_color(color_id)
        finally:
            curses.endwin()

if __name__ == "__main__":
    ColorPicker().run()
