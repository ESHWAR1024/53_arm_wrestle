import math
import random
import pygame


class GameEngine:

    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        self.arm_position = 0.0
        self.target_limit = 100.0
        self.last_key = None
        
        self.stamina = 100.0
        self.max_stamina = 100.0
        
        self.winner = None
        self.game_state = "PLAYING"
        self.ai_strength = 0.35  
        
        # AI surge cycle state
        self.ai_phase = "NORMAL"       # NORMAL, SURGE, or COOLDOWN
        self.ai_phase_timer = 0        # frame counter for current phase
        self.ai_normal_duration = 300  # ~5 seconds at 60fps
        self.ai_surge_duration = 120   # ~2 seconds at 60fps
        self.ai_cooldown_duration = 180  # ~3 seconds at 60fps
        self.ai_surge_multiplier = 2.5   # force multiplier during surge
        self.ai_cooldown_multiplier = 0.4  # force multiplier during cooldown
        
        self.frame_counter = 0  # drives warning indicator animations
        
        # Counter-surge bonus state
        self.counter_surge_window = 30    # frames at start of COOLDOWN that count as the window
        self.counter_surge_active = False # whether the bonus is currently active
        self.counter_surge_timer = 0      # remaining frames of bonus
        self.counter_surge_duration = 120 # ~2 seconds of bonus at 60fps
        self.counter_surge_push_mult = 2.0  # push strength multiplier during bonus
        self.counter_surge_recovery_mult = 3.0  # stamina recovery multiplier during bonus
        
        self.font_big = pygame.font.SysFont(None, 44)
        self.font_med = pygame.font.SysFont(None, 26)
        self.font_warn = pygame.font.SysFont(None, 30)

    def handle_event(self, event):
        if self.game_state != "PLAYING":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()
            return

        if event.type == pygame.KEYDOWN:
            if self.stamina <= 10:
                return
                
            # Check if player is pushing during the counter-surge window
            in_counter_window = (
                self.ai_phase == "COOLDOWN"
                and self.ai_phase_timer <= self.counter_surge_window
                and not self.counter_surge_active
            )

            # Determine push strength (doubled during counter-surge bonus)
            push_strength = 4.2
            if self.counter_surge_active:
                push_strength *= self.counter_surge_push_mult

            if event.key == pygame.K_LEFT:
                if self.last_key != pygame.K_LEFT: 
                    self.arm_position -= push_strength
                    self.stamina = max(0.0, self.stamina - 2.0)
                    self.last_key = pygame.K_LEFT
                    if in_counter_window:
                        self._activate_counter_surge()
            elif event.key == pygame.K_RIGHT:
                if self.last_key != pygame.K_RIGHT: 
                    self.arm_position -= push_strength
                    self.stamina = max(0.0, self.stamina - 2.0)
                    self.last_key = pygame.K_RIGHT
                    if in_counter_window:
                        self._activate_counter_surge()

    def _activate_counter_surge(self):
        """Activate counter-surge bonus: stamina boost + double push strength."""
        self.counter_surge_active = True
        self.counter_surge_timer = self.counter_surge_duration
        # Instant stamina recovery burst
        self.stamina = min(self.max_stamina, self.stamina + 25.0)

    def update(self):
        if self.game_state != "PLAYING":
            return

        self.frame_counter += 1

        # AI surge cycle: advance timer and transition between phases
        self.ai_phase_timer += 1
        if self.ai_phase == "NORMAL" and self.ai_phase_timer >= self.ai_normal_duration:
            self.ai_phase = "SURGE"
            self.ai_phase_timer = 0
        elif self.ai_phase == "SURGE" and self.ai_phase_timer >= self.ai_surge_duration:
            self.ai_phase = "COOLDOWN"
            self.ai_phase_timer = 0
        elif self.ai_phase == "COOLDOWN" and self.ai_phase_timer >= self.ai_cooldown_duration:
            self.ai_phase = "NORMAL"
            self.ai_phase_timer = 0

        # Apply force multiplier based on current AI phase
        if self.ai_phase == "SURGE":
            phase_multiplier = self.ai_surge_multiplier
        elif self.ai_phase == "COOLDOWN":
            phase_multiplier = self.ai_cooldown_multiplier
        else:
            phase_multiplier = 1.0

        ai_variance = random.uniform(0.3, 1.0)
        self.arm_position += self.ai_strength * ai_variance * phase_multiplier

        # Tick down counter-surge bonus timer
        if self.counter_surge_active:
            self.counter_surge_timer -= 1
            if self.counter_surge_timer <= 0:
                self.counter_surge_active = False
                self.counter_surge_timer = 0

        # Stamina recovery (boosted during counter-surge)
        recovery_rate = 0.8
        if self.counter_surge_active:
            recovery_rate *= self.counter_surge_recovery_mult
        if self.stamina < self.max_stamina:
            self.stamina = min(self.max_stamina, self.stamina + recovery_rate)

        if self.arm_position <= -self.target_limit:
            self.winner = "PLAYER"
            self.game_state = "GAME_OVER"
        elif self.arm_position >= self.target_limit:
            self.winner = "COMPUTER"
            self.game_state = "GAME_OVER"

    def reset(self):
        self.arm_position = 0.0
        self.stamina = 100.0
        self.last_key = None
        self.winner = None
        self.game_state = "PLAYING"
        self.ai_phase = "NORMAL"
        self.ai_phase_timer = 0
        self.frame_counter = 0
        self.counter_surge_active = False
        self.counter_surge_timer = 0

    def render(self, screen):
        screen.fill((25, 28, 35))

        title_surf = self.font_big.render("ARM WRESTLE SHOWDOWN", True, (240, 240, 240))
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 12))

        player_header = self.font_med.render("PLAYER", True, (80, 160, 255))
        computer_header = self.font_med.render("COMPUTER", True, (255, 100, 80))
        screen.blit(player_header, (60, 55))
        screen.blit(computer_header, (self.width - 150, 55))

        table_rect = pygame.Rect(40, 100, self.width - 80, 310)
        pygame.draw.rect(screen, (110, 50, 15), table_rect, border_radius=14)
        pygame.draw.rect(screen, (70, 30, 8), table_rect, width=5, border_radius=14)

        pygame.draw.line(screen, (45, 18, 4), (self.width // 2, 100), (self.width // 2, 410), 4)

        offset_x = (self.arm_position / self.target_limit) * 95
        hand_x = (self.width // 2) + int(offset_x)
        hand_y = 235

        p_shoulder = (70, 330)
        p_elbow = (140, 215)
        c_shoulder = (self.width - 70, 330)
        c_elbow = (self.width - 140, 215)

        pygame.draw.line(screen, (200, 145, 110), p_shoulder, p_elbow, 32)
        pygame.draw.line(screen, (215, 160, 125), p_elbow, (hand_x, hand_y), 26)
        pygame.draw.circle(screen, (185, 130, 95), p_elbow, 18)

        pygame.draw.line(screen, (170, 110, 85), c_shoulder, c_elbow, 32)
        pygame.draw.line(screen, (185, 125, 95), c_elbow, (hand_x, hand_y), 26)
        pygame.draw.circle(screen, (150, 95, 70), c_elbow, 18)

        pygame.draw.circle(screen, (225, 175, 140), (hand_x, hand_y), 24)
        pygame.draw.circle(screen, (160, 115, 85), (hand_x, hand_y), 24, width=3)

        stamina_label = self.font_med.render("STAMINA", True, (220, 220, 220))
        screen.blit(stamina_label, (40, 445))

        stamina_bg = pygame.Rect(140, 448, 240, 22)
        stamina_fill = pygame.Rect(140, 448, int(240 * (self.stamina / self.max_stamina)), 22)
        pygame.draw.rect(screen, (45, 50, 60), stamina_bg, border_radius=6)
        bar_color = (60, 210, 100) if self.stamina > 25 else (220, 60, 60)
        pygame.draw.rect(screen, bar_color, stamina_fill, border_radius=6)

        # --- WARNING INDICATORS ---
        # AI Surge warning: pulsing red/orange banner at top of the table
        if self.ai_phase == "SURGE" and self.game_state == "PLAYING":
            pulse = (math.sin(self.frame_counter * 0.15) + 1) / 2  # 0.0 – 1.0
            alpha = int(60 + 140 * pulse)
            # Red tint overlay on the table
            surge_overlay = pygame.Surface((self.width - 80, 310), pygame.SRCALPHA)
            surge_overlay.fill((255, 40, 40, int(alpha * 0.25)))
            screen.blit(surge_overlay, (40, 100))
            # Flashing border around table
            border_color = (255, int(60 + 80 * pulse), 30)
            pygame.draw.rect(screen, border_color, pygame.Rect(40, 100, self.width - 80, 310), width=4, border_radius=14)
            # Warning text banner
            warn_text = self.font_warn.render("\u26a0 AI POWER SURGE!", True, (255, int(180 * pulse), 50))
            banner_x = self.width // 2 - warn_text.get_width() // 2
            banner_bg = pygame.Surface((warn_text.get_width() + 20, 32), pygame.SRCALPHA)
            banner_bg.fill((180, 30, 20, alpha))
            screen.blit(banner_bg, (banner_x - 10, 420))
            screen.blit(warn_text, (banner_x, 422))

        # Player exhaustion warning: shown when stamina <= 10 (input locked)
        if self.stamina <= 10 and self.game_state == "PLAYING":
            pulse = (math.sin(self.frame_counter * 0.2) + 1) / 2
            alpha = int(100 + 155 * pulse)
            # Red tint behind stamina bar
            exhaust_bg = pygame.Surface((260, 30), pygame.SRCALPHA)
            exhaust_bg.fill((200, 30, 30, int(alpha * 0.4)))
            screen.blit(exhaust_bg, (130, 444))
            # "EXHAUSTED" label
            exhaust_text = self.font_warn.render("EXHAUSTED", True, (255, int(80 + 80 * pulse), int(80 * pulse)))
            screen.blit(exhaust_text, (400, 445))

        # Counter-surge bonus active indicator: golden/cyan glow
        if self.counter_surge_active and self.game_state == "PLAYING":
            pulse = (math.sin(self.frame_counter * 0.12) + 1) / 2
            alpha = int(80 + 120 * pulse)
            # Cyan/gold glow overlay on table
            cs_overlay = pygame.Surface((self.width - 80, 310), pygame.SRCALPHA)
            cs_overlay.fill((50, 220, 255, int(alpha * 0.15)))
            screen.blit(cs_overlay, (40, 100))
            # Gold border
            gold_color = (255, int(200 + 55 * pulse), 50)
            pygame.draw.rect(screen, gold_color, pygame.Rect(40, 100, self.width - 80, 310), width=4, border_radius=14)
            # "COUNTER-SURGE!" text banner
            cs_text = self.font_warn.render("\u26a1 COUNTER-SURGE!", True, (255, int(220 + 35 * pulse), 60))
            cs_x = self.width // 2 - cs_text.get_width() // 2
            cs_bg = pygame.Surface((cs_text.get_width() + 20, 32), pygame.SRCALPHA)
            cs_bg.fill((40, 160, 200, alpha))
            screen.blit(cs_bg, (cs_x - 10, 420))
            screen.blit(cs_text, (cs_x, 422))
            # Timer bar showing remaining bonus time
            ratio = self.counter_surge_timer / self.counter_surge_duration
            timer_w = int(200 * ratio)
            timer_rect = pygame.Rect(self.width // 2 - 100, 456, timer_w, 8)
            pygame.draw.rect(screen, (50, 220, 255), timer_rect, border_radius=4)

        if self.game_state == "GAME_OVER":
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))

            win_text = "PLAYER WINS THE MATCH!" if self.winner == "PLAYER" else "COMPUTER WINS!"
            color = (80, 240, 100) if self.winner == "PLAYER" else (240, 80, 80)
            text_surf = self.font_big.render(win_text, True, color)
            screen.blit(
                text_surf,
                (self.width // 2 - text_surf.get_width() // 2, self.height // 2 - 45)
            )

            restart_surf = self.font_med.render(
                "Press [R] to Rematch", True, (240, 240, 240)
            )
            screen.blit(
                restart_surf,
                (self.width // 2 - restart_surf.get_width() // 2, self.height // 2 + 10)
            )
