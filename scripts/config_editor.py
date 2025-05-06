import curses
import json
import os

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.template.json')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.json')

# ASCII art for DREAM RECORDER (GENERATED WITH https://patorjk.com/software/taag)
ASCII_ART = [
"   .-.                                         .-.                                                 ",
"  (_) )-.                                     (_) )-.                               .'             ",
"    .:   \    .;.::..-.  .-.    . ,';.,';.      .:   \   .-.  .-.   .-.  .;.::..-..'  .-.   .;.::. ",
"   .:'    \   .;  .;.-' ;   :   ;;  ;;  ;;     .::.   ).;.-' ;     ;   ;'.;   :   ; .;.-'   .;     ",
" .-:.      ).;'    `:::'`:::'-'';  ;;  ';    .-:. `:-'  `:::'`;;;;'`;;'.;'    `:::'`.`:::'.;'      ",
"(_/  `----'                   _;        `-' (_/     `:._.                                          ",
]

# Color pair indices
COLOR_HEADER = 1
COLOR_INSTR = 2
COLOR_SELECTED = 3
COLOR_NORMAL = 4
COLOR_DESC = 5
COLOR_EDIT = 6
COLOR_ERROR = 7
COLOR_SUCCESS = 8
COLOR_CATEGORY = 9

# Load config template
def load_template():
    with open(TEMPLATE_PATH, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(config, f, indent=2)

def load_current_config():
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, 'r') as f:
            return json.load(f)
    return {}

