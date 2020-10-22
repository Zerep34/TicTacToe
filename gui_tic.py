from tkinter import *
import sys

class Game(Tk):
    """
    Main class
    """
    def __init__(self, tk, P2pGame, Player):
        self.p2pGame = P2pGame
        self.GRID_LINE_WIDTH = 2 # pixels
        self.WINDOW_SIZE = 400 # pixels*
        self.SYMBOL_SIZE = 0.5
        self.X_COLOR = 'goldenrod'
        self.O_COLOR = 'red3'
        self.DRAW_SCREEN_COLOR = 'light sea green'
        self.GRID_COLOR = 'light grey'
        self.BG_COLOR = 'white'
        self.FIRST_PLAYER = 2
        self.ACTUAL_PLAYER_TURN = 'O'
        self.CELL_SIZE = self.WINDOW_SIZE / 3
        self.STATE_TITLE_SCREEN = 0
        self.STATE_X_TURN = 1
        self.STATE_O_TURN = 2
        self.STATE_GAME_OVER = 3
        self.EMPTY = 0
        self.player = Player
        self.X = 1
        self.O = 2
        self.SYMBOL_WIDTH = self.WINDOW_SIZE/12 # pixels - adjust ratio
        self.tk = tk
        # Tk.__init__(self)
        self.canvas = Canvas(
            height=self.WINDOW_SIZE, width=self.WINDOW_SIZE,
            bg=self.BG_COLOR)

        self.canvas.pack()
        self.bind('<x>', self.exit)
        self.canvas.bind('<Button-1>', self.click)

        self.gamestate = self.STATE_TITLE_SCREEN
        self.title_screen()

        self.board = [
            [self.EMPTY, self.EMPTY, self.EMPTY],
            [self.EMPTY, self.EMPTY, self.EMPTY],
            [self.EMPTY, self.EMPTY, self.EMPTY]]
        self.new_board()
        self.gamestate = self.FIRST_PLAYER
        # #self.launch()


    def title_screen(self):
    # placeholder title screen
        self.canvas.delete('all') #just in case 

        self.canvas.create_rectangle(
            0, 0,
            self.WINDOW_SIZE, self.WINDOW_SIZE,
            fill="gray",
            outline='')

        # self.canvas.create_rectangle(
        #     int(WINDOW_SIZE/15), int(WINDOW_SIZE/15),
        #     int(WINDOW_SIZE*14/15), int(WINDOW_SIZE*14/15),
        #     width=int(WINDOW_SIZE/20),
        #     outline=X_COLOR)    

        # self.canvas.create_rectangle(
        #     int(WINDOW_SIZE/10), int(WINDOW_SIZE/10),
        #     int(WINDOW_SIZE*9/10), int(WINDOW_SIZE*9/10),
        #     fill=X_COLOR,
        #     outline='')

        self.canvas.create_text(
            self.WINDOW_SIZE/2,
            self.WINDOW_SIZE/3,
            text='TIC TAC TOE', fill='white',
            font=('Franklin Gothic', int(-self.WINDOW_SIZE/12), 'bold'))

        self.canvas.create_text(
            int(self.WINDOW_SIZE/2),
            int(self.WINDOW_SIZE/2.5),
            text='[play]', fill='white',
            font=('Franklin Gothic', int(-self.WINDOW_SIZE/25)))

    def new_board(self):
        """
        Clears canvas and game board memory, draws a new board on the canvas
        """

        # delete all objects
        self.canvas.delete('all')

        # reset
        self.board = [
            [self.EMPTY, self.EMPTY, self.EMPTY],
            [self.EMPTY, self.EMPTY, self.EMPTY],
            [self.EMPTY, self.EMPTY, self.EMPTY]]

        # draw grid
        for n in range(1, 3):
            # vertical
            self.canvas.create_line(
                self.CELL_SIZE*n, 0,
                self.CELL_SIZE*n, self.WINDOW_SIZE,
                width=self.GRID_LINE_WIDTH, fill=self.GRID_COLOR)
            # horizontal
            self.canvas.create_line(
                0, self.CELL_SIZE*n,
                self.WINDOW_SIZE, self.CELL_SIZE*n,
                width=self.GRID_LINE_WIDTH, fill=self.GRID_COLOR)

    def gameover_screen(self, outcome):
        #placeholder gameover screen

        self.canvas.delete('all')

        if outcome == 'X WINS':
            wintext = 'X wins'
            wincolor = self.X_COLOR

        elif outcome == 'O WINS':
            wintext = 'O wins'
            wincolor = self.O_COLOR

        elif outcome == 'DRAW':
            wintext = 'Draw'
            wincolor = self.DRAW_SCREEN_COLOR

        self.canvas.create_rectangle(
            0, 0,
            self.WINDOW_SIZE, self.WINDOW_SIZE,
            fill=wincolor, outline='')

        self.canvas.create_text(
            int(self.WINDOW_SIZE/2), int(self.WINDOW_SIZE/2),
            text=wintext, fill='white',
            font=('Franklin Gothic', int(-self.WINDOW_SIZE/6), 'bold'))

        self.canvas.create_text(
                int(self.WINDOW_SIZE/2), int(self.WINDOW_SIZE/1.65),
                text='[click to play again]', fill='white',
                font=('Franklin Gothic', int(-self.WINDOW_SIZE/25)))

    # def launch(self):
        
    #     loc = [-1,-1]
    #     while(loc[0] < 0 or loc[0] > 2 or loc[1] < 0 or loc[1] > 2 ):
    #         print("-> new : restart the game\n -> end : stop the game \n ->  Case [x,y] : input")
    #         mess = input() 
    #         if(mess == "new"):
    #             self.new_board()
    #             self.gamestate = FIRST_PLAYER
    #         elif(mess == "end"):
    #             print("quit")
    #             sys.exit()
    #         else:
    #             try:
    #                 print("Case X 0<=X<=2 : ")
    #                 x = int(mess)
    #                 print("Case Y 0<=Y<=2: ")
    #                 mess = input()
    #                 y = int(mess)
    #                 loc = [x,y]
    #                 print(loc)
    #             except:
    #                 print("Veuillez fournir un entier ! ")
    #                 pass
    #     self.click(loc)
    def click(self, event):
        """
        Handles most of the game logic
        I probably should move it elswhere but it's pretty short
        """
        x = self.ptgrid(event.x)
        y = self.ptgrid(event.y)
        
        # x = loc[0]
        # y = loc[1]

        # if self.gamestate == self.STATE_TITLE_SCREEN:
            # self.new_board()
            # self.gamestate = FIRST_PLAYER


        #duplication /!\
        if (self.gamestate == self.STATE_X_TURN and self.board[y][x] == self.EMPTY):
            self.new_move(x, y, self.player)

            if self.has_won(self.X):
                self.gamestate = self.STATE_GAME_OVER
                self.gameover_screen('X WINS')
                data = "--W:X"
                self.p2pGame.sendTicTacToeData(text=data)


            elif self.is_a_draw():
                self.gamestate = self.STATE_GAME_OVER
                self.gameover_screen('DRAW')
                data = "--D"
                self.p2pGame.sendTicTacToeData(text=data)

            else:
                data = "--X:" + str(x) + ":" + str(y)
                self.p2pGame.sendTicTacToeData(text=data)
                self.gamestate = self.STATE_O_TURN
                #self.launch()

        elif (self.gamestate == self.STATE_O_TURN and self.board[y][x] == self.EMPTY):
            self.new_move(x, y, self.player)

            if self.has_won(self.O):
                self.gamestate = self.STATE_GAME_OVER
                self.gameover_screen('O WINS')
                data = "--W:O"
                self.p2pGame.sendTicTacToeData(text=data)

            elif self.is_a_draw():
                self.gamestate = self.STATE_GAME_OVER
                self.gameover_screen('DRAW')
                data = "--D"
                self.p2pGame.sendTicTacToeData(text=data)

            else:
                self.gamestate = self.STATE_X_TURN
                data = "--O:" + str(x) + ":" + str(y)
                self.p2pGame.sendTicTacToeData(text=data)
                #self.launch()

        elif self.gamestate == self.STATE_GAME_OVER:
            #reset
            self.new_board()
            self.gamestate = self.FIRST_PLAYER
        

    def new_move(self, grid_x, grid_y, player):
        """
        player is either X or O
        x and y are 0-based grid coordinates

          0 1 2
        0 _|_|_
        1 _|_|_
        2  | |

        """
        #duplication /!\
        if player == self.X:
            self.draw_X(grid_x, grid_y)
            self.board[grid_y][grid_x] = self.X

        elif player == self.O:
            self.draw_O(grid_x, grid_y)
            self.board[grid_y][grid_x] = self.O

    def draw_X(self, grid_x, grid_y):
        """
        draw the X symbol at x, y in the grid
        """

        x = self.gtpix(grid_x)
        y = self.gtpix(grid_y)
        delta = self.CELL_SIZE/2*self.SYMBOL_SIZE

        self.canvas.create_line(
            x-delta, y-delta,
            x+delta, y+delta,
            width=self.SYMBOL_WIDTH, fill=self.X_COLOR)

        self.canvas.create_line(
            x+delta, y-delta,
            x-delta, y+delta,
            width=self.SYMBOL_WIDTH, fill=self.X_COLOR)

    def draw_O(self, grid_x, grid_y):
        """
        draw an O symbol at x, y in the grid

        note : a big outline value appears to cause a visual glitch in tkinter
        """

        x = self.gtpix(grid_x)
        y = self.gtpix(grid_y)
        delta = self.CELL_SIZE/2*self.SYMBOL_SIZE

        self.canvas.create_oval(
            x-delta, y-delta,
            x+delta, y+delta,
            width=self.SYMBOL_WIDTH, outline=self.O_COLOR)

    def has_won(self, symbol):
        for y in range(3):
            if self.board[y] == [symbol, symbol, symbol]:
                return True

        for x in range(3):
            if self.board[0][x] == self.board[1][x] == self.board[2][x] == symbol:
                return True

        if self.board[0][0] == self.board[1][1] == self.board[2][2] == symbol:
            return True

        elif self.board[0][2] == self.board[1][1] == self.board[2][0] == symbol:
            return True

        # no win sequence found
        return False

    def is_a_draw(self):
        for row in self.board:
            if self.EMPTY in row:
                return False

        #no self.EMPTY cell left, the game is a draw
        return True

    def gtpix(self, grid_coord):
        # gtpix = grid_to_pixels
        # for a grid coordinate, returns the pixel coordinate of the center
        # of the corresponding cell

        pixel_coord = grid_coord * self.CELL_SIZE + self.CELL_SIZE / 2
        return pixel_coord

    def ptgrid(self, pixel_coord):
        # ptgrid = pixels_to_grid
        # the opposit of gtpix()

        # somehow the canvas has a few extra pixels on the right and bottom side
        if pixel_coord >= self.WINDOW_SIZE:
            pixel_coord = self.WINDOW_SIZE - 1    

        grid_coord = int(pixel_coord / self.CELL_SIZE)
        return grid_coord

    def exit(self, event):
        self.destroy()

# def main():
#     root = Game()
#     root.mainloop()

# main()