import sys

from tkinter import *
import threading
import socket

# GLOBALS
conn_array = []  # stores open sockets
# value: integers for encryption
username_array = dict()  # key: the open sockets in conn_array,
# value: usernames for the connection
contact_array = dict()  # key: ip address as a string, value: [port, username]

username = "Self"
location = 0
port = 0
top = ""

main_body_text = 0

def formatNumber(number):
    """Ensures that number is at least length 4 by
    adding extra 0s to the front.
    """
    temp = str(number)
    while len(temp) < 4:
        temp = '0' + temp
    return temp


def netThrow(conn, message):
    """Sends message through the open socket conn with the encryption key
    secret. Sends the length of the incoming message, then sends the actual
    message.
    """
    try:
        conn.send(formatNumber(len(message)).encode())
        conn.send(message.encode())
    except socket.error:
        if len(conn_array) != 0:
            writeToScreen(
                "Connection issue. Sending message failed.", "System")
            processFlag("-001")


def netCatch(conn):
    """Receive and return the message through open socket conn, decrypting
    using key secret. If the message length begins with - instead of a number,
    process as a flag and return 1.
    """
    try:
        data = conn.recv(4)
        if data.decode()[0] == '-':
            processFlag(data.decode(), conn)
            return 1
        data = conn.recv(int(data.decode()))
        return data.decode()
    except socket.error:
        if len(conn_array) != 0:
            writeToScreen(
                "Connection issue. Receiving message failed.", "System")
        processFlag("-001")

def processFlag(number, conn=None):
    """Process the flag corresponding to number, using open socket conn
    if necessary.
    """
    global statusConnect
    global conn_array
    global username_array
    global contact_array
    t = int(number[1:])
    if t == 1:  # disconnect
        # in the event of single connection being left or if we're just a
        # client
        if len(conn_array) == 1:
            writeToScreen("Connection closed.", "System")
            dump = conn_array.pop()
            try:
                dump.close()
            except socket.error:
                print("Issue with someone being bad about disconnecting")
            statusConnect.set("Connect")
            connecter.config(state=NORMAL)
            return

        if conn != None:
            writeToScreen("Connect to " + conn.getsockname()
            [0] + " closed.", "System")
            conn_array.remove(conn)
            conn.close()

    if t == 2:  # username change
        name = netCatch(conn)
        if (isUsernameFree(name)):
            writeToScreen(
                "User " + username_array[conn] + " has changed their username to " + name, "System")
            username_array[conn] = name
            contact_array[
                conn.getpeername()[0]] = [conn.getpeername()[1], name]

    # passing a friend who this should connect to (I am assuming it will be
    # running on the same port as the other session)
    if t == 4:
        data = conn.recv(4)
        data = conn.recv(int(data.decode()))
        Client(data.decode(),
               int(contact_array[conn.getpeername()[0]][0])).start()


def processUserCommands(command, param):
    """Processes commands passed in via the / text input."""
    global conn_array

    global username

    if command == "nick":  # change nickname
        for letter in param[0]:
            if letter == " " or letter == "\n":
                error_window(root, "Invalid username. No spaces allowed.")
                return
        if isUsernameFree(param[0]):
            writeToScreen("Username is being changed to " + param[0], "System")
            for conn in conn_array:
                conn.send("-002".encode())
                netThrow(conn, param[0])
            username = param[0]
        else:
            writeToScreen(param[0] +
                          " is already taken as a username", "System")
    if command == "disconnect":  # disconnects from current connection
        for conn in conn_array:
            conn.send("-001".encode())
        processFlag("-001")
    if command == "connect":  # connects to passed in host port
        if (options_sanitation(param[1], param[0])):
            Client(param[0], int(param[1])).start()
    if command == "host":  # starts server on passed in port
        if (options_sanitation(param[0])):
            Server(int(param[0])).start()


def isUsernameFree(name):
    """Checks to see if the username name is free for use."""
    global username_array
    global username
    for conn in username_array:
        if name == username_array[conn] or name == username:
            return False
    return True


def passFriends(conn):
    """Sends conn all of the people currently in conn_array so they can connect
    to them.
    """
    global conn_array
    for connection in conn_array:
        if conn != connection:
            conn.send("-004".encode())
            conn.send(
                formatNumber(len(connection.getpeername()[0])).encode())  # pass the ip address
            conn.send(connection.getpeername()[0].encode())
            # conn.send(formatNumber(len(connection.getpeername()[1])).encode()) #pass the port number
            # conn.send(connection.getpeername()[1].encode())


