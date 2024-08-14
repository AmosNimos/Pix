def generate_256_colors():
    colors = {}
    color_id = 0
    
    # Generate colors by varying the hue across the RGB spectrum
    for r in range(0, 256, 32):
        for g in range(0, 256, 32):
            for b in range(0, 256, 32):
                if color_id >= 256:
                    break
                colors[str(color_id)] = (r, g, b)
                color_id += 1
            if color_id >= 256:
                break
        if color_id >= 256:
            break
    
    return colors

def main():
    colors = generate_256_colors()
    
    # Print a sample of the generated colors
    for key in list(colors.keys())[:10]:  # Print first 10 colors
        print(f'{key}: {colors[key]}')
    
    # Optionally, save the dictionary to a file
    with open('256_colors_dict.py', 'w') as f:
        f.write('colors = ' + repr(colors) + '\n')

if __name__ == "__main__":
    main()
