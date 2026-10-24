#### IMPORT LIBRARIES ####
import pygame
import random
import time

# Screen parameters
screen_width = 1000
screen_height = 800


# Function that sets up the game window
def setup():
    global screen
    global clock
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))  # Screen
    pygame.display.set_caption("Battleship")  # Title for screen

    clock = pygame.time.Clock()

    # Background
    global bg
    bg = pygame.image.load('bg.jpg')
    bg = pygame.transform.scale(bg, (screen_width, screen_height))


# Text class with background feature
class Text(object):
    def __init__(self, text, font_name, text_size, pos_x_text, pos_y_text):
        self.text = text
        self.font_name = font_name
        self.text_size = text_size
        self.pos_x_text = pos_x_text
        self.pos_y_text = pos_y_text
        self.font = pygame.font.Font(font_name, text_size)
        self.text_surf, self.text_rect = self.text_objects(text, self.font)
        self.draw_text()

    def text_objects(self, text, font):
        text_surface = font.render(text, True, (0, 0, 0))
        return text_surface, text_surface.get_rect()

    def draw_text(self):
        self.text_rect.center = (self.pos_x_text, self.pos_y_text)
        screen.blit(self.text_surf, self.text_rect)

    def draw_bg(self, length, width, x, y, color):
        pygame.draw.rect(screen, color, (x, y, length, width))


