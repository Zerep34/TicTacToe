from tkinter import *
import threading
import socket

connectionList = []  # Store sockets
usernameList = dict()  # Store Username 
contact_array = dict()  # Store IP and Port for open connections

username = "Self"
location = 0
port = 0
top = ""

mainTextArea = 0

PLAYER_TYPE = ""

"""
Verify that at least the lenght of each number is 4 long.
Otherwise add 0
"""
def checkNumberStructure(number):
    temp = str(number)
    while len(temp) < 4:
        temp = '0' + temp
    return temp


"""
Send message through the socker 'conn'. 
The first step is to send the length of the message, then sends the actual
message
"""
def socketSend(conn, message):
    try:
        conn.send(checkNumberStructure(len(message)).encode())
        conn.send(message.encode())
    except socket.error:
        if len(connectionList) != 0:
            writeToScreen(
                "Connection issue. Sending message failed.", "System")
            headerCheck("-001")


"""
Receive the message from the socket 'conn'
"""
def socketReceive(conn):
    try:
        data = conn.recv(4)
        if data.decode()[0] == '-':
            headerCheck(data.decode(), conn)
            return 1
        data = conn.recv(int(data.decode()))
        return data.decode()
    except socket.error:
        if len(connectionList) != 0:
            writeToScreen(
                "Connection issue. Receiving message failed.", "System")
        headerCheck("-001")


"""
Process the header corresponding to number, using open socket conn
if necessary.
"""
def headerCheck(number, conn=None):
    t = int(number[1:])
    if t == 1:  # disconnect
        # in the event of single connection being left or if we're just a
        # client
        if len(connectionList) == 1:
            writeToScreen("Connection closed.", "System")
            dump = connectionList.pop()
            try:
                dump.close()
            except socket.error:
                print("Issue with someone being bad about disconnecting")
            statusConnect.set("Connect")
            connectionButton.config(state=NORMAL)
            return

        if conn != None:
            writeToScreen("Connect to " + conn.getsockname()
            [0] + " closed.", "System")
            connectionList.remove(conn)
            conn.close()

    if t == 2:  # username change
        name = socketReceive(conn)
        if (AvailableUsername(name)):
            writeToScreen(
                "User " + usernameList[conn] + " has changed their username to " + name, "System")
            usernameList[conn] = name
            contact_array[
                conn.getpeername()[0]] = [conn.getpeername()[1], name]

    # passing a friend who this should connect to (I am assuming it will be
    # running on the same port as the other session)
    if t == 4:
        data = conn.recv(4)
        data = conn.recv(int(data.decode()))
        Client(data.decode(),
               int(contact_array[conn.getpeername()[0]][0])).start()


"""
Processes commands like
Nickname change, connection change, host change
"""
def optionCommands(command, param):
    global connectionList
    global username
    if command == "nick":  # change nickname
        for letter in param[0]:
            if letter == " " or letter == "\n":
                ExceptionWindow(root, "Invalid username. No spaces allowed.")
                return
        if AvailableUsername(param[0]):
            writeToScreen("Username is being changed to " + param[0], "System")
            for conn in connectionList:
                conn.send("-002".encode())
                socketSend(conn, param[0])
            username = param[0]
        else:
            writeToScreen(param[0] +
                          " is already taken as a username", "System")
    if command == "disconnect":  # disconnects from current connection
        for conn in connectionList:
            conn.send("-001".encode())
        headerCheck("-001")
    if command == "connect":  # connects to passed in host port
        if checkOptionsStructure(param[1], param[0]):
            Client(param[0], int(param[1])).start()
    if command == "host":  # starts server on passed in port
        if checkOptionsStructure(param[0]):
            Server(int(param[0])).start()


"""
Check if the the param name is not in the array usernameList
"""
def AvailableUsername(name):

    global usernameList
    global username
    for conn in usernameList:
        if name == usernameList[conn] or name == username:
            return False
    return True


"""
Sends conn all of the people currently in connectionList so they can connect
to them.
"""
def connectionExchange(conn):
    global connectionList
    for connection in connectionList:
        if conn != connection:
            conn.send("-004".encode())
            conn.send(
                checkNumberStructure(len(connection.getpeername()[0])).encode())  # pass the ip address
            conn.send(connection.getpeername()[0].encode())


