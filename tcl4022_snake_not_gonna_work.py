import tkinter as tk
import random

# Desktop prototype for a 240x320 feature-phone screen.
# Controls: arrows or 2/4/6/8 = move, Enter/Space = start or pause,
# R = restart, Esc = return to the menu.

SCREEN_W, SCREEN_H = 240, 320
CELL = 10
COLS, ROWS = SCREEN_W // CELL, SCREEN_H // CELL
TICK_MS = 145

BG = "#101820"
SCREEN_BG = "#071018"
GREEN = "#9bbc0f"
DARK_GREEN = "#306230"
LIGHT = "#d7e6a5"
WHITE = "#f1f5df"
MUTED = "#8a9a86"
RED = "#e45b5b"


class SnakePhoneGame:
    def __init__(self, root):
        self.root = root
        self.root.title("TCL 4022 - Snake Prototype")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        shell = tk.Frame(root, bg="#27333b", padx=14, pady=14)
        shell.pack(padx=18, pady=18)

        self.canvas = tk.Canvas(
            shell, width=SCREEN_W, height=SCREEN_H,
            bg=SCREEN_BG, highlightthickness=2,
            highlightbackground="#5a6971"
        )
        self.canvas.pack()

        tk.Label(
            shell, text="TCL 4022  |  DESKTOP TEST",
            bg="#27333b", fg="#dce5e8",
            font=("Segoe UI", 9, "bold")
        ).pack(pady=(10, 0))

        tk.Label(
            shell,
            text="Arrows / 2 4 6 8: move   Enter: start/pause   R: restart   Esc: menu",
            bg=BG, fg="#dce5e8", font=("Segoe UI", 9)
        ).pack(pady=(0, 10))

        self.root.bind("<KeyPress>", self.on_key)
        self.state = "menu"
        self.score = 0
        self.best = 0
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.snake = []
        self.food = None
        self.after_id = None
        self.draw_menu()

    def clear_timer(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def draw_text(self, x, y, text, fill=WHITE, size=12, anchor="center", bold=False):
        self.canvas.create_text(
            x, y, text=text, fill=fill,
            font=("TkFixedFont", size, "bold" if bold else "normal"),
            anchor=anchor
        )

    def draw_menu(self):
        self.clear_timer()
        self.state = "menu"
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, SCREEN_W, SCREEN_H, fill=SCREEN_BG, outline="")
        self.draw_text(SCREEN_W // 2, 45, "SNAKE", GREEN, 23, bold=True)
        self.draw_text(SCREEN_W // 2, 75, "TCL 4022 prototype", MUTED, 10)
        # Tiny snake illustration
        for x, y in [(80, 125), (90, 125), (100, 125), (110, 125), (120, 125)]:
            self.canvas.create_rectangle(x, y, x + 8, y + 8, fill=GREEN, outline=DARK_GREEN)
        self.canvas.create_rectangle(130, 105, 138, 113, fill=RED, outline="")
        self.draw_text(SCREEN_W // 2, 180, "ENTER / SPACE", WHITE, 12, bold=True)
        self.draw_text(SCREEN_W // 2, 200, "to start", MUTED, 10)
        self.draw_text(SCREEN_W // 2, 255, "Move: arrows or 2 4 6 8", LIGHT, 9)
        self.draw_text(SCREEN_W // 2, 275, "R: restart   ESC: menu", LIGHT, 9)
        self.draw_text(SCREEN_W // 2, 304, "Windows test build", MUTED, 8)

    def start_game(self):
        self.clear_timer()
        self.state = "playing"
        self.score = 0
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.snake = [(COLS // 2 - i, ROWS // 2) for i in range(4)]
        self.place_food()
        self.draw_game()
        self.tick()

    def place_food(self):
        free = [(x, y) for x in range(COLS) for y in range(ROWS)
                if (x, y) not in self.snake]
        self.food = random.choice(free) if free else None

    def on_key(self, event):
        key = event.keysym.lower()
        if key in ("return", "space"):
            if self.state in ("menu", "gameover", "won"):
                self.start_game()
            elif self.state == "playing":
                self.state = "paused"
                self.clear_timer()
                self.draw_game()
            elif self.state == "paused":
                self.state = "playing"
                self.draw_game()
                self.tick()
            return

        if key == "escape":
            self.draw_menu()
            return
        if key == "r":
            self.start_game()
            return

        moves = {
            "up": (0, -1), "8": (0, -1), "w": (0, -1),
            "down": (0, 1), "2": (0, 1), "s": (0, 1),
            "left": (-1, 0), "4": (-1, 0), "a": (-1, 0),
            "right": (1, 0), "6": (1, 0), "d": (1, 0),
        }
        if key in moves and self.state == "playing":
            new_dir = moves[key]
            if new_dir != (-self.direction[0], -self.direction[1]):
                self.next_direction = new_dir

    def tick(self):
        self.after_id = None
        if self.state != "playing":
            return

        self.direction = self.next_direction
        hx, hy = self.snake[0]
        dx, dy = self.direction
        new_head = (hx + dx, hy + dy)

        # Classic wrap-around edges keep the first prototype forgiving.
        new_head = (new_head[0] % COLS, new_head[1] % ROWS)
        eating = new_head == self.food
        body_to_check = self.snake if eating else self.snake[:-1]

        if new_head in body_to_check:
            self.state = "gameover"
            self.best = max(self.best, self.score)
            self.draw_game()
            return

        self.snake.insert(0, new_head)
        if eating:
            self.score += 10
            self.best = max(self.best, self.score)
            if len(self.snake) == COLS * ROWS:
                self.state = "won"
            else:
                self.place_food()
        else:
            self.snake.pop()

        self.draw_game()
        if self.state == "playing":
            speed = max(75, TICK_MS - (self.score // 50) * 5)
            self.after_id = self.root.after(speed, self.tick)

    def draw_game(self):
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, SCREEN_W, SCREEN_H, fill=SCREEN_BG, outline="")
        self.canvas.create_rectangle(0, 0, SCREEN_W, 24, fill="#17252c", outline="")
        self.draw_text(8, 12, f"SCORE {self.score}", LIGHT, 9, anchor="w", bold=True)
        self.draw_text(SCREEN_W - 8, 12, f"BEST {self.best}", MUTED, 9, anchor="e")

        # Sparse grid, subtle enough to resemble a small LCD.
        for x in range(0, SCREEN_W, CELL):
            self.canvas.create_line(x, 25, x, SCREEN_H, fill="#0c1820")
        for y in range(25, SCREEN_H, CELL):
            self.canvas.create_line(0, y, SCREEN_W, y, fill="#0c1820")

        if self.food:
            fx, fy = self.food
            px, py = fx * CELL, fy * CELL
            self.canvas.create_oval(px + 1, py + 1, px + CELL - 1, py + CELL - 1,
                                    fill=RED, outline="#ff9b8e")

        for i, (sx, sy) in enumerate(self.snake):
            x, y = sx * CELL, sy * CELL
            color = "#d7f46b" if i == 0 else GREEN
            self.canvas.create_rectangle(x + 1, y + 1, x + CELL - 1, y + CELL - 1,
                                         fill=color, outline=DARK_GREEN)

        if self.state == "paused":
            self.overlay("PAUSED", "Enter / Space to continue")
        elif self.state == "gameover":
            self.overlay("GAME OVER", "Enter: play again")
        elif self.state == "won":
            self.overlay("YOU WIN!", "Enter: play again")

    def overlay(self, title, subtitle):
        self.canvas.create_rectangle(15, 116, SCREEN_W - 15, 194,
                                     fill="#17252c", outline=GREEN, width=2)
        self.draw_text(SCREEN_W // 2, 139, title, GREEN, 15, bold=True)
        self.draw_text(SCREEN_W // 2, 166, subtitle, WHITE, 8)
        self.draw_text(SCREEN_W // 2, 182, "ESC: menu  |  R: restart", MUTED, 8)


if __name__ == "__main__":
    root = tk.Tk()
    SnakePhoneGame(root)
    root.mainloop()