def get_merged_config(template, loaded_config):
    config = {}
    for item in template:
        name = item['name']
        if name in loaded_config:
            config[name] = loaded_config[name]
        else:
            config[name] = item['default']
    return config

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(COLOR_HEADER, curses.COLOR_MAGENTA, -1)
    curses.init_pair(COLOR_INSTR, curses.COLOR_CYAN, -1)
    curses.init_pair(COLOR_SELECTED, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(COLOR_NORMAL, curses.COLOR_WHITE, -1)
    curses.init_pair(COLOR_DESC, curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_EDIT, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(COLOR_ERROR, curses.COLOR_RED, -1)
    curses.init_pair(COLOR_SUCCESS, curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_CATEGORY, curses.COLOR_MAGENTA, -1)

def main(stdscr):
    curses.curs_set(0)
    stdscr.clear()
    init_colors()
    template = load_template()
    # Sort template by category, then by name for consistent grouping
    template = sorted(template, key=lambda x: (x.get('category', ''), x['name']))
    loaded_config = load_current_config()
    config = get_merged_config(template, loaded_config)
    current = 0
    editing = False
    edit_value = ''
    msg = ''
    msg_is_error = False

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        min_height = 10 + len(ASCII_ART)
        min_width = 50
        if h < min_height or w < min_width:
            stdscr.addstr(0, 0, "Terminal too small. Resize and try again.", curses.color_pair(COLOR_ERROR) | curses.A_BOLD)
            stdscr.refresh()
            key = stdscr.getch()
            if key in (ord('q'), ord('Q')):
                break
            continue
        # Draw ASCII art heading
        for i, line in enumerate(ASCII_ART):
            if i >= h: break
            stdscr.addstr(i, max(0, (w - len(line)) // 2), line[:w], curses.color_pair(COLOR_HEADER) | curses.A_BOLD)
        y_offset = len(ASCII_ART)
        stdscr.addstr(y_offset, 2, 'Dream Recorder Config Editor', curses.color_pair(COLOR_HEADER) | curses.A_BOLD)
        stdscr.addstr(y_offset+1, 2, 'Up/Down: Navigate  Enter: Edit  S: Save  Q: Quit', curses.color_pair(COLOR_INSTR) | curses.A_BOLD)
        # Calculate how many items fit
        max_items = h - (y_offset + 8)
        # Find the visible window of items
        start = max(0, current - max_items // 2)
        end = min(len(template), start + max_items)
        if end - start < max_items:
            start = max(0, end - max_items)
        y = y_offset + 3
        last_category = None
        for idx in range(start, end):
            item = template[idx]
            category = item.get('category', '')
            if category != last_category:
                # Print category heading
                cat_str = f"[{category}]" if category else "[Uncategorized]"
                try:
                    stdscr.addstr(y, 2, cat_str[:w-4], curses.color_pair(COLOR_CATEGORY) | curses.A_BOLD)
                except curses.error:
                    pass
                y += 1
                last_category = category
            highlight = curses.color_pair(COLOR_SELECTED) if idx == current else curses.color_pair(COLOR_NORMAL)
            val = config[item['name']]
            val_str = str(val)
            name_str = item['name'][:22]  # Truncate name if needed
            val_str = val_str[:w-30]      # Truncate value if needed
            try:
                stdscr.addstr(y, 2, f"{name_str}", highlight)
                stdscr.addstr(y, 25, f"= {val_str}", highlight)
            except curses.error:
                pass  # Ignore if out of bounds
            y += 1
        # Show description and edit box
        item = template[current]
        desc = item['description'][:w-4]
        stdscr.addstr(h-5, 2, desc, curses.color_pair(COLOR_DESC) | curses.A_UNDERLINE)
        stdscr.addstr(h-4, 2, f"Type: {item['type']}", curses.color_pair(COLOR_INSTR))
        if 'options' in item:
            opts_str = str(item['options'])[:w-4]
            stdscr.addstr(h-3, 2, f"Options: {opts_str}", curses.color_pair(COLOR_INSTR))
        if editing:
            edit_prompt = f"Enter new value for {item['name']}: {edit_value}"
            stdscr.addstr(h-2, 2, edit_prompt[:w-4], curses.color_pair(COLOR_EDIT) | curses.A_BOLD)
        if msg:
            color = curses.color_pair(COLOR_ERROR) if msg_is_error else curses.color_pair(COLOR_SUCCESS)
            stdscr.addstr(h-1, 2, msg[:w-4], color | curses.A_BOLD)
        stdscr.refresh()
        key = stdscr.getch()
        msg = ''
        msg_is_error = False
        if editing:
            if key in (curses.KEY_ENTER, 10, 13):
                # Validate and set value
                try:
                    if item['type'] == 'integer':
                        val = int(edit_value)
                    elif item['type'] == 'float':
                        val = float(edit_value)
                    elif item['type'] == 'boolean':
                        val = edit_value.lower() in ('true', '1', 'yes', 'y')
                    elif item['type'] == 'string' or item['type'] == 'url':
                        val = edit_value
                    else:
                        val = edit_value
                    if 'options' in item and val not in item['options']:
                        raise ValueError('Value not in options')
                    config[item['name']] = val
                    editing = False
                    edit_value = ''
                    msg = f"Set {item['name']}!"
                except Exception as e:
                    msg = f"Invalid value: {e}"
                    msg_is_error = True
            elif key == 27:  # ESC
                editing = False
                edit_value = ''
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                edit_value = edit_value[:-1]
            elif 32 <= key <= 126:
                if len(edit_value) < w-30:
                    edit_value += chr(key)
            continue
        if key == curses.KEY_UP:
            current = (current - 1) % len(template)
        elif key == curses.KEY_DOWN:
            current = (current + 1) % len(template)
        elif key in (ord('q'), ord('Q')):
            break
        elif key in (ord('s'), ord('S')):
            save_config(config)
            msg = f"Saved to {OUTPUT_PATH}"
            msg_is_error = False
        elif key in (curses.KEY_ENTER, 10, 13):
            item = template[current]
            if 'options' in item:
                # Cycle through options
                cur_val = config[item['name']]
                opts = item['options']
                idx = opts.index(cur_val) if cur_val in opts else 0
                idx = (idx + 1) % len(opts)
                config[item['name']] = opts[idx]
            else:
                editing = True
                edit_value = str(config[item['name']])

if __name__ == '__main__':
    curses.wrapper(main) 