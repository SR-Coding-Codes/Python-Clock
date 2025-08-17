import pygame
import sys, os
import time
from itertools import cycle

# --- Init ---
pygame.init()
pygame.mixer.init()

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# ---- LOAD SOUND / ICON ----
ALARM_SOUND = pygame.mixer.Sound(resource_path("assets/Alarm.wav"))

# Window setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Stopwatch v0.0.3.5")
icon_surface = pygame.image.load(resource_path("assets/logo.png"))
pygame.display.set_icon(icon_surface)

clock = pygame.time.Clock()
running = True

# Colors
DARK_GRAY = (10, 10, 10)
WHITE     = (255, 255, 255)
BUTTON_BG = (50, 50, 50)

# Title color cycle
colors = [(255, 0, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255)]
color_cycle = cycle(colors)
TITLE_COLOR = WHITE
COLOR_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(COLOR_EVENT, 0)

# Fonts
title_font  = pygame.font.Font(None, 48)
timer_font  = pygame.font.Font(None, 96)
button_font = pygame.font.Font(None, 36)
hint_font   = pygame.font.Font(None, 24)

# --- Tabs ---
current_tab = "stopwatch"  # "stopwatch" | "timer" | "time"
tab_h = 40
tab_y = 20
tab_w = 180
tab_gap = 10
stopwatch_tab_rect = pygame.Rect(20, tab_y, tab_w, tab_h)
timer_tab_rect     = pygame.Rect(20 + tab_w + tab_gap, tab_y, tab_w, tab_h)
time_tab_rect      = pygame.Rect(20 + 2*(tab_w + tab_gap), tab_y, tab_w, tab_h)

# --- Buttons ---
toggle_box = pygame.Rect(WIDTH // 2 - 200, HEIGHT - 90, 180, 50)
reset_box  = pygame.Rect(WIDTH // 2 + 20,  HEIGHT - 90, 180, 50)

# Click cooldown (mouse)
last_toggle_time = 0
TOGGLE_COOLDOWN = 200  # ms

# --- Stopwatch state ---
sw_running    = False
sw_start_time = 0.0
sw_elapsed    = 0.0  # accumulated when paused

# --- Timer state (inline adjustable, no pop-up) ---
timer_running      = False
timer_set_seconds  = 60  # default 1 minute (shown when stopped)
timer_end_time     = 0.0
alarm_playing      = False

# --- Helpers ---
def draw_tabs():
    for rect, label in [
        (stopwatch_tab_rect, "Stopwatch"),
        (timer_tab_rect,     "Timer"),
        (time_tab_rect,      "Time")
    ]:
        pygame.draw.rect(screen, BUTTON_BG, rect, border_radius=6)
        pygame.draw.rect(screen, WHITE, rect, 2, border_radius=6)
        s = button_font.render(label, True, WHITE)
        screen.blit(s, s.get_rect(center=rect.center))

def start_color_cycle():
    pygame.time.set_timer(COLOR_EVENT, 250)

def stop_color_cycle_if_idle():
    global TITLE_COLOR
    if not sw_running and not timer_running:
        pygame.time.set_timer(COLOR_EVENT, 0)
        TITLE_COLOR = WHITE

def toggle_alarm(play):
    global alarm_playing
    if play and not alarm_playing:
        ALARM_SOUND.play(-1)  # loop
        alarm_playing = True
    elif not play and alarm_playing:
        ALARM_SOUND.stop()
        alarm_playing = False

def stopwatch_display_time():
    if sw_running:
        elapsed = sw_elapsed + (time.time() - sw_start_time)
    else:
        elapsed = sw_elapsed
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    hundredths = int((elapsed - int(elapsed)) * 100)
    return f"{minutes:02d}:{seconds:02d}.{hundredths:02d}"

def timer_remaining_seconds():
    if timer_running:
        return max(0, int(timer_end_time - time.time()))
    else:
        return max(0, int(timer_set_seconds))

def draw_button(box, label):
    pygame.draw.rect(screen, BUTTON_BG, box, border_radius=8)
    pygame.draw.rect(screen, WHITE, box, 2, border_radius=8)
    s = button_font.render(label, True, WHITE)
    screen.blit(s, s.get_rect(center=box.center))

def draw_title(text):
    s = title_font.render(text, True, TITLE_COLOR)
    screen.blit(s, (20, 80))

def draw_stopwatch_tab():
    draw_title("Stopwatch")
    ts = stopwatch_display_time()
    surf = timer_font.render(ts, True, WHITE)
    screen.blit(surf, surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))
    draw_button(toggle_box, "Stop" if sw_running else "Start")
    draw_button(reset_box,  "Reset")
    hint = hint_font.render("SPACE start/stop | R reset", True, WHITE)
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 25)))  # moved 5 px lower

