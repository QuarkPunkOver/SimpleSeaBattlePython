import pygame
import random
import sys
import threading
from config import WINDOW_WIDTH, WINDOW_HEIGHT, Debug_status, FIELD_SIZE, CELL_SIZE, FIELD_WIDTH, FIELD_HEIGHT
from enums import GameState, BotDifficulty, CellState
from game_field import GameField
from ui import Button, ShipTemplate, ShipPlacer
from network import NetworkGame
from theme import theme

class SeaBattle:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Морской бой")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 32)
        
        self.state = GameState.MENU
        self.player_field = GameField(300, 150)
        self.enemy_field = GameField(800, 150)
        self.ship_placer = ShipPlacer()
        self.network = NetworkGame()
        self.game_mode = None
        self.my_turn = False
        self.game_over_message = ""
        self.servers = []
        self.scan_progress = 0
        self.scan_total = 0
        self.scanning = False
        self.scan_thread = None
        self.server_list_buttons = []
        self.refresh_button = None
        self.direct_connect_button = None
        self.back_button = None
        self.bot_timer = 0
        self.bot_thinking = False
        self.ship_templates = []
        self.player_ready = False
        self.opponent_ready = False
        self.opponent_ships_received = False
        self.sent_ships_to_client = False
        self.last_send_time = 0
        self.game_over_buttons = []
        
        self.bot_difficulty = BotDifficulty.MEDIUM
        self.settings_buttons = []
        self.difficulty_buttons = []
        self.back_to_menu_button = None

        self.error_message = ""
        self.error_timer = 0
        self.debug_mode = False

        self.direct_connect_ip = ""
        self.direct_connect_active = False
        
        self.create_menu_buttons()
        self.create_settings_buttons()
        self.create_preparation_buttons()
        self.create_server_list_buttons()
        self.create_direct_connect_buttons()
        self.create_ship_templates()
    
    def debug_print(self, message):
        if self.debug_mode:
            print(f"[DEBUG] {message}")
    
    def create_ship_templates(self):
        x_start = 1100
        y_start = 200
        sizes = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
        
        for size in sorted(set(sizes), reverse=True):
            template = ShipTemplate(size, x_start, y_start, True)
            template.count = sizes.count(size)
            self.ship_templates.append(template)
            y_start += 70
    
    def reset_ship_templates(self):
        sizes = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
        for template in self.ship_templates:
            template.count = sizes.count(template.size)
    
    def create_direct_connect_buttons(self):
        self.dc_input_rect = pygame.Rect(WINDOW_WIDTH//2 - 200, 250, 400, 50)
        self.dc_connect_btn = Button(WINDOW_WIDTH//2 - 150, 350, 300, 50, "Подключиться", "button", "button_hover")
        self.dc_back_btn = Button(WINDOW_WIDTH//2 - 150, 420, 300, 50, "Назад", "button", "button_hover")
    
    def draw_direct_connect(self):
        colors = theme.colors
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(colors["overlay"])
        self.screen.blit(overlay, (0,0))
        
        title = self.font.render("Прямое подключение", True, colors["title"])
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 150))
        self.screen.blit(title, title_rect)
        
        pygame.draw.rect(self.screen, colors["bg"], self.dc_input_rect, border_radius=5)
        pygame.draw.rect(self.screen, colors["field_border"], self.dc_input_rect, 2, border_radius=5)
        ip_surface = self.small_font.render(self.direct_connect_ip, True, colors["text"])
        self.screen.blit(ip_surface, (self.dc_input_rect.x + 5, self.dc_input_rect.y + 10))
        
        if not self.direct_connect_active and not self.direct_connect_ip:
            hint = self.small_font.render("Введите IP (например, 192.168.1.10)", True, colors["disabled_text"])
            self.screen.blit(hint, (self.dc_input_rect.x + 5, self.dc_input_rect.y + 10))
        
        self.dc_connect_btn.draw(self.screen)
        self.dc_back_btn.draw(self.screen)
    
    def create_settings_buttons(self):
        y_start = 250
        difficulties = [
            (BotDifficulty.EASY, "Легкий", 0),
            (BotDifficulty.MEDIUM, "Средний", 1),
            (BotDifficulty.HARD, "Сложный", 2)
        ]
        
        for difficulty, text, index in difficulties:
            btn = Button(WINDOW_WIDTH//2 - 150, y_start + index * 70, 300, 50, 
                        text, "button", "button_hover")
            self.difficulty_buttons.append((difficulty, btn))
        
        self.back_to_menu_button = Button(WINDOW_WIDTH//2 - 150, 550, 300, 50, 
                                         "Назад", "button", "button_hover")
        
    def create_menu_buttons(self):
        self.menu_buttons = [
            Button(WINDOW_WIDTH//2 - 150, 250, 300, 60, "Против бота", "button", "button_hover"),
            Button(WINDOW_WIDTH//2 - 150, 330, 300, 60, "Создать игру", "button", "button_hover"),
            Button(WINDOW_WIDTH//2 - 150, 410, 300, 60, "Найти игру", "button", "button_hover"),
            Button(WINDOW_WIDTH//2 - 150, 490, 300, 60, "Настройки", "button", "button_hover"),
            Button(WINDOW_WIDTH//2 - 150, 570, 300, 60, "Выход", "button", "button_hover")
        ]
        
    def create_preparation_buttons(self):
        self.prep_buttons = [
            Button(100, 50, 150, 40, "Рандом", "button", "button_hover"),
            Button(270, 50, 150, 40, "Сброс", "button", "button_hover"),
            Button(440, 50, 150, 40, "Готово", "button", "button_hover"),
            Button(WINDOW_WIDTH - 250, 50, 150, 40, "Назад", "button", "button_hover")
        ]
        
    def create_game_over_buttons(self):
        self.game_over_buttons = [
            Button(WINDOW_WIDTH//2 - 150, 450, 300, 60, "В меню", "button", "button_hover"),
            Button(WINDOW_WIDTH//2 - 150, 530, 300, 60, "Выход", "button", "button_hover")
        ]
    
    def create_server_list_buttons(self):
        self.server_list_buttons = []
        y = 200
        for i in range(5):
            btn = Button(300, y, 600, 50, "", "button", "button_hover")
            self.server_list_buttons.append(btn)
            y += 70
        
        self.refresh_button = Button(WINDOW_WIDTH//2 - 150, 600, 300, 50, "Найти серверы", "button", "button_hover")
        self.direct_connect_button = Button(WINDOW_WIDTH//2 - 150, 660, 300, 50, "Прямое подключение", "button", "button_hover")
        self.back_button = Button(WINDOW_WIDTH//2 - 150, 720, 300, 50, "Назад", "button", "button_hover")
    
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.handle_event(event)
            
            self.update(dt)
            self.draw()
            pygame.display.flip()
        
        if self.network.is_server:
            self.network.stop()
        pygame.quit()
        sys.exit()
    
    def handle_event(self, event):
        if self.state == GameState.MENU:
            self.handle_menu_event(event)
        elif self.state == GameState.SETTINGS:
            self.handle_settings_event(event)
        elif self.state == GameState.WAITING_CONNECTION:
            self.handle_waiting_connection_event(event)
        elif self.state == GameState.SERVER_LIST:
            self.handle_server_list_event(event)
        elif self.state == GameState.DIRECT_CONNECT:
            self.handle_direct_connect_event(event)
        elif self.state == GameState.PREPARATION:
            self.handle_preparation_event(event)
        elif self.state == GameState.BATTLE:
            self.handle_battle_event(event)
        elif self.state == GameState.WAITING_PLAYER:
            self.handle_waiting_event(event)
        elif self.state == GameState.GAME_OVER:
            self.handle_game_over_event(event)
    
    def handle_menu_event(self, event):
        for i, button in enumerate(self.menu_buttons):
            if button.handle_event(event):
                if i == 0:
                    self.game_mode = "bot"
                    self.state = GameState.PREPARATION
                    self.player_field.clear()
                    self.reset_ship_templates()
                    self.sent_ships_to_client = False
                elif i == 1:
                    self.game_mode = "network"
                    self.network.start_server()
                    self.state = GameState.WAITING_CONNECTION
                    self.sent_ships_to_client = False
                elif i == 2:
                    self.state = GameState.SERVER_LIST
                    self.servers = []
                    self.scanning = False
                    self.sent_ships_to_client = False
                    self.scan_for_servers()
                elif i == 3:
                    self.state = GameState.SETTINGS
                elif i == 4:
                    pygame.quit()
                    sys.exit()
    
    def handle_settings_event(self, event):
        for difficulty, button in self.difficulty_buttons:
            if button.handle_event(event):
                self.bot_difficulty = difficulty
        
        if self.back_to_menu_button and self.back_to_menu_button.handle_event(event):
            self.state = GameState.MENU
    
    def handle_waiting_connection_event(self, event):
        msg = self.network.get_message()
        if msg:
            pass
        
        if self.network.connected:
            self.state = GameState.PREPARATION
            self.player_field.clear()
            self.reset_ship_templates()
            return
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = GameState.MENU
            self.network.stop()
    
    def handle_direct_connect_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.dc_input_rect.collidepoint(event.pos):
                self.direct_connect_active = True
            else:
                self.direct_connect_active = False
            
            if self.dc_connect_btn.handle_event(event):
                if self.direct_connect_ip:
                    if self.network.connect(self.direct_connect_ip):
                        self.game_mode = "network"
                        self.state = GameState.PREPARATION
                        self.player_field.clear()
                        self.reset_ship_templates()
                        self.player_ready = False
                        self.opponent_ready = False
                        self.opponent_ships_received = False
                    else:
                        self.direct_connect_ip = ""
                        self.error_message = "Ошибка подключения"
                        self.error_timer = pygame.time.get_ticks() + 3000
            
            if self.dc_back_btn.handle_event(event):
                self.state = GameState.SERVER_LIST
                self.direct_connect_ip = ""
                self.direct_connect_active = False
        
        elif event.type == pygame.KEYDOWN and self.direct_connect_active:
            if event.key == pygame.K_BACKSPACE:
                self.direct_connect_ip = self.direct_connect_ip[:-1]
            elif event.key == pygame.K_RETURN:
                if self.direct_connect_ip and self.network.connect(self.direct_connect_ip):
                    self.game_mode = "network"
                    self.state = GameState.PREPARATION
                    self.player_field.clear()
                    self.reset_ship_templates()
                    self.player_ready = False
                    self.opponent_ready = False
                    self.opponent_ships_received = False
            else:
                if event.unicode in "0123456789.":
                    self.direct_connect_ip += event.unicode
    
    def scan_for_servers(self):
        if self.scanning:
            return
            
        self.scanning = True
        self.servers = []
        self.scan_progress = 0
        self.scan_total = 254
        
        def scan_thread():
            self.servers = self.network.scan_network(self.update_scan_progress)
            self.scanning = False
            self.update_server_buttons()
        
        self.scan_thread = threading.Thread(target=scan_thread)
        self.scan_thread.daemon = True
        self.scan_thread.start()
    
    def update_scan_progress(self, scanned, total):
        self.scan_progress = scanned
        self.scan_total = total
        
    def update_server_buttons(self):
        for i, button in enumerate(self.server_list_buttons):
            if i < len(self.servers):
                server = self.servers[i]
                players = server['players']
                max_players = server['max_players']
                
                status = "СВОБОДЕН" if players < max_players else "ПОЛНЫЙ"
                button.text = f"{server['name']} ({server['ip']}) - {players}/{max_players} {status}"
                
                button.disabled = (players >= max_players)
            else:
                button.text = ""
                button.disabled = False
            
    def handle_server_list_event(self, event):
        if self.refresh_button and self.refresh_button.handle_event(event):
            self.scan_for_servers()
        
        if self.direct_connect_button and self.direct_connect_button.handle_event(event):
            self.state = GameState.DIRECT_CONNECT
            self.direct_connect_ip = ""
            self.direct_connect_active = True
        
        if self.back_button and self.back_button.handle_event(event):
            self.state = GameState.MENU
        
        for i, button in enumerate(self.server_list_buttons):
            if button.handle_event(event) and i < len(self.servers) and not button.disabled:
                server = self.servers[i]
                
                if self.network.connect(server['ip']):
                    self.game_mode = "network"
                    self.state = GameState.PREPARATION
                    self.player_field.clear()
                    self.reset_ship_templates()
                    self.player_ready = False
                    self.opponent_ready = False
                    self.opponent_ships_received = False
                else:
                    self.error_message = f"Не удалось подключиться к {server['ip']}"
                    self.error_timer = pygame.time.get_ticks() + 3000
    
    def handle_waiting_event(self, event):
        messages_received = False
        while True:
            msg = self.network.get_message()
            if not msg:
                break
                
            messages_received = True
            
            if msg["type"] == "ready":
                if "ships" in msg:
                    self.enemy_field.load_ships_data(msg["ships"])
                    self.opponent_ships_received = True
                    self.opponent_ready = True
                    
                    if self.network.is_server and self.player_ready and not hasattr(self, 'sent_ships'):
                        ships_data = self.player_field.get_ships_data()
                        self.network.send_data({"type": "ready", "ships": ships_data})
                        self.sent_ships = True
        
        if self.player_ready and self.opponent_ready and self.opponent_ships_received:
            self.start_network_battle()
            return
        
        if not self.network.is_server and self.player_ready and not self.opponent_ships_received:
            current_time = pygame.time.get_ticks()
            if not hasattr(self, 'last_ship_send') or current_time - self.last_ship_send > 3000:
                self.last_ship_send = current_time
                ships_data = self.player_field.get_ships_data()
                self.network.send_data({"type": "ready", "ships": ships_data})
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = GameState.MENU
            self.network.stop()
    
    def start_network_battle(self):
        self.state = GameState.BATTLE
        self.my_turn = self.network.is_server
        
    def handle_preparation_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and self.ship_placer.dragging:
                self.ship_placer.rotate_ship()
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for template in self.ship_templates:
                    if template.rect.collidepoint(event.pos) and template.count > 0:
                        self.ship_placer.start_drag_from_template(template, event.pos, self.player_field)
                        return
                
                self.ship_placer.start_drag_from_field(event.pos, self.player_field)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.ship_placer.end_drag(event.pos, self.player_field, self.ship_templates)
        
        elif event.type == pygame.MOUSEMOTION:
            if self.ship_placer.dragging:
                self.ship_placer.update_drag(event.pos, self.player_field)
        
        for button in self.prep_buttons:
            if button.handle_event(event):
                if button.text == "Рандом":
                    self.player_field.randomize_ships()
                    for template in self.ship_templates:
                        template.count = 0
                
                elif button.text == "Сброс":
                    self.player_field.clear()
                    self.reset_ship_templates()
                
                elif button.text == "Готово":
                    error = self.player_field.get_fleet_error()
                    if error == "OK":
                        if self.game_mode == "bot":
                            self.start_battle()
                        
                        elif self.game_mode == "network":
                            self.player_ready = True
                            
                            ships_data = self.player_field.get_ships_data()
                            self.network.send_data({"type": "ready", "ships": ships_data})
                            
                            self.state = GameState.WAITING_PLAYER
                            self.last_ship_send = pygame.time.get_ticks()
                    else:
                        self.error_message = error
                        self.error_timer = pygame.time.get_ticks() + 5000
                
                elif button.text == "Назад":
                    self.state = GameState.MENU
                    if self.network.is_server:
                        self.network.stop()
                    self.player_field.clear()
                    self.reset_ship_templates()
                    self.player_ready = False
                    self.opponent_ready = False
                    self.opponent_ships_received = False
    
    def start_battle(self):
        if self.game_mode == "bot":
            self.enemy_field.randomize_ships()
            self.my_turn = random.choice([True, False])
            self.bot_thinking = not self.my_turn
            self.bot_timer = pygame.time.get_ticks() + 500
            self.state = GameState.BATTLE
            if self.debug_mode:
                print(f"[DEBUG] Битва с ботом началась. Первый ход у {'игрока' if self.my_turn else 'бота'}")
    
    def bot_turn(self):
        if not self.bot_thinking or self.my_turn:
            return
            
        available = []
        for r in range(FIELD_SIZE):
            for c in range(FIELD_SIZE):
                if self.player_field.grid[r][c] not in [CellState.HIT, CellState.MISS, CellState.DESTROYED]:
                    available.append((r, c))
        
        if available:
            if self.bot_difficulty == BotDifficulty.EASY:
                row, col = random.choice(available)
            elif self.bot_difficulty == BotDifficulty.MEDIUM:
                hit_nearby = []
                for r, c in available:
                    for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < FIELD_SIZE and 0 <= nc < FIELD_SIZE:
                            if self.player_field.grid[nr][nc] == CellState.HIT:
                                hit_nearby.append((r, c))
                                break
                
                if hit_nearby and random.random() < 0.7:
                    row, col = random.choice(hit_nearby)
                else:
                    row, col = random.choice(available)
            else:
                hit_nearby = []
                for r, c in available:
                    for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < FIELD_SIZE and 0 <= nc < FIELD_SIZE:
                            if self.player_field.grid[nr][nc] == CellState.HIT:
                                hit_nearby.append((r, c))
                                break
                
                if hit_nearby:
                    row, col = random.choice(hit_nearby)
                else:
                    center = [(r, c) for r, c in available if 3 <= r <= 6 and 3 <= c <= 6]
                    if center and random.random() < 0.6:
                        row, col = random.choice(center)
                    else:
                        row, col = random.choice(available)
            
            result = self.player_field.receive_shot(row, col)
            self.debug_print(f"Бот стреляет по [{row},{col}]: {'Попадание' if result else 'Промах'}")
            
            if result:
                self.bot_thinking = True
                self.my_turn = False
                self.bot_timer = pygame.time.get_ticks() + 500
                self.debug_print("Бот продолжает ход (попадание)")
            else:
                self.bot_thinking = False
                self.my_turn = True
                self.debug_print("Ход переходит к игроку")
    
    def handle_battle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.my_turn:
                pos = event.pos
                if (self.enemy_field.x <= pos[0] < self.enemy_field.x + FIELD_WIDTH and
                    self.enemy_field.y <= pos[1] < self.enemy_field.y + FIELD_HEIGHT):
                    
                    col = (pos[0] - self.enemy_field.x) // CELL_SIZE
                    row = (pos[1] - self.enemy_field.y) // CELL_SIZE
                    
                    if self.game_mode == "bot":
                        if self.enemy_field.grid[row][col] not in [CellState.HIT, CellState.MISS, CellState.DESTROYED]:
                            result = self.enemy_field.receive_shot(row, col)
                            if result is not None:
                                self.debug_print(f"Выстрел по [{row},{col}]: {'Попадание' if result else 'Промах'}")
                                
                                if result:
                                    self.my_turn = True
                                    self.bot_thinking = False
                                    self.debug_print("Игрок продолжает ход (попадание)")
                                else:
                                    self.my_turn = False
                                    self.bot_thinking = True
                                    self.bot_timer = pygame.time.get_ticks() + 500
                                    self.debug_print("Ход переходит к боту")
                    else:
                        if self.enemy_field.grid[row][col] not in [CellState.HIT, CellState.MISS, CellState.DESTROYED]:
                            self.network.send_data({"type": "shot", "row": row, "col": col})
                            self.my_turn = False
    
    def handle_game_over_event(self, event):
        for button in self.game_over_buttons:
            if button.handle_event(event):
                if button.text == "В меню":
                    self.state = GameState.MENU
                    if self.network.is_server:
                        self.network.stop()
                    self.player_ready = False
                    self.opponent_ready = False
                    self.opponent_ships_received = False
                elif button.text == "Выход":
                    pygame.quit()
                    sys.exit()
    
    def update(self, dt):
        if self.state == GameState.WAITING_PLAYER and self.game_mode == "network":
            if self.player_ready and self.opponent_ships_received:
                self.start_network_battle()

            if self.state == GameState.BATTLE and self.game_mode == "bot":
                if self.bot_thinking and not self.my_turn:
                    if pygame.time.get_ticks() >= self.bot_timer:
                        self.bot_turn()

            if not self.network.is_server and self.player_ready and not self.opponent_ready:
                if pygame.time.get_ticks() % 3000 < 50:
                    ships_data = self.player_field.get_ships_data()
                    self.network.send_data({"type": "ready", "ships": ships_data})
        
        if self.state == GameState.BATTLE and self.game_mode == "network":
            msg = self.network.get_message()
            if msg:
                if msg["type"] == "shot":
                    row, col = msg["row"], msg["col"]
                    result = self.player_field.receive_shot(row, col)
                    self.network.send_data({"type": "result", "hit": result, "row": row, "col": col})
                    if not result:
                        self.my_turn = True
                    else:
                        self.my_turn = False
                elif msg["type"] == "result":
                    if msg["hit"]:
                        self.enemy_field.receive_shot(msg["row"], msg["col"])
                        self.my_turn = True
                    else:
                        self.enemy_field.receive_shot(msg["row"], msg["col"])
                        self.my_turn = False
        
        if self.state == GameState.BATTLE and self.game_mode == "bot" and self.bot_thinking:
            if pygame.time.get_ticks() >= self.bot_timer:
                self.bot_turn()
        
        if self.state == GameState.BATTLE:
            if self.enemy_field.all_ships_destroyed():
                self.game_over_message = "Победа!"
                self.state = GameState.GAME_OVER
                self.create_game_over_buttons()
            elif self.player_field.all_ships_destroyed():
                self.game_over_message = "Поражение!"
                self.state = GameState.GAME_OVER
                self.create_game_over_buttons()

    def draw(self):
        colors = theme.colors
        self.screen.fill(colors["bg"])
        
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.SETTINGS:
            self.draw_settings()
        elif self.state == GameState.SERVER_LIST:
            self.draw_server_list()
        elif self.state == GameState.PREPARATION:
            self.draw_preparation()
        elif self.state == GameState.BATTLE:
            self.draw_battle()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()
        elif self.state == GameState.WAITING_PLAYER:
            self.draw_waiting()
        elif self.state == GameState.DIRECT_CONNECT:
            self.draw_direct_connect()
        elif self.state == GameState.WAITING_CONNECTION:
            self.draw_waiting_connection()
    
    def draw_menu(self):
        colors = theme.colors
        title = self.font.render("МОРСКОЙ БОЙ", True, colors["title"])
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 150))
        self.screen.blit(title, title_rect)
        
        for button in self.menu_buttons:
            button.draw(self.screen)
        
        local_ip = self.network.get_local_ip()
        ip_text = self.small_font.render(f"Ваш IP: {local_ip}", True, colors["dark_gray"])
        ip_rect = ip_text.get_rect(center=(WINDOW_WIDTH//2, 650))
        self.screen.blit(ip_text, ip_rect)
        
        if self.debug_mode:
            debug_text = self.small_font.render("РЕЖИМ ОТЛАДКИ ВКЛЮЧЕН", True, colors["hit"])
            debug_rect = debug_text.get_rect(center=(WINDOW_WIDTH//2, 700))
            self.screen.blit(debug_text, debug_rect)
    
    def draw_settings(self):
        colors = theme.colors
        title = self.font.render("НАСТРОЙКИ", True, colors["title"])
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 150))
        self.screen.blit(title, title_rect)
        
        diff_title = self.small_font.render("Сложность бота:", True, colors["text"])
        diff_rect = diff_title.get_rect(center=(WINDOW_WIDTH//2, 210))
        self.screen.blit(diff_title, diff_rect)
        
        for difficulty, button in self.difficulty_buttons:
            if difficulty == self.bot_difficulty:
                original_color = button.color_key
                button.color_key = "gold"
                button.draw(self.screen)
                button.color_key = original_color
            else:
                button.draw(self.screen)
        
        self.back_to_menu_button.draw(self.screen)
    
    def draw_server_list(self):
        colors = theme.colors
        title = self.font.render("Доступные серверы", True, colors["title"])
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 100))
        self.screen.blit(title, title_rect)

        if self.scanning:
            text = self.small_font.render(f"Сканирование сети... {self.scan_progress}/{self.scan_total}", 
                                         True, colors["text"])
            text_rect = text.get_rect(center=(WINDOW_WIDTH//2, 300))
            self.screen.blit(text, text_rect)
            
            bar_width = 400
            bar_height = 20
            bar_x = WINDOW_WIDTH//2 - bar_width//2
            bar_y = 350
            
            pygame.draw.rect(self.screen, colors["gray"], (bar_x, bar_y, bar_width, bar_height), border_radius=5)
            if self.scan_total > 0:
                progress = (self.scan_progress / self.scan_total) * bar_width
                pygame.draw.rect(self.screen, colors["ship"], (bar_x, bar_y, progress, bar_height), border_radius=5)
        else:
            if self.servers:
                for i, button in enumerate(self.server_list_buttons):
                    if i < len(self.servers):
                        button.draw(self.screen)
            else:
                text = self.small_font.render("Серверы не найдены. Нажмите 'Найти серверы' для поиска", True, colors["disabled_text"])
                text_rect = text.get_rect(center=(WINDOW_WIDTH//2, 300))
                self.screen.blit(text, text_rect)

            if self.refresh_button:
                self.refresh_button.draw(self.screen)
            if self.direct_connect_button:
                self.direct_connect_button.draw(self.screen)
            if self.back_button:
                self.back_button.draw(self.screen)
    
    def draw_waiting(self):
        colors = theme.colors
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(colors["overlay"])
        self.screen.blit(overlay, (0, 0))
        
        status_text = "Ожидание противника..."
        if self.player_ready and not self.opponent_ready:
            status_text = "Ожидание готовности противника..."
        elif self.opponent_ready and not self.player_ready:
            status_text = "Противник готов! Нажмите Готово"
        elif self.player_ready and self.opponent_ready and not self.opponent_ships_received:
            status_text = "Получение данных о кораблях..."
        
        player_status = "ГОТОВ" if self.player_ready else "НЕ ГОТОВ"
        opponent_status = "ГОТОВ" if self.opponent_ready else "НЕ ГОТОВ"
        
        text1 = self.font.render(status_text, True, colors["text"])
        text2 = self.small_font.render(f"Вы: {player_status}", True, colors["text"])
        text3 = self.small_font.render(f"Противник: {opponent_status}", True, colors["text"])
        text4 = self.small_font.render("Нажмите ESC для отмены", True, colors["text"])
        
        text_rect = text1.get_rect(center=(WINDOW_WIDTH//2, 250))
        self.screen.blit(text1, text_rect)
        text_rect = text2.get_rect(center=(WINDOW_WIDTH//2, 320))
        self.screen.blit(text2, text_rect)
        text_rect = text3.get_rect(center=(WINDOW_WIDTH//2, 360))
        self.screen.blit(text3, text_rect)
        text_rect = text4.get_rect(center=(WINDOW_WIDTH//2, 420))
        self.screen.blit(text4, text_rect)
    
    def draw_waiting_connection(self):
        colors = theme.colors
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(colors["overlay"])
        self.screen.blit(overlay, (0, 0))
        
        text1 = self.font.render("Ожидание подключения игрока...", True, colors["text"])
        text2 = self.small_font.render(f"Ваш IP: {self.network.get_local_ip()}", True, colors["text"])
        text3 = self.small_font.render("Порт: 5555", True, colors["text"])
        text4 = self.small_font.render("Нажмите ESC для отмены", True, colors["text"])
        
        text_rect = text1.get_rect(center=(WINDOW_WIDTH//2, 250))
        self.screen.blit(text1, text_rect)
        text_rect = text2.get_rect(center=(WINDOW_WIDTH//2, 320))
        self.screen.blit(text2, text_rect)
        text_rect = text3.get_rect(center=(WINDOW_WIDTH//2, 360))
        self.screen.blit(text3, text_rect)
        text_rect = text4.get_rect(center=(WINDOW_WIDTH//2, 420))
        self.screen.blit(text4, text_rect)
    
    def draw_preparation(self):
        colors = theme.colors
        if self.game_mode == "network" and self.network.is_server:
            title = self.small_font.render("Расставьте корабли (Вы - сервер)", True, colors["text"])
        else:
            title = self.small_font.render("Расставьте корабли", True, colors["text"])
        
        title_x = (WINDOW_WIDTH - title.get_width()) // 2
        self.screen.blit(title, (title_x, 20))

        if self.error_message and pygame.time.get_ticks() < self.error_timer:
            s = pygame.Surface((800, 80))
            s.set_alpha(220)
            s.fill(colors["error_bg"])
            self.screen.blit(s, (WINDOW_WIDTH//2 - 400, 100))
            
            if len(self.error_message) > 50:
                parts = self.error_message.split("нужно:")
                if len(parts) > 1:
                    line1 = parts[0] + "нужно:"
                    line2 = parts[1]
                    text1 = self.small_font.render(line1, True, colors["error_text"])
                    text2 = self.small_font.render(line2, True, colors["error_text"])
                    text1_rect = text1.get_rect(center=(WINDOW_WIDTH//2, 115))
                    text2_rect = text2.get_rect(center=(WINDOW_WIDTH//2, 145))
                    self.screen.blit(text1, text1_rect)
                    self.screen.blit(text2, text2_rect)
            else:
                text = self.small_font.render(self.error_message, True, colors["error_text"])
                text_rect = text.get_rect(center=(WINDOW_WIDTH//2, 140))
                self.screen.blit(text, text_rect)
        
        for button in self.prep_buttons:
            button.draw(self.screen)
        
        self.player_field.draw(self.screen, show_ships=True)
        
        panel_bg = pygame.Surface((250, 500))
        panel_bg.set_alpha(30)
        panel_bg.fill(colors["gray"])
        self.screen.blit(panel_bg, (1080, 150))
        
        ships_title = self.small_font.render("Доступные корабли:", True, colors["text"])
        self.screen.blit(ships_title, (1080, 120))
        
        for template in self.ship_templates:
            template.draw(self.screen)
        
        self.ship_placer.draw_preview(self.screen, self.player_field)
        
        instructions = [
            "Перетаскивайте корабли из правой панели",
            "Нажмите R при перетаскивании для поворота",
            f"Осталось кораблей: {sum(t.count for t in self.ship_templates)}"
        ]
        y = 700
        for instruction in instructions:
            text = self.small_font.render(instruction, True, colors["disabled_text"])
            self.screen.blit(text, (100, y))
            y += 30
    
    def draw_battle(self):
        colors = theme.colors
        player_title = self.small_font.render("Ваше поле", True, colors["text"])
        enemy_title = self.small_font.render("Поле противника", True, colors["text"])
        
        player_title_x = self.player_field.x + (FIELD_WIDTH - player_title.get_width()) // 2
        enemy_title_x = self.enemy_field.x + (FIELD_WIDTH - enemy_title.get_width()) // 2
        
        self.screen.blit(player_title, (player_title_x, self.player_field.y - 30))
        self.screen.blit(enemy_title, (enemy_title_x, self.enemy_field.y - 30))
        
        self.player_field.draw(self.screen, show_ships=True)
        self.enemy_field.draw(self.screen, show_ships=Debug_status)
        
        if self.game_mode == "bot":
            if self.my_turn:
                turn_text = self.font.render("Ваш ход", True, colors["ship"])
            else:
                turn_text = self.font.render("Ход бота...", True, colors["hit"])
        else:
            if self.my_turn:
                turn_text = self.font.render("Ваш ход", True, colors["ship"])
            else:
                turn_text = self.font.render("Ход противника", True, colors["hit"])
                
        turn_rect = turn_text.get_rect(center=(WINDOW_WIDTH//2, 50))
        self.screen.blit(turn_text, turn_rect)
    
    def draw_game_over(self):
        colors = theme.colors
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(colors["overlay"])
        self.screen.blit(overlay, (0, 0))
        
        game_over_text = self.font.render(self.game_over_message, True, colors["text"])
        text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH//2, 300))
        self.screen.blit(game_over_text, text_rect)
        
        for button in self.game_over_buttons:
            button.draw(self.screen)