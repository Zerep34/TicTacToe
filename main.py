from tkinter import *
from gui_tic import Game
import threading
import socket


class P2pGame:

    def __init__(self):
        self.connectionList = []  # Store sockets
        self.usernameList = dict()  # Store Username
        self.contact_array = dict()  # Store IP and Port for open connections

        self.username = "Self"
        self.location = 0
        self.port = 0
        self.top = ""
        self.isReady = False
        self.nbJoueurReady = 0

        self.mainTextArea = 0

        self.PLAYER_TYPE = ""
        self.playerTurn = 'X'
        self.TicGame = None
        self.root = Tk()
        self.root.title("Tic Tac Toe")

        self.menubar = Menu(self.root)

        file_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_command(label="Changer pseudo",
                            command=lambda: self.usernameWindowSetUp(self.root))
        self.menubar.add_command(label="Quitter", command=lambda: self.root.destroy())
        self.menubar.add_command(label="TicTacToe", command=lambda: self.launchTicTacToe(self.root))
        self.menubar.entryconfig("TicTacToe", state="disabled")
        self.root.config(menu=self.menubar)

        main_body = Frame(self.root, height=20, width=50)

        main_body
        self.mainTextArea = Text(main_body)
        body_text_scroll = Scrollbar(main_body)
        self.mainTextArea.focus_set()
        body_text_scroll.pack(side=RIGHT, fill=Y)
        self.mainTextArea.pack(side=LEFT, fill=Y)
        body_text_scroll.config(command=self.mainTextArea.yview)
        self.mainTextArea.config(yscrollcommand=body_text_scroll.set)

        main_body.pack()

        self.mainTextArea.insert(END, "Bienvenue dans ce Tic Tac Toe!")
        self.mainTextArea.config(state=DISABLED)

        self.text_input = Entry(self.root, width=60)
        self.text_input.bind("<Return>", self.processUserText)
        self.text_input.pack()

        self.statusConnect = StringVar()
        self.statusConnect.set("Connexion")
        self.clientType = 1
        Radiobutton(self.root, text="Client", variable=self.clientType,
                    value=0, command=self.ClientRadioButton).pack(anchor=E)

        Radiobutton(self.root, text="Serveur", variable=self.clientType,
                    value=1, command=self.ServerRadioButton).pack(anchor=E)

        self.connectionButton = Button(self.root, textvariable=self.statusConnect,
                                command=lambda: self.connection(self.clientType))
        self.connectionButton.pack()

        self.root.mainloop()

    """
    Verify that at least the lenght of each number is 4 long.
    Otherwise add 0
    """


    def checkNumberStructure(self, number):
        temp = str(number)
        while len(temp) < 4:
            temp = '0' + temp
        return temp


    """
    Send message through the socker 'conn'. 
    The first step is to send the length of the message, then sends the actual
    message
    """


    def socketSend(self, conn, message):
        try:
            conn.send(self.checkNumberStructure(len(message)).encode())
            conn.send(message.encode())
        except socket.error:
            if len(self.connectionList) != 0:
                self.writeToScreen(
                    "Problème de connexion. Erreur lors de l'envoie d'un message.", "Système")
                self.headerCheck("-001")


    """
    Receive the message from the socket 'conn'
    """


    def socketReceive(self, conn):
        try:
            data = conn.recv(4)
            if data.decode()[0] == '-':
                self.headerCheck(data.decode(), conn)
                return 1
            data = conn.recv(int(data.decode()))
            return data.decode()
        except socket.error:
            if len(self.connectionList) != 0:
                self.writeToScreen(
                    "Problème de connexion. Erreur lors de l'envoie d'un message", "Système")
            self.headerCheck("-001")


    """
    Process the header corresponding to number, using open socket conn
    if necessary.
    """


    def headerCheck(self, number, conn=None):
        t = int(number[1:])
        if t == 1:  # disconnect
            # in the event of single connection being left or if we're just a
            # client
            if len(self.connectionList) == 1:
                self.writeToScreen("Connexion fermé", "Système")
                dump = self.connectionList.pop()
                try:
                    dump.close()
                except socket.error:
                    print("Problème avec un contact")
                self.statusConnect.set("Connect")
                self.connectionButton.config(state=NORMAL)
                return

            if conn != None:
                self.writeToScreen("Connexion à " + conn.getsockname()
                            [0] + " fermé", "Système")
                self.connectionList.remove(conn)
                conn.close()

        if t == 2:  # username change
            name = self.socketReceive(conn)
            if (self.AvailableUsername(name)):
                self.writeToScreen(
                    "L'utilisateur " + self.usernameList[conn] + " a changé son pseudo sur " + name, "Système")
                self.usernameList[conn] = name
                self.contact_array[
                    conn.getpeername()[0]] = [conn.getpeername()[1], name]

        # passing a friend who this should connect to (I am assuming it will be
        # running on the same port as the other session)
        if t == 4:
            data = conn.recv(4)
            data = conn.recv(int(data.decode()))
            Client(data.decode(),
                int(self.contact_array[conn.getpeername()[0]][0]), self).start()


    """
    Processes commands like
    Nickname change, connection change, host change
    """


    def optionCommands(self, command, param):
        if command == "nick":  # change nickname
            for letter in param[0]:
                if letter == " " or letter == "\n":
                    self.ExceptionWindow(self.root, "Pseudo non valide. Les espaces ne sont pas autorisés")
                    return
            if self.AvailableUsername(param[0]):
                self.writeToScreen("Le pseudo a été changé pour " + param[0], "Système")
                for conn in self.connectionList:
                    conn.send("-002".encode())
                    self.socketSend(conn, param[0])
                self.username = param[0]
            else:
                self.writeToScreen(param[0] +
                            " est déjà pris par un autre utilisateur", "Système")
        if command == "disconnect":  # disconnects from current connection
            for conn in self.connectionList:
                conn.send("-001".encode())
            self.headerCheck("-001")
        if command == "connect":  # connects to passed in host port
            if self.checkOptionsStructure(param[1], param[0]):
                Client(param[0], int(param[1]), self).start()
        if command == "host":  # starts server on passed in port
            if self.checkOptionsStructure(param[0]):
                Server(int(param[0]), self).start()


    """
    Check if the the param name is not in the array usernameList
    """


    def AvailableUsername(self, name):

        for conn in self.usernameList:
            if name == self.usernameList[conn] or name == self.username:
                return False
        return True


    """
    Sends conn all of the people currently in connectionList so they can connect
    to them.
    """


    def connectionExchange(self, conn):
        for connection in self.connectionList:
            if conn != connection:
                conn.send("-004".encode())
                conn.send(
                    self.checkNumberStructure(len(connection.getpeername()[0])).encode())  # pass the ip address
                conn.send(connection.getpeername()[0].encode())


    """
    Display options windows, for client
    """


    def optionsWindowClientSide(self, master):
        top = Toplevel(master)
        top.title("Option de connexion")
        top.protocol("WM_DELETE_WINDOW", lambda: self.optionDelete(top))
        top.grab_set()
        Label(top, text="Adresse IP :").grid(row=0)
        location = Entry(top)
        location.grid(row=0, column=1)
        location.focus_set()
        Label(top, text="Port :").grid(row=1)
        port = Entry(top)
        port.grid(row=1, column=1)
        go = Button(top, text="Connexion", command=lambda:
                    self.processClientOptions(location.get(), port.get(), top))
        go.grid(row=2, column=1)


    """
    Application of settings for the client
    """


    def processClientOptions(self, dest, port, window):
        if self.checkOptionsStructure(port, dest):
            window.destroy()
            Client(dest, int(port), self).start()


    """
    Check structure of IP and port
    """


    def checkOptionsStructure(self, por, loc=""):
        global root
        if not por.isdigit():
            self.ExceptionWindow(self.root, "Entrez un numéro de port valide")
            return False
        if int(por) < 0 or 65555 < int(por):
            self.ExceptionWindow(self.root, "Entrez un numéro de port compris entre 0 and 65555")
            return False
        if loc != "":
            if not self.checkIpStructure(loc.split(".")):
                self.ExceptionWindow(self.root, "Entrez une adresse IP valide")
                return False
        return True


    """
    Check IP Structure
    """


    def checkIpStructure(self, ipArray):
        if len(ipArray) != 4:
            return False
        for ip in ipArray:
            if not ip.isdigit():
                return False
            t = int(ip)
            if t < 0 or 255 < t:
                return False
        return True


    """
    Display server side options panel
    """


    def optionsWindowServerSide(self, master):
        top = Toplevel(master)
        top.title("Options de connexion")
        top.grab_set()
        top.protocol("WM_DELETE_WINDOW", lambda: self.optionDelete(top))
        Label(top, text="Port:").grid(row=0)
        port = Entry(top)
        port.grid(row=0, column=1)
        port.focus_set()
        go = Button(top, text="Lancer", command=lambda:
                    self.processServerOptions(port.get(), top))
        go.grid(row=1, column=1)


    """
    Processes the server side options window
    """


    def processServerOptions(self, port, window):

        if self.checkOptionsStructure(port):
            window.destroy()
            Server(int(port), self).start()


    """
    Display username options window
    """


    def usernameWindowSetUp(self, master):
        top = Toplevel(master)
        top.title("Options de pseudo")
        top.grab_set()
        Label(top, text="Pseudo:").grid(row=0)
        name = Entry(top)
        name.focus_set()
        name.grid(row=0, column=1)
        go = Button(top, text="Changer", command=lambda:
                    self.processUsernameOptions(name.get(), top))
        go.grid(row=1, column=1)


    def launchTicTacToe(self, root):
        # top = Toplevel(master)
        # top.title("Tic Tac Toe")
        # top.grab_set()
        self.menubar.entryconfig("TicTacToe", state="disabled")
        self.TicGame = Game(root, self, Player=self.PLAYER_TYPE)
        self.sendReadyToPlay("--R")
        self.nbJoueurReady += 1
        self.TicGame.mainloop()


    """
    Processes server options window.
    """


    def processUsernameOptions(self, name, window):
        self.optionCommands("nick", [name])
        window.destroy()


    """
    Display error window
    """


    def ExceptionWindow(self, master, texty):
        window = Toplevel(master)
        window.title("ERREUR")
        window.grab_set()
        Label(window, text=texty).pack()
        go = Button(window, text="OK", command=window.destroy)
        go.pack()
        go.focus_set()


    """
    Delete all options
    """


    def optionDelete(self, window):
        self.connectionButton.config(state=NORMAL)
        window.destroy()


    """
    Place the param 'text' inside the text Aread and then send it to the client
    """


    def placeText(self, text):
        self.writeToScreen(text, self.username)
        for person in self.connectionList:
            self.socketSend(person, text)


    """
    Send TicTacToe data to be display on other screen
    """


    def sendTicTacToeData(self, text):
        if("--" in text):
            for person in self.connectionList:
                self.socketSend(person, text)
        else:
            return


    def sendReadyToPlay(self, text):
        if("--R" in text):
            for person in self.connectionList:
                self.socketSend(person, text)
        else:
            return

    def sendPlayAgain(self, text):
        if("--A" in text):
            for person in self.connectionList:
                self.socketSend(person, text)
        else:
            return



    """
    Structure the response like this 'username : text'
    """


    def writeToScreen(self, text, username=""):
        self.mainTextArea.config(state=NORMAL)
        self.mainTextArea.insert(END, '\n')
        if username:
            self.mainTextArea.insert(END, username + " : ")
        self.mainTextArea.insert(END, text)
        self.mainTextArea.yview(END)
        self.mainTextArea.config(state=DISABLED)


    """
    Accept Text from the input aread and then delete it
    """


    def processUserText(self, event):
        data = self.text_input.get()
        if(not str(data).startswith("--")):
            self.placeText(data)
            self.text_input.delete(0, END)
        else:
            self.placeText("Vous ne pouvez pas envoyer de phrase commencant par '--'.")
            self.text_input.delete(0, END)



    """
    Function use by the Thread
    """


    def exchange(self, conn):
        while 1:
            data = self.socketReceive(conn)
            if data != 1:
                if("--D" == data):
                    self.TicGame.gamestate = self.TicGame.STATE_GAME_OVER
                    self.TicGame.gameover_screen('Egalité')
                elif("--W:O" == data):
                    self.TicGame.gamestate = self.TicGame.STATE_GAME_OVER
                    self.TicGame.gameover_screen('O Gagne')
                elif("--W:X" == data):
                    self.TicGame.gamestate = self.TicGame.STATE_GAME_OVER
                    self.TicGame.gameover_screen('X Gagne')
                elif("--X:" in data):
                    x = int(data[4:].split(":")[0])
                    y = int(data[4:].split(":")[1])
                    self.TicGame.new_move(x, y, 1)
                    self.playerTurn = 'O'
                elif("--O:" in data):
                    x = int(data[4:].split(":")[0])
                    y = int(data[4:].split(":")[1])
                    self.TicGame.new_move(x, y, 2)
                    self.playerTurn = 'X'
                elif ("--A" in data):
                    self.TicGame.new_board()
                    self.TicGame.gamestate = self.TicGame.FIRST_PLAYER
                    self.playerTurn = 'X'
                elif ("--R" == data):
                    self.isReady = True
                    self.nbJoueurReady += 1
                    self.writeToScreen("L'autre joueur est prêt à jouer.", "Système")
                    if self.nbJoueurReady == 2:
                        self.placeText("Les deux joueurs sont prets")
                        self.placeText("Serveur commence")
                else:
                    self.writeToScreen(data, self.usernameList[conn])


    """
    Display Client or Server window if they need to be configurate
    Or send First exchange between server and his client
    """


    def connection(self, clientType):
        self.connectionButton.config(state=DISABLED)
        if len(self.connectionList) == 0:
            if clientType == 0:
                self.optionsWindowClientSide(self.root)
            if clientType == 1:
                self.optionsWindowServerSide(self.root)
        else:
            for connection in self.connectionList:
                connection.send("-001".encode())
            self.headerCheck("-001")


    def ClientRadioButton(self ):
        self.clientType = 0


    def ServerRadioButton(self ):
        self.clientType = 1




