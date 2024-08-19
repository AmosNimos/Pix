<img src="./pix.png" alt="./PIX">

# PIX - USER MANUAL

### Canvas and Palette Basics:
- **Canvas**: The drawable area where you can place pixels.
- **Palette**: The available colors. You can select a color using the number keys (`0-9`). The palette can be loaded from a file as a list of hex color values.
- **Tools**: Select a tool using the number keys with the `Shift` key (`1-7`).

---

### Palette and Color Management

Your drawing program offers a versatile palette system with the following features:

#### Palette Basics:
- **10 Colors Accessible via Number Keys (`0-9`)**:
  - **0**: Black (Default)
  - **1**: White (Default)
  - **2-9**: Colors from your selected palette.

- **Customizable Palettes**:
  - Up to **8 different color palettes** can be loaded into the program.
  - Each palette is a set of colors defined by hexadecimal values, with one hex color per line in a text file.
  - These palettes can be loaded dynamically to customize the colors available at your fingertips.

#### Extended Colors:
- **Additional Colors**:
  - The program generates several random colors to add variety.
  - When you open an image in the program, it analyzes the most common colors in the image and adds them to the palette. This helps to better represent the image within the program's color limitations.
  
- **Color Limitation**:
  - The program supports a maximum of **128 colors**. This limitation is due to performance considerations, as the display process involves searching the color array for the closest match. Increasing the number of colors would slow down the program significantly.
  - The algorithm used for matching colors is not fully optimized, so this limit ensures smooth performance.

#### Display and GUI:
- **Palette Display**:
  - The 10 default colors of your active palette are displayed on the top left of the screen.
  - The current selected color is highlighted in this palette.
  - You can toggle the visibility of this palette with the **`G` key** to hide or show the GUI.
  
- **Active Tool Display**:
  - The tool you are currently using is also displayed at the top left of the screen.
  - Similar to the palette, the tool display can be toggled on or off with the **`G` key**.

---

### Key Controls:

> (NOTE: These are case sensitive:)

#### Movement:
- **Arrow Keys (`↑`, `↓`, `←`, `→`) or `W`, `A`, `S`, `D`**: Move the cursor on the canvas.

#### Drawing Actions:
- **`Space` or `Enter`**: Start or stop drawing with the selected tool.
- **`D`**: Draw a single pixel using the Dot tool.
- **`b`**: Perform a bucket fill at the current cursor position.
- **`u`**: Undo the last action.
- **`c`**: Copy the color from the pixel at the cursor position.
- **`p`**: Toggle the pen tool. If the pen is currently down, this will lift it off the canvas; otherwise, it will lower the pen for drawing.
- **`h`**: Toggle horizontal mirroring.
- **`v`**: Toggle vertical mirroring.
- **`u`**: undo change.

#### Color Adjustments:
- **Number Keys (`0-9`)**: Select a color from the palette.
- **`=`**: Increase the current color value.
- **`-`**: Decrease the current color value.
- **`H`**: Enter a custom hex value for the current color. (In development)

#### Tool Selection:
- **`Shift` + `1-7`**: Select a tool from the tool list:
  1. **Dot**: Draw a single pixel.
  2. **Pen**: Draw continuously while moving.
  3. **Bucket**: Fill an area with the selected color.
  4. **Line**: Draw a straight line.
  5. **Rectangle**: Draw a rectangle.
  6. **Ellipse**: Draw an ellipse.
  7. **Copy**: Pick the color of the pixel under the cursor.
  
- **`+`**: Cycle forward through the tools.
- **`_`**: Cycle backward through the tools.
  
#### GUI OPTIONS:
- **`g`**: Toggle the info bar on/off.

> (NOTE: There aren’t many GUI options because there isn’t much GUI—this minimalist design keeps you focused solely on the pixels, avoiding the clutter of overly complicated apps with more buttons than a spaceship.)

### Saving and Exiting:

- **`e`**: **Enter Name, Export, and Quit**  
  - Prompts you to enter a file name for the image. After providing a name, the program saves the image and quits. This gives you full control over the file name before exiting.

- **`q`**: **Ask to Save, Enter File Name, and Quit**  
  - When you press `q`, the program asks if you want to save the current image before quitting. If you confirm, it will prompt you to enter a file name, with the default being "pix.save.png". After saving, the program will exit. If you decline, the program will quit without saving.

- **`Shift` + `Q`**: **Save Without Confirmation and Quit**  
  - Immediately saves the current image as "pix.save.png" without asking for confirmation and then quits. This is a quick way to ensure your work is saved under a default name before exiting.

- **`S`**: **Save Without Quitting**  
  - Saves the current image without quitting the program. This allows you to save your progress and continue working without interruption.

> (NOTE: None of these options will promptly quit the program without saving. This is to prevent accidental key presses from causing you to lose your work. PIX also includes built-in autosave features to further ensure your work is protected. This approach is part of PIX's philosophy of "overkill preservation"—we understand that losing something you've poured your heart into is frustrating, so we've taken extra steps to keep your creations safe.)

---

### Arguments:

- **Single Argument**: By default, if you provide a single argument, it will be treated as the filename to load an image.

- **`-f` <filename>**: Specify a file to load an image from. This flag is used to explicitly define the image file to be opened.

- **`-H` <height>**: Set the height of the canvas if starting with a blank image. Must be followed by an integer value.

- **`-W` <width>**: Set the width of the canvas if starting with a blank image. Must be followed by an integer value.

- **`-P` <palette_file>**: Load a custom hex color palette from a file. Defaults to `pix.hex` if no file is specified.


