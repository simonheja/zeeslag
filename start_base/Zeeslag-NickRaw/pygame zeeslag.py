#### IMPORT LIBRARIES ####
import pygame
import random
import time

# Screen parameters
screenwidth = 1000
screenheight = 800

# Function that starts the game
def setup():
      global screen
      global clock
      pygame.init()
      screen = pygame.display.set_mode((screenwidth, screenheight)) # Screen
      pygame.display.set_caption("Battleship") # Title for screen

      clock = pygame.time.Clock()

      # Background
      global bg
      bg = pygame.image.load('bg.jpg')
      bg = pygame.transform.scale(bg, (screenwidth, screenheight))

# Button class with background feature
class tekst(object):
      def __init__(self, text, fontname, textsize, posX_text, posY_text):
            self.text = text
            self.fontname = fontname
            self.textsize = textsize
            self.posX_text = posX_text
            self.posY_text = posY_text
            self.font = pygame.font.Font(fontname, textsize)
            self.textSurf, self.textRect = self.text_objects(text, self.font)
            self.drawTekst()

      def text_objects(self, text, font):
            textSurface = font.render(text, True, (0,0,0))
            return textSurface, textSurface.get_rect()

      def drawTekst(self):
            self.textRect.center = (self.posX_text, self.posY_text)
            screen.blit(self.textSurf, self.textRect)

      def drawBG(self, length, width, X, Y, color):
            pygame.draw.rect(screen, color,(X,Y,length,width))

