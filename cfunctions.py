# This is a file containing complementary functions

def validIPv4(IPv4): # checks if the address follows the IPv4 format
    IPv4 = IPv4.split(".")
    if (len(IPv4) == 4):
        for num in IPv4:
            try:
                n = int(num)
                if not (0 <= n <= 255):
                    return False
            except:
                return False
    else:
        return False
    
    return True

def validPortNumber():
    portNumber = None
    while portNumber == None:
        try:
            portNumber = int(input("Pass the port number of the tracker (must be in the range 35,000-35,499): "))
            if not (34999 < portNumber < 35500):
                print("The port number is out of range\n")
                portNumber = None
        except:
            print("please pass an integer\n")
    return portNumber