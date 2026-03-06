import pygame
from config import CELL_SIZE, BUTTON_RADIUS, FIELD_WIDTH, FIELD_HEIGHT
from theme import theme

class Button:
    def __init__(self, x, y, width, height, text, color_key, hover_color_key, text_color_key="button_text", disabled=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color_key = color_key
        self.hover_color_key = hover_color_key
        self.text_color_key = text_color_key
        self.is_hovered = False
        self.disabled = disabled
        self.font = pygame.font.Font(None, 36)
        
    def draw(self, screen):
        colors = theme.colors
        if self.disabled:
            color = colors["disabled"]
            text_color = colors["disabled_text"]
        else:
            color = colors[self.hover_color_key] if self.is_hovered else colors[self.color_key]
            text_color = colors[self.text_color_key]
        
        pygame.draw.rect(screen, color, self.rect, border_radius=BUTTON_RADIUS)
        pygame.draw.rect(screen, colors["field_border"], self.rect, 2, border_radius=BUTTON_RADIUS)
        
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def handle_event(self, event):
        if self.disabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False

class ShipTemplate:
    def __init__(self, size, x, y, horizontal=True):
        self.size = size
        self.x = x
        self.y = y
        self.horizontal = horizontal
        self.dragging = False
        if horizontal:
            self.rect = pygame.Rect(x, y, size * CELL_SIZE, CELL_SIZE)
        else:
            self.rect = pygame.Rect(x, y, CELL_SIZE, size * CELL_SIZE)
        self.count = 0
        self.max_count = {4: 1, 3: 2, 2: 3, 1: 4}[size]
    
    def draw(self, screen):
        colors = theme.colors
        color = colors["gold"] if self.count > 0 else colors["gray"]
        
        if self.horizontal:
            for i in range(self.size):
                rect = pygame.Rect(self.x + i * CELL_SIZE, self.y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, color, rect, border_radius=5)
                pygame.draw.rect(screen, colors["field_border"], rect, 2, border_radius=5)
                font = pygame.font.Font(None, 20)
                text = font.render(str(i+1), True, colors["text"])
                screen.blit(text, (rect.x + 5, rect.y + 5))
        else:
            for i in range(self.size):
                rect = pygame.Rect(self.x, self.y + i * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, color, rect, border_radius=5)
                pygame.draw.rect(screen, colors["field_border"], rect, 2, border_radius=5)
                font = pygame.font.Font(None, 20)
                text = font.render(str(i+1), True, colors["text"])
                screen.blit(text, (rect.x + 5, rect.y + 5))
        
        if self.count > 0:
            text = pygame.font.Font(None, 24).render(f"x{self.count}", True, colors["text"])
            screen.blit(text, (self.x + 5, self.y - 20))

class ShipPlacer:
    def __init__(self):
        self.current_ship = None
        self.current_template = None
        self.current_ship_size = 0
        self.current_ship_horizontal = True
        self.dragging = False
        self.drag_offset = (0, 0)
        self.preview_cells = []
        
    def start_drag_from_template(self, template, pos, field):
        if template.count > 0:
            self.current_template = template
            self.current_ship_size = template.size
            self.current_ship_horizontal = template.horizontal
            self.dragging = True
            grid_pos = self.get_grid_pos(pos, field)
            if grid_pos:
                row, col = grid_pos
                self.drag_offset = (0, 0)
                
    def start_drag_from_field(self, pos, field):
        grid_pos = self.get_grid_pos(pos, field)
        if grid_pos:
            row, col = grid_pos
            for ship in field.ships:
                if (row, col) in ship.cells:
                    self.current_ship = ship
                    self.dragging = True
                    first_cell = ship.cells[0]
                    self.drag_offset = (row - first_cell[0], col - first_cell[1])
                    field.remove_ship(ship)
                    self.current_ship_size = ship.get_size()
                    self.current_ship_horizontal = ship.horizontal
                    break
    
    def update_drag(self, pos, field):
        if self.dragging:
            grid_pos = self.get_grid_pos(pos, field)
            if grid_pos:
                row, col = grid_pos
                
                if self.current_template:
                    start_row = row
                    start_col = col
                else:
                    start_row = row - self.drag_offset[0]
                    start_col = col - self.drag_offset[1]
                
                ship_cells = []
                if self.current_ship_horizontal:
                    for i in range(self.current_ship_size):
                        ship_cells.append((start_row, start_col + i))
                else:
                    for i in range(self.current_ship_size):
                        ship_cells.append((start_row + i, start_col))
                
                if field.can_place_ship(ship_cells):
                    self.preview_cells = ship_cells
                else:
                    self.preview_cells = []
                return ship_cells
        return None
    
    def end_drag(self, pos, field, templates):
        if self.dragging:
            ship_cells = self.update_drag(pos, field)
            
            if ship_cells and field.can_place_ship(ship_cells):
                field.place_ship(ship_cells)
                
                if self.current_template:
                    self.current_template.count -= 1
                    if self.current_template.count == 0:
                        self.current_template = None
            else:
                if self.current_ship:
                    field.place_ship(self.current_ship.cells)
            
            self.current_ship = None
            self.current_template = None
            self.dragging = False
            self.preview_cells = []
    
    def rotate_ship(self):
        if self.dragging:
            self.current_ship_horizontal = not self.current_ship_horizontal
    
    def get_grid_pos(self, pos, field):
        x, y = pos
        if (field.x <= x < field.x + FIELD_WIDTH and 
            field.y <= y < field.y + FIELD_HEIGHT):
            col = (x - field.x) // CELL_SIZE
            row = (y - field.y) // CELL_SIZE
            return (row, col)
        return None
    
    def draw_preview(self, screen, field):
        colors = theme.colors
        if self.preview_cells and field.can_place_ship(self.preview_cells):
            for row, col in self.preview_cells:
                cell_x = field.x + col * CELL_SIZE
                cell_y = field.y + row * CELL_SIZE
                s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                s.fill(colors["preview"])
                screen.blit(s, (cell_x, cell_y))