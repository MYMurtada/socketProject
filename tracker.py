import socket
import cfunctions

class Tracker:
    def __init__(self, IPv4, port):
        self.IPv4 = IPv4
        self.port = port
        self.players = {}
        self.games = {}

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.bind((self.IPv4, self.port))
        print(f"Tracker listening on {self.IPv4}:{self.port}")
        
        while True:
            data, addr = server.recvfrom(1024)
            message = data.decode('utf-8')
            response = self.handle_request(message)
            server.sendto(response.encode('utf-8'), addr)

    def handle_request(self, message):
        command = message.split()
        if command[0] == 'register':
            return self.register_player(command[1:])
        
        elif command[0] == 'query':
            if command[1] == 'players':
                return self.query_players()
            
            elif command[1] == 'games':
                return self.query_games()
        
        elif command[0] == 'start':
            return self.start_game(command[1:])
    
        elif command[0] == 'de-register':
            return self.deregister_player(command[1])
        
        else:
            return "Invalid command"

    def register_player(self, params):
        player_name, ipv4, t_port, p_port = params
        if player_name not in self.players:
            self.players[player_name] = [ipv4, t_port, p_port]
            return "SUCCESS: Player registered"
        else:
            return "FAILURE: Player already registered"

    def query_players(self):
        try:
            if not self.players:
                return "No players registered"
            length =0;
            for i in self.players.items():  
                length+=1
            response = str(length)
            response+=" - Registered players:\n"
            for player, info in self.players.items():
                # players += (f"{player} at {info[0]}",)
                response += f"{player} at {info[0]}:{info[1]}|{info[2]}\n"
            # response += f"{players}"
            return response
        except:
            return "cannot be done"

    def query_games(self):
        if len(self.games) == 0:
            return "No games running"
        response = ""
        for game, info in self.games.info():
            response += f"Game: {game} Dealer: {info[0]} Players: {info[1:]}"

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