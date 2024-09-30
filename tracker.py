import socket
import cfunctions

class Tracker:
    def __init__(self, IPv4, port):
        self.IPv4 = IPv4 # saves the IPv4 of the tracker
        self.port = port # saves the port of the tracker
        self.players = {} # a dictionary containing player names as keys, and their information as values
        self.games = {} # a dictionary containing all the game IDs as keys, player information as the values (dealer is the first in the list)

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.bind((self.IPv4, self.port)) # binding the socket to the given IPv4 and port
        print(f"Tracker listening on {self.IPv4}:{self.port}")
        
        while True: # constantly listening to messages from the designated port
            data, addr = server.recvfrom(1024)
            message = data.decode('utf-8') # decoding data to the commonly used UTF-8 format
            response, systemResponse = self.handle_request(message, addr) # sends the message to a handling method
            server.sendto(response.encode('utf-8'), addr) # reply to the sender
            if systemResponse:
                print(systemResponse)

    def handle_request(self, message, addr):
        command = message.split()
        if command[0] == 'register':
            print(f"A registration request to register {command[1]} was received from:", addr)
            return self.register_player(command[1:])
        
        elif command[0] == 'query':
            if command[1] == 'players':
                print("A query players request received from the address:", addr)
                return self.query_players()
            
            elif command[1] == 'games':
                print("A query games request received from the address:", addr)
                return self.query_games()
        
        # elif command[0] == 'start':                   to be implemented
        #   return self.start_game(command[1:])         to be implemented
            
        elif command[0] == 'de-register':
            print(f"A de-register request to de-register {command[1]} received from the address:", addr)
            return self.deregister_player(command[1])
        
        else:
            return "Invalid command"

    def register_player(self, params):
        player_name, ipv4, t_port, p_port = params
        if player_name not in self.players: # checks if there is a duplicate name
            self.players[player_name] = [ipv4, t_port, p_port]
            print(f"Player {player_name} was successfully registered")
            return "SUCCESS: Player registered", None
        else:
            print(f"Player {player_name} is already registered")
            return "FAILURE: Player already registered", None

    def query_players(self):
        length = len(self.players)
        response = str(length)
        response+="\nRegistered players:\n"
        for player, info in self.players.items():
            response += f"{player} at {info[0]}:{info[1]}|{info[2]}\n"
           
        return response, "Query response is sent to the player"


    def query_games(self): 
        response = f"{len(self.games)}\n"
        response+="\Current games:\n"
        for game, info in self.games.items():
            response += f"Game: {game} Dealer: {info[0]} Players: {info[1:]}"
        return response, "Query games response is sent to the player"
    
    def start_game(self, params):
        pass

    def deregister_player(self, player_name):
        if player_name in self.players:
            del self.players[player_name]
            print(f"{player_name} is deregistered from the system")
            return "SUCCESS: Player deregistered", None
        else:
            print(f"The request to deregister {player_name} could not be completed")
            return "FAILURE: Player not registered", None

if __name__ == "__main__":
    IPv4 = input("Enter the IPv4: ")
    portNumber = cfunctions.validPortNumber()
    tracker = Tracker(IPv4, portNumber)
    tracker.start()