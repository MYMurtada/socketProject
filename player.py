import socket
import threading
import sys
import cfunctions
import random
import time

class Player:
    standardDeck = {}
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

        # Define stop_event for thread control
        self.stop_event = threading.Event()
        self.in_game = threading.Event()

        self.tracker_thread = threading.Thread(target=self.listen_to_tracker)
        self.peer_thread = threading.Thread(target=self.listen_to_peers)
        self.main_thread = threading.Thread(target=self.main)

        self.peers = {}
        self.state = None
        self.hand = [None] * 6
        self.peer_sockets = {}
        self.game_id = None
        self.holes = 0
        self.current_hole = 0
  
    def setName(self, name):
        self.name = name

    def send_to_tracker(self, message):
        """we are group 68, hence we are assigned the numbers in the range [35000, 35499]"""
        self.pt_socket.sendto(message.encode('utf-8'), (self.IPv4, self.tracker_port))
        
        # Signal the tracker thread to stop gracefully
        self.stop_event.set()
        self.pt_socket.setblocking(True)
        response = self.pt_socket.recvfrom(1024)[0]
        print(f"Tracker response:\n{response.decode('utf-8')}")
        self.pt_socket.setblocking(False)

        # Clear stop_event to allow restarting the thread if needed
        self.stop_event.clear()
        
        # Restart the thread if it's not alive
        if not self.tracker_thread.is_alive():
            self.tracker_thread = threading.Thread(target=self.listen_to_tracker)
            self.tracker_thread.start()
            
        return response.decode('utf-8')

    def send_to_peer(self, ip, port, message):
        """Send a message to a peer via the peer-to-peer socket."""
        self.pp_socket.sendto(message.encode('utf-8'), (ip, port))

    def register(self, name, IPv4, tracker_port, player_port):
        message = f"register {name} {IPv4} {tracker_port} {player_port}"
        print("Register request is sent to the tracker")
        return self.send_to_tracker(message) == "SUCCESS: Player registered"

    def query_games(self):
        message = "query games"
        print("Query games request is sent to the tracker")
        self.send_to_tracker(message)

    def start_game(self, player, n, holes):
        message = f"start game {player} {n}"
        response = self.send_to_tracker(message)
        if response.split(":")[0] == "FAILURE":
            print(response)
            return
        else:
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
            
            # self.players = {"Name": hand}
            """

            for player in self.players:
                if player != self.name:
                    send to player that it is your turn
                    listen to the outcome
                    update the deck
                    send the updated deck to every other player
                if player == self.name
                    tell the user that it is your player
                    take the inptu
                    update the deck
                    send the updated to others
            """

    def deregister(self, name):
        message = f"de-register {name}"
        print(f"De-register request for the player {name} is sent to the tracker")
        return self.send_to_tracker(message) == "SUCCESS: Player deregistered"

    def query_players(self):
        message = "query players"
        print(f"Query players request is sent to the tracker")
        self.send_to_tracker(message)

    def listen_to_tracker(self):
        """Listen for messages from the tracker."""
        while not self.stop_event.is_set():  # Check if the stop_event is set to stop the thread
            try:
                data, addr = self.pt_socket.recvfrom(1024)
                message = data.decode('utf-8')
                self.handle_tracker(message)
            except BlockingIOError:
                pass

    def listen_to_peers(self):
        """Listen for messages from other peers."""
        while True:
            data, addr = self.pp_socket.recvfrom(1024)
            message = data.decode('utf-8')
            try:
                self.handle_peers(message)
            except:
                pass
    
    def handle_tracker(self, message):
        pass # To be implemented

    def handle_peers(self, message):
        """are you dealer:
            yes:
                استقبل من اللاعبين الحالة للعبة
                ارسل الحالة الجديدة لجميع اللاعبين
            No:
                استقبل من الديلر
                حدث عندك الحالة
        """
        splittedMessage = message.split()                
        print(message, splittedMessage)
        if self.state == "Dealer":
            pass
        elif self.state == "Player":
            match splittedMessage[0]:
                case "Winner": # game ends
                    print("The winner of the game is:", splittedMessage[1])
                    self.in_game.clear()
                case "state": # message = "state, deck ومعلومات اللاعبين"
                    self.current_hole = splittedMessage[1]
                    pass # Here we need to handle the state
                case "turn":
                    print("It is your turn, choice one of the options!\n'stock' to draw a card from the stock\n'discard' to draw a card from the discarded cards\n")

        else: # None
            match splittedMessage[0]:
                case "invite":
                    print("You got an invite to join a game by:", splittedMessage[1])
                    self.state = "Player"
                    self.in_game.set()
                
    def set_up_game(self, game_info):
        """Sets up the game with the given player information."""
        players_info = game_info.split('\n')[1:]
        self.peer_sockets = {}
        for player_info in players_info:
            player_name, ip, port = player_info.split()
            if player_name != self.name:
                self.peer_sockets[player_name] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.peer_sockets[player_name].connect((ip, int(port)))
        self.deal_cards()

    def deal_cards(self):
        """Deals 6 cards to the player."""
        deck = list(range(1, 53))  # 1 to 52 represent cards
        random.shuffle(deck)
        self.hand = deck[:6]
        self.turn_two_cards_face_up()
        self.print_hand()

    def turn_two_cards_face_up(self):
        """Turns two random cards face-up."""
        face_up_indices = random.sample(range(6), 2)
        for i in face_up_indices:
            self.hand[i] = abs(self.hand[i])  # Ensure positive value represents face-up

    def print_deck(self, game_state): # game list is a list containing: Discard piles: K10, Stock, print all other player hands
        print('')


        """Prints the player's hand."""
        hand_display = []
        for card in self.hand:
            if card is None:
                hand_display.append('***')
            else:
                hand_display.append(str(card) if card > 0 else '***')
        print('Your hand:', ' '.join(hand_display))

    def play_turn_from_stock(self):
        """Plays the player's turn."""
        card = random.randint(1, 52)  # Simulate drawing a card
        print(f"Drawn card: {card}\n")
        replace_index = input("Choice the index to swap (1-6) or 'discard' to discard it: ")
        if replace_index == 'discard':
            self.discarded = card 
        else:
            self.print_hand()
            self.hand[replace_index] = card
            self.discarded = random.randint(1, 52)
        print("\n")
        self.print_hand()
        
    def play_turn_from_discard(self):
        """Plays the player's turn."""
        card = self.discarded  
        print(f"Drawn card: {card}\n")
        replace_index = input("Choice the index to swap (1-6): ")
        self.print_hand()
        if self.hand[replace_index] == "***":
            self.hand[replace_index] = card
            self.discarded = random.randint(1, 52)
        else:
            self.discarded = self.hand[replace_index]
            self.hand[replace_index] = card
           
        print("\n")
        self.print_hand()

    def play_game(self):
        """Plays the entire game for the specified number of holes."""
        for hole in range(self.holes):
            self.current_hole = hole + 1
            print(f"Starting hole {self.current_hole}")
            self.play_turn()
            time.sleep(1)  # Simulate time between turns
        self.end_game()

    def end_game(self):
        """Ends the game and notifies the tracker."""
        message = f"end {self.game_id} {self.name}"
        print(f"Ending game {self.game_id}")
        self.send_to_tracker(message)
        self.in_game.clear()

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
        splittedCmd = command.split()
        if splittedCmd[0] == "stock":
            self.play_turn_from_stock()
            
        elif splittedCmd[0] == "discard":
            self.play_turn_from_discard()
            
        else:
            print("Unknown game command")

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
