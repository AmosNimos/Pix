# Pixel-art Independent of X11 or P.I.X for short

# The - and = key allow to move up and down the palette the palette as a default hard coded, 0 to 9 to select specefic color index from the palet, you could have a color selection screen for the palet, the palet can be altered using shift + palette index as number key to add the current color to that index, palet can be saved, pallet can be loaded

#########################################
# TODO:                                 #
#########################################
#                                       #
# - Option to enter hex as color        #
# - Full 256 color preview in cli       #
# - Grid colorwheel color picker        #
# - Save as ascii                       #
# - Save as colored ascii-escape code   #
# - Line Pen                            #
# - Select copy and paste               #
# - Accurate warp boundary colors arrow #
# - Image filter                        #
# - Animation frame                     #
# - Layer guides and decals             #
#                                       #
#########################################

# Done
# x added hex value input
# x added more color support

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
            curses.init_pair(i, i, -1)

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
        #print(f"Selected color: {self.color}")

class Drawing:
    def __init__(self, stdscr, width=64, height=64, view_size=64, filename=None, background=-1):
        self.stdscr = stdscr
        # for line pen:
        self.rect_pen=False
        self.x1=-1
        self.x2=-1
        self.y1=-1
        self.y2=-1     
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

        #215 colors
        self.colors = {'0': (0, 0, 0), '1': (255, 255, 255), '2': (0, 0, 96), '3': (0, 0, 144), '4': (0, 0, 192), '5': (0, 0, 240), '6': (0, 48, 0), '7': (0, 48, 48), '8': (0, 48, 96), '9': (0, 48, 144), '10': (0, 48, 192), '11': (0, 48, 240), '12': (0, 96, 0), '13': (0, 96, 48), '14': (0, 96, 96), '15': (0, 96, 144), '16': (0, 96, 192), '17': (0, 96, 240), '18': (0, 144, 0), '19': (0, 144, 48), '20': (0, 144, 96), '21': (0, 144, 144), '22': (0, 144, 192), '23': (0, 144, 240), '24': (0, 192, 0), '25': (0, 192, 48), '26': (0, 192, 96), '27': (0, 192, 144), '28': (0, 192, 192), '29': (0, 192, 240), '30': (0, 240, 0), '31': (0, 240, 48), '32': (0, 240, 96), '33': (0, 240, 144), '34': (0, 240, 192), '35': (0, 240, 240), '36': (48, 0, 0), '37': (48, 0, 48), '38': (48, 0, 96), '39': (48, 0, 144), '40': (48, 0, 192), '41': (48, 0, 240), '42': (48, 48, 0), '43': (48, 48, 48), '44': (48, 48, 96), '45': (48, 48, 144), '46': (48, 48, 192), '47': (48, 48, 240), '48': (48, 96, 0), '49': (48, 96, 48), '50': (48, 96, 96), '51': (48, 96, 144), '52': (48, 96, 192), '53': (48, 96, 240), '54': (48, 144, 0), '55': (48, 144, 48), '56': (48, 144, 96), '57': (48, 144, 144), '58': (48, 144, 192), '59': (48, 144, 240), '60': (48, 192, 0), '61': (48, 192, 48), '62': (48, 192, 96), '63': (48, 192, 144), '64': (48, 192, 192), '65': (48, 192, 240), '66': (48, 240, 0), '67': (48, 240, 48), '68': (48, 240, 96), '69': (48, 240, 144), '70': (48, 240, 192), '71': (48, 240, 240), '72': (96, 0, 0), '73': (96, 0, 48), '74': (96, 0, 96), '75': (96, 0, 144), '76': (96, 0, 192), '77': (96, 0, 240), '78': (96, 48, 0), '79': (96, 48, 48), '80': (96, 48, 96), '81': (96, 48, 144), '82': (96, 48, 192), '83': (96, 48, 240), '84': (96, 96, 0), '85': (96, 96, 48), '86': (96, 96, 96), '87': (96, 96, 144), '88': (96, 96, 192), '89': (96, 96, 240), '90': (96, 144, 0), '91': (96, 144, 48), '92': (96, 144, 96), '93': (96, 144, 144), '94': (96, 144, 192), '95': (96, 144, 240), '96': (96, 192, 0), '97': (96, 192, 48), '98': (96, 192, 96), '99': (96, 192, 144), '100': (96, 192, 192), '101': (96, 192, 240), '102': (96, 240, 0), '103': (96, 240, 48), '104': (96, 240, 96), '105': (96, 240, 144), '106': (96, 240, 192), '107': (96, 240, 240), '108': (144, 0, 0), '109': (144, 0, 48), '110': (144, 0, 96), '111': (144, 0, 144), '112': (144, 0, 192), '113': (144, 0, 240), '114': (144, 48, 0), '115': (144, 48, 48), '116': (144, 48, 96), '117': (144, 48, 144), '118': (144, 48, 192), '119': (144, 48, 240), '120': (144, 96, 0), '121': (144, 96, 48), '122': (144, 96, 96), '123': (144, 96, 144), '124': (144, 96, 192), '125': (144, 96, 240), '126': (144, 144, 0), '127': (144, 144, 48), '128': (144, 144, 96), '129': (144, 144, 144), '130': (144, 144, 192), '131': (144, 144, 240), '132': (144, 192, 0), '133': (144, 192, 48), '134': (144, 192, 96), '135': (144, 192, 144), '136': (144, 192, 192), '137': (144, 192, 240), '138': (144, 240, 0), '139': (144, 240, 48), '140': (144, 240, 96), '141': (144, 240, 144), '142': (144, 240, 192), '143': (144, 240, 240), '144': (192, 0, 0), '145': (192, 0, 48), '146': (192, 0, 96), '147': (192, 0, 144), '148': (192, 0, 192), '149': (192, 0, 240), '150': (192, 48, 0), '151': (192, 48, 48), '152': (192, 48, 96), '153': (192, 48, 144), '154': (192, 48, 192), '155': (192, 48, 240), '156': (192, 96, 0), '157': (192, 96, 48), '158': (192, 96, 96), '159': (192, 96, 144), '160': (192, 96, 192), '161': (192, 96, 240), '162': (192, 144, 0), '163': (192, 144, 48), '164': (192, 144, 96), '165': (192, 144, 144), '166': (192, 144, 192), '167': (192, 144, 240), '168': (192, 192, 0), '169': (192, 192, 48), '170': (192, 192, 96), '171': (192, 192, 144), '172': (192, 192, 192), '173': (192, 192, 240), '174': (192, 240, 0), '175': (192, 240, 48), '176': (192, 240, 96), '177': (192, 240, 144), '178': (192, 240, 192), '179': (192, 240, 240), '180': (240, 0, 0), '181': (240, 0, 48), '182': (240, 0, 96), '183': (240, 0, 144), '184': (240, 0, 192), '185': (240, 0, 240), '186': (240, 48, 0), '187': (240, 48, 48), '188': (240, 48, 96), '189': (240, 48, 144), '190': (240, 48, 192), '191': (240, 48, 240), '192': (240, 96, 0), '193': (240, 96, 48), '194': (240, 96, 96), '195': (240, 96, 144), '196': (240, 96, 192), '197': (240, 96, 240), '198': (240, 144, 0), '199': (240, 144, 48), '200': (240, 144, 96), '201': (240, 144, 144), '202': (240, 144, 192), '203': (240, 144, 240), '204': (240, 192, 0), '205': (240, 192, 48), '206': (240, 192, 96), '207': (240, 192, 144), '208': (240, 192, 192), '209': (240, 192, 240), '210': (240, 240, 0), '211': (240, 240, 48), '212': (240, 240, 96), '213': (240, 240, 144), '214': (240, 240, 192), '215': (192, 224, 180),
        '216': (36, 240, 168),
        '217': (71, 55, 40),
        '218': (7, 244, 70),
        '219': (230, 130, 107),
        '220': (125, 187, 239),
        '221': (4, 143, 228),
        '222': (63, 149, 127),
        '223': (242, 23, 25),
        '224': (201, 72, 88),
        '225': (176, 18, 126),
        '226': (186, 50, 121),
        '227': (179, 52, 210),
        '228': (22, 29, 217),
        '229': (150, 110, 196),
        '230': (118, 178, 147),
        '231': (40, 97, 78),
        '232': (120, 160, 35),
        '233': (102, 9, 157),
        '234': (111, 34, 42),
        '235': (121, 24, 186),
        '236': (115, 184, 82),
        '237': (136, 252, 229),
        '238': (90, 123, 14),
        '239': (220, 68, 135),
        '240': (98, 237, 174),
        '241': (36, 100, 36),
        '242': (233, 2, 54),
        '243': (143, 215, 159),
        '244': (0, 0, 48)
        }
        
        #254
        # NOTE: Ideally I would like for that dictionary to be procedurally generated instead of hard coded and work up to 256 colors.
        #self.colors = {'0': (0, 0, 0), '1': (0, 0, 32), '2': (0, 0, 64), '3': (0, 0, 96), '4': (0, 0, 128), '5': (0, 0, 160), '6': (0, 0, 192), '7': (0, 0, 224), '8': (0, 32, 0), '9': (0, 32, 32), '10': (0, 32, 64), '11': (0, 32, 96), '12': (0, 32, 128), '13': (0, 32, 160), '14': (0, 32, 192), '15': (0, 32, 224), '16': (0, 64, 0), '17': (0, 64, 32), '18': (0, 64, 64), '19': (0, 64, 96), '20': (0, 64, 128), '21': (0, 64, 160), '22': (0, 64, 192), '23': (0, 64, 224), '24': (0, 96, 0), '25': (0, 96, 32), '26': (0, 96, 64), '27': (0, 96, 96), '28': (0, 96, 128), '29': (0, 96, 160), '30': (0, 96, 192), '31': (0, 96, 224), '32': (0, 128, 0), '33': (0, 128, 32), '34': (0, 128, 64), '35': (0, 128, 96), '36': (0, 128, 128), '37': (0, 128, 160), '38': (0, 128, 192), '39': (0, 128, 224), '40': (0, 160, 0), '41': (0, 160, 32), '42': (0, 160, 64), '43': (0, 160, 96), '44': (0, 160, 128), '45': (0, 160, 160), '46': (0, 160, 192), '47': (0, 160, 224), '48': (0, 192, 0), '49': (0, 192, 32), '50': (0, 192, 64), '51': (0, 192, 96), '52': (0, 192, 128), '53': (0, 192, 160), '54': (0, 192, 192), '55': (0, 192, 224), '56': (0, 224, 0), '57': (0, 224, 32), '58': (0, 224, 64), '59': (0, 224, 96), '60': (0, 224, 128), '61': (0, 224, 160), '62': (0, 224, 192), '63': (0, 224, 224), '64': (32, 0, 0), '65': (32, 0, 32), '66': (32, 0, 64), '67': (32, 0, 96), '68': (32, 0, 128), '69': (32, 0, 160), '70': (32, 0, 192), '71': (32, 0, 224), '72': (32, 32, 0), '73': (32, 32, 32), '74': (32, 32, 64), '75': (32, 32, 96), '76': (32, 32, 128), '77': (32, 32, 160), '78': (32, 32, 192), '79': (32, 32, 224), '80': (32, 64, 0), '81': (32, 64, 32), '82': (32, 64, 64), '83': (32, 64, 96), '84': (32, 64, 128), '85': (32, 64, 160), '86': (32, 64, 192), '87': (32, 64, 224), '88': (32, 96, 0), '89': (32, 96, 32), '90': (32, 96, 64), '91': (32, 96, 96), '92': (32, 96, 128), '93': (32, 96, 160), '94': (32, 96, 192), '95': (32, 96, 224), '96': (32, 128, 0), '97': (32, 128, 32), '98': (32, 128, 64), '99': (32, 128, 96), '100': (32, 128, 128), '101': (32, 128, 160), '102': (32, 128, 192), '103': (32, 128, 224), '104': (32, 160, 0), '105': (32, 160, 32), '106': (32, 160, 64), '107': (32, 160, 96), '108': (32, 160, 128), '109': (32, 160, 160), '110': (32, 160, 192), '111': (32, 160, 224), '112': (32, 192, 0), '113': (32, 192, 32), '114': (32, 192, 64), '115': (32, 192, 96), '116': (32, 192, 128), '117': (32, 192, 160), '118': (32, 192, 192), '119': (32, 192, 224), '120': (32, 224, 0), '121': (32, 224, 32), '122': (32, 224, 64), '123': (32, 224, 96), '124': (32, 224, 128), '125': (32, 224, 160), '126': (32, 224, 192), '127': (32, 224, 224), '128': (64, 0, 0), '129': (64, 0, 32), '130': (64, 0, 64), '131': (64, 0, 96), '132': (64, 0, 128), '133': (64, 0, 160), '134': (64, 0, 192), '135': (64, 0, 224), '136': (64, 32, 0), '137': (64, 32, 32), '138': (64, 32, 64), '139': (64, 32, 96), '140': (64, 32, 128), '141': (64, 32, 160), '142': (64, 32, 192), '143': (64, 32, 224), '144': (64, 64, 0), '145': (64, 64, 32), '146': (64, 64, 64), '147': (64, 64, 96), '148': (64, 64, 128), '149': (64, 64, 160), '150': (64, 64, 192), '151': (64, 64, 224), '152': (64, 96, 0), '153': (64, 96, 32), '154': (64, 96, 64), '155': (64, 96, 96), '156': (64, 96, 128), '157': (64, 96, 160), '158': (64, 96, 192), '159': (64, 96, 224), '160': (64, 128, 0), '161': (64, 128, 32), '162': (64, 128, 64), '163': (64, 128, 96), '164': (64, 128, 128), '165': (64, 128, 160), '166': (64, 128, 192), '167': (64, 128, 224), '168': (64, 160, 0), '169': (64, 160, 32), '170': (64, 160, 64), '171': (64, 160, 96), '172': (64, 160, 128), '173': (64, 160, 160), '174': (64, 160, 192), '175': (64, 160, 224), '176': (64, 192, 0), '177': (64, 192, 32), '178': (64, 192, 64), '179': (64, 192, 96), '180': (64, 192, 128), '181': (64, 192, 160), '182': (64, 192, 192), '183': (64, 192, 224), '184': (64, 224, 0), '185': (64, 224, 32), '186': (64, 224, 64), '187': (64, 224, 96), '188': (64, 224, 128), '189': (64, 224, 160), '190': (64, 224, 192), '191': (64, 224, 224), '192': (96, 0, 0), '193': (96, 0, 32), '194': (96, 0, 64), '195': (96, 0, 96), '196': (96, 0, 128), '197': (96, 0, 160), '198': (96, 0, 192), '199': (96, 0, 224), '200': (96, 32, 0), '201': (96, 32, 32), '202': (96, 32, 64), '203': (96, 32, 96), '204': (96, 32, 128), '205': (96, 32, 160), '206': (96, 32, 192), '207': (96, 32, 224), '208': (96, 64, 0), '209': (96, 64, 32), '210': (96, 64, 64), '211': (96, 64, 96), '212': (96, 64, 128), '213': (96, 64, 160), '214': (96, 64, 192), '215': (96, 64, 224), '216': (96, 96, 0), '217': (96, 96, 32), '218': (96, 96, 64), '219': (96, 96, 96), '220': (96, 96, 128), '221': (96, 96, 160), '222': (96, 96, 192), '223': (96, 96, 224), '224': (96, 128, 0), '225': (96, 128, 32), '226': (96, 128, 64), '227': (96, 128, 96), '228': (96, 128, 128), '229': (96, 128, 160), '230': (96, 128, 192), '231': (96, 128, 224), '232': (96, 160, 0), '233': (96, 160, 32), '234': (96, 160, 64), '235': (96, 160, 96), '236': (96, 160, 128), '237': (96, 160, 160), '238': (96, 160, 192), '239': (96, 160, 224), '240': (96, 192, 0), '241': (96, 192, 32), '242': (96, 192, 64), '243': (96, 192, 96), '244': (96, 192, 128), '245': (96, 192, 160), '246': (96, 192, 192), '247': (96, 192, 224), '248': (96, 224, 0), '249': (96, 224, 32), '250': (96, 224, 64), '251': (96, 224, 96), '252': (96, 224, 128), '253': (240, 240, 192), '254': (255, 255, 255)}

        # The default color palette
        self.palette = {
            '245': (255, 5, 5),        # Off-black with a hint of blue
            '246': (5, 255, 5),     # Rich red
            '247': (5, 5, 255),    # Warm orange
            '248': (255, 255, 18),    # Soft yellow
            '249': (18, 252, 80),     # Vibrant green
            '250': (10, 10, 240),     # Deep blue
            '251': (238, 15, 244),    # Bright magenta
            '252': (130, 130, 130),   # Neutral gray
        }

        start_index = len(self.colors)
        self.colors.update({str(start_index + i): v for i, v in enumerate(self.palette.values())})        

        #self.colors["0"]=(0, 0, 0)
        #self.colors["1"]=(255,255,255)
        self.color_pairs = {}
        self.initialize_colors()
        self.pen_down = False  # Initialize pen state
        self.set_color(str(len(self.colors)-1))

        if filename:
            self.load_image(filename)


    def read_hex_colors_from_file(file_path):
      """Reads hex colors from a file and creates a dictionary of RGB values.

      Args:
        file_path: The path to the .hex file.

      Returns:
        A dictionary where keys are string integers and values are RGB tuples.
      """
      color_dict = {}
      with open(file_path, 'r') as f:
        for i, hex_color in enumerate(f):
          rgb_color = tuple(int(hex_color.strip()[j:j+2], 16) for j in (0, 2, 4))
          color_dict[str(i)] = rgb_color
      return color_dict

    def initialize_colors(self):
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
        self.color = self.colors[str(int(color_key))]
        self.color_pair = self.color_pairs[str(int(color_key))]

    def set_palette(self, color_key):
        if (int(color_key) <= 1):
            self.color = self.colors[str(int(color_key))]
            self.color_pair = self.color_pairs[str(int(color_key))]
        else :
            index=int(len(self.colors)-10)+int(color_key)
            self.color = self.colors[str(index)]
            self.color_pair = self.color_pairs[str(index)]
        

    def increase_color(self):
        colors_count=int(len(self.colors))
        if self.color_pair < colors_count:
            self.color = self.colors[str(self.color_pair)]
            self.color_pair+=1
        else:
            self.color_pair=1
            self.color = self.colors[str(self.color_pair)]
            
    def decrease_color(self):
        colors_count=int(len(self.colors))
        if self.color_pair > 1:
            self.color_pair-=1
            self.color = self.colors[str(self.color_pair-1)]
        else:
            self.color_pair=colors_count
            #self.color = self.colors[str(self.color_pair+1)]
        #self.color_pair = self.color_pairs[self.color_pair]

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
        # ◯
        if (self.pen_down):
            self.stdscr.addch(self.view_size // 2, self.view_size // 2, '•', curses.color_pair(self.color_pair) | curses.A_REVERSE)
        else:
            self.stdscr.addch(self.view_size // 2, self.view_size // 2, '◘', curses.color_pair(self.color_pair) | curses.A_REVERSE)
        self.stdscr.move(self.view_size // 2, self.view_size // 2)

    def display_view(self):
        # Example setup
        start_x = self.cursor_x - self.view_size // 2
        start_y = self.cursor_y - self.view_size // 2
        for y in range(-1,self.view_size):
            for x in range(-1,self.view_size):
                img_x = start_x + x
                img_y = start_y + y
                char=" "


                # check if within the image canvas
                if 0 <= img_x < self.width and 0 <= img_y < self.height:
                    # get the rgb value for the current selected pixel
                    r, g, b = self.image.getpixel((img_x, img_y))
                    rgb_color = (r,g,b)

                    # set the color id to black if blank
                    if (r + g + b == 0):
                        color_id = -1
                    else:
                        color_id = self.get_closest_color_id(r, g, b)

                    # Assigning the char
                    if img_y == 0 or img_y == self.height-1 or img_x == 0 or img_x == self.width-1:
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
                            color_id = -1
                        #else:
                            #color_id = self.get_closest_color_id(r, g, b)
                    else:
                        char = '█'
                        color_id = self.get_closest_color_id(r, g, b)
                        if self.rect_pen: 
                            if img_x >= self.x1 and img_y >= self.y1 and img_x <= self.cursor_x and img_y <= self.cursor_y or img_x <= self.x1 and img_y <= self.y1 and img_x >= self.cursor_x and img_y >= self.cursor_y or img_x >= self.x1 and img_y <= self.y1 and img_x <= self.cursor_x and img_y >= self.cursor_y or img_x <= self.x1 and img_y >= self.y1 and img_x >= self.cursor_x and img_y <= self.cursor_y:
                                char = 'x'
                                color_id=self.color_pair
                elif img_x > 0 and img_x < self.width:
                        color_id=-1
                        if (img_y == -1):
                            r, g, b = self.image.getpixel((img_x, self.height-1))
                            #color_id = self.get_closest_color_id(r, g, b)
                            char = '▲'
                        elif (img_y == self.height):
                            r, g, b = self.image.getpixel((img_x, 0))
                            #color_id = self.get_closest_color_id(r, g, b)
                            char = '▼'
                        else:
                            char = ' '
                elif img_y > 0 and img_y < self.height:
                        color_id=-1
                        if (img_x == -1):
                            r, g, b = self.image.getpixel((self.width-1, img_y))
                            #color_id = self.get_closest_color_id(r, g, b)
                            char = '◀'
                        elif (img_x == self.width):
                            r, g, b = self.image.getpixel((0, img_y))
                            #color_id = self.get_closest_color_id(r, g, b)
                            char = '▶'
                        else:
                            char = ' '
                else:
                    char = ' '
                    color_id = -1

                try:
                    if color_id != -1:
                        # Color character only
                        self.stdscr.addch(y, x, char, curses.color_pair(color_id))
                        #else:
                        #    self.stdscr.addch(y, x, "z", curses.color_pair(12))
                    else:
                        # Default color
                        self.stdscr.addch(y, x, char)
                except curses.error:
                    pass

                # Draw pallet bar
                for i in range(9):

                    if (i > 1):
                        index=int(len(self.colors)-9+i) # index in the color palette
                    else:
                        index=i

                    # This is for the last color of the palette
                    if self.color_pair==index:
                        char="X"
                    else:
                        char="█"
                    
                    self.stdscr.addch(5+i, 5, char, curses.color_pair(index))
                    self.stdscr.addstr(5+i, 7, str(self.colors[str(index)])+", "+str(index)+", "+str(i+1), curses.color_pair(0))

                # default black and white
                #self.stdscr.addch(5, 5, char, curses.color_pair(0))
                #self.stdscr.addch(13, 5, char, curses.color_pair(1))
                # Use addstr to add a string at position (5, 5)
                self.stdscr.addstr(20, 7, str(self.color), curses.color_pair(0))
                self.stdscr.addstr(22, 7, str(self.color_pair), curses.color_pair(0))
                

#    def get_closest_color_id(self, r, g, b):
#        dif=0
#        for key, color in self.colors.items():
#            # this is a very dumb way of getting the dif value
#            if color[0]>r:
#                new_dif=color[0]-r
#            else:
#                new_dif=r-color[0]
#            if color[1]>g:
#                new_dif=color[1]-g
#            else:
#                new_dif=g-color[1]
#            if color[2]>b:
#                new_dif=color[2]-b
#            else:
#                new_dif=b-color[2]
#
#            #if color == (r, g, b):
#            if new_dif<dif or dif==0:
#                closest_color=self.color_pairs[key]
#                dif+new_dif
#        return closest_color

        #return -1

# get exact match
#    def get_closest_color_id(self, r, g, b):
#        return -1


#    actually get the closest even if not exact match
    def get_closest_color_id(self, r, g, b):
        for key, color in self.colors.items():
            if color == (r, g, b):
                return self.color_pairs[key]

        closest_key = None
        min_distance = float('inf')

        for key, color in self.colors.items():
            # Calculate the Euclidean distance between the colors
            distance = math.sqrt((color[0] - r) ** 2 + (color[1] - g) ** 2 + (color[2] - b) ** 2)
            
            if distance < min_distance:
                min_distance = distance
                closest_key = key

        # Return the closest color pair if found, otherwise return -1
        return self.color_pairs[closest_key] if closest_key is not None else -1

    def load_image(self, filename):
        with Image.open(filename) as img:
            self.image = img.convert('RGB')
            self.width, self.height = self.image.size
            self.cursor_x = self.width // 2
            self.cursor_y = self.height // 2


#    def hex_prompt(self):
#        curses.endwin()  # End curses mode to allow normal input
#        # Could be a single input taking hex value instead
#        r=input("R: ")
#        g=input("G: ")
#        b=input("B: ")
#        self.color= (int(r),int(g),int(b))
#        #curses.initscr()
#        color_id=self.get_closest_color_id(int(r),int(g),int(b))
#        
#        #self.set_color(color_id)
#        curses.setupterm()


    def hex_prompt(self):
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
        if (color_id>1):
            color_id-=1
        self.color_pair = self.color_pairs[str(int(color_id))]

        curses.setupterm()
        

#    def hex_prompt(self):
#        # Exit curses mode to allow normal input
#        curses.endwin()
#        
#        # Prompt the user for RGB values
#        r = input("Enter Red value (0-255): ")
#        g = input("Enter Green value (0-255): ")
#        b = input("Enter Blue value (0-255): ")
#        
#        try:
#            r = int(r)
#            g = int(g)
#            b = int(b)
#            
#            if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
#                raise ValueError("RGB values must be between 0 and 255.")
#            
#            # Set the color
#            self.color = (r, g, b)
#            
#            # Re-initialize curses mode
#            curses.initscr()
#            curses.start_color()
#            curses.setupterm()
#
#            # Set the color in curses
#            color_id = 1  # Assuming a fixed color ID for now
#            curses.init_color(color_id, int(r * 1000 / 255), int(g * 1000 / 255), int(b * 1000 / 255))
#            curses.init_pair(color_id, color_id, self.background_color)  # Using the defined background color
#            
#        except ValueError as e:
#            print(f"Invalid input: {e}")
#            self.hex_prompt()  # Retry if invalid input        

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


#    def take_screenshot(self):
#        self.screenshot = self.image.copy()
#
#    def load_screenshot(self):
#        if self.screenshot:
#            self.image = self.screenshot.convert('RGB')

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
        drawing.set_palette(chr(key))
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