"""
Display options windows, for client
"""
def optionsWindowClientSide(master):
    top = Toplevel(master)
    top.title("Option de connexion")
    top.protocol("WM_DELETE_WINDOW", lambda: optionDelete(top))
    top.grab_set()
    Label(top, text="Adresse IP :").grid(row=0)
    location = Entry(top)
    location.grid(row=0, column=1)
    location.focus_set()
    Label(top, text="Port :").grid(row=1)
    port = Entry(top)
    port.grid(row=1, column=1)
    go = Button(top, text="Connexion", command=lambda:
    processClientOptions(location.get(), port.get(), top))
    go.grid(row=2, column=1)


"""
Application of settings for the client
"""
def processClientOptions(dest, port, window):
    if checkOptionsStructure(port, dest):
        window.destroy()
        Client(dest, int(port)).start()


"""
Check structure of IP and port
"""
def checkOptionsStructure(por, loc=""):
    global root
    if not por.isdigit():
        ExceptionWindow(root, "Please input a port number.")
        return False
    if int(por) < 0 or 65555 < int(por):
        ExceptionWindow(root, "Please input a port number between 0 and 65555")
        return False
    if loc != "":
        if not checkIpStructure(loc.split(".")):
            ExceptionWindow(root, "Please input a valid ip address.")
            return False
    return True


"""
Check IP Structure
"""
def checkIpStructure(ipArray):
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
def optionsWindowServerSide(master):
    top = Toplevel(master)
    top.title("Connection options")
    top.grab_set()
    top.protocol("WM_DELETE_WINDOW", lambda: optionDelete(top))
    Label(top, text="Port:").grid(row=0)
    port = Entry(top)
    port.grid(row=0, column=1)
    port.focus_set()
    go = Button(top, text="Launch", command=lambda:
    processServerOptions(port.get(), top))
    go.grid(row=1, column=1)


"""
Processes the server side options window
"""
def processServerOptions(port, window):

    if checkOptionsStructure(port):
        window.destroy()
        Server(int(port)).start()


"""
Display username options window
"""
def usernameWindowSetUp(master):
    top = Toplevel(master)
    top.title("Username options")
    top.grab_set()
    Label(top, text="Username:").grid(row=0)
    name = Entry(top)
    name.focus_set()
    name.grid(row=0, column=1)
    go = Button(top, text="Change", command=lambda:
    processUsernameOptions(name.get(), top))
    go.grid(row=1, column=1)


"""
Processes server options window.
"""
def processUsernameOptions(name, window):
    optionCommands("nick", [name])
    window.destroy()


"""
Display error window
"""
def ExceptionWindow(master, texty):
    window = Toplevel(master)
    window.title("ERROR")
    window.grab_set()
    Label(window, text=texty).pack()
    go = Button(window, text="OK", command=window.destroy)
    go.pack()
    go.focus_set()


"""
Delete all options
"""
def optionDelete(window):
    connectionButton.config(state=NORMAL)
    window.destroy()


"""
Place the param 'text' inside the text Aread and then send it to the client
"""
def placeText(text):
    global connectionList
    global username
    writeToScreen(text, username)
    for person in connectionList:
        socketSend(person, text)

"""
Send TicTacToe data to be display on other screen
"""
def sendTicTacToeData(text):
    global connectionList
    global username
    for person in connectionList:
        socketSend(person, text)


"""
Structure the response like this 'username : text'
"""
def writeToScreen(text, username=""):
    global mainTextArea
    mainTextArea.config(state=NORMAL)
    mainTextArea.insert(END, '\n')
    if username:
        mainTextArea.insert(END, username + " : ")
    mainTextArea.insert(END, text)
    mainTextArea.yview(END)
    mainTextArea.config(state=DISABLED)


"""
Accept Text from the input aread and then delete it
"""
def processUserText(event):
    data = text_input.get()
    if "--C:" in data:

    placeText(data)
    text_input.delete(0, END)