# --------------------------------------------------------------------------

def client_options_window(master):
    """Launches client options window for getting destination hostname
    and port.
    """
    top = Toplevel(master)
    top.title("Connection options")
    top.protocol("WM_DELETE_WINDOW", lambda: optionDelete(top))
    top.grab_set()
    Label(top, text="Server IP:").grid(row=0)
    location = Entry(top)
    location.grid(row=0, column=1)
    location.focus_set()
    Label(top, text="Port:").grid(row=1)
    port = Entry(top)
    port.grid(row=1, column=1)
    go = Button(top, text="Connect", command=lambda:
    client_options_go(location.get(), port.get(), top))
    go.grid(row=2, column=1)


def client_options_go(dest, port, window):
    "Processes the options entered by the user in the client options window."""
    if options_sanitation(port, dest):
        window.destroy()
        Client(dest, int(port)).start()


def options_sanitation(por, loc=""):
    """Checks to make sure the port and destination ip are both valid.
    Launches error windows if there are any issues.
    """
    global root
    if not por.isdigit():
        error_window(root, "Please input a port number.")
        return False
    if int(por) < 0 or 65555 < int(por):
        error_window(root, "Please input a port number between 0 and 65555")
        return False
    if loc != "":
        if not ip_process(loc.split(".")):
            error_window(root, "Please input a valid ip address.")
            return False
    return True


def ip_process(ipArray):
    """Checks to make sure every section of the ip is a valid number."""
    if len(ipArray) != 4:
        return False
    for ip in ipArray:
        if not ip.isdigit():
            return False
        t = int(ip)
        if t < 0 or 255 < t:
            return False
    return True


# ------------------------------------------------------------------------------

def server_options_window(master):
    """Launches server options window for getting port."""
    top = Toplevel(master)
    top.title("Connection options")
    top.grab_set()
    top.protocol("WM_DELETE_WINDOW", lambda: optionDelete(top))
    Label(top, text="Port:").grid(row=0)
    port = Entry(top)
    port.grid(row=0, column=1)
    port.focus_set()
    go = Button(top, text="Launch", command=lambda:
    server_options_go(port.get(), top))
    go.grid(row=1, column=1)


def server_options_go(port, window):
    """Processes the options entered by the user in the
    server options window.
    """
    if options_sanitation(port):
        window.destroy()
        Server(int(port)).start()


# -------------------------------------------------------------------------

def username_options_window(master):
    """Launches username options window for setting username."""
    top = Toplevel(master)
    top.title("Username options")
    top.grab_set()
    Label(top, text="Username:").grid(row=0)
    name = Entry(top)
    name.focus_set()
    name.grid(row=0, column=1)
    go = Button(top, text="Change", command=lambda:
    username_options_go(name.get(), top))
    go.grid(row=1, column=1)


def username_options_go(name, window):
    """Processes the options entered by the user in the
    server options window.
    """
    processUserCommands("nick", [name])
    window.destroy()


# -------------------------------------------------------------------------

def error_window(master, texty):
    """Launches a new window to display the message texty."""
    window = Toplevel(master)
    window.title("ERROR")
    window.grab_set()
    Label(window, text=texty).pack()
    go = Button(window, text="OK", command=window.destroy)
    go.pack()
    go.focus_set()


def optionDelete(window):
    connecter.config(state=NORMAL)
    window.destroy()


# places the text from the text bar on to the screen and sends it to
# everyone this program is connected to
def placeText(text):
    """Places the text from the text bar on to the screen and sends it to
    everyone this program is connected to.
    """
    global conn_array
    global username
    writeToScreen(text, username)
    for person in conn_array:
        netThrow(person, text)


def writeToScreen(text, username=""):
    """Places text to main text body in format "username: text"."""
    global main_body_text
    main_body_text.config(state=NORMAL)
    main_body_text.insert(END, '\n')
    if username:
        main_body_text.insert(END, username + ": ")
    main_body_text.insert(END, text)
    main_body_text.yview(END)
    main_body_text.config(state=DISABLED)


def processUserText(event):
    """Takes text from text bar input and calls processUserCommands if it
    begins with '/'.
    """
    data = text_input.get()
    if data[0] != "/":  # is not a command
        placeText(data)
    else:
        if data.find(" ") == -1:
            command = data[1:]
        else:
            command = data[1:data.find(" ")]
        params = data[data.find(" ") + 1:].split(" ")
        processUserCommands(command, params)
    text_input.delete(0, END)


