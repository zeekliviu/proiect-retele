import socket


def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((socket.gethostname(), 6969))

    while True:
        message = input("Introduceți o comandă pentru ZethNews (pentru o listă de comenzi scrie /ajutor): ")
        client.send(message.encode("utf-8"))
        response = client.recv(2048).decode("utf-8")
        if response == "deconectat":
            print("Ați fost deconectat cu succes!")
            break
        print(response)


if __name__ == "__main__":
    main()