"""
Class for Server side configuration
"""
class Server(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port

    def run(self):
        global connectionList
        global PLAYER_TYPE
        PLAYER_TYPE = "X"
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', self.port))

        if len(connectionList) == 0:
            writeToScreen(
                "Socket is good, waiting for connections on port: " +
                str(self.port), "System")
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
        connectionList.append(conn)  # add an array entry for this connection
        writeToScreen("Connected by " + str(addr[0]), "System")

        global statusConnect
        statusConnect.set("Disconnect")
        connectionButton.config(state=NORMAL)

        conn.send(checkNumberStructure(len(username)).encode())
        conn.send(username.encode())

        data = conn.recv(4)
        data = conn.recv(int(data.decode()))
        if data.decode() != "Self":
            usernameList[conn] = data.decode()
            contact_array[str(addr[0])] = [str(self.port), data.decode()]
        else:
            usernameList[conn] = addr[0]
            contact_array[str(addr[0])] = [str(self.port), "No_nick"]

        connectionExchange(conn)
        threading.Thread(target=exchange, args=(conn,)).start()
        Server(self.port).start()


"""
Class for Server side configuration
"""
class Client(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.port = port
        self.host = host

    def run(self):
        global connectionList
        global PLAYER_TYPE
        PLAYER_TYPE = "O"
        conn_init = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn_init.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        conn_init.settimeout(5.0)
        try:
            conn_init.connect((self.host, self.port))
        except socket.timeout:
            writeToScreen("Timeout issue. Host possible not there.", "System")
            connectionButton.config(state=NORMAL)
            raise SystemExit(0)
        except socket.error:
            writeToScreen(
                "Connection issue. Host actively refused connection.", "System")
            connectionButton.config(state=NORMAL)
            raise SystemExit(0)
        porta = conn_init.recv(5)
        porte = int(porta.decode())
        conn_init.close()
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((self.host, porte))

        writeToScreen("Connected to: " + self.host +
                      " on port: " + str(porte), "System")

        global statusConnect
        statusConnect.set("Disconnect")
        connectionButton.config(state=NORMAL)

        connectionList.append(conn)

        conn.send(checkNumberStructure(len(username)).encode())
        conn.send(username.encode())

        data = conn.recv(4)
        data = conn.recv(int(data.decode()))
        if data.decode() != "Self":
            usernameList[conn] = data.decode()
            contact_array[
                conn.getpeername()[0]] = [str(self.port), data.decode()]
        else:
            usernameList[conn] = self.host
            contact_array[conn.getpeername()[0]] = [str(self.port), "No_nick"]
        threading.Thread(target=exchange, args=(conn,)).start()


"""
Function use by the Thread
"""
def exchange(conn):
    global usernameList
    while 1:
        data = socketReceive(conn)
        if data != 1:
            if "--C:" in data :
                coord = data[4:].split(':')
                if PLAYER_TYPE == "X":
                    draw_X((int) coord[0], (int) coord[1])
                else:
                    draw_Y((int) coord[0], (int) coord[1])
            else :
                writeToScreen(data, usernameList[conn])


"""
Display Client or Server window if they need to be configurate
Or send First exchange between server and his client
"""
def connection(clientType):
    global connectionList
    connectionButton.config(state=DISABLED)
    if len(connectionList) == 0:
        if clientType == 0:
            optionsWindowClientSide(root)
        if clientType == 1:
            optionsWindowServerSide(root)
    else:
        for connection in connectionList:
            connection.send("-001".encode())
        headerCheck("-001")


def ClientRadioButton():
    global clientType
    clientType = 0


def ServerRadioButton():
    global clientType
    clientType = 1


root = Tk()
root.title("Tic Tac Toe")

menubar = Menu(root)

file_menu = Menu(menubar, tearoff=0)
menubar.add_command(label="Change username",
                    command=lambda: usernameWindowSetUp(root))
menubar.add_command(label="Exit", command=lambda: root.destroy())

root.config(menu=menubar)

main_body = Frame(root, height=20, width=50)

main_body
mainTextArea = Text(main_body)
body_text_scroll = Scrollbar(main_body)
mainTextArea.focus_set()
body_text_scroll.pack(side=RIGHT, fill=Y)
mainTextArea.pack(side=LEFT, fill=Y)
body_text_scroll.config(command=mainTextArea.yview)
mainTextArea.config(yscrollcommand=body_text_scroll.set)

main_body.pack()

mainTextArea.insert(END, "Welcome to the chat program!")
mainTextArea.config(state=DISABLED)

text_input = Entry(root, width=60)
text_input.bind("<Return>", processUserText)
text_input.pack()

statusConnect = StringVar()
statusConnect.set("Connect")
clientType = 1
Radiobutton(root, text="Client", variable=clientType,
            value=0, command=ClientRadioButton).pack(anchor=E)

Radiobutton(root, text="Server", variable=clientType,
            value=1, command=ServerRadioButton).pack(anchor=E)

connectionButton = Button(root, textvariable=statusConnect,
                   command=lambda: connection(clientType))
connectionButton.pack()

root.mainloop()
