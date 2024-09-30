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
            response = self.handle_request(message) # sends the message to a handling method
            server.sendto(response.encode('utf-8'), addr) # reply to the sender

    def handle_request(self, message):
        command = message.split()
        if command[0] == 'register':
            return self.register_player(command[1:])
        
        elif command[0] == 'query':
            if command[1] == 'players':
                return self.query_players()
            
            elif command[1] == 'games':
                return self.query_games()
        
        # elif command[0] == 'start':                   to be implemented later
        #   return self.start_game(command[1:])         to be implemented later
            
        elif command[0] == 'de-register':
            return self.deregister_player(command[1])
        
        else:
            return "Invalid command"

    def register_player(self, params):
        player_name, ipv4, t_port, p_port = params
        if player_name not in self.players: # checks if there is a duplicate name
            self.players[player_name] = [ipv4, t_port, p_port]
            return "SUCCESS: Player registered"
        else:
            return "FAILURE: Player already registered"

    def query_players(self):
        try:
            length = 0
            for i in self.players.items():  
                length+=1
            response = str(length)
            response+="\nRegistered players:\n"
            for player, info in self.players.items():
                response += f"{player} at {info[0]}:{info[1]}|{info[2]}\n"
            return response
        except:
            return "cannot be done"

    def query_games(self): 
        response = f"{len(self.games)}\n"
        for game, info in self.games.items():
            response += f"Game: {game} Dealer: {info[0]} Players: {info[1:]}"
        return response
    
    def start_game(self, params):
        pass

    def deregister_player(self, player_name):
        if player_name in self.players:
            del self.players[player_name]
            return "SUCCESS: Player deregistered"
        else:
            return "FAILURE: Player not registered"


if __name__ == "__main__":
    IPv4 = input("Enter the IPv4: ")
    portNumber = cfunctions.validPortNumber()
    tracker = Tracker(IPv4, portNumber)
    tracker.start()