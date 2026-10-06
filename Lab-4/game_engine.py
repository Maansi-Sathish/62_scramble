import random
import pygame
from game.text_box import TextBox


class GameEngine:
    ROUND_SECONDS = 20   # Task 3: time allowed per word
    TILE_GAP = 8         # Task 4: spacing between tiles
    POOL_Y = 125         # Task 4: y of the scrambled-letter row
    ROW_Y = 240          # y of the input box / SUBMIT / HINT row

    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.words = ["PYTHON", "PYGAME", "PLANET", "ROCKET", "GALAXY", "STREAM", "PUZZLE", "ALGORITHM"]
        self.secret_word = ""
        self.scrambled_word = ""

        self.score = 0
        self.feedback_msg = "Unscramble the letters above!"
        self.feedback_color = (210, 215, 225)

        # Row layout: input (160) + gap + SUBMIT (95) + gap + HINT (80)
        row_left = width // 2 - 177
        self.input_box = TextBox(row_left, self.ROW_Y, 160, 46)
        self.submit_btn = pygame.Rect(row_left + 170, self.ROW_Y, 95, 46)
        self.hint_btn = pygame.Rect(row_left + 275, self.ROW_Y, 80, 46)
        self.hints_used = 0

        # Task 3: timer state
        self.round_start = 0
        self.time_left = self.ROUND_SECONDS

        # Task 4: tile state
        self.tiles = []        # the scrambled letters
        self.rack = []         # indices into self.tiles, in the order the player placed them
        self.pool_rects = []
        self.rack_rects = []
        self.tile_size = 44

        self.font_title = pygame.font.SysFont(None, 40)
        self.font_word = pygame.font.SysFont(None, 52)
        self.font_msg = pygame.font.SysFont(None, 26)
        self.font_btn = pygame.font.SysFont(None, 24)
        self.font_tile = pygame.font.SysFont(None, 34)

        self.next_round()

    def scramble_string(self, word):
        letters = list(word)
        while True:
            random.shuffle(letters)
            shuffled = "".join(letters)
            if shuffled != word or len(word) <= 1:
                return shuffled

    def build_layout(self):
        """Task 4: compute tile rectangles for the current word."""
        n = len(self.secret_word)
        gap = self.TILE_GAP
        size = max(24, min(44, (self.width - 60) // n - gap))
        total = n * size + (n - 1) * gap
        left = self.width // 2 - total // 2
        rack_y = self.POOL_Y + size + 12
        self.tile_size = size
        self.pool_rects = [pygame.Rect(left + i * (size + gap), self.POOL_Y, size, size) for i in range(n)]
        self.rack_rects = [pygame.Rect(left + i * (size + gap), rack_y, size, size) for i in range(n)]

    def rack_string(self):
        return "".join(self.tiles[i] for i in self.rack)

    def sync_input_from_rack(self):
        # Mirror the rack into the text box so SUBMIT / Enter work as usual
        self.input_box.text = self.rack_string()

    def next_round(self):
        self.secret_word = random.choice(self.words)
        self.scrambled_word = self.scramble_string(self.secret_word)
        self.hints_used = 0
        self.round_start = pygame.time.get_ticks()   # restart the timer
        self.time_left = self.ROUND_SECONDS
        self.tiles = list(self.scrambled_word)
        self.rack = []
        self.build_layout()
        self.input_box.clear()

    def submit_guess(self):
        guess = self.input_box.text.strip().upper()
        if not guess:
            self.feedback_msg = "Type a word before submitting!"
            self.feedback_color = (240, 170, 50)
            return

        # Task 1 fix: compare against the secret word, not the scrambled one
        is_correct = (guess == self.secret_word)

        if is_correct:
            self.score += 1
            self.feedback_msg = f"CORRECT! '{self.secret_word}' is right."
            self.feedback_color = (80, 230, 110)
            self.next_round()
        else:
            self.feedback_msg = "WRONG GUESS! Try again."
            self.feedback_color = (240, 80, 80)
            self.input_box.clear()
            self.rack = []   # Task 4: send all tiles back to the pool

    def use_hint(self):
        if self.hints_used >= len(self.secret_word):
            self.feedback_msg = "No more letters to reveal!"
            self.feedback_color = (240, 170, 50)
            return
        self.hints_used += 1
        self.score = max(0, self.score - 1)  # penalty, never below 0
        self.feedback_msg = "Hint used: -1 point"
        self.feedback_color = (240, 170, 50)

    def handle_tile_click(self, pos):
        """Task 4: click a pool tile to place it in the rack, click a rack tile to return it."""
        for i, rect in enumerate(self.pool_rects):
            if rect.collidepoint(pos) and i not in self.rack:
                self.rack.append(i)
                self.sync_input_from_rack()
                return True
        for j, rect in enumerate(self.rack_rects):
            if j < len(self.rack) and rect.collidepoint(pos):
                self.rack.pop(j)
                self.sync_input_from_rack()
                return True
        return False

    def handle_event(self, event):
        self.input_box.handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.submit_guess()
            elif self.input_box.text != self.rack_string():
                # Player typed instead of using tiles: typing takes over
                self.rack = []
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.submit_btn.collidepoint(event.pos):
                self.submit_guess()
            elif self.hint_btn.collidepoint(event.pos):
                self.use_hint()
            else:
                self.handle_tile_click(event.pos)

    def update(self):
        # Task 3: count down and handle expiry
        elapsed = (pygame.time.get_ticks() - self.round_start) / 1000
        self.time_left = max(0, self.ROUND_SECONDS - elapsed)

        if self.time_left <= 0:
            # Reveal the answer in the message, then move on automatically
            self.feedback_msg = f"TIME'S UP! The word was {self.secret_word}"
            self.feedback_color = (240, 80, 80)
            self.next_round()

    def draw_tile(self, screen, rect, letter, fill):
        pygame.draw.rect(screen, fill, rect, border_radius=8)
        pygame.draw.rect(screen, (230, 230, 235), rect, width=2, border_radius=8)
        surf = self.font_tile.render(letter, True, (255, 255, 255))
        screen.blit(surf, (rect.centerx - surf.get_width() // 2,
                           rect.centery - surf.get_height() // 2))

    def draw_empty_slot(self, screen, rect):
        pygame.draw.rect(screen, (36, 41, 52), rect, border_radius=8)
        pygame.draw.rect(screen, (70, 76, 92), rect, width=2, border_radius=8)

    def render(self, screen):
        screen.fill((26, 30, 38))

        title_surf = self.font_title.render("Word Scramble Arena", True, (245, 245, 245))
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 25))

        score_surf = self.font_msg.render(f"Score: {self.score}", True, (255, 220, 80))
        screen.blit(score_surf, (self.width // 2 - score_surf.get_width() // 2, 70))

        # Task 3: countdown timer bar
        bar_w, bar_h = 300, 10
        bar_x = self.width // 2 - bar_w // 2
        bar_y = 102
        fraction = self.time_left / self.ROUND_SECONDS
        if fraction > 0.5:
            bar_color = (80, 230, 110)
        elif fraction > 0.25:
            bar_color = (240, 170, 50)
        else:
            bar_color = (240, 80, 80)
        pygame.draw.rect(screen, (55, 60, 72), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
        pygame.draw.rect(screen, bar_color, (bar_x, bar_y, int(bar_w * fraction), bar_h), border_radius=5)

        # Task 4: scrambled letter tiles (top row) and the rearrangement rack (second row)
        for i, rect in enumerate(self.pool_rects):
            if i in self.rack:
                self.draw_empty_slot(screen, rect)      # tile has been moved to the rack
            else:
                self.draw_tile(screen, rect, self.tiles[i], (45, 110, 175))
        for j, rect in enumerate(self.rack_rects):
            if j < len(self.rack):
                self.draw_tile(screen, rect, self.tiles[self.rack[j]], (90, 70, 160))
            else:
                self.draw_empty_slot(screen, rect)

        self.input_box.render(screen)

        # SUBMIT button
        pygame.draw.rect(screen, (50, 150, 85), self.submit_btn, border_radius=6)
        pygame.draw.rect(screen, (220, 220, 220), self.submit_btn, width=2, border_radius=6)
        btn_text = self.font_btn.render("SUBMIT", True, (255, 255, 255))
        screen.blit(btn_text, (self.submit_btn.centerx - btn_text.get_width() // 2,
                               self.submit_btn.centery - btn_text.get_height() // 2))

        # HINT button
        pygame.draw.rect(screen, (190, 140, 40), self.hint_btn, border_radius=6)
        pygame.draw.rect(screen, (220, 220, 220), self.hint_btn, width=2, border_radius=6)
        hint_text = self.font_btn.render("HINT", True, (255, 255, 255))
        screen.blit(hint_text, (self.hint_btn.centerx - hint_text.get_width() // 2,
                                self.hint_btn.centery - hint_text.get_height() // 2))

        feedback_surf = self.font_msg.render(self.feedback_msg, True, self.feedback_color)
        screen.blit(feedback_surf, (self.width // 2 - feedback_surf.get_width() // 2, 305))

        # Hint line: revealed letters, underscores for the rest
        shown = [self.secret_word[i] if i < self.hints_used else "_"
                 for i in range(len(self.secret_word))]
        hint_line = self.font_word.render(" ".join(shown), True, (255, 200, 90))
        screen.blit(hint_line, (self.width // 2 - hint_line.get_width() // 2, 340))