"""
Class for Server side configuration
"""


class Server(threading.Thread):
    def __init__(self, port, P2pGame):
        self.p2pgame = P2pGame
        threading.Thread.__init__(self)
        self.port = port

    def run(self):
        self.p2pgame.PLAYER_TYPE = 1
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', self.port))

        if len(self.p2pgame.connectionList) == 0:
            self.p2pgame.writeToScreen(
                "Le socket est bon, en attente d'une connexion sur le port: " +
                str(self.port), "Système")
        s.listen(1)
        global conn_init
        conn_init, addr_init = s.accept()
        serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serv.bind(('', 0))  # get a random empty port
        serv.listen(1)

        portVal = str(serv.getsockname()[1])
        if len(portVal) == 5:
            conn_init.send(portVal.encode())
        else:
            conn_init.send(("0" + portVal).encode())

        conn_init.close()
        conn, addr = serv.accept()
        self.p2pgame.connectionList.append(conn)  # add an array entry for this connection
        self.p2pgame.writeToScreen(str(addr[0] + " est connecté"), "Système")
        self.p2pgame.menubar.entryconfig("TicTacToe", state="active")
        self.p2pgame.statusConnect.set("Déconnecté")
        self.p2pgame.connectionButton.config(state=NORMAL)

        conn.send(self.p2pgame.checkNumberStructure(len(self.p2pgame.username)).encode())
        conn.send(self.p2pgame.username.encode())

        data = conn.recv(4)
        data = conn.recv(int(data.decode()))
        if data.decode() != "Self":
            self.p2pgame.usernameList[conn] = data.decode()
            self.p2pgame.contact_array[str(addr[0])] = [str(self.port), data.decode()]
        else:
            self.p2pgame.usernameList[conn] = addr[0]
            self.p2pgame.contact_array[str(addr[0])] = [str(self.port), "No_nick"]

        self.p2pgame.connectionExchange(conn)
        threading.Thread(target=self.p2pgame.exchange, args=(conn,)).start()
        Server(self.port, self.p2pgame).start()