# Board class
class board(object):
      def __init__(self, box_size, amount_boxes):
            self.box_size = box_size
            self.amount_boxes = amount_boxes
            self.rowstart = 50
            self.kolomstart = 50
            self.compbord = []
            self.bombord = []
            self.hit_ships = 0
            self.used_bombs = 0
            self.check_result = None

      def draw(self, win, bordmaken = False): # Function that draws the board
            y = self.rowstart
            list_x = 0
            for row in self.compbord:
                  x = self.kolomstart
                  list_y = 0
                  for col in row:
                        if bordmaken:
                              if self.compbord[list_x][list_y] != 'O':
                                    pygame.draw.rect(win, (255,0,0), (x,y,self.box_size,self.box_size))
                              else:
                                    pygame.draw.rect(win, (0,0,255), (x,y,self.box_size,self.box_size))
                        elif self.bombord[list_x][list_y] == 'O':
                              pygame.draw.rect(win, (0,0,255), (x,y,self.box_size,self.box_size))
                        
                        else:
                              if self.compbord[list_x][list_y] != 'O':
                                    pygame.draw.rect(win, (255,0,0), (x,y,self.box_size,self.box_size))
                              else:
                                    pygame.draw.rect(win, (0,0,0), (x,y,self.box_size,self.box_size))
                        x+=self.box_size+4
                        list_y += 1
                  y+=self.box_size+4
                  list_x += 1

      
      def bordmaker(self): # Function that makes a twodimensional list that stores the data for the board
            self.hit_ships = 0
            self.used_bombs = 0
            self.bombord = []
            self.compbord = []

            # For loop that makes the rows and colums for the bombbord and the compbord
            for x in range(0, self.amount_boxes):
                  # Making the row
                  self.compbord.append([])
                  self.bombord.append([])

                  for y in range(0, self.amount_boxes):
                        # Filling the row with empty spaces
                        self.compbord[x].append('O')
                        self.bombord[x].append('O')

      # Function that places a ship in the compbord
      def schip_plaatser(self, schip, schipsize, richting, x, y, bord): # Functie die het schip plaatst in het bord
            if richting == 1:
                  if y + schipsize > len(bord[x]):
                        #############  GOING LEFT  ############
                        # While loop that runs until every square around the ship has been checkt.
                        i = 0
                        while i < schipsize:
                              # Checking if the ship has been placed at the top of the board.
                              # That means only checking the bottom.
                              if x == 0:
                                    if bord[x+1][y-i] != 'O':
                                          return False
                              # Checking if the ship has been placed at the bottom of the board.
                              # That means only checking the top.
                              elif x == len(bord)-1:
                                    if bord[x-1][y-i] != 'O':
                                          return False
                              # If the ship hasn't been placed at the top or bottom than you can check the top and bottom for another ship.
                              elif bord[x-1][y-i] != 'O' or bord[x+1][y-i] != 'O':
                                    return False
                              # Going to the next square
                              i+=1

                        # Checking if there is a ship in front or behind the placed ship
                        if y+1 < len(bord[x])-1:
                              if bord[x][y+1] != 'O':
                                    return False
                        if y-schipsize > 0:
                              if bord[x][y-schipsize] != 'O':
                                    return False

                        # For loop that places the ship if there isn't a ship already there.
                        for i in range(y, y-schipsize, -1):
                              if bord[x][i] == 'O':
                                    bord[x][i] = schip
                              else:
                                    return False
                        return True
                  else:
                        ########################  GOING RIGHT  ########################
                        # Same code as with GOING LEFT but then going from left to right.
                        i = 0
                        while i < schipsize:
                              if x == 0:
                                    if bord[x+1][y+i] != 'O':
                                          return False
                              elif x == len(bord)-1:
                                    if bord[x-1][y+i] != 'O':
                                          return False
                              elif bord[x-1][y+i] != 'O' or bord[x+1][y+i] != 'O':
                                    return False
                              i+=1
                        
                        if y+schipsize < len(bord[x])-1:
                              if bord[x][y+schipsize] != 'O':
                                    return False
                        if y-1 > 0:
                              if bord[x][y-1] != 'O':
                                    return False
                        try:
                              if bord[x][y+schipsize] != 'O':
                                    return False
                        except:
                              pass
                              
                        
                        for i in range(y, y+schipsize):
                              if bord[x][i] == 'O':
                                    bord[x][i] = schip
                              else:
                                    return False
                        return True
            elif richting == 2:
                  # Direction is VERTICAL so checking if you have to go UP or DOWN
                  if x + schipsize > len(bord):
                        ########################  GOING UP  ########################
                        # Same code as with GOING LEFT but then altered to going UP.
                        i = 0
                        while i < schipsize:
                              if y == 0:
                                    if bord[x-i][y+1] != 'O':
                                          return False
                              elif y == len(bord[x])-1:
                                    if bord[x-i][y-1] != 'O':
                                          return False
                              elif bord[x-i][y-1] != 'O' or bord[x-i][y+1] != 'O':
                                    return False
                              i+=1

                        if x+1 < len(bord)-1:
                              if bord[x+1][y] != 'O':
                                    return False
                        if x-schipsize > 0:
                              if bord[x-schipsize][y] != 'O':
                                    return False
                        
                        for i in range(x, x-schipsize, -1):
                              if bord[i][y] == 'O':
                                    bord[i][y] = schip
                              else:
                                    return False
                        return True
                  else:
                        ########################  GOING DOWN  ########################
                        # Same code as with GOING LEFT but then altered to going DOWN.
                        i = 0
                        while i < schipsize:
                              if y == 0:
                                    if bord[x+i][y+1] != 'O':
                                          return False
                              elif y == len(bord[x])-1:
                                    if bord[x+i][y-1] != 'O':
                                          return False
                              elif bord[x+i][y-1] != 'O' or bord[x+i][y+1] != 'O':
                                    return False
                              i+=1

                        
                        if x+schipsize < len(bord)-1:
                              if bord[x+schipsize][y] != 'O':
                                    return False
                        if x-1 > 0:
                              if bord[x-1][y] != 'O':
                                    return False

                        for i in range(x, x+schipsize):
                              if bord[i][y] == 'O':
                                    bord[i][y] = schip
                              else:
                                    return False

                        return True


      def coor_vinder(self, x, y):
            # Getting the starting coördinates.
            rij = self.rowstart
            kolom = self.kolomstart

            # Counter variables for X and Y axis.
            x_counter = 0
            y_counter = 0

            # Boolean variable to close the while loop when it is done.
            rij_niet_klaar = True

            # While loop that runs until boolean is set to FALSE and x_counter is smaller that the amount of squares.
            while rij_niet_klaar and x_counter < self.amount_boxes:

                  # Checking if the x value bigger is than the row coördinate and smaller is than the row coördinate + the size of the box.
                  if x > rij and x < rij+self.box_size+4:

                        # Give value x_coor the value of x_counter so the place in the list can be found.
                        x_coor = x_counter

                        # While loop that runs until boolean is set to FALSE and y_counter smaller is than the amount of squares.
                        while rij_niet_klaar and y_counter < self.amount_boxes:

                              # Checking if the y value smaller is than the column coördinate and smaller is than the column coördinate - the size of the box.
                              if y > kolom and y < kolom+self.box_size+4:

                                    # Giving y_coor the value of y_counter so the place in the list can be found.
                                    y_coor = y_counter

                                    # Set boolean to FALSE
                                    rij_niet_klaar = False

                                    return x_coor, y_coor

                              else:
                                    # Go a column down. Size is size of square in this case 'boxsize'.
                                    kolom = kolom+self.box_size+4

                              # 1 bij y_counter optellen
                              y_counter+=1
                  else:
                        # Move row to the right and check again. Size is size of square in this case 'boxsize'.
                        rij = rij+self.box_size+4

                  # Add 1 to x_counter
                  x_counter+=1
      
      def bordchecker(self, x, y, hit_ships, used_bombs, win): # Function that checks if ship has been hit or not.
            global player
            try:
                  x_coor, y_coor = self.coor_vinder(x, y)
                  # Check if at place y_coor and x_coor a ship is.
                  if self.compbord[y_coor][x_coor] != 'O':

                        # There is a ship.
                        if self.bombord[y_coor][x_coor] == 'O':
                              self.bombord[y_coor][x_coor] = 'X'
                              self.hit_ships+=1
                              self.used_bombs+=1
                              return True
                        else:
                              return False
                  else:
                        # There is no ship.
                        if self.bombord[y_coor][x_coor] == 'O':
                              self.bombord[y_coor][x_coor] = 'X'
                              self.used_bombs+=1
                              return True
                        else:
                              return False
            except:
                  return False


