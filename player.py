import socket
import re

class Player:
    def __init__(self, name, IPv4, tracker_port, player_port):
        self.name = name
        self.IPv4 = IPv4
        self.tracker_port = tracker_port
        self.player_port = player_port
        register(name, IPv4, tracker_port, player_port)

def send_to_tracker(message):
    tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tracker_socket.sendto(message.encode('utf-8'), ("localhost", 35000)) # we are group 68, hence we are assigned the numbers in the  range [35000, 35499]
    response, _ = tracker_socket.recvfrom(1024)
    print(response.decode('utf-8'))

def register(name, IPv4, tracker_port, player_port):
    message = f"register {name} {IPv4} {tracker_port} {player_port}"
    send_to_tracker(message)

def query_games():
    message = "query games"
    send_to_tracker(message)

def start_game(player, n, holes):
    message = f"start {player} {n} {holes}"
    send_to_tracker(message)

def deregister(name):
    message = f"de-register {name}"
    send_to_tracker(message)

def query_players():
    message = "query players"
    send_to_tracker(message)


if __name__ == "__main__":
    player = None
    
    while True:
        command = input(f"> ")
        
        if command.split()[0] == "register":
            if player != None:
                print("player is already registered")
                continue

            splittedCmd = command.split()
            if len(splittedCmd) != 5:
                print("please use the command in the following manner: register <player> <IPv4> <t-port> <p-port>")
                continue

            name = splittedCmd[1]
            if not (name.isalpha() and len(name) <= 15):
                print("Invalid name, name should consist of only alphabetic characters and its length is at most 15 characters")
                continue

            IPv4 = splittedCmd[2].split(".")
            validIPv4 = True
            if (len(IPv4) == 4):
                for num in IPv4:
                    try:
                        n = int(num)
                        if not (0 < n < 255):
                            validIPv4 = False
                    except:
                        validIPv4 = False
            else:
                validIPv4 = False
            
            if not validIPv4:
                print("Invalid IPv4 address")
                continue

            t_port = splittedCmd[3]
            try:
                t_port = int(t_port)
            except:
                print("t-port should be an integer")
                continue

            p_port = splittedCmd[4]
            try:
                p_port = int(p_port)
            except:
                print("p-port should be an integer")
                continue

            player = Player(name, splittedCmd[2], t_port, p_port)
        
        elif command == "query players":
            query_players()        
        elif command == "query games":
            query_games()
        elif command[0] == "start game":
            start_game(command[1], int(command[2]), int(command[3]))
        elif command[0] == "de-register":
            deregister(command[1])
        else:
            print("Unknown command")