import random
from collections import Counter
import pygame
from config import FIELD_SIZE, CELL_SIZE, FIELD_WIDTH, FIELD_HEIGHT
from enums import CellState
from models import Ship
from theme import theme

class GameField:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.grid = [[CellState.EMPTY for _ in range(FIELD_SIZE)] for _ in range(FIELD_SIZE)]
        self.ships = []
        self.shots = []
        self.debug_mode = False
    
    def debug_print(self, message):
        if self.debug_mode:
            print(f"[FIELD DEBUG] {message}")
    
    def print_field(self, title="Поле", show_ships=True):
        if self.debug_mode:
            print(f"\n=== {title} ===")
            print("   " + " ".join([str(i) for i in range(FIELD_SIZE)]))
            for row in range(FIELD_SIZE):
                line = f"{row:2} "
                for col in range(FIELD_SIZE):
                    cell = self.grid[row][col]
                    if cell == CellState.SHIP and not show_ships:
                        line += ". "
                    else:
                        line += cell.to_symbol() + " "
                print(line)
            print()
        
    def draw(self, screen, show_ships=True):
        colors = theme.colors
        for i in range(FIELD_SIZE + 1):
            pygame.draw.line(screen, colors["field_border"], 
                           (self.x + i * CELL_SIZE, self.y),
                           (self.x + i * CELL_SIZE, self.y + FIELD_HEIGHT), 1)
            pygame.draw.line(screen, colors["field_border"],
                           (self.x, self.y + i * CELL_SIZE),
                           (self.x + FIELD_WIDTH, self.y + i * CELL_SIZE), 1)
        
        for row in range(FIELD_SIZE):
            for col in range(FIELD_SIZE):
                cell_x = self.x + col * CELL_SIZE
                cell_y = self.y + row * CELL_SIZE
                
                if self.grid[row][col] == CellState.SHIP and show_ships:
                    pygame.draw.rect(screen, colors["ship"], 
                                   (cell_x + 1, cell_y + 1, CELL_SIZE - 2, CELL_SIZE - 2))
                elif self.grid[row][col] == CellState.HIT:
                    pygame.draw.rect(screen, colors["hit"],
                                   (cell_x + 1, cell_y + 1, CELL_SIZE - 2, CELL_SIZE - 2))
                    pygame.draw.line(screen, colors["field_border"],
                                   (cell_x + 5, cell_y + 5),
                                   (cell_x + CELL_SIZE - 5, cell_y + CELL_SIZE - 5), 2)
                    pygame.draw.line(screen, colors["field_border"],
                                   (cell_x + CELL_SIZE - 5, cell_y + 5),
                                   (cell_x + 5, cell_y + CELL_SIZE - 5), 2)
                elif self.grid[row][col] == CellState.MISS:
                    pygame.draw.circle(screen, colors["miss"],
                                     (cell_x + CELL_SIZE // 2, cell_y + CELL_SIZE // 2), 5)
                elif self.grid[row][col] == CellState.DESTROYED:
                    pygame.draw.rect(screen, colors["destroyed"],
                                   (cell_x + 1, cell_y + 1, CELL_SIZE - 2, CELL_SIZE - 2))
                    pygame.draw.line(screen, colors["field_border"],
                                   (cell_x + 5, cell_y + 5),
                                   (cell_x + CELL_SIZE - 5, cell_y + CELL_SIZE - 5), 2)
                    pygame.draw.line(screen, colors["field_border"],
                                   (cell_x + CELL_SIZE - 5, cell_y + 5),
                                   (cell_x + 5, cell_y + CELL_SIZE - 5), 2)
    
    def can_place_ship(self, ship_cells):
        for row, col in ship_cells:
            if row < 0 or row >= FIELD_SIZE or col < 0 or col >= FIELD_SIZE:
                return False
            if self.grid[row][col] != CellState.EMPTY:
                return False
            
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    r, c = row + dr, col + dc
                    if 0 <= r < FIELD_SIZE and 0 <= c < FIELD_SIZE:
                        if self.grid[r][c] == CellState.SHIP:
                            return False
        return True
    
    def place_ship(self, ship_cells):
        ship = Ship(ship_cells, [False] * len(ship_cells))
        self.ships.append(ship)
        for row, col in ship_cells:
            self.grid[row][col] = CellState.SHIP
        return ship
    
    def remove_ship(self, ship):
        if ship in self.ships:
            self.ships.remove(ship)
            for row, col in ship.cells:
                self.grid[row][col] = CellState.EMPTY
    
    def randomize_ships(self):
        self.clear()
        ship_sizes = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
        max_attempts = 10000
        for size in ship_sizes:
            placed = False
            attempts = 0
            while not placed and attempts < max_attempts:
                horizontal = random.choice([True, False])
                row = random.randint(0, FIELD_SIZE - 1)
                col = random.randint(0, FIELD_SIZE - 1)
                
                ship_cells = []
                if horizontal:
                    if col + size <= FIELD_SIZE:
                        for i in range(size):
                            ship_cells.append((row, col + i))
                else:
                    if row + size <= FIELD_SIZE:
                        for i in range(size):
                            ship_cells.append((row + i, col))
                
                if ship_cells and self.can_place_ship(ship_cells):
                    self.place_ship(ship_cells)
                    placed = True
                attempts += 1
            
            if not placed:
                return self.randomize_ships()
    
    def clear(self):
        self.grid = [[CellState.EMPTY for _ in range(FIELD_SIZE)] for _ in range(FIELD_SIZE)]
        self.ships = []
        self.shots = []
    
    def receive_shot(self, row, col):
        if self.grid[row][col] == CellState.SHIP:
            self.grid[row][col] = CellState.HIT
            
            for ship in self.ships:
                if (row, col) in ship.cells:
                    index = ship.cells.index((row, col))
                    ship.hits[index] = True
                    
                    if not ship.is_alive():
                        for r, c in ship.cells:
                            self.grid[r][c] = CellState.DESTROYED
                        
                        for r, c in ship.cells:
                            for dr in [-1, 0, 1]:
                                for dc in [-1, 0, 1]:
                                    nr, nc = r + dr, c + dc
                                    if (0 <= nr < FIELD_SIZE and 0 <= nc < FIELD_SIZE and 
                                        self.grid[nr][nc] == CellState.EMPTY):
                                        self.grid[nr][nc] = CellState.MISS
                    break
            return True
        elif self.grid[row][col] == CellState.EMPTY:
            self.grid[row][col] = CellState.MISS
            return False
        return None
    
    def all_ships_destroyed(self):
        for ship in self.ships:
            if ship.is_alive():
                return False
        return True
    
    def is_full_fleet(self):
        if len(self.ships) != 10:
            return False
        
        ship_sizes = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
        sizes = [ship.get_size() for ship in self.ships]
        sizes.sort()
        if sizes != ship_sizes:
            return False
        
        occupied = set()
        for ship in self.ships:
            for row, col in ship.cells:
                occupied.add((row, col))
        
        for row, col in occupied:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if (nr, nc) in occupied:
                        same_ship = False
                        for ship in self.ships:
                            if (row, col) in ship.cells and (nr, nc) in ship.cells:
                                same_ship = True
                                break
                        if not same_ship:
                            return False
        
        return True

    def get_fleet_error(self):
        if len(self.ships) != 10:
            return f"Не хватает {10 - len(self.ships)} кораблей"
        
        required = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
        current = [ship.get_size() for ship in self.ships]
        
        if sorted(current) != sorted(required):
            req_count = Counter(required)
            cur_count = Counter(current)
            diffs = []
            for size in sorted(set(req_count.keys()) | set(cur_count.keys())):
                diff = cur_count.get(size, 0) - req_count.get(size, 0)
                if diff > 0:
                    diffs.append(f"лишние {diff} {size}-палубных")
                elif diff < 0:
                    diffs.append(f"не хватает {-diff} {size}-палубных")
            return "Ошибка размеров: " + ", ".join(diffs)
        
        occupied = set()
        for ship in self.ships:
            for cell in ship.cells:
                occupied.add(cell)
        
        for ship in self.ships:
            for r, c in ship.cells:
                for dr, dc in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in occupied and (nr, nc) not in ship.cells:
                        return f"Корабли касаются в клетках ({r},{c}) и ({nr},{nc})"
        
        return "OK"
    
    def get_ships_data(self):
        return [ship.to_dict() for ship in self.ships]
    
    def load_ships_data(self, ships_data):
        self.clear()
        for i, ship_data in enumerate(ships_data):
            try:
                cells = [tuple(cell) for cell in ship_data["cells"]]
                ship_data["cells"] = cells
                ship = Ship.from_dict(ship_data)
                self.ships.append(ship)
                for row, col in ship.cells:
                    if 0 <= row < FIELD_SIZE and 0 <= col < FIELD_SIZE:
                        self.grid[row][col] = CellState.SHIP
            except Exception as e:
                pass