def draw_timer_tab():
    draw_title("Timer")
    remaining = timer_remaining_seconds()
    minutes = remaining // 60
    seconds = remaining % 60
    ts = f"{minutes:02d}:{seconds:02d}"
    surf = timer_font.render(ts, True, WHITE)
    screen.blit(surf, surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))
    draw_button(toggle_box, "Stop" if timer_running else "Start")
    draw_button(reset_box,  "Reset")
    hint = hint_font.render("UP/DOWN adjust | SPACE start/stop | R reset", True, WHITE)
    screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 25)))  # moved 5 px lower

def draw_time_tab():
    draw_title("Time")
    now_str = time.strftime("%H:%M:%S")
    surf = timer_font.render(now_str, True, WHITE)
    screen.blit(surf, surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))

def handle_mouse(event, current_time_ms):
    global last_toggle_time
    global sw_running, sw_start_time, sw_elapsed
    global timer_running, timer_end_time, timer_set_seconds

    # Tab switching
    if stopwatch_tab_rect.collidepoint(event.pos):
        return "stopwatch"
    if timer_tab_rect.collidepoint(event.pos):
        return "timer"
    if time_tab_rect.collidepoint(event.pos):
        return "time"

    # Buttons (with cooldown on toggle)
    if toggle_box.collidepoint(event.pos):
        if current_time_ms - last_toggle_time > TOGGLE_COOLDOWN:
            if current_tab == "stopwatch":
                if sw_running:
                    sw_elapsed += time.time() - sw_start_time
                    sw_running = False
                    stop_color_cycle_if_idle()
                else:
                    sw_start_time = time.time()
                    sw_running = True
                    start_color_cycle()
            elif current_tab == "timer":
                if timer_running:
                    timer_running = False
                    toggle_alarm(False)
                    stop_color_cycle_if_idle()
                else:
                    timer_end_time = time.time() + max(0, int(timer_set_seconds))
                    timer_running = True
                    start_color_cycle()
                    toggle_alarm(False)
            last_toggle_time = current_time_ms

    elif reset_box.collidepoint(event.pos):
        if current_tab == "stopwatch":
            sw_running = False
            sw_elapsed = 0.0
            stop_color_cycle_if_idle()
        elif current_tab == "timer":
            timer_running = False
            toggle_alarm(False)
            stop_color_cycle_if_idle()

    return None

# --- Main loop ---
while running:
    dt = clock.tick(60) / 1000.0
    current_time_ms = pygame.time.get_ticks()

    # Trigger alarm when timer hits zero (stay running until user stops)
    if timer_running and timer_remaining_seconds() == 0:
        toggle_alarm(True)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == COLOR_EVENT:
            TITLE_COLOR = next(color_cycle)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            switched = handle_mouse(event, current_time_ms)
            if switched is not None:
                current_tab = switched

        elif event.type == pygame.KEYDOWN:
            # SPACE: Start/Stop
            if event.key == pygame.K_SPACE:
                if current_tab == "stopwatch":
                    if sw_running:
                        sw_elapsed += time.time() - sw_start_time
                        sw_running = False
                        stop_color_cycle_if_idle()
                    else:
                        sw_start_time = time.time()
                        sw_running = True
                        start_color_cycle()

                elif current_tab == "timer":
                    if timer_running:
                        timer_running = False
                        toggle_alarm(False)
                        stop_color_cycle_if_idle()
                    else:
                        timer_end_time = time.time() + max(0, int(timer_set_seconds))
                        timer_running = True
                        start_color_cycle()
                        toggle_alarm(False)

            # R: Reset
            elif event.key == pygame.K_r:
                if current_tab == "stopwatch":
                    sw_running = False
                    sw_elapsed = 0.0
                    stop_color_cycle_if_idle()
                elif current_tab == "timer":
                    timer_running = False
                    toggle_alarm(False)
                    stop_color_cycle_if_idle()

            # Timer adjustments when stopped
            elif current_tab == "timer" and not timer_running:
                if event.key == pygame.K_UP:
                    timer_set_seconds = max(0, int(timer_set_seconds) + 10)
                elif event.key == pygame.K_DOWN:
                    timer_set_seconds = max(0, int(timer_set_seconds) - 10)

    # Draw
    screen.fill(DARK_GRAY)
    draw_tabs()

    if current_tab == "stopwatch":
        draw_stopwatch_tab()
    elif current_tab == "timer":
        draw_timer_tab()
    elif current_tab == "time":
        draw_time_tab()

    pygame.display.flip()

pygame.quit()
sys.exit()
