import socket
import threading
import sys
import cfunctions
import random
import time

class Player:
    standardDeck = {'1C':1,'1D':1,'1H':1,'1S':1,
                    '2C':-2,'2D':-2,'2H':-2,'2S':-2,
                    '3C':3,'3D':3,'3H':3,'3S':3,
                    '4C':4,'4D':4,'4H':4,'4S':4,
                    '5C':5,'5D':5,'5H':5,'5S':5,
                    '6C':6,'6D':6,'6H':6,'6S':6,
                    '7C':7,'7D':7,'7H':7,'7S':7,
                    '8C':8,'8D':8,'8H':8,'8S':8,
                    '9C':9,'9D':9,'9H':9,'9S':9,
                    '10C':10,'10D':10,'10H':10,'10S':10,
                    'JC':10,'JD':10,'JH':10,'JS':10,
                    'QC':10,'QD':10,'QH':10,'QS':10,
                    'KC':0,'KD':0,'KH':0,'KS':0}    
    
    def __init__(self, IPv4, tracker_port, pt_port, pp_port):
        """stores the information need as described in the specification"""
        self.name = None
        self.IPv4 = IPv4
        self.tracker_port = tracker_port
        
        self.pt_port = pt_port
        self.pt_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.pt_socket.bind((IPv4, pt_port))
        self.pt_socket.setblocking(False)
        
        self.pp_port = pp_port
        self.pp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.pp_socket.bind((IPv4, pp_port))
        self.pp_socket.setblocking(False)

        # Define stop events for thread control
        self.stop_tracker = threading.Event()
        self.stop_peer = threading.Event()
        self.in_game = threading.Event()

        self.tracker_thread = threading.Thread(target=self.listen_to_tracker)
        self.peer_thread = threading.Thread(target=self.listen_to_peers)
        self.main_thread = threading.Thread(target=self.main)

        self.peers = {}
        self.players = None
        self.dealer = None
        self.state = None
        self.hand = [None] * 6
        self.game_id = None
        self.holes = 0
        self.current_hole = 0
        self.turn = False
  
    def setName(self, name):
        self.name = name

    def send_to_tracker(self, message):
        """we are group 68, hence we are assigned the numbers in the range [35000, 35499]"""
        self.pt_socket.sendto(message.encode('utf-8'), (self.IPv4, self.tracker_port))
        
        # Signal the tracker thread to stop gracefully
        self.stop_tracker.set()
        self.pt_socket.setblocking(True)
        response = self.pt_socket.recvfrom(1024)[0]
        print(f"Tracker response:\n{response.decode('utf-8')}")
        self.pt_socket.setblocking(False)

        # Clear stop_tracker to allow restarting the thread if needed
        self.stop_tracker.clear()
        
        # Restart the thread if it's not alive
        if not self.tracker_thread.is_alive():
            self.tracker_thread = threading.Thread(target=self.listen_to_tracker)
            self.tracker_thread.start()
            
        return response.decode('utf-8')

    def send_to_peer(self, ip, port, message):
        self.pp_socket.sendto(message.encode('utf-8'), (ip, port))

    def send_to_peer_rec(self, ip, port, message):
        """Send a message to a peer via the peer-to-peer socket and wait until the peer responds."""
        self.pp_socket.sendto(message.encode('utf-8'), (ip, port))
        
        self.stop_peer.set()
        self.pp_socket.setblocking(True)
        response, addr = self.pp_socket.recv(1024)
        self.handle_peers(response)
        self.pp_socket.setblocking(False)
        
        if not self.peer_thread.is_alive():
            self.peer_thread = threading.Thread(target=self.listen_to_peers)
            self.peer_thread.start()

        self.stop_peer.clear()
        #return response.decode('utf-8')

    def register(self, name, IPv4, tracker_port, player_port):
        message = f"register {name} {IPv4} {tracker_port} {player_port}"
        print("Register request is sent to the tracker")
        return self.send_to_tracker(message) == "SUCCESS: Player registered"

    def deregister(self, name):
        message = f"de-register {name}"
        print(f"De-register request for the player {name} is sent to the tracker")
        return self.send_to_tracker(message) == "SUCCESS: Player deregistered"

    def query_games(self):
        message = "query games"
        print("Query games request is sent to the tracker")
        self.send_to_tracker(message)

    def query_players(self):
        message = "query players"
        print(f"Query players request is sent to the tracker")
        self.send_to_tracker(message)

    def listen_to_tracker(self):
        """Listen for messages from the tracker."""
        while not self.stop_tracker.is_set():  # Check if the stop_tracker is set to stop the thread
            try:
                data, addr = self.pt_socket.recvfrom(1024)
                message = data.decode('utf-8')
                self.handle_tracker(message)
            except BlockingIOError:
                pass

    def listen_to_peers(self):
        """Listen for messages from other peers."""
        while not self.stop_peer.is_set():
            try:
                data, addr = self.pp_socket.recvfrom(1024)
                message = data.decode('utf-8')
                self.handle_peers(message, addr)
            except:
                pass

    def start_game(self, player, n, holes):
        message = f"start game {player} {n}"
        response = self.send_to_tracker(message)
        if response.split(":")[0] == "FAILURE":
            print(response)
            return

        self.in_game.set()
        self.state = "Dealer"
        print("response")
        players_list = response.split('\n')
        players_list.pop(-1)
        print("Game starting with players:")
        print("Player list", players_list)
        for player_info in players_list[1:]:
            player_details = player_info.split(" ")
            print(player_details)
            self.peers[player_details[0]] = [player_details[1], int(player_details[2])] # peers[name] = [ipv4, port number]
            self.send_to_peer(player_details[1], int(player_details[2]), f"invite {player}")        
        
        self.players = list(self.peers.keys()) + [self.name]
        self.deck = Player.decodeDeck(self.dealCards(self.players))

        self.updatePlayers()
        time.sleep(0.1)
        for i in range(holes):
            for p in self.players:
                if p == player:
                    stockCard = self.getCardFromStock()
                    discardCard = self.getCardFromDiscarded()
                    command = input("It is your turn, choice one of the options!\n'stock' to draw a card from the stock\n'discard' to draw a card from the discarded cards\n")
                    while True:
                        try:
                            match command:
                                case 'stock':
                                    command2 = input(f"The card you got is: {stockCard}, you can either discard or swap it (enter swap row col)")
                                    if command2 == "discard":
                                        self.discard(stockCard)
                                    elif command2.split()[0] == "swap":
                                        self.swap(stockCard, command2.split()[1], command2.split()[2])
                                case 'discard':
                                    command2 = input(f"With which card do you want to swap? (enter row col)")
                                    self.swap(discardCard, command2.split()[0], command2.split()[1])
                            self.turn = False
                        except:
                            command = input("Incorrect Format! Please try again, do you want to draw from stock or discard?")
                    self.updatePlayers()

                else:
                    self.send_to_peer_rec(self.peers[p][0], self.peers[p][1], "turn " + Player.encodeDeck(self.deck))
                time.sleep(0.1)
                

    def updatePlayers(self):
        self.print_deck()
        for peer in self.peers.keys():
            self.send_to_peer(self.peers[peer][0], self.peers[peer][1], "update " + Player.encodeDeck(self.deck))


    def dealCards(self, players):
        shuffledSet = list(Player.standardDeck.keys())
        random.shuffle(shuffledSet)
        deck = ""
        index = 0
        for i in range(51-len(players) * 6):
            deck += f"{shuffledSet[index]} "
            index += 1
        deck = deck[:-1]
        deck += ";"
        deck += f"{shuffledSet[index]};"
        index += 1
        for player in players:
            deck += f"{player} "
            for i in range(6):
                deck += f"h{shuffledSet[index]} "
                index += 1
            deck = deck[:-1]
            deck += ";"
        return deck[:-1]

    # Converting the deck from a string to a dictionary
    def decodeDeck(deck):
        splittedDeck = deck.split(";")
        state = {}
        state["stock"] = splittedDeck[0].split(" ")
        state["discard"] = splittedDeck[1].split(" ")
        state["players"] = {}
        for p in splittedDeck[2:]:
            playerInfo = p.split(" ")
            state["players"][playerInfo[0]] = playerInfo[1:]
        return state

    # Converting the deck from a dictionary to string
    def encodeDeck(deck):
        encodedDeck = ""
        for card in deck["stock"]:
            encodedDeck += f"{card} "
        encodedDeck = encodedDeck[:-1] + ";"
        for card in deck["discard"]:
            encodedDeck += f"{card} "
        encodedDeck = encodedDeck[:-1] + ";"

        for player, l in deck["players"].items():
            encodedDeck += f"{player} "
            for item in l:
                encodedDeck += f"{item} "
            encodedDeck = encodedDeck[:-1] + ";"
        encodedDeck = encodedDeck[:-1]
        return encodedDeck

    def print_deck(self): # game list is a list containing: Discard piles: K10, Stock, print all other player hands
        """Prints the player's hand."""
        print("New state of the game:")
        print("Discard piles: %-3s Stock: ***" % (self.deck["discard"][0]))
        deck = ""
        players = list(self.deck["players"].keys())
        deck += f"%11s" % players[0]
        for player in players[1:]:
            deck += f"%13s" % player
        deck += "\n"
        for player in players:
            for i in range(3):
                if self.deck["players"][player][i][0] == "h": # Hidden card
                    deck += "*** "
                else:
                    deck += "%3s " % self.deck["players"][player][i]
            deck += " "
        deck += "\n"
        for player in players:
            for i in range(3):
                if self.deck["players"][player][i+3][0] == "h": # Hidden card
                    deck += "*** "
                else:
                    deck += "%3s " % self.deck["players"][player][i+3]
            deck += " "
        print(deck)

    def getCardFromStock(self):
        pass
    
    def getCardFromDiscarded(self):
        pass

    def swap(self, card, row, col):
        pass

    def discard(self, card):
        pass

    def handle_tracker(self, message):
        pass

    def handle_peers(self, message, addr):
        splittedMessage = message.split(" ")                
        print(splittedMessage[0])
        if self.state == "Dealer":
            match splittedMessage[0]:
                case "update":
                    self.deck = Player.decodeDeck(message[7:])
                    self.updatePlayers()
        
        elif self.state == "Player":
            match splittedMessage[0]:
                case "winner": # game ends
                    print("The winner of the game is:", splittedMessage[1])
                    self.in_game.clear()

                case "update": # message = "state, deck ومعلومات اللاعبين"
                    print("Update entered")
                         = Player.decodeDeck(message[7:])
                    self.print_deck()

                case "turn":
                    self.turn = True
                    print("It is your turn, choice one of the options!\n'stock' to draw a card from the stock\n'discard' to draw a card from the discarded cards\n")

        else: # None
            if splittedMessage[0] == "invite":
                print(f"----------- Welcome You Joined a Game With the Host {splittedMessage[1]} -----------")
                self.state = "Player"
                self.dealer = [addr[0], addr[1]]
                self.in_game.set()

    # def unfoldDeck(self, game):
    #     pass

    def handle_menu_input(self, command):
        splittedCmd = command.split()
        if splittedCmd[0] == "register":
            if len(splittedCmd) != 5:
                print("please use the command in the following manner: register <player> <IPv4> <t-port> <p-port>")
                return

            name = splittedCmd[1]
            if not (name.isalpha() and len(name) <= 15):
                print("Invalid name, name should consist of only alphabetic characters and its length is at most 15 characters")
                return

            if not (cfunctions.validIPv4(splittedCmd[2])):
                print("Invalid IPv4 address")
                return

            t_port = splittedCmd[3]
            try:
                t_port = int(t_port)
            except:
                print("t-port should be an integer")
                return

            p_port = splittedCmd[4]
            try:
                p_port = int(p_port)
            except:
                print("p-port should be an integer")
                return

            if self.register(splittedCmd[1], splittedCmd[2], t_port, p_port):
                self.setName(splittedCmd[1])
            
        elif command == "query players":
            self.query_players()     

        elif command == "query games":
            self.query_games()

        elif splittedCmd[0]+splittedCmd[1] == "startgame":
            if len(splittedCmd) != 5:
                print("please use the command in the following manner: start game <player> <n> <holes>")
                return
            try:
                player_name = splittedCmd[2]
                n = int(splittedCmd[3])
                holes = int(splittedCmd[4])
            except ValueError:
                print("Invalid command parameters")
                return
            self.start_game(player_name, n, holes)


        elif splittedCmd[0] == "de-register":
            if self.deregister(splittedCmd[1]) and self.name == splittedCmd[1]:
                sys.exit()

        else:
            print("Unknown command")

    def handle_game_input(self, command):
        if not self.turn:
            print("It is not your turn!")
            return
        
        stockCard = self.getCardFromStock()
        discardCard = self.getCardFromDiscarded()
        while True:
            try:
                match command:
                    case 'stock':
                        command2 = input(f"The card you got is: {stockCard}, you can either discard or swap it (enter swap row col)")
                        if command2 == "discard":
                            self.discard(stockCard)
                        elif command2.split()[0] == "swap":
                            self.swap(stockCard, command2.split()[1], command2.split()[2])
                    case 'discard':
                        command2 = input(f"With which card do you want to swap? (enter row col)")
                        self.swap(discardCard, command2.split()[0], command2.split()[1])
                self.turn = False
                self.send_to_peer(self.dealer[0], self.dealer[1], "update " + self.encodeDeck(self.deck))
            except:
                command = input("Incorrect Format! Please try again, do you want to draw from stock or discard?")

    def end_game(self):
        """Ends the game and notifies the tracker."""
        message = f"end {self.game_id} {self.name}"
        print(f"Ending game {self.game_id}")
        self.send_to_tracker(message)
        self.in_game.clear()

    def main(self):
        while True:
            name = self.name if self.name != None else ""
            command = input(f"{name}> ")
            if self.in_game.is_set(): # Change that to an event
                self.handle_game_input(command)
            else:
                self.handle_menu_input(command)
    
    def start(self):    
        self.tracker_thread.start()  # Start listening to the tracker
        self.peer_thread.start()  # Start listening to peers
        self.main_thread.start()  # Start the main menu

if __name__ == "__main__":
    pInformation = input("Enter the following information: <Tracker IPv4> <Tracker port number> <Peer-Tracker port number> <Peer-Peer port number>: \n").split()
    player = Player(pInformation[0], int(pInformation[1]), int(pInformation[2]), int(pInformation[3]))
    player.start()