# Board class
class Board(object):
    def __init__(self, box_size, amount_boxes):
        self.box_size = box_size
        self.amount_boxes = amount_boxes
        self.row_start = 50
        self.column_start = 50
        self.comp_board = []
        self.bomb_board = []
        self.hit_ships = 0
        self.used_bombs = 0
        self.check_result = None

    def draw(self, win, placing=False):  # Function that draws the board
        y = self.row_start
        list_x = 0
        for row in self.comp_board:
            x = self.column_start
            list_y = 0
            for col in row:
                if placing:
                    if self.comp_board[list_x][list_y] != 'O':
                        pygame.draw.rect(win, (255, 0, 0), (x, y, self.box_size, self.box_size))
                    else:
                        pygame.draw.rect(win, (0, 0, 255), (x, y, self.box_size, self.box_size))
                elif self.bomb_board[list_x][list_y] == 'O':
                    pygame.draw.rect(win, (0, 0, 255), (x, y, self.box_size, self.box_size))

                else:
                    if self.comp_board[list_x][list_y] != 'O':
                        pygame.draw.rect(win, (255, 0, 0), (x, y, self.box_size, self.box_size))
                    else:
                        pygame.draw.rect(win, (0, 0, 0), (x, y, self.box_size, self.box_size))
                x += self.box_size + 4
                list_y += 1
            y += self.box_size + 4
            list_x += 1

    def create_board(self):  # Function that makes two-dimensional lists that store the data for the board
        self.hit_ships = 0
        self.used_bombs = 0
        self.bomb_board = []
        self.comp_board = []

        # For loop that makes the rows and columns for the bomb board and the comp board
        for x in range(0, self.amount_boxes):
            # Making the row
            self.comp_board.append([])
            self.bomb_board.append([])

            for y in range(0, self.amount_boxes):
                # Filling the row with empty spaces
                self.comp_board[x].append('O')
                self.bomb_board[x].append('O')

    # Function that places a ship on the board
    def place_ship(self, ship, ship_size, direction, x, y, grid):
        if direction == 1:
            if y + ship_size > len(grid[x]):
                #############  GOING LEFT  ############
                # While loop that runs until every square around the ship has been checked.
                i = 0
                while i < ship_size:
                    # Checking if the ship has been placed at the top of the board.
                    # That means only checking the bottom.
                    if x == 0:
                        if grid[x+1][y-i] != 'O':
                            return False
                    # Checking if the ship has been placed at the bottom of the board.
                    # That means only checking the top.
                    elif x == len(grid)-1:
                        if grid[x-1][y-i] != 'O':
                            return False
                    # If the ship hasn't been placed at the top or bottom, check the top and bottom for another ship.
                    elif grid[x-1][y-i] != 'O' or grid[x+1][y-i] != 'O':
                        return False
                    # Going to the next square
                    i += 1

                # Checking if there is a ship in front of or behind the placed ship
                if y+1 < len(grid[x])-1:
                    if grid[x][y+1] != 'O':
                        return False
                if y-ship_size > 0:
                    if grid[x][y-ship_size] != 'O':
                        return False

                # For loop that places the ship if there isn't a ship already there.
                for i in range(y, y-ship_size, -1):
                    if grid[x][i] == 'O':
                        grid[x][i] = ship
                    else:
                        return False
                return True
            else:
                ########################  GOING RIGHT  ########################
                # Same code as with GOING LEFT but going from left to right.
                i = 0
                while i < ship_size:
                    if x == 0:
                        if grid[x+1][y+i] != 'O':
                            return False
                    elif x == len(grid)-1:
                        if grid[x-1][y+i] != 'O':
                            return False
                    elif grid[x-1][y+i] != 'O' or grid[x+1][y+i] != 'O':
                        return False
                    i += 1

                if y+ship_size < len(grid[x])-1:
                    if grid[x][y+ship_size] != 'O':
                        return False
                if y-1 > 0:
                    if grid[x][y-1] != 'O':
                        return False
                try:
                    if grid[x][y+ship_size] != 'O':
                        return False
                except:
                    pass

                for i in range(y, y+ship_size):
                    if grid[x][i] == 'O':
                        grid[x][i] = ship
                    else:
                        return False
                return True
        elif direction == 2:
            # Direction is VERTICAL so check whether you have to go UP or DOWN
            if x + ship_size > len(grid):
                ########################  GOING UP  ########################
                # Same code as with GOING LEFT but altered to go UP.
                i = 0
                while i < ship_size:
                    if y == 0:
                        if grid[x-i][y+1] != 'O':
                            return False
                    elif y == len(grid[x])-1:
                        if grid[x-i][y-1] != 'O':
                            return False
                    elif grid[x-i][y-1] != 'O' or grid[x-i][y+1] != 'O':
                        return False
                    i += 1

                if x+1 < len(grid)-1:
                    if grid[x+1][y] != 'O':
                        return False
                if x-ship_size > 0:
                    if grid[x-ship_size][y] != 'O':
                        return False

                for i in range(x, x-ship_size, -1):
                    if grid[i][y] == 'O':
                        grid[i][y] = ship
                    else:
                        return False
                return True
            else:
                ########################  GOING DOWN  ########################
                # Same code as with GOING LEFT but altered to go DOWN.
                i = 0
                while i < ship_size:
                    if y == 0:
                        if grid[x+i][y+1] != 'O':
                            return False
                    elif y == len(grid[x])-1:
                        if grid[x+i][y-1] != 'O':
                            return False
                    elif grid[x+i][y-1] != 'O' or grid[x+i][y+1] != 'O':
                        return False
                    i += 1

                if x+ship_size < len(grid)-1:
                    if grid[x+ship_size][y] != 'O':
                        return False
                if x-1 > 0:
                    if grid[x-1][y] != 'O':
                        return False

                for i in range(x, x+ship_size):
                    if grid[i][y] == 'O':
                        grid[i][y] = ship
                    else:
                        return False

                return True

    def find_coordinates(self, x, y):
        # Getting the starting coordinates.
        row = self.row_start
        column = self.column_start

        # Counter variables for X and Y axis.
        x_counter = 0
        y_counter = 0

        # Boolean variable to close the while loop when it is done.
        row_not_done = True

        # While loop that runs until the boolean is set to FALSE and x_counter is smaller than the amount of squares.
        while row_not_done and x_counter < self.amount_boxes:

            # Checking if x is bigger than the row coordinate and smaller than the row coordinate + the size of the box.
            if x > row and x < row+self.box_size+4:

                # Give x_coor the value of x_counter so the place in the list can be found.
                x_coor = x_counter

                # While loop that runs until the boolean is set to FALSE and y_counter is smaller than the amount of squares.
                while row_not_done and y_counter < self.amount_boxes:

                    # Checking if y is bigger than the column coordinate and smaller than the column coordinate + the size of the box.
                    if y > column and y < column+self.box_size+4:

                        # Giving y_coor the value of y_counter so the place in the list can be found.
                        y_coor = y_counter

                        # Set boolean to FALSE
                        row_not_done = False

                        return x_coor, y_coor

                    else:
                        # Go a column down. Size is the size of a square, in this case 'box_size'.
                        column = column+self.box_size+4

                    # Add 1 to y_counter
                    y_counter += 1
            else:
                # Move row to the right and check again. Size is the size of a square, in this case 'box_size'.
                row = row+self.box_size+4

            # Add 1 to x_counter
            x_counter += 1

    def check_board(self, x, y, hit_ships, used_bombs, win):  # Function that checks if a ship has been hit or not.
        global player
        try:
            x_coor, y_coor = self.find_coordinates(x, y)
            # Check if there is a ship at y_coor and x_coor.
            if self.comp_board[y_coor][x_coor] != 'O':

                # There is a ship.
                if self.bomb_board[y_coor][x_coor] == 'O':
                    self.bomb_board[y_coor][x_coor] = 'X'
                    self.hit_ships += 1
                    self.used_bombs += 1
                    return True
                else:
                    return False
            else:
                # There is no ship.
                if self.bomb_board[y_coor][x_coor] == 'O':
                    self.bomb_board[y_coor][x_coor] = 'X'
                    self.used_bombs += 1
                    return True
                else:
                    return False
        except:
            return False


