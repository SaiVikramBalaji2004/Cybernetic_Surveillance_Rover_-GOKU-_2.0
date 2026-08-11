import logging
import time
import os
import math

# Suppress ALSA warnings before pygame loads
import alsa_suppress

os.environ['DISPLAY'] = ':0'
import pygame
from config import DISPLAY_WIDTH, DISPLAY_HEIGHT, DISPLAY_FPS

logger = logging.getLogger('GOKU.Display')

try:
    if 'DISPLAY' not in os.environ:
        os.environ['DISPLAY'] = ':0'
    pygame.init()
    pygame.display.init()
    PYGAME_AVAILABLE = True
except Exception as e:
    PYGAME_AVAILABLE = False
    logger.warning("Pygame not available: %s", e)

class DisplayController:
    def __init__(self, width: int = DISPLAY_WIDTH, height: int = DISPLAY_HEIGHT):
        self.width = width
        self.height = height
        self.screen = None
        self.font = None
        self.small_font = None
        self.micro_font = None
        self.running = False
        self.current_expression = 'neutral'
        self.status_text = "Initializing..."
        self.led_color = (0, 180, 255)
        self.metal_color = (180, 185, 190)
        self.dark_metal = (60, 65, 70)
        self.eye_glow = (0, 220, 255)
        self.blink_state = 0
        self.blink_timer = 0
        self.anim_frame = 0
        self.scan_angle = 0
        self.alert_pulse = 0
        self.servo_pos = 0
        
    def initialize(self) -> bool:
        if not PYGAME_AVAILABLE:
            logger.warning("Pygame not available")
            return False
            
        try:
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("GOKU - Realistic Robot Interface")
            self.font = pygame.font.Font(None, 48)
            self.small_font = pygame.font.Font(None, 32)
            self.micro_font = pygame.font.Font(None, 22)
            self.running = True
            logger.info("Display initialized - Realistic Robot Mode")
            return True
        except Exception as e:
            logger.error("Display initialization error: %s", e)
            return False
    
    def set_expression(self, expression: str):
        self.current_expression = expression
        if expression == 'alert':
            self.alert_pulse = 0
        
    def set_status(self, text: str):
        self.status_text = text
    
    def update(self):
        if not self.running or not self.screen:
            return
        try:
            self.anim_frame += 1
            self._draw()
        except Exception as e:
            logger.error("Display draw error: %s", e)
    
    def _draw(self):
        # Dark industrial background
        self.screen.fill((15, 18, 25))
        self._draw_tech_background()
        
        center_x = self.width // 2
        center_y = self.height // 2
        
        # Draw robot head assembly
        self._draw_robot_head(center_x, center_y)
        
        # Draw facial features
        self._draw_robot_eyes(center_x, center_y)
        self._draw_robot_mouth(center_x, center_y)
        self._draw_antenna_array(center_x, center_y)
        
        # Draw HUD elements
        self._draw_hud_overlay(center_x)
        self._draw_status_panel()
        
        pygame.display.flip()
    
    def _draw_tech_background(self):
        # Animated grid
        grid_color = (30, 35, 50)
        for x in range(0, self.width, 50):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, self.height), 1)
        for y in range(0, self.height, 50):
            pygame.draw.line(self.screen, grid_color, (0, y), (self.width, y), 1)
        
        # Corner brackets
        corner_size = 30
        corners = [(10, 10), (self.width-10, 10), (10, self.height-10), (self.width-10, self.height-10)]
        for (x, y) in corners:
            pygame.draw.line(self.screen, (0, 180, 255), (x-10, y), (x+10, y), 2)
            pygame.draw.line(self.screen, (0, 180, 255), (x, y-10), (x, y+10), 2)
    
    def _draw_robot_head(self, cx, cy):
        # Main head casing - metallic
        head_rect = pygame.Rect(cx - 200, cy - 170, 400, 340)
        
        # Metallic gradient effect
        for i in range(340):
            alpha = 100 + int(math.sin(i * 0.02) * 30)
            color = (150 + i % 30, 155 + i % 25, 160 + i % 35)
            pygame.draw.line(self.screen, color, 
                           (cx - 200, cy - 170 + i), (cx + 200, cy - 170 + i), 1)
        
        # Head outline with beveled edges
        pygame.draw.rect(self.screen, self.dark_metal, head_rect, 0, border_radius=20)
        pygame.draw.rect(self.screen, self.metal_color, head_rect, 4, border_radius=20)
        
        # Panel lines
        pygame.draw.line(self.screen, (80, 85, 90), 
                       (cx - 180, cy - 170), (cx - 180, cy + 170), 2)
        pygame.draw.line(self.screen, (80, 85, 90), 
                       (cx + 180, cy - 170), (cx + 180, cy + 170), 2)
        pygame.draw.line(self.screen, (80, 85, 90), 
                       (cx - 180, cy - 170), (cx + 180, cy - 170), 2)
        pygame.draw.line(self.screen, (80, 85, 90), 
                       (cx - 180, cy + 170), (cx + 180, cy + 170), 2)
        
        # Rivets/screws
        for x in [cx - 190, cx + 190]:
            for y in [cy - 160, cy, cy + 160]:
                pygame.draw.circle(self.screen, (100, 105, 110), (x, y), 5)
                pygame.draw.circle(self.screen, (60, 65, 70), (x, y), 3)
                pygame.draw.line(self.screen, (40, 45, 50), 
                               (x - 3, y), (x + 3, y), 1)
    
    def _draw_robot_eyes(self, cx, cy):
        eye_y = cy - 40
        left_eye = (cx - 80, eye_y)
        right_eye = (cx + 80, eye_y)
        
        # Blink mechanism
        self.blink_timer += 1
        if self.blink_timer > 140:
            self.blink_state = 10
            self.blink_timer = 0
        if self.blink_state > 0:
            self.blink_state -= 1
        
        # Eye sockets (recessed)
        pygame.draw.circle(self.screen, (30, 35, 45), left_eye, 50)
        pygame.draw.circle(self.screen, (30, 35, 45), right_eye, 50)
        pygame.draw.circle(self.screen, (40, 45, 55), left_eye, 48)
        pygame.draw.circle(self.screen, (40, 45, 55), right_eye, 48)
        
        if self.blink_state > 0:
            # Mechanical shutter blink
            shutter_y = eye_y - 50 + (10 - self.blink_state) * 10
            pygame.draw.rect(self.screen, self.dark_metal, 
                          (left_eye[0] - 50, shutter_y, 100, 100))
            pygame.draw.rect(self.screen, self.dark_metal, 
                          (right_eye[0] - 50, shutter_y, 100, 100))
        else:
            # LED eyes with glow
            for i in range(4):
                glow_color = (*self.eye_glow, 80 - i * 20)
                glow_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, glow_color, (60, 60), 45 - i * 8)
                self.screen.blit(glow_surf, (left_eye[0] - 60, left_eye[1] - 60))
                self.screen.blit(glow_surf, (right_eye[0] - 60, right_eye[1] - 60))
            
            # Main LED lenses
            pygame.draw.circle(self.screen, self.eye_glow, left_eye, 35)
            pygame.draw.circle(self.screen, self.eye_glow, right_eye, 35)
            
            # Lens reflection
            pygame.draw.circle(self.screen, (200, 240, 255), 
                             (left_eye[0] - 8, left_eye[1] - 8), 12)
            pygame.draw.circle(self.screen, (200, 240, 255), 
                             (right_eye[0] - 8, right_eye[1] - 8), 12)
            
            # LED grid pattern
            for offset in [(-15, -15), (15, -15), (-15, 15), (15, 15)]:
                pygame.draw.circle(self.screen, (0, 100, 150), 
                                 (left_eye[0] + offset[0], left_eye[1] + offset[1]), 3)
                pygame.draw.circle(self.screen, (0, 100, 150), 
                                 (right_eye[0] + offset[0], right_eye[1] + offset[1]), 3)
        
        # Eye casing
        pygame.draw.circle(self.screen, self.metal_color, left_eye, 52, 3)
        pygame.draw.circle(self.screen, self.metal_color, right_eye, 52, 3)
    
    def _draw_robot_mouth(self, cx, cy):
        mouth_y = cy + 100
        
        if self.current_expression == 'happy':
            # Smile LED strip
            for i in range(-50, 51, 5):
                height = int(math.sqrt(2500 - i**2)) if abs(i) < 50 else 0
                color = (*self.led_color, 150 - abs(i))
                surf = pygame.Surface((3, height), pygame.SRCALPHA)
                surf.fill(color)
                self.screen.blit(surf, (cx + i - 1, mouth_y - height))
        elif self.current_expression == 'alert':
            # Flashing red alert
            self.alert_pulse = (self.alert_pulse + 1) % 20
            if self.alert_pulse < 10:
                alert_color = (255, 50, 50)
                pygame.draw.rect(self.screen, alert_color, 
                               (cx - 60, mouth_y - 10, 120, 20), 0, 5)
                pygame.draw.rect(self.screen, (255, 100, 100), 
                               (cx - 55, mouth_y - 5, 110, 10), 0, 3)
        elif self.current_expression == 'scanning':
            # Scanning line
            self.scan_angle = (self.scan_angle + 3) % 360
            scan_x = cx + int(math.cos(math.radians(self.scan_angle)) * 60)
            pygame.draw.line(self.screen, (0, 255, 255), 
                           (cx, mouth_y), (scan_x, mouth_y - 30), 3)
        elif self.current_expression == 'speaking':
            # Audio waveform
            for i in range(-40, 41, 8):
                h = 10 + int(math.sin(self.anim_frame * 0.2 + i * 0.3) * 15)
                pygame.draw.line(self.screen, self.led_color, 
                               (cx + i, mouth_y), (cx + i, mouth_y - h), 4)
        elif self.current_expression == 'listening':
            # Wave pattern
            for i in range(5):
                x = cx - 40 + i * 20
                h = 15 + int(math.sin(self.anim_frame * 0.1 + i) * 10)
                pygame.draw.line(self.screen, (180, 50, 255), 
                               (x, mouth_y), (x, mouth_y - h), 3)
        else:
            # Neutral LED line
            pygame.draw.rect(self.screen, (40, 45, 55), 
                           (cx - 70, mouth_y - 8, 140, 16), 0, 5)
            pygame.draw.line(self.screen, self.led_color, 
                           (cx - 50, mouth_y), (cx + 50, mouth_y), 4)
        
        # Mouth grill
        for i in range(-60, 61, 10):
            pygame.draw.line(self.screen, (60, 65, 70), 
                           (cx + i, mouth_y - 15), (cx + i, mouth_y + 15), 1)
    
    def _draw_antenna_array(self, cx, cy):
        # Main antenna
        antenna_base = (cx, cy - 170)
        pygame.draw.rect(self.screen, self.dark_metal, 
                        (cx - 8, cy - 200, 16, 30))
        pygame.draw.line(self.screen, self.metal_color, 
                       (cx, cy - 200), (cx, cy - 230), 4)
        
        # Antenna tip LED
        pulse = int(math.sin(self.anim_frame * 0.05) * 5 + 8)
        pygame.draw.circle(self.screen, (0, 255, 100), antenna_base, pulse)
        pygame.draw.circle(self.screen, (200, 255, 220), antenna_base, 3)
        
        # Side sensors
        for side in [-1, 1]:
            sensor_x = cx + side * 180
            sensor_y = cy - 150
            pygame.draw.circle(self.screen, (40, 45, 55), (sensor_x, sensor_y), 15)
            pygame.draw.circle(self.screen, (0, 180, 255), (sensor_x, sensor_y), 8)
    
    def _draw_hud_overlay(self, cx):
        # System status indicators
        indicators = [
            ('SYS', (0, 255, 100)),
            ('AI', (0, 180, 255)),
            ('NET', (180, 50, 255)),
        ]
        
        for i, (label, color) in enumerate(indicators):
            x = cx - 250 + i * 80
            y = 30
            
            # LED indicator
            pulse = int(math.sin(self.anim_frame * 0.1 + i) * 3 + 5)
            pygame.draw.circle(self.screen, color, (x, y), pulse)
            pygame.draw.circle(self.screen, (40, 40, 50), (x, y), pulse + 2, 1)
            
            # Label
            if self.micro_font:
                label_surf = self.micro_font.render(label, True, color)
                self.screen.blit(label_surf, (x - 12, y + 10))
    
    def _draw_status_panel(self):
        # Bottom status bar
        panel_rect = pygame.Rect(0, self.height - 60, self.width, 60)
        pygame.draw.rect(self.screen, (20, 25, 35), panel_rect)
        pygame.draw.line(self.screen, self.led_color, 
                       (0, self.height - 60), (self.width, self.height - 60), 2)
        
        # Status text
        if self.small_font:
            text_surface = self.small_font.render(self.status_text, True, (220, 230, 240))
            self.screen.blit(text_surface, (20, self.height - 45))
        
        # Expression indicator
        if self.micro_font:
            expr_text = f"MODE: {self.current_expression.upper()}"
            expr_surface = self.micro_font.render(expr_text, True, self.led_color)
            self.screen.blit(expr_surface, 
                           (self.width - expr_surface.get_width() - 20, self.height - 45))
        
        # Decorative elements
        for i in range(8):
            x = 100 + i * 80
            color = self.led_color if i < 3 else (40, 45, 60)
            pygame.draw.circle(self.screen, color, (x, self.height - 15), 4)
    
    def cleanup(self):
        self.running = False
        if PYGAME_AVAILABLE:
            try:
                pygame.quit()
            except:
                pass
        logger.info("Display cleanup complete")

display_controller = DisplayController()