# Function to update the screen.
def redrawgamescreen(player):
      # Update screen and add background img
      screen.blit(bg, (0,0))

      # Check which player it is and if it is SINGLEPLAYER or MULTIPLAYER.
      if player == 1:
            player2.draw(screen)
            playerName = tekst('Player 1 is aan de beurt', 'secret.ttf', 30, 700, 750)
      elif player == 2:
            player1.draw(screen)
            playerName = tekst('Player 2 is aan de beurt', 'secret.ttf', 30, 700, 750)
      else:
            bord.draw(screen)
      # Add exitbutton
      exitBTN = tekst('Stop', 'secret.ttf', 30, 900, 100)
      # Update the screen.
      pygame.display.update()

# Funtion that shows screen with the winner.
def gewonnen(winnaar, bommen, verliezer = None, schepen_verliezer = None):
      global clock
      gewonnen_speler = 'Speler '+str(winnaar)+' heeft gewonnen!'
      bommen_gegooid = str(bommen)+' bommen zijn er gegooid'
      verloren_speler = 'Speler '+str(verliezer)+' heeft '+str(schepen_verliezer)+' schepen geraakt'

      # While loop that runs until user wants to close the screen.
      run = True
      while run:
            clock.tick(27)
            for event in pygame.event.get():
                  if event.type ==pygame.QUIT:
                        run = False
                  if event.type == pygame.MOUSEBUTTONDOWN:
                        run = False
            screen.blit(bg, (0,0))
            if winnaar != 0:
                  gewonnen_winnaar = tekst(gewonnen_speler, 'secret.ttf', 50, 500, 100)
                  verliezer = tekst(verloren_speler, 'secret.ttf', 25, 500, 570)
            else:
                  single_winnaar = tekst('You won!', 'secret.ttf', 50, 500, 100)
            gegooid = tekst(bommen_gegooid, 'secret.ttf', 25, 500, 620)
            
            terug = tekst('Click anywhere on the screen to get back...', 'secret.ttf', 20, 500, 770)
            
            pygame.display.update()

# Ship class
class schip(object):
      def __init__(self, schipgrootte, richting, schip, blokgrootte):
            self.schipgrootte = schipgrootte
            self.richting = richting # 1 is Horizontal 2 is Vertical
            self.schip = schip
            self.blokgrootte = blokgrootte

      # Function that draws the ship according to the direction.
      def draw_ship(self, x, y, bloksize, shipsize):
            for piece in range(0,shipsize):
                  pygame.draw.rect(screen, (0,0,0), (x,y,bloksize,bloksize))
                  if self.richting == 1:
                        x+=bloksize+4
                  elif self.richting == 2:
                        y+=bloksize+4

      # Function that changes the direction of the ship.
      def switch_oor(self):
            if self.richting == 1:
                  self.richting = 2
            elif self.richting == 2:
                  self.richting = 1

