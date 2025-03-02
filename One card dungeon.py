import random
import pygame
import sys
from enum import Enum
import time
import traceback  # Aggiungiamo questo per il debug

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
TILE_SIZE = 65
GRID_SIZE = 7  # 6x6 grid for the dungeon
BUTTON_HEIGHT = 50
INFO_HEIGHT = 80

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 205, 0)
BROWN = (165, 42, 42)
LIGHT_BROWN = (210, 180, 140)
DARK_GREEN = (0, 100, 0)
PURPLE = (128, 0, 128)

# Direction enums
class Direction(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

# Tile types
class TileType(Enum):
    FLOOR = 0
    WALL = 1
    STAIRS = 2

# Game screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("One Card Dungeon")

# Fonts
font = pygame.font.SysFont('Arial', 24)
small_font = pygame.font.SysFont('Arial', 18)
title_font = pygame.font.SysFont('Arial', 32)

class DungeonLevel:
    def __init__(self, level_number):
        self.level_number = level_number
        self.grid = [[TileType.FLOOR for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.monster_data = self.get_monster_data()
        self.create_layout()
        
    def get_monster_data(self):
        # Monster data by level: [count, health, speed, attack, defense, range]
        monster_data = {
            1: [2, 2, 5, 4, 1, 3, "Spider"],
            2: [2, 3, 4, 5, 1, 2, "Goblin"],
            3: [2, 3, 5, 4, 2, 3, "Skeleton"],
            4: [3, 3, 4, 5, 2, 3, "Zombie"],
            5: [2, 4, 5, 5, 2, 4, "Orc"],
            6: [2, 4, 6, 5, 3, 3, "Wolf"],
            7: [3, 4, 5, 6, 3, 4, "Ghoul"],
            8: [2, 5, 5, 6, 3, 4, "Troll"],
            9: [2, 5, 6, 6, 3, 5, "Ghost"],
            10: [3, 5, 6, 7, 4, 4, "Vampire"],
            11: [2, 6, 6, 7, 4, 5, "Golem"],
            12: [3, 6, 7, 8, 4, 5, "Dragon"],
        }
        return monster_data.get(self.level_number, [2, 2, 5, 4, 1, 3, "Monster"])
    
    def create_layout(self):
        # Add walls around border
        for i in range(GRID_SIZE):
            self.grid[0][i] = TileType.WALL
            self.grid[GRID_SIZE-1][i] = TileType.WALL
            self.grid[i][0] = TileType.WALL
            self.grid[i][GRID_SIZE-1] = TileType.WALL
            
        # Add inner walls based on level
        if self.level_number % 4 == 1:  # Levels 1, 5, 9
            self.grid[2][2] = TileType.WALL
            self.grid[2][3] = TileType.WALL
            self.grid[3][3] = TileType.WALL
        elif self.level_number % 4 == 2:  # Levels 2, 6, 10
            self.grid[1][3] = TileType.WALL
            self.grid[2][3] = TileType.WALL
            self.grid[3][2] = TileType.WALL
            self.grid[3][4] = TileType.WALL
        elif self.level_number % 4 == 3:  # Levels 3, 7, 11
            self.grid[2][1] = TileType.WALL
            self.grid[2][4] = TileType.WALL
            self.grid[3][2] = TileType.WALL
            self.grid[3][3] = TileType.WALL
            self.grid[4][3] = TileType.WALL
        else:  # Levels 4, 8, 12
            self.grid[1][2] = TileType.WALL
            self.grid[2][2] = TileType.WALL
            self.grid[2][4] = TileType.WALL
            self.grid[3][1] = TileType.WALL
            self.grid[4][3] = TileType.WALL
            self.grid[4][4] = TileType.WALL
        
        # Add stairs
        self.grid[GRID_SIZE-2][GRID_SIZE-2] = TileType.STAIRS

class Monster:
    def __init__(self, x, y, health, speed, attack, defense, range_val, name):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = health
        self.speed = speed
        self.attack = attack
        self.defense = defense
        self.range = range_val
        self.name = name
        
    def move(self, target_x, target_y, dungeon, adventurer, other_monsters):
        # Try/except per gestire errori che potrebbero verificarsi durante il movimento
        try:
            # Calculate path to best position (at maximum range with line of sight)
            best_position = self.find_best_position(target_x, target_y, dungeon, adventurer, other_monsters)
            if best_position is None:
                return False  # Can't move
                
            # Move towards best position
            remaining_speed = self.speed
            current_x, current_y = self.x, self.y
            
            while remaining_speed > 0:
                next_step = self.get_next_step(current_x, current_y, best_position[0], best_position[1], dungeon, adventurer, other_monsters)
                if next_step is None:
                    break
                    
                next_x, next_y, cost = next_step
                if cost > remaining_speed:
                    break
                    
                current_x, current_y = next_x, next_y
                remaining_speed -= cost
                
            self.x, self.y = current_x, current_y
            return True
        except Exception as e:
            print(f"Errore durante il movimento del mostro: {e}")
            traceback.print_exc()
            return False
        
    def find_best_position(self, target_x, target_y, dungeon, adventurer, other_monsters):
        # Find tiles at maximum range from adventurer with line of sight
        candidates = []
        
        try:
            for x in range(GRID_SIZE):
                for y in range(GRID_SIZE):
                    # Skip if wall, adventurer position or has another monster
                    if dungeon.grid[y][x] == TileType.WALL or (x == adventurer.x and y == adventurer.y):
                        continue
                        
                    occupied = False
                    for m in other_monsters:
                        if m != self and m.x == x and m.y == y:
                            occupied = True
                            break
                    if occupied:
                        continue
                        
                    # Calculate range
                    range_to_adv = calculate_range(x, y, adventurer.x, adventurer.y)
                    
                    # Check line of sight
                    if has_line_of_sight(x, y, adventurer.x, adventurer.y, dungeon, other_monsters):
                        candidates.append((x, y, range_to_adv, calculate_range(x, y, self.x, self.y)))
            
            # Filter candidates at maximum range
            max_range_candidates = [c for c in candidates if c[2] <= self.range]
            
            # If no candidates at maximum range, use any candidates with line of sight
            if not max_range_candidates and candidates:
                max_range_candidates = candidates
                
            # Sort by how close they are to maximum range, then by distance from monster
            if max_range_candidates:
                max_range_candidates.sort(key=lambda c: (abs(self.range - c[2]), c[3]))
                return (max_range_candidates[0][0], max_range_candidates[0][1])
        except Exception as e:
            print(f"Errore in find_best_position: {e}")
            traceback.print_exc()
            
        return None  # Return None if no valid positions or error occurs
        
    def get_next_step(self, from_x, from_y, to_x, to_y, dungeon, adventurer, other_monsters):
        # Get the best next step towards the target
        try:
            possible_moves = []
            
            # Orthogonal moves (cost 2)
            directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
            for dx, dy in directions:
                nx, ny = from_x + dx, from_y + dy
                if self.is_valid_move(nx, ny, dungeon, adventurer, other_monsters):
                    distance = abs(to_x - nx) + abs(to_y - ny)
                    possible_moves.append((nx, ny, 2, distance))
                    
            # Diagonal moves (cost 3)
            directions = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
            for dx, dy in directions:
                nx, ny = from_x + dx, from_y + dy
                if self.is_valid_move(nx, ny, dungeon, adventurer, other_monsters):
                    distance = abs(to_x - nx) + abs(to_y - ny)
                    possible_moves.append((nx, ny, 3, distance))
                    
            # Sort by distance to target
            if possible_moves:
                possible_moves.sort(key=lambda m: m[3])
                return (possible_moves[0][0], possible_moves[0][1], possible_moves[0][2])
        except Exception as e:
            print(f"Errore in get_next_step: {e}")
            traceback.print_exc()
            
        return None
        
    def is_valid_move(self, x, y, dungeon, adventurer, other_monsters):
        # Check bounds
        if x < 0 or y < 0 or x >= GRID_SIZE or y >= GRID_SIZE:
            return False
            
        # Check for walls
        if dungeon.grid[y][x] == TileType.WALL:
            return False
            
        # Check for adventurer
        if x == adventurer.x and y == adventurer.y:
            return False
            
        # Check for other monsters
        for m in other_monsters:
            if m != self and m.x == x and m.y == y:
                return False
                
        return True
        
    def can_attack(self, target_x, target_y, other_monsters, dungeon):
        # Check if can attack (in range and line of sight)
        try:
            range_to_target = calculate_range(self.x, self.y, target_x, target_y)
            return range_to_target <= self.range and has_line_of_sight(self.x, self.y, target_x, target_y, dungeon, other_monsters)
        except Exception as e:
            print(f"Errore in can_attack: {e}")
            traceback.print_exc()
            return False

class Adventurer:
    def __init__(self):
        self.x = 1
        self.y = 1
        self.health = 6
        self.max_health = 6
        self.speed = 1
        self.attack = 1
        self.defense = 1
        self.range = 2
        self.class_name = None
        self.class_ability_used = False
        
    def move(self, dx, dy, dungeon, monsters, remaining_speed):
        try:
            new_x = self.x + dx
            new_y = self.y + dy
            
            # Check bounds
            if new_x < 0 or new_y < 0 or new_x >= GRID_SIZE or new_y >= GRID_SIZE:
                return False, remaining_speed
                
            # Check for walls
            if dungeon.grid[new_y][new_x] == TileType.WALL:
                return False, remaining_speed
                
            # Check for monsters
            for monster in monsters:
                if monster.x == new_x and monster.y == new_y:
                    return False, remaining_speed
                    
            # Calculate cost (2 for orthogonal, 3 for diagonal)
            cost = 2 if dx == 0 or dy == 0 else 3
            
            # Check if enough speed points
            if cost > remaining_speed:
                return False, remaining_speed
                
            # Move
            self.x = new_x
            self.y = new_y
            return True, remaining_speed - cost
        except Exception as e:
            print(f"Errore nel movimento dell'avventuriero: {e}")
            traceback.print_exc()
            return False, remaining_speed
        
    def upgrade_skill(self, skill):
        if skill == "speed":
            self.speed += 1
        elif skill == "attack":
            self.attack += 1
        elif skill == "defense":
            self.defense += 1
        elif skill == "range":
            self.range += 1
            
    def heal_full(self):
        self.health = self.max_health
        
    def use_class_ability(self, ability_type, energy_dice=None):
        if self.class_ability_used:
            return False
            
        self.class_ability_used = True
        return True

class Game:
    def __init__(self):
        self.level = 1
        self.adventurer = Adventurer()
        self.dungeon = DungeonLevel(self.level)
        self.monsters = []
        self.spawn_monsters()
        self.game_state = "energy"  # energy, adventurer, monster_move, monster_attack, level_complete, game_over, victory
        self.energy_dice = [1, 1, 1]
        self.total_speed = 0
        self.total_attack = 0
        self.total_defense = 0
        self.remaining_speed = 0
        self.remaining_attack = 0
        self.message = "Welcome to One Card Dungeon! Roll energy dice to begin."
        self.last_message = ""
        self.dice_assigned = [False, False, False]
        
    def spawn_monsters(self):
        try:
            self.monsters.clear()
            monster_count, health, speed, attack, defense, range_val, name = self.dungeon.monster_data
            
            # Generate positions for monsters
            positions = []
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    # Don't spawn on walls, stairs, or near adventurer start
                    if self.dungeon.grid[y][x] != TileType.FLOOR:
                        continue
                    if abs(x - self.adventurer.x) <= 1 and abs(y - self.adventurer.y) <= 1:
                        continue
                    positions.append((x, y))
                    
            # Shuffle positions
            random.shuffle(positions)
            
            # Create monsters
            for i in range(min(monster_count, len(positions))):
                if i < len(positions):  # Controllo aggiuntivo per evitare IndexError
                    x, y = positions[i]
                    self.monsters.append(Monster(x, y, health, speed, attack, defense, range_val, name))
        except Exception as e:
            print(f"Errore durante lo spawn dei mostri: {e}")
            traceback.print_exc()
            
    def roll_energy_dice(self):
        self.energy_dice = [random.randint(1, 6) for _ in range(3)]
        self.dice_assigned = [False, False, False]
        self.message = "Assign dice to your skills."
        
    def assign_dice(self, dice_index, skill):
        try:
            if dice_index < 0 or dice_index >= len(self.dice_assigned):
                print(f"Indice dado non valido: {dice_index}")
                return False
                
            if self.dice_assigned[dice_index]:
                return False
                
            value = self.energy_dice[dice_index]
            if skill == "speed":
                self.total_speed = self.adventurer.speed + value
                self.remaining_speed = self.total_speed
            elif skill == "attack":
                self.total_attack = self.adventurer.attack + value
                self.remaining_attack = self.total_attack
            elif skill == "defense":
                self.total_defense = self.adventurer.defense + value
                
            self.dice_assigned[dice_index] = True
            
            # Check if all dice assigned
            if all(self.dice_assigned):
                self.game_state = "adventurer"
                self.message = "Your turn. Move and attack monsters."
                
            return True
        except Exception as e:
            print(f"Errore durante l'assegnazione dei dadi: {e}")
            traceback.print_exc()
            return False
        
    def attack_monster(self, monster_index):
        try:
            if monster_index < 0 or monster_index >= len(self.monsters):
                print(f"Indice mostro non valido: {monster_index}")
                return False
                
            monster = self.monsters[monster_index]
            
            # Check range
            range_to_monster = calculate_range(self.adventurer.x, self.adventurer.y, monster.x, monster.y)
            if range_to_monster > self.adventurer.range:
                self.message = f"Monster out of range. Your range is {self.adventurer.range}."
                return False
                
            # Check line of sight
            if not has_line_of_sight(self.adventurer.x, self.adventurer.y, monster.x, monster.y, self.dungeon, self.monsters):
                self.message = "No line of sight to monster."
                return False
                
            # Check attack points
            attack_cost = monster.defense
            if self.remaining_attack < attack_cost:
                self.message = f"Not enough attack points. Need {attack_cost}, have {self.remaining_attack}."
                return False
                
            # Attack monster
            monster.health -= 1
            self.remaining_attack -= attack_cost
            
            if monster.health <= 0:
                self.monsters.pop(monster_index)
                self.message = f"Monster killed! {len(self.monsters)} remaining."
                
                # Check for level complete
                if not self.monsters:
                    self.game_state = "level_complete"
                    self.message = "Level complete! Choose to upgrade a skill or heal."
            else:
                self.message = f"Monster hit! {monster.health}/{monster.max_health} health remaining."
                
            return True
        except Exception as e:
            print(f"Errore durante l'attacco al mostro: {e}")
            traceback.print_exc()
            return False
        
    def end_adventurer_turn(self):
        try:
            if not all(self.dice_assigned):
                self.message = "Assign all energy dice first."
                return False
                
            self.game_state = "monster_move"
            self.process_monster_move()
            return True
        except Exception as e:
            print(f"Errore alla fine del turno: {e}")
            traceback.print_exc()
            return False
        
    def process_monster_move(self):
        try:
            # Sort monsters by distance to adventurer
            self.monsters.sort(key=lambda m: calculate_range(m.x, m.y, self.adventurer.x, self.adventurer.y))
            
            # Move each monster
            for monster in self.monsters:
                monster.move(self.adventurer.x, self.adventurer.y, self.dungeon, self.adventurer, self.monsters)
                
            self.game_state = "monster_attack"
            self.process_monster_attack()
        except Exception as e:
            print(f"Errore durante il movimento dei mostri: {e}")
            traceback.print_exc()
            self.game_state = "energy"  # Ripristina lo stato del gioco per evitare blocchi
            
    def process_monster_attack(self):
        try:
            total_monster_attack = 0
            attacking_monsters = []
            
            # Calculate total attack
            for monster in self.monsters:
                if monster.can_attack(self.adventurer.x, self.adventurer.y, self.monsters, self.dungeon):
                    total_monster_attack += monster.attack
                    attacking_monsters.append(monster)
                    
            # Calculate damage
            damage = 0
            if total_monster_attack > 0 and self.total_defense > 0:
                damage = total_monster_attack // self.total_defense
                
            # Apply damage
            self.adventurer.health -= damage
            
            # Update message
            if attacking_monsters:
                self.message = f"{len(attacking_monsters)} monsters attacked for {damage} damage."
            else:
                self.message = "No monsters could attack this turn."
                
            # Check for game over
            if self.adventurer.health <= 0:
                self.adventurer.health = 0
                self.game_state = "game_over"
                self.message = "Game Over! You died in the dungeon."
            else:
                # Start new turn
                self.game_state = "energy"
                self.last_message = self.message
                self.message = "Roll energy dice for the next turn."
        except Exception as e:
            print(f"Errore durante l'attacco dei mostri: {e}")
            traceback.print_exc()
            self.game_state = "energy"  # Ripristina lo stato del gioco per evitare blocchi
            
    def advance_level(self, choice):
        try:
            if choice == "heal":
                self.adventurer.heal_full()
            elif choice in ["speed", "attack", "defense", "range"]:
                self.adventurer.upgrade_skill(choice)
                
            # Go to next level
            self.level += 1
            
            if self.level > 12:
                self.game_state = "victory"
                self.message = "Congratulations! You've completed all 12 levels and found the Sceptre of M'Guf-yn!"
            else:
                self.dungeon = DungeonLevel(self.level)
                self.adventurer.x = 1
                self.adventurer.y = 1
                self.spawn_monsters()
                self.game_state = "energy"
                self.adventurer.class_ability_used = False
                self.message = f"Level {self.level} - Roll energy dice to begin."
        except Exception as e:
            print(f"Errore durante l'avanzamento di livello: {e}")
            traceback.print_exc()
            # Resetta lo stato del gioco in caso di errore
            self.dungeon = DungeonLevel(self.level)
            self.game_state = "energy"
            
    def choose_class(self, class_name):
        self.adventurer.class_name = class_name
        self.adventurer.class_ability_used = False
        
    def use_class_ability(self, energy_dice=None):
        try:
            if not self.adventurer.class_name or self.adventurer.class_ability_used:
                return False
                
            ability_used = True
            
            if self.adventurer.class_name == "Paladin":
                # Implemented elsewhere when rolling dice
                pass
            elif self.adventurer.class_name == "Barbarian":
                if self.adventurer.health == 1:
                    self.roll_energy_dice()
                    self.message = "Rerolled all dice with Barbarian ability."
                else:
                    ability_used = False
                    self.message = "Barbarian ability can only be used at 1 health."
            elif self.adventurer.class_name == "Ranger":
                if energy_dice is not None and 0 <= energy_dice < len(self.energy_dice):  # Controllo range
                    value = self.energy_dice[energy_dice]
                    self.adventurer.range += value
                    self.dice_assigned[energy_dice] = True
                    self.message = f"Assigned {value} to Range with Ranger ability."
                    
                    # Check if all dice assigned
                    if all(self.dice_assigned):
                        self.game_state = "adventurer"
                        self.message = "Your turn. Move and attack monsters."
                else:
                    ability_used = False
            elif self.adventurer.class_name == "Wizard":
                self.roll_energy_dice()
                self.message = "Rerolled all dice with Wizard ability."
                
            if ability_used:
                self.adventurer.class_ability_used = True
                
            return ability_used
        except Exception as e:
            print(f"Errore durante l'uso dell'abilità di classe: {e}")
            traceback.print_exc()
            return False

# Helper functions
def calculate_range(x1, y1, x2, y2):
    try:
        # Calculates the range between two points (in movement cost)
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        diag = min(dx, dy)
        orth = max(dx, dy) - diag
        return diag * 3 + orth * 2  # 3 for each diagonal, 2 for each orthogonal
    except Exception as e:
        print(f"Errore in calculate_range: {e}")
        traceback.print_exc()
        return 999  # Valore elevato per indicare che è fuori portata

def has_line_of_sight(x1, y1, x2, y2, dungeon, monsters):
    try:
        # Simple line of sight check
        # For a more accurate check, implement Bresenham's line algorithm
        
        # Check corners of tiles
        corners1 = [(x1, y1), (x1+1, y1), (x1, y1+1), (x1+1, y1+1)]
        corners2 = [(x2, y2), (x2+1, y2), (x2, y2+1), (x2+1, y2+1)]
        
        for cx1, cy1 in corners1:
            for cx2, cy2 in corners2:
                if check_line(cx1, cy1, cx2, cy2, dungeon, monsters):
                    return True
                    
        return False
    except Exception as e:
        print(f"Errore in has_line_of_sight: {e}")
        traceback.print_exc()
        return False

def check_line(x1, y1, x2, y2, dungeon, monsters):
    try:
        # Check if a line between two points crosses any walls or monsters
        
        # Bresenham's line algorithm
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        while True:
            # Check if current point is in a wall
            tile_x, tile_y = int(x1), int(y1)
            if 0 <= tile_x < GRID_SIZE and 0 <= tile_y < GRID_SIZE:
                if dungeon.grid[tile_y][tile_x] == TileType.WALL:
                    return False
                    
                # Check for monsters (except at endpoints)
                if (tile_x, tile_y) != (int(x2), int(y2)) and (tile_x, tile_y) != (int(x1), int(y1)):
                    for monster in monsters:
                        if monster.x == tile_x and monster.y == tile_y:
                            return False
            
            if x1 == x2 and y1 == y2:
                break
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
                
        return True
    except Exception as e:
        print(f"Errore in check_line: {e}")
        traceback.print_exc()
        return False

def draw_game(game, selected_dice=None):
    try:
        screen.fill(WHITE)
        
        # Draw grid
        grid_offset_x = (SCREEN_WIDTH - GRID_SIZE * TILE_SIZE) // 2
        grid_offset_y = 100
        
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                tile_x = grid_offset_x + x * TILE_SIZE
                tile_y = grid_offset_y + y * TILE_SIZE
                
                # Draw tile
                if game.dungeon.grid[y][x] == TileType.WALL:
                    pygame.draw.rect(screen, BROWN, (tile_x, tile_y, TILE_SIZE, TILE_SIZE))
                elif game.dungeon.grid[y][x] == TileType.STAIRS:
                    pygame.draw.rect(screen, LIGHT_BROWN, (tile_x, tile_y, TILE_SIZE, TILE_SIZE))
                    stair_text = font.render("↓", True, BLACK)
                    screen.blit(stair_text, (tile_x + TILE_SIZE//2 - 10, tile_y + TILE_SIZE//2 - 10))
                else:
                    pygame.draw.rect(screen, LIGHT_BROWN, (tile_x, tile_y, TILE_SIZE, TILE_SIZE))
                
                # Draw grid lines
                pygame.draw.rect(screen, BLACK, (tile_x, tile_y, TILE_SIZE, TILE_SIZE), 1)
        
        # Draw adventurer
        adv_x = grid_offset_x + game.adventurer.x * TILE_SIZE
        adv_y = grid_offset_y + game.adventurer.y * TILE_SIZE
        pygame.draw.circle(screen, GREEN, (adv_x + TILE_SIZE//2, adv_y + TILE_SIZE//2), TILE_SIZE//3)
        
        # Draw monsters
        for i, monster in enumerate(game.monsters):
            monster_x = grid_offset_x + monster.x * TILE_SIZE
            monster_y = grid_offset_y + monster.y * TILE_SIZE
            pygame.draw.circle(screen, RED, (monster_x + TILE_SIZE//2, monster_y + TILE_SIZE//2), TILE_SIZE//3)
            
            # Draw health
            health_text = small_font.render(f"{monster.health}", True, WHITE)
            screen.blit(health_text, (monster_x + TILE_SIZE//2 - 5, monster_y + TILE_SIZE//2 - 8))
            
            # Draw monster number
            number_text = small_font.render(f"{i+1}", True, BLACK)
            screen.blit(number_text, (monster_x + 5, monster_y + 5))
        
        # Draw UI elements
        title_text = title_font.render(f"One Card Dungeon - Level {game.level}", True, BLACK)
        screen.blit(title_text, (20, 20))
        
        # Draw health
        health_text = font.render(f"Health: {game.adventurer.health}/{game.adventurer.max_health}", True, RED)
        screen.blit(health_text, (20, 60))
        
        # Calculate bonuses from dice
        speed_bonus = game.total_speed - game.adventurer.speed if game.total_speed > 0 else 0
        attack_bonus = game.total_attack - game.adventurer.attack if game.total_attack > 0 else 0
        defense_bonus = game.total_defense - game.adventurer.defense if game.total_defense > 0 else 0
        
        # PLAYER STATS - Now positioned on the left side vertically
        stat_x = 20  # Move to the left
        stat_y_start = 90  # Start below health
        stat_spacing = 25  # Space between stat lines
        
        # If dice haven't been assigned yet, show base values
        if not all(game.dice_assigned) and sum(game.dice_assigned) == 0:
            speed_text = font.render(f"Speed: {game.adventurer.speed}", True, BLUE)
            screen.blit(speed_text, (stat_x, stat_y_start))
            
            attack_text = font.render(f"Attack: {game.adventurer.attack}", True, PURPLE)
            screen.blit(attack_text, (stat_x, stat_y_start + stat_spacing))
            
            defense_text = font.render(f"Defense: {game.adventurer.defense}", True, DARK_GREEN)
            screen.blit(defense_text, (stat_x, stat_y_start + 2 * stat_spacing))
            
            range_text = font.render(f"Range: {game.adventurer.range}", True, YELLOW)
            screen.blit(range_text, (stat_x, stat_y_start + 3 * stat_spacing))
        else:
            # Display stats with bonuses clearly indicated on separate lines
            speed_text = font.render(f"Speed: {game.adventurer.speed} + {speed_bonus} = {game.total_speed} ({game.remaining_speed})", True, BLUE)
            screen.blit(speed_text, (stat_x, stat_y_start))
            
            attack_text = font.render(f"Attack: {game.adventurer.attack} + {attack_bonus} = {game.total_attack} ({game.remaining_attack})", True, PURPLE)
            screen.blit(attack_text, (stat_x, stat_y_start + stat_spacing))
            
            defense_text = font.render(f"Defense: {game.adventurer.defense} + {defense_bonus} = {game.total_defense}", True, DARK_GREEN)
            screen.blit(defense_text, (stat_x, stat_y_start + 2 * stat_spacing))
            
            range_text = font.render(f"Range: {game.adventurer.range}", True, YELLOW)
            screen.blit(range_text, (stat_x, stat_y_start + 3 * stat_spacing))
        
        # MONSTER STATS - Display on the right side of the grid
        if game.monsters:
            # Calculate position for monster stats (right side of the grid)
            monster_stats_x = grid_offset_x + GRID_SIZE * TILE_SIZE + 20
            monster_stats_y = grid_offset_y
            monster_stats_spacing = 25
            
            # Draw a title for monster section
            monster_title = font.render("Monsters", True, RED)
            screen.blit(monster_title, (monster_stats_x, monster_stats_y - 30))
            
            # Draw monster type information
            monster_type = font.render(f"Type: {game.dungeon.monster_data[6]}", True, BLACK)
            screen.blit(monster_type, (monster_stats_x, monster_stats_y))
            
            # Draw shared monster stats (same for all monsters of this level)
            monster_speed = font.render(f"Speed: {game.dungeon.monster_data[2]}", True, BLUE)
            screen.blit(monster_speed, (monster_stats_x, monster_stats_y + monster_stats_spacing))
            
            monster_attack = font.render(f"Attack: {game.dungeon.monster_data[3]}", True, PURPLE)
            screen.blit(monster_attack, (monster_stats_x, monster_stats_y + 2 * monster_stats_spacing))
            
            monster_defense = font.render(f"Defense: {game.dungeon.monster_data[4]}", True, DARK_GREEN)
            screen.blit(monster_defense, (monster_stats_x, monster_stats_y + 3 * monster_stats_spacing))
            
            monster_range = font.render(f"Range: {game.dungeon.monster_data[5]}", True, YELLOW)
            screen.blit(monster_range, (monster_stats_x, monster_stats_y + 4 * monster_stats_spacing))
            
            # Draw individual monster health
            monster_list_y = monster_stats_y + 6 * monster_stats_spacing
            monster_list_title = font.render("Monster Health:", True, BLACK)
            screen.blit(monster_list_title, (monster_stats_x, monster_list_y))
            
            for i, monster in enumerate(game.monsters):
                monster_health = font.render(f"Monster {i+1}: {monster.health}/{monster.max_health} HP", True, RED)
                screen.blit(monster_health, (monster_stats_x, monster_list_y + (i+1) * monster_stats_spacing))
        
        # Draw message
        message_text = font.render(game.message, True, BLACK)
        screen.blit(message_text, (20, SCREEN_HEIGHT - INFO_HEIGHT + 10))
        
        # Draw last message
        if game.last_message:
            last_message_text = small_font.render(game.last_message, True, GRAY)
            screen.blit(last_message_text, (20, SCREEN_HEIGHT - INFO_HEIGHT + 40))
        
        # Draw energy dice
        if game.game_state == "energy" or not all(game.dice_assigned):
            dice_width = 50
            dice_spacing = 20
            total_width = 3 * dice_width + 2 * dice_spacing
            dice_start_x = (SCREEN_WIDTH - total_width) // 2
            dice_y = SCREEN_HEIGHT - INFO_HEIGHT - BUTTON_HEIGHT - dice_width - 10
            
            for i, value in enumerate(game.energy_dice):
                dice_x = dice_start_x + i * (dice_width + dice_spacing)
                
                # Highlight selected dice with a yellow background
                if selected_dice == i and not game.dice_assigned[i]:
                    color = YELLOW
                elif game.dice_assigned[i]:
                    color = GRAY
                else:
                    color = WHITE
                    
                pygame.draw.rect(screen, color, (dice_x, dice_y, dice_width, dice_width))
                pygame.draw.rect(screen, BLACK, (dice_x, dice_y, dice_width, dice_width), 1)
                
                value_text = font.render(str(value), True, BLACK)
                screen.blit(value_text, (dice_x + dice_width//2 - 7, dice_y + dice_width//2 - 10))
        
        # Draw buttons
        button_y = SCREEN_HEIGHT - INFO_HEIGHT - BUTTON_HEIGHT
        
        if game.game_state == "energy":
            # Roll dice button
            pygame.draw.rect(screen, BLUE, (20, button_y, 120, BUTTON_HEIGHT))
            roll_text = font.render("Roll Dice", True, WHITE)
            screen.blit(roll_text, (40, button_y + 10))
            
            # Assign dice buttons (if dice rolled)
            if not all(game.dice_assigned):
                skills = ["Speed", "Attack", "Defense"]
                for i, skill in enumerate(skills):
                    pygame.draw.rect(screen, GREEN, (200 + i*150, button_y, 120, BUTTON_HEIGHT))
                    skill_text = font.render(f"To {skill}", True, WHITE)
                    screen.blit(skill_text, (220 + i*150, button_y + 10))
            
        elif game.game_state == "adventurer":
            # End turn button
            pygame.draw.rect(screen, RED, (SCREEN_WIDTH - 140, button_y, 120, BUTTON_HEIGHT))
            end_text = font.render("End Turn", True, WHITE)
            screen.blit(end_text, (SCREEN_WIDTH - 120, button_y + 10))
            
            # Attack buttons (one for each monster)
            if game.monsters:
                for i in range(min(3, len(game.monsters))):
                    pygame.draw.rect(screen, PURPLE, (20 + i*150, button_y, 120, BUTTON_HEIGHT))
                    attack_text = font.render(f"Attack {i+1}", True, WHITE)
                    screen.blit(attack_text, (30 + i*150, button_y + 10))
        
        elif game.game_state == "level_complete":
            options = ["Speed", "Attack", "Defense", "Range", "Heal"]
            for i, option in enumerate(options):
                pygame.draw.rect(screen, GREEN, (20 + i*150, button_y, 120, BUTTON_HEIGHT))
                option_text = font.render(option, True, WHITE)
                screen.blit(option_text, (50 + i*150, button_y + 10))
                
        elif game.game_state == "game_over" or game.game_state == "victory":
            pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH//2 - 60, button_y, 120, BUTTON_HEIGHT))
            restart_text = font.render("New Game", True, WHITE)
            screen.blit(restart_text, (SCREEN_WIDTH//2 - 40, button_y + 10))
        
        pygame.display.flip()
    except Exception as e:
        print(f"Errore durante il disegno del gioco: {e}")
        traceback.print_exc()

def main():
    game = Game()
    running = True
    selected_dice = None  # Variabile per tenere traccia del dado selezionato
    
    # Main game loop
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                button_y = SCREEN_HEIGHT - INFO_HEIGHT - BUTTON_HEIGHT
                
                # Handle UI interactions
                if game.game_state == "energy":
                    # Roll dice button
                    if 20 <= x <= 140 and button_y <= y <= button_y + BUTTON_HEIGHT:
                        game.roll_energy_dice()
                        selected_dice = None  # Reset selected dice when rolling
                        
                    # Dice selection and assignment
                    if not all(game.dice_assigned):
                        # Check which dice is clicked
                        dice_width = 50
                        dice_spacing = 20
                        total_width = 3 * dice_width + 2 * dice_spacing
                        dice_start_x = (SCREEN_WIDTH - total_width) // 2
                        dice_y = SCREEN_HEIGHT - INFO_HEIGHT - BUTTON_HEIGHT - dice_width - 10
                        
                        # First check if a dice is being selected
                        for i in range(3):
                            dice_x = dice_start_x + i * (dice_width + dice_spacing)
                            if dice_x <= x <= dice_x + dice_width and dice_y <= y <= dice_y + dice_width:
                                if not game.dice_assigned[i]:
                                    selected_dice = i
                                    game.message = f"Dado {i+1} selezionato. Scegli un'abilità."
                                    break
                        
                        # Then check if a skill button is clicked (only if a dice is selected)
                        if selected_dice is not None:
                            for j, skill in enumerate(["speed", "attack", "defense"]):
                                if 200 + j*150 <= x <= 320 + j*150 and button_y <= y <= button_y + BUTTON_HEIGHT:
                                    if game.assign_dice(selected_dice, skill):
                                        game.message = f"Dado {selected_dice+1} assegnato a {skill}."
                                        selected_dice = None  # Reset selection after assignment
                
                elif game.game_state == "adventurer":
                    # End turn button
                    if SCREEN_WIDTH - 140 <= x <= SCREEN_WIDTH - 20 and button_y <= y <= button_y + BUTTON_HEIGHT:
                        game.end_adventurer_turn()
                        
                    # Attack buttons
                    if game.monsters:
                        for i in range(min(3, len(game.monsters))):
                            if 20 + i*150 <= x <= 140 + i*150 and button_y <= y <= button_y + BUTTON_HEIGHT:
                                game.attack_monster(i)
                    
                    # Handle movement
                    grid_offset_x = (SCREEN_WIDTH - GRID_SIZE * TILE_SIZE) // 2
                    grid_offset_y = 100
                    
                    for grid_y in range(GRID_SIZE):
                        for grid_x in range(GRID_SIZE):
                            tile_x = grid_offset_x + grid_x * TILE_SIZE
                            tile_y = grid_offset_y + grid_y * TILE_SIZE
                            
                            if tile_x <= x <= tile_x + TILE_SIZE and tile_y <= y <= tile_y + TILE_SIZE:
                                dx = grid_x - game.adventurer.x
                                dy = grid_y - game.adventurer.y
                                
                                # Only allow movement to adjacent tiles
                                if abs(dx) <= 1 and abs(dy) <= 1 and (dx != 0 or dy != 0):
                                    moved, game.remaining_speed = game.adventurer.move(dx, dy, game.dungeon, game.monsters, game.remaining_speed)
                                    
                                    # Check if moved to stairs
                                    if moved and game.dungeon.grid[game.adventurer.y][game.adventurer.x] == TileType.STAIRS:
                                        game.game_state = "level_complete"
                                        game.message = "Level complete! Choose to upgrade a skill or heal."
                
                elif game.game_state == "level_complete":
                    options = ["speed", "attack", "defense", "range", "heal"]
                    for i, option in enumerate(options):
                        if 20 + i*150 <= x <= 140 + i*150 and button_y <= y <= button_y + BUTTON_HEIGHT:
                            game.advance_level(option)
                            
                elif game.game_state == "game_over" or game.game_state == "victory":
                    if SCREEN_WIDTH//2 - 60 <= x <= SCREEN_WIDTH//2 + 60 and button_y <= y <= button_y + BUTTON_HEIGHT:
                        game = Game()  # Start a new game
                        selected_dice = None  # Reset selection for new game
            
            elif event.type == pygame.KEYDOWN:
                if game.game_state == "adventurer":
                    # Movement with arrow keys
                    dx, dy = 0, 0
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        dy = -1
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        dy = 1
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        dx = -1
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        dx = 1
                        
                    if dx != 0 or dy != 0:
                        moved, game.remaining_speed = game.adventurer.move(dx, dy, game.dungeon, game.monsters, game.remaining_speed)
                        
                        # Check if moved to stairs
                        if moved and game.dungeon.grid[game.adventurer.y][game.adventurer.x] == TileType.STAIRS:
                            game.game_state = "level_complete"
                            game.message = "Level complete! Choose to upgrade a skill or heal."
        
        # Modify the draw_game function to show selected dice
        draw_game(game, selected_dice)
        
        # Limit FPS
        pygame.time.Clock().tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()