"""
Class for Server side configuration
"""


class Client(threading.Thread):
    def __init__(self, host, port, P2pGame):
        self.p2pGame = P2pGame
        threading.Thread.__init__(self)
        self.port = port
        self.host = host

    def run(self):
        self.p2pGame.PLAYER_TYPE = 2
        conn_init = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn_init.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        conn_init.settimeout(5.0)
        try:
            conn_init.connect((self.host, self.port))
        except socket.timeout:
            self.p2pGame.writeToScreen("Temps de réponse dépassé. Le serveur n'est pas disponible", "Système")
            self.p2pGame.connectionButton.config(state=NORMAL)
            raise SystemExit(0)
        except socket.error:
            self.p2pGame.writeToScreen(
                "Problème de connexion, le serveur a refusé la connexion", "Système")
            self.p2pGame.connectionButton.config(state=NORMAL)
            raise SystemExit(0)
        porta = conn_init.recv(5)
        porte = int(porta.decode())
        conn_init.close()
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((self.host, porte))

        self.p2pGame.writeToScreen("Connecté à: " + self.host +
                      " sur le port: " + str(porte), "Système")
        self.p2pGame.menubar.entryconfig("TicTacToe", state="active")

        self.p2pGame.statusConnect.set("Disconnect")
        self.p2pGame.connectionButton.config(state=NORMAL)

        self.p2pGame.connectionList.append(conn)

        conn.send(self.p2pGame.checkNumberStructure(len(self.p2pGame.username)).encode())
        conn.send(self.p2pGame.username.encode())

        data = conn.recv(4)
        data = conn.recv(int(data.decode()))
        if data.decode() != "Self":
            self.p2pGame.usernameList[conn] = data.decode()
            self.p2pGame.contact_array[
                conn.getpeername()[0]] = [str(self.port), data.decode()]
        else:
            self.p2pGame.usernameList[conn] = self.host
            self.p2pGame.contact_array[conn.getpeername()[0]] = [str(self.port), "No_nick"]
        threading.Thread(target=self.p2pGame.exchange, args=(conn,)).start()


p1 = P2pGame()