# Function to display the screen in which a player can drag and drop their ship in the board.
def draganddrop(speler):
      global clock
      global player
      global bg
      screen = pygame.display.set_mode((screenwidth+200, screenheight))
      bg = pygame.transform.scale(bg, (screenwidth+200, screenheight))
      run_drag = True
      clicked = False
      schepen = [schip(5, 1, 'S', 60), schip(4, 1, 'K', 60), schip(3, 1, 'F', 60), schip(3, 1, 'F', 60), schip(2, 1, 'M', 60)]
      
      speler.bordmaker()
      mosx,mosy = 800,400

      # While loop that runs until player has dropped all ships in.
      i = 0
      while run_drag:
            clock.tick(27)
            
            for event in pygame.event.get():
                  if event.type == pygame.QUIT:
                        run_player = False
                        
                  elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:
                              clicked = True
                              x,y = event.pos
                              if x > 870 and x < 988 and y > 685 and y < 718:
                                    schepen[i].switch_oor()
                              
                  elif event.type == pygame.MOUSEBUTTONUP:
                        if event.button == 1:
                              
                              clicked = False
                              if mosx > 50 and mosx < 680 and mosy > 50 and mosy < 690:
                                    bory, borx = speler.coor_vinder(mosx, mosy)
                                    if schepen[i].richting == 1:
                                          if bory + schepen[i].schipgrootte <= len(speler.compbord[borx]):
                                                print(borx,bory)
                                                if speler.schip_plaatser(schepen[i].schip, schepen[i].schipgrootte, schepen[i].richting, borx, bory, speler.compbord):
                                                      i+=1
                                                      mosx,mosy = 800,400
                                                else:
                                                      mosx,mosy = 800,400
                                          else:
                                                mosx,mosy = 800,400
                                    else:
                                          if borx + schepen[i].schipgrootte <= len(speler.compbord):
                                                print(borx,bory)
                                                if speler.schip_plaatser(schepen[i].schip, schepen[i].schipgrootte, schepen[i].richting, borx, bory, speler.compbord):
                                                      i+=1
                                                      mosx,mosy = 800,400
                                                else:
                                                      mosx,mosy = 800,400
                                          else:
                                                mosx,mosy = 800,400
                                          
                                          
                  elif event.type == pygame.MOUSEMOTION:
                        if clicked:
                              mosx,mosy = event.pos
                              
            if i == len(schepen):
                  run_drag = False
                  i = 0
            
            
            # Update screen                        
            screen.blit(bg, (0,0))
            turnBTN = tekst('SWITCH', 'secret.ttf', 30, 930, 700)
            speler.draw(screen, True)
            schepen[i].draw_ship(mosx-20,mosy-20,schepen[i].blokgrootte,schepen[i].schipgrootte)
            info = tekst("Speler X it's your turn", 'secret.ttf', 30, 930, 100)
            uitlegtitle = tekst('RULES', 'secret.ttf', 30, 915, 150)
            uitleg = tekst('1. Place the ship on the bord.', 'secret.ttf', 21, 895, 200)
            uitleg_2 = tekst("2. Don't put it next to another ship", 'secret.ttf', 21, 935, 250)
            pygame.display.flip()
            
      # If done put screen back to original sizes.
      screen = pygame.display.set_mode((screenwidth, screenheight))
      bg = pygame.transform.scale(bg, (screenwidth, screenheight))