# Function to update the screen.
def redraw_game_screen(player):
    # Update screen and add background image
    screen.blit(bg, (0, 0))

    # Check which player it is and if it is SINGLEPLAYER or MULTIPLAYER.
    if player == 1:
        player2.draw(screen)
        player_name = Text('Player 1, it is your turn', 'secret.ttf', 30, 700, 750)
    elif player == 2:
        player1.draw(screen)
        player_name = Text('Player 2, it is your turn', 'secret.ttf', 30, 700, 750)
    else:
        board.draw(screen)
    # Add exit button
    exit_btn = Text('Stop', 'secret.ttf', 30, 900, 100)
    # Update the screen.
    pygame.display.update()


# Function that shows the screen with the winner.
def game_won(winner, bombs, loser=None, loser_ships=None):
    global clock
    winner_text = 'Player ' + str(winner) + ' has won!'
    bombs_thrown = str(bombs) + ' bombs were thrown'
    loser_message = 'Player ' + str(loser) + ' has hit ' + str(loser_ships) + ' ships'

    # While loop that runs until the user wants to close the screen.
    run = True
    while run:
        clock.tick(27)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                run = False
        screen.blit(bg, (0, 0))
        if winner != 0:
            winner_label = Text(winner_text, 'secret.ttf', 50, 500, 100)
            loser_label = Text(loser_message, 'secret.ttf', 25, 500, 570)
        else:
            single_winner = Text('You won!', 'secret.ttf', 50, 500, 100)
        thrown_label = Text(bombs_thrown, 'secret.ttf', 25, 500, 620)

        back_label = Text('Click anywhere on the screen to go back...', 'secret.ttf', 20, 500, 770)

        pygame.display.update()


# Ship class
class Ship(object):
    def __init__(self, ship_size, direction, ship, block_size):
        self.ship_size = ship_size
        self.direction = direction  # 1 is Horizontal, 2 is Vertical
        self.ship = ship
        self.block_size = block_size

    # Function that draws the ship according to the direction.
    def draw_ship(self, x, y, block_size, ship_size):
        for piece in range(0, ship_size):
            pygame.draw.rect(screen, (0, 0, 0), (x, y, block_size, block_size))
            if self.direction == 1:
                x += block_size + 4
            elif self.direction == 2:
                y += block_size + 4

    # Function that changes the direction of the ship.
    def switch_direction(self):
        if self.direction == 1:
            self.direction = 2
        elif self.direction == 2:
            self.direction = 1