def processUserInput(text):
    """ClI version of processUserText."""
    if text[0] != "/":
        placeText(text)
    else:
        if text.find(" ") == -1:
            command = text[1:]
        else:
            command = text[1:text.find(" ")]
        params = text[text.find(" ") + 1:].split(" ")
        processUserCommands(command, params)


# -------------------------------------------------------------------------

class Server(threading.Thread):
    "A class for a Server instance."""

    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port

    def run(self):
        global conn_array
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', self.port))

        if len(conn_array) == 0:
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
        conn_array.append(conn)  # add an array entry for this connection
        writeToScreen("Connected by " + str(addr[0]), "System")

        global statusConnect
        statusConnect.set("Disconnect")
        connecter.config(state=NORMAL)

        conn.send(formatNumber(len(username)).encode())
        conn.send(username.encode())

        data = conn.recv(4)
        data = conn.recv(int(data.decode()))
        if data.decode() != "Self":
            username_array[conn] = data.decode()
            contact_array[str(addr[0])] = [str(self.port), data.decode()]
        else:
            username_array[conn] = addr[0]
            contact_array[str(addr[0])] = [str(self.port), "No_nick"]

        passFriends(conn)
        threading.Thread(target=Runner, args=(conn,)).start()
        Server(self.port).start()


class Client(threading.Thread):
    """A class for a Client instance."""

    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.port = port
        self.host = host

    def run(self):
        global conn_array
        conn_init = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn_init.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        conn_init.settimeout(5.0)
        try:
            conn_init.connect((self.host, self.port))
        except socket.timeout:
            writeToScreen("Timeout issue. Host possible not there.", "System")
            connecter.config(state=NORMAL)
            raise SystemExit(0)
        except socket.error:
            writeToScreen(
                "Connection issue. Host actively refused connection.", "System")
            connecter.config(state=NORMAL)
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
        connecter.config(state=NORMAL)

        conn_array.append(conn)

        conn.send(formatNumber(len(username)).encode())
        conn.send(username.encode())

        data = conn.recv(4)
        data = conn.recv(int(data.decode()))
        if data.decode() != "Self":
            username_array[conn] = data.decode()
            contact_array[
                conn.getpeername()[0]] = [str(self.port), data.decode()]
        else:
            username_array[conn] = self.host
            contact_array[conn.getpeername()[0]] = [str(self.port), "No_nick"]
        threading.Thread(target=Runner, args=(conn,)).start()


def Runner(conn):
    global username_array
    while 1:
        data = netCatch(conn)
        if data != 1:
            writeToScreen(data, username_array[conn])


def connects(clientType):
    global conn_array
    connecter.config(state=DISABLED)
    if len(conn_array) == 0:
        if clientType == 0:
            client_options_window(root)
        if clientType == 1:
            server_options_window(root)
    else:
        # connecter.config(state=NORMAL)
        for connection in conn_array:
            connection.send("-001".encode())
        processFlag("-001")


def toOne():
    global clientType
    clientType = 0


def toTwo():
    global clientType
    clientType = 1


# -------------------------------------------------------------------------


if len(sys.argv) > 1 and sys.argv[1] == "-cli":
    print("Starting command line chat")

else:
    root = Tk()
    root.title("Chat")

    menubar = Menu(root)

    file_menu = Menu(menubar, tearoff=0)
    menubar.add_command(label="Change username",
                        command=lambda: username_options_window(root))
    menubar.add_command(label="Exit", command=lambda: root.destroy())

    root.config(menu=menubar)

    main_body = Frame(root, height=20, width=50)

    main_body_text = Text(main_body)
    body_text_scroll = Scrollbar(main_body)
    main_body_text.focus_set()
    body_text_scroll.pack(side=RIGHT, fill=Y)
    main_body_text.pack(side=LEFT, fill=Y)
    body_text_scroll.config(command=main_body_text.yview)
    main_body_text.config(yscrollcommand=body_text_scroll.set)
    main_body.pack()

    main_body_text.insert(END, "Welcome to the chat program!")
    main_body_text.config(state=DISABLED)

    text_input = Entry(root, width=60)
    text_input.bind("<Return>", processUserText)
    text_input.pack()

    statusConnect = StringVar()
    statusConnect.set("Connect")
    clientType = 1
    Radiobutton(root, text="Client", variable=clientType,
                value=0, command=toOne).pack(anchor=E)
    Radiobutton(root, text="Server", variable=clientType,
                value=1, command=toTwo).pack(anchor=E)
    connecter = Button(root, textvariable=statusConnect,
                       command=lambda: connects(clientType))
    connecter.pack()

    root.mainloop()
