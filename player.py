import socket
import threading
import sys
import cfunctions

class Player:
    def __init__(self, IPv4, tracker_port, pt_port, pp_port):
        """stores the information need as described in the specification"""
        self.name = None
        self.in_game = False
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

        self.tracker_thread = threading.Thread(target=self.listen_to_tracker)
        self.peer_thread = threading.Thread(target=self.listen_to_peers)
        self.main_thread = threading.Thread(target=self.main)

    def setName(self, name):
        self.name = name

    def send_to_tracker(self, message):
        """we are group 68, hence we are assigned the numbers in the range [35000, 35499]"""
        self.pt_socket.sendto(message.encode('utf-8'), (self.IPv4, self.tracker_port))
        
        # Signal the tracker thread to stop gracefully
        self.stop_event.set()
        self.pt_socket.setblocking(True)
        response, _ = self.pt_socket.recvfrom(1024)
        print(f"Tracker response:\n{response.decode('utf-8')}")
        self.pt_socket.setblocking(False)

        # Clear stop_event to allow restarting the thread if needed
        self.stop_event.clear()
        
        # Restart the thread if it's not alive
        if not self.tracker_thread.is_alive():
            self.tracker_thread = threading.Thread(target=self.listen_to_tracker)
            self.tracker_thread.start()
            
        
        return response.decode('utf-8')

    def register(self, name, IPv4, tracker_port, player_port):
        message = f"register {name} {IPv4} {tracker_port} {player_port}"
        print("Register request is sent to the tracker")
        return self.send_to_tracker(message) == "SUCCESS: Player registered"

    def query_games(self):
        message = "query games"
        print("Query games request is sent to the tracker")
        self.send_to_tracker(message)

    def start_game(self, player, n, holes):
        message = f"start {player} {n} {holes}"
        self.send_to_tracker(message)

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
                if message == "game":
                    pass
                print(f"Tracker response:\n{message}")
            except BlockingIOError:
                pass

    def listen_to_peers(self):
        """Listen for messages from other peers."""
        while True:
            data, addr = self.pp_socket.recvfrom(1024)
            message = data.decode('utf-8')
            print(message)

    def main_page(self, command):
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

        elif splittedCmd[0:2] == ["start", "game"]:
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

    def game(self, command):
        pass # Here we will complete the game functionalities

    def main(self):
        while True:
            name = self.name if self.name != None else ""
            command = input(f"{name}> ")

            if self.in_game:
                self.game(command)
            else:
                self.main_page(command)
    
    def start(self):    
        self.tracker_thread.start()  # Start listening to the tracker
        self.peer_thread.start()  # Start listening to peers
        self.main_thread.start()  # Start the main menu


if __name__ == "__main__":
    pInformation = input("Enter the following information: <Tracker IPv4> <Tracker port number> <Peer-Tracker port number> <Peer-Peer port number>: \n").split()
    player = Player(pInformation[0], int(pInformation[1]), int(pInformation[2]), int(pInformation[3]))
    player.start()