# Function to display the screen in which a player can drag and drop their ships onto the board.
def drag_and_drop(player_board):
    global clock
    global player
    global bg
    screen = pygame.display.set_mode((screen_width+200, screen_height))
    bg = pygame.transform.scale(bg, (screen_width+200, screen_height))
    run_drag = True
    clicked = False
    ships = [Ship(5, 1, 'S', 60), Ship(4, 1, 'K', 60), Ship(3, 1, 'F', 60), Ship(3, 1, 'F', 60), Ship(2, 1, 'M', 60)]

    player_board.create_board()
    mouse_x, mouse_y = 800, 400

    # While loop that runs until the player has dropped all ships in.
    i = 0
    while run_drag:
        clock.tick(27)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run_player = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    clicked = True
                    x, y = event.pos
                    if x > 870 and x < 988 and y > 685 and y < 718:
                        ships[i].switch_direction()

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:

                    clicked = False
                    if mouse_x > 50 and mouse_x < 680 and mouse_y > 50 and mouse_y < 690:
                        board_y, board_x = player_board.find_coordinates(mouse_x, mouse_y)
                        if ships[i].direction == 1:
                            if board_y + ships[i].ship_size <= len(player_board.comp_board[board_x]):
                                print(board_x, board_y)
                                if player_board.place_ship(ships[i].ship, ships[i].ship_size, ships[i].direction, board_x, board_y, player_board.comp_board):
                                    i += 1
                                    mouse_x, mouse_y = 800, 400
                                else:
                                    mouse_x, mouse_y = 800, 400
                            else:
                                mouse_x, mouse_y = 800, 400
                        else:
                            if board_x + ships[i].ship_size <= len(player_board.comp_board):
                                print(board_x, board_y)
                                if player_board.place_ship(ships[i].ship, ships[i].ship_size, ships[i].direction, board_x, board_y, player_board.comp_board):
                                    i += 1
                                    mouse_x, mouse_y = 800, 400
                                else:
                                    mouse_x, mouse_y = 800, 400
                            else:
                                mouse_x, mouse_y = 800, 400

            elif event.type == pygame.MOUSEMOTION:
                if clicked:
                    mouse_x, mouse_y = event.pos

        if i == len(ships):
            run_drag = False
            i = 0

        # Update screen
        screen.blit(bg, (0, 0))
        switch_btn = Text('SWITCH', 'secret.ttf', 30, 930, 700)
        player_board.draw(screen, True)
        ships[i].draw_ship(mouse_x-20, mouse_y-20, ships[i].block_size, ships[i].ship_size)
        info = Text("Player X, it's your turn", 'secret.ttf', 30, 930, 100)
        rules_title = Text('RULES', 'secret.ttf', 30, 915, 150)
        rules_1 = Text('1. Place the ship on the board.', 'secret.ttf', 21, 895, 200)
        rules_2 = Text("2. Don't put it next to another ship", 'secret.ttf', 21, 935, 250)
        pygame.display.flip()

    # If done, put the screen back to its original size.
    screen = pygame.display.set_mode((screen_width, screen_height))
    bg = pygame.transform.scale(bg, (screen_width, screen_height))


