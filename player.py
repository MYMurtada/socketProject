import socket
import cfunctions

class Player:
    def __init__(self, IPv4, tracker_port, pt_port, pp_port):
        self.name = None
        self.IPv4 = IPv4
        self.tracker_port = tracker_port
        self.pt_port = pt_port
        self.pt_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.pt_socket.bind((IPv4, pt_port))
        self.pp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.pp_socket.bind((IPv4, pp_port))

    def setName(self, name):
        self.name = name

    def send_to_tracker(self, message):
        self.pt_socket.sendto(message.encode('utf-8'), (self.IPv4, self.tracker_port)) # we are group 68, hence we are assigned the numbers in the  range [35000, 35499]
        response, _ = self.pt_socket.recvfrom(1024)
        print(response.decode('utf-8'))
        return response.decode('utf-8')

    def register(self, name, IPv4, tracker_port, player_port):
        message = f"register {name} {IPv4} {tracker_port} {player_port}"
        return self.send_to_tracker(message) == "SUCCESS: Player registered"

    def query_games(self):
        message = "query games"
        self.send_to_tracker(message)

    def start_game(self, player, n, holes):
        message = f"start {player} {n} {holes}"
        self.send_to_tracker(message)

    def deregister(self, name):
        message = f"de-register {name}"
        return self.send_to_tracker(message) == "SUCCESS: Player deregistered"

    def query_players(self):
        message = "query players"
        self.send_to_tracker(message)


if __name__ == "__main__":
    pInformation = input("Enter the following information: <Tracker IPv4> <Tracker port number> <Peer-Tracker port number> <Peer-Peer port number>: \n").split()
    player = Player(pInformation[0], int(pInformation[1]), int(pInformation[2]), int(pInformation[3]))
    while True:
        name = player.name if player.name != None else ""
        command = input(f"{name}> ")
        splittedCmd = command.split()

        if splittedCmd[0] == "register":
            if len(splittedCmd) != 5:
                print("please use the command in the following manner: register <player> <IPv4> <t-port> <p-port>")
                continue

            name = splittedCmd[1]
            if not (name.isalpha() and len(name) <= 15):
                print("Invalid name, name should consist of only alphabetic characters and its length is at most 15 characters")
                continue

            if not (cfunctions.validIPv4(splittedCmd[2])):
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

            if (player.register(splittedCmd[1], splittedCmd[2], t_port, p_port)):
                player.setName(splittedCmd[1])
            
        elif command == "query players":
            player.query_players()        
        elif command == "query games":
            player.query_games()

        #elif command[0] == "start game":
        #    player.start_game(command[1], int(command[2]), int(command[3]))

        elif splittedCmd[0] == "de-register":
            if player.deregister(splittedCmd[1]) == True and player.name == splittedCmd[1]:
                break
        else:
            print("Unknown command")