# Function that starts the game
def gamestart():
      global player
      global clock
      global bord
      global player1
      global player2
      run = True

      if player != None:
            print('-- Player 1 --')
            player1 = board(60, 10)
            draganddrop(player1)

            for row in player1.compbord:
                  print(row)
                  
            print('-- Player 2 --')
            player2 = board(60, 10)
            draganddrop(player2)

            for row in player2.compbord:
                  print(row)
                  
            print('Player 1 begint')
      else: # SINGLEPLAYER
            bord = board(60, 10)
            bord.bordmaker()
            # Placing Battleship
            while not bord.schip_plaatser('S', 5, random.randint(1,2), random.randint(0,bord.amount_boxes-1), random.randint(0,bord.amount_boxes-1), bord.compbord):
                  print()

            # Placing Kruiser
            while not bord.schip_plaatser('K', 4,  random.randint(1,2), random.randint(0,bord.amount_boxes-1), random.randint(0,bord.amount_boxes-1), bord.compbord):
                  print()

            # Placing First fregat
            while not bord.schip_plaatser('F', 3,  random.randint(1,2), random.randint(0,bord.amount_boxes-1), random.randint(0,bord.amount_boxes-1), bord.compbord):
                  print()

            # Placing Second fregat
            while not bord.schip_plaatser('F', 3,  random.randint(1,2), random.randint(0,bord.amount_boxes-1), random.randint(0,bord.amount_boxes-1), bord.compbord):
                  print()

            # Placing Minesweeper
            while not bord.schip_plaatser('M', 2,  random.randint(1,2), random.randint(0,bord.amount_boxes-1), random.randint(0,bord.amount_boxes-1), bord.compbord):
                  print()
            for row in bord.compbord:
                  print(row)
      
      #### WHILE LOOP THAT RUNS THE GAME ####
      while run:
            clock.tick(27)
            #### For loop than handeles the events happening in the game ####
            for event in pygame.event.get():
                  if event.type == pygame.QUIT:
                        run = False
                  if event.type == pygame.MOUSEBUTTONDOWN:
                        pos_click = pygame.mouse.get_pos()
                        if pos_click[0] > 855 and pos_click[0] < 940 and pos_click[1] > 80 and pos_click[1] < 120:
                              run = False
                        if player == 1:
                              if pos_click[0] > 50 and pos_click[0] < 50 + (player2.box_size + 4)*10 and pos_click[1] > 50 and pos_click[1] < 50 + (player2.box_size + 4)*10:
                                    player2.check_result = player2.bordchecker(pos_click[0], pos_click[1], 0, 0, screen)
                                    redrawgamescreen(player)
                                    time.sleep(0.5)
                                    if player2.check_result == True:
                                          player = 2
                                    if player2.hit_ships == 17:
                                          gewonnen(1, player1.used_bombs, 2, player2.hit_ships)
                                          run = False
                                    redrawgamescreen(player)
                        elif player == 2:
                              if pos_click[0] > 50 and pos_click[0] < 50 + (player1.box_size + 4)*10 and pos_click[1] > 50 and pos_click[1] < 50 + (player1.box_size + 4)*10:
                                    player1.check_result = player1.bordchecker(pos_click[0], pos_click[1], 0, 0, screen)
                                    redrawgamescreen(player)
                                    time.sleep(0.5)
                                    if player1.check_result == True:
                                          player = 1
                                    if player1.hit_ships == 17:
                                          gewonnen(2, player2.used_bombs, 1, player1.hit_ships)
                                          run = False
                                    redrawgamescreen(player)
                        else:
                              bord.check_result = bord.bordchecker(pos_click[0], pos_click[1], 0, 0, screen)
                              if bord.hit_ships == 17:
                                    gewonnen(0, bord.used_bombs)
                                    run = False
            redrawgamescreen(player)


def startmenu():
      setup()
      global clock
      global player
      intro = True
      # While loop that runs until event has happend in the menu
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
                                    gamestart()
                              elif pos_click[1] > 500 and pos_click[1] < 550:
                                    print('multiplayer')
                                    player = 1
                                    gamestart()
                                    
            screen.blit(bg, (0,0))
            largeText = pygame.font.Font('secret.ttf',115)
            smallText = pygame.font.Font('secret.ttf',30)
            title = tekst('Battleship', 'secret.ttf', 115, screenwidth/2, screenheight/4)
            
            singleplayerBTN = tekst('singleplayer', 'secret.ttf', 30, 500, 420)
            multiplayerBTN = tekst('multiplayer', 'secret.ttf', 30, 500, 520)
            pygame.display.update()
      pygame.quit()

# Starting program with startmenu if run from this script.
if __name__ == "__main__":
      startmenu()