# Function that starts the game
def start_game():
    global player
    global clock
    global board
    global player1
    global player2
    run = True

    if player != None:
        print('-- Player 1 --')
        player1 = Board(60, 10)
        drag_and_drop(player1)

        for row in player1.comp_board:
            print(row)

        print('-- Player 2 --')
        player2 = Board(60, 10)
        drag_and_drop(player2)

        for row in player2.comp_board:
            print(row)

        print('Player 1 starts')
    else:  # SINGLEPLAYER
        board = Board(60, 10)
        board.create_board()
        # Placing Battleship
        while not board.place_ship('S', 5, random.randint(1, 2), random.randint(0, board.amount_boxes-1), random.randint(0, board.amount_boxes-1), board.comp_board):
            print()

        # Placing Cruiser
        while not board.place_ship('K', 4, random.randint(1, 2), random.randint(0, board.amount_boxes-1), random.randint(0, board.amount_boxes-1), board.comp_board):
            print()

        # Placing first frigate
        while not board.place_ship('F', 3, random.randint(1, 2), random.randint(0, board.amount_boxes-1), random.randint(0, board.amount_boxes-1), board.comp_board):
            print()

        # Placing second frigate
        while not board.place_ship('F', 3, random.randint(1, 2), random.randint(0, board.amount_boxes-1), random.randint(0, board.amount_boxes-1), board.comp_board):
            print()

        # Placing minesweeper
        while not board.place_ship('M', 2, random.randint(1, 2), random.randint(0, board.amount_boxes-1), random.randint(0, board.amount_boxes-1), board.comp_board):
            print()
        for row in board.comp_board:
            print(row)

    #### WHILE LOOP THAT RUNS THE GAME ####
    while run:
        clock.tick(27)
        #### For loop that handles the events happening in the game ####
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos_click = pygame.mouse.get_pos()
                if pos_click[0] > 855 and pos_click[0] < 940 and pos_click[1] > 80 and pos_click[1] < 120:
                    run = False
                if player == 1:
                    if pos_click[0] > 50 and pos_click[0] < 50 + (player2.box_size + 4)*10 and pos_click[1] > 50 and pos_click[1] < 50 + (player2.box_size + 4)*10:
                        player2.check_result = player2.check_board(pos_click[0], pos_click[1], 0, 0, screen)
                        redraw_game_screen(player)
                        time.sleep(0.5)
                        if player2.check_result == True:
                            player = 2
                        if player2.hit_ships == 17:
                            game_won(1, player1.used_bombs, 2, player2.hit_ships)
                            run = False
                        redraw_game_screen(player)
                elif player == 2:
                    if pos_click[0] > 50 and pos_click[0] < 50 + (player1.box_size + 4)*10 and pos_click[1] > 50 and pos_click[1] < 50 + (player1.box_size + 4)*10:
                        player1.check_result = player1.check_board(pos_click[0], pos_click[1], 0, 0, screen)
                        redraw_game_screen(player)
                        time.sleep(0.5)
                        if player1.check_result == True:
                            player = 1
                        if player1.hit_ships == 17:
                            game_won(2, player2.used_bombs, 1, player1.hit_ships)
                            run = False
                        redraw_game_screen(player)
                else:
                    board.check_result = board.check_board(pos_click[0], pos_click[1], 0, 0, screen)
                    if board.hit_ships == 17:
                        game_won(0, board.used_bombs)
                        run = False
        redraw_game_screen(player)


def start_menu():
    setup()
    global clock
    global player
    intro = True
    # While loop that runs until an event has happened in the menu
    while intro:
        clock.tick(27)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                intro = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos_click = pygame.mouse.get_pos()
                if pos_click[0] > 350 and pos_click[0] < 650:
                    if pos_click[1] > 400 and pos_click[1] < 450:
                        print('singleplayer')
                        player = None
                        start_game()
                    elif pos_click[1] > 500 and pos_click[1] < 550:
                        print('multiplayer')
                        player = 1
                        start_game()

        screen.blit(bg, (0, 0))
        large_text = pygame.font.Font('secret.ttf', 115)
        small_text = pygame.font.Font('secret.ttf', 30)
        title = Text('Battleship', 'secret.ttf', 115, screen_width/2, screen_height/4)

        singleplayer_btn = Text('singleplayer', 'secret.ttf', 30, 500, 420)
        multiplayer_btn = Text('multiplayer', 'secret.ttf', 30, 500, 520)
        pygame.display.update()
    pygame.quit()


# Starting program with start_menu if run from this script.
if __name__ == "__main__":
    start_menu()
