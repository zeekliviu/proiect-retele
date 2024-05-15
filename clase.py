import socket
import threading


class Client:
    def __init__(self, socket_p: socket.socket, address):
        self.socket = socket_p
        self.address = address
        self.autentificat = False
        self.buffer = ""

    def send(self, message) -> None:
        if self.buffer:
            message = self.buffer + message
            self.buffer = ""
        self.socket.send(message.encode("utf-8"))

    def recv(self, size: int) -> str:
        try:
            return self.socket.recv(size).decode("utf-8")
        except ConnectionAbortedError:
            print(f"Conexiune întreruptă de către clientul {self.address[0]}:{self.address[1]}!")

    def close(self) -> None:
        self.socket.close()


class CanalStiri:
    def __init__(self, client: Client, nume: str, descriere: str):
        self.owner = client.address
        self.nume = nume
        self.descriere = descriere
        self.abonati = [client]

    def notifica_stergere(self):
        for abonat in self.abonati:
            abonat.send(f"Canalul {self.nume} a fost șters de către proprietarul său!")

    def notifica_stire_noua(self, stire: str):
        for abonat in self.abonati:
            abonat.send(f"\n-------------------ȘTIRE NOUĂ DE PE CANALUL {self.nume}-------------------\n\n{stire}\n\n-----------------------------------------------\n")


class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password


class Server:
    def __init__(self):
        self.canale_stiri = []
        self.cuvinte_interzise = ["zebra", "leu", "girafa"]
        self.clienti = []
        self.useri = []
        self.endpoints = {
            "/autentificare": "Autentifică-te folosind /autentificare <username> <parolă>",
            "/inregistrare": "Înregistrează-te folosind /inregistrare <username> <parolă>",
            "/canale": "Afișează lista de canale de știri folosind /canale",
            "/refresh": "Reîmprospătează fluxul de știri folosind /refresh",
            "/creare": "Creează un canal de știri folosind /creare <nume> <descriere>",
            "/abonare": "Abonează-te la un canal de știri folosind /abonare <nume>",
            "/dezabonare": "Dezactivează notificările de la un canal de știri folosind /dezabonare <nume>",
            "/abonamente": "Afișează lista de canale la care ești abonat/ă folosind /abonamente",
            "/postare": "Postează o știre într-un canal folosind /postare <nume> <știre> (doar pentru proprietari)",
            "/sterge": "Șterge un canal de știri folosind /sterge <nume> (doar pentru proprietari)",
            "/deconectare": "Deconectează-te de la server folosind /deconectare",
            "/ajutor": "Afișează lista de comenzi disponibile",
        }
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = socket.gethostname()
        self.port = 6969

    def start(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        print(f"Serverul rulează pe {self.host}:{self.port}")
        while True:
            client, address = self.socket.accept()
            print(f"Conexiune nouă de la {address}")
            client_obj = Client(client, address)
            self.clienti.append(client_obj)
            threading.Thread(target=self.handle_client, args=(client_obj,)).start()

    def handle_client(self, client):
        while True:
            try:
                message = client.recv(1024).lower()
                if message.startswith("/autentificare"):
                    self.autentificare(client, message)
                elif message.startswith("/inregistrare"):
                    self.inregistrare(client, message)
                elif message == "/ajutor":
                    self.send_help(client)
                elif message == "/refresh":
                    self.refresh(client)
                elif message == "/canale":
                    self.send_channels(client)
                elif message == "/deconectare":
                    client.send("deconectat")
                    client.close()
                    break
                elif message.startswith("/creare"):
                    self.creare_canal(client, message)
                elif message.startswith("/abonare"):
                    self.abonare_canal(client, message)
                elif message.startswith("/dezabonare"):
                    self.dezabonare_canal(client, message)
                elif message.startswith("/abonamente"):
                    self.abonamente(client)
                elif message.startswith("/sterge"):
                    self.sterge_canal(client, message)
                elif message.startswith("/postare"):
                    self.postare_stire(client, message)
                else:
                    client.send("Comandă invalidă!")
            except ConnectionResetError:
                client.close()
                break

    @staticmethod
    def refresh(client):
        if client.buffer:
            client.send(client.buffer)
            client.buffer = ""
        else:
            client.send("Nu există știri noi!")

    def creare_canal(self, client, message):
        if not client.autentificat:
            client.send("Trebuie să fii autentificat pentru a crea un canal")
            return
        if len(message.split(" ")) < 3:
            client.send("Comandă invalidă! Sintaxă: /creare nume_canal (fără spații) descriere_canal")
            return
        nume = message.split(" ")[1]
        descriere = " ".join(message.split(" ")[2:])
        if nume in [canal.nume for canal in self.canale_stiri]:
            client.send("Numele canalului există deja!")
            return
        self.canale_stiri.append(CanalStiri(client, nume, descriere))
        client.buffer += f"Canalul \"{nume}\" a fost creat cu succes!\nAi fost automat abonat la acesta. Pentru a dezactiva notificările, scrie: /dezabonare {nume}\nPentru a posta o știre, scrie: /postare {nume} <știre>\n"
        self.notifica_canal_nou(self.canale_stiri[-1])

    def notifica_canal_nou(self, canal):
        for client in self.clienti:
            if client.autentificat:  # and client.address != canal.owner: // daca aplicatia n-ar fi pe acelasi calculator; merge cu client.address[1] != canal.owner[1], dar n-are rost
                client.buffer += f"-------------------CANAL NOU-------------------\n\nA fost creat un nou canal de știri: {canal.nume} - {canal.descriere}\n\nPentru a te abona, scrie: /abonare {canal.nume}\n\n-----------------------------------------------"
                client.send("")

    def abonare_canal(self, client, message):
        if not client.autentificat:
            client.send("Trebuie să fii autentificat pentru a te abona la un canal")
            return
        if len(message.split(" ")) < 2:
            client.send("Comandă invalidă! Sintaxă: /abonare nume_canal")
            return
        nume = message.split(" ")[1]
        for canal in self.canale_stiri:
            if canal.nume == nume:
                canal.abonati.append(client)
                client.send(
                    f"Te-ai abonat la canalul {canal.nume}! Începând de acum vei primi știri de la acesta când vor apărea.\nTastează /dezabonare {canal.nume} pentru a dezactiva notificările.\nTastează /refresh pentru a reîmprospăta fluxul.")
                return
        client.send("Canalul nu există în lista de canale disponibile!\nPentru a vedea lista de canale, scrie: /canale")

    def dezabonare_canal(self, client, message):
        if not client.autentificat:
            client.send("Trebuie să fii autentificat pentru a te dezabona de la un canal")
            return
        if len(message.split(" ")) < 2:
            client.send("Comandă invalidă! Sintaxă: /dezabonare nume_canal")
            return
        nume = message.split(" ")[1]
        for canal in self.canale_stiri:
            if canal.nume == nume:
                canal.abonati.remove(client)
                client.send(
                    f"Te-ai dezabonat de la canalul {canal.nume}! Nu vei mai primi notificări de la acesta.\nTastează /abonare {canal.nume} pentru a te abona din nou.\nTastează /refresh pentru a reîmprospăta fluxul.")
                return
        client.send(
            "Nu ești abonat la acest canal!\nPentru a vedea lista de canale la care ești abonat, scrie: /abonamente")

    def abonamente(self, client):
        if not client.autentificat:
            client.send("Trebuie să fii autentificat pentru a vedea canalele la care ești abonat!")
            return
        message = ""
        for canal in self.canale_stiri:
            if client in canal.abonati:
                message += f"{canal.nume}: {canal.descriere}\n"
        if not message:
            message = "Nu ești abonat la niciun canal de știri!\nPentru a vedea lista de canale disponibile, scrie: /canale"
        else:
            message = "Ești abonat la următoarele canale de știri:\n-----------------------------------------------\n" + message + "-----------------------------------------------\n"
        client.send(message)

    def sterge_canal(self, client, message):
        if not client.autentificat:
            client.send("Trebuie să fii autentificat pentru a șterge un canal!")
            return
        if len(message.split(" ")) < 2:
            client.send("Comandă invalidă! Sintaxă: /sterge nume_canal")
            return
        nume = message.split(" ")[1]
        if nume not in [canal.nume for canal in self.canale_stiri]:
            client.send("Canalul nu există!")
            return
        for canal in self.canale_stiri:
            if canal.nume == nume and canal.owner == client.address:
                self.canale_stiri.remove(canal)
                client.buffer += f"Canalul {canal.nume} a fost șters cu succes!"
                canal.notifica_stergere()
                return
        client.send("Nu ești proprietarul acestui canal!")

    def postare_stire(self, client, message):
        if not client.autentificat:
            client.send("Trebuie să fii autentificat pentru a posta o știre!")
            return
        if len(message.split(" ")) < 3:
            client.send("Comandă invalidă! Sintaxă: /postare nume_canal știre")
            return
        nume = message.split(" ")[1]
        stire = " ".join(message.split(" ")[2:])
        for cuvant in self.cuvinte_interzise:
            if cuvant in stire:
                client.send("Știrea conține cuvinte interzise!")
                return
        if nume not in [canal.nume for canal in self.canale_stiri]:
            client.send("Canalul nu există!")
            return
        for canal in self.canale_stiri:
            if canal.nume == nume and client.address == canal.owner:
                client.buffer += f"Știrea a fost postată cu succes în canalul {canal.nume}!"
                canal.notifica_stire_noua(stire)
                return
        client.send("Nu ești proprietarul acestui canal!")

    def autentificare(self, client, message):
        if client.autentificat:
            client.send("Deja autentificat!")
            return
        if len(message.split(" ")) < 3:
            client.send("Comandă invalidă! Sintaxă: /autentificare <username> <parolă>")
            return
        username = message.split(" ")[1]
        password = message.split(" ")[2]
        for user in self.useri:
            if user.username == username and user.password == password:
                client.autentificat = True
                client.send(f"Bun venit, {username}! Pentru o listă de comenzi disponibile, scrie: /ajutor")
                return
        client.send(
            "Credențiale greșite sau cont inexistent! Încearcă din nou sau înregistrează-te folosind \"/inregistrare <username> <parolă>\"!")

    def inregistrare(self, client, message):
        if client.autentificat:
            client.send("Deja autentificat!")
            return
        if len(message.split(" ")) < 3:
            client.send("Comandă invalidă! Sintaxă: /inregistrare <username> <parolă>")
            return
        username = message.split(" ")[1]
        password = message.split(" ")[2]
        if len(username) < 3 or len(password) < 3:
            client.send("Numele de utilizator și parola trebuie să aibă cel puțin 3 caractere")
            return
        for user in self.useri:
            if user.username == username:
                client.send("Utilizator existent. Loghează-te!")
                return
        client.send("Înregistrare reușită.\nAutentifică-te acum folosind \"/autentificare <user> <parolă>\"!")
        self.useri.append(User(username, password))

    def send_channels(self, client):
        if not client.autentificat:
            client.send(
                "Trebuie să fii autentificat pentru a vedea canalele disponibile! Scrie: /autentificare <username> <parolă>")
            return
        if len(self.canale_stiri) == 0:
            message = "Nu există canale de știri disponibile\nPentru a crea un canal, scrie: /creare nume_canal descriere_canal"
        else:
            message = "Canalele disponibile sunt:\n-----------------------------------------------\n"
            for canal in self.canale_stiri:
                message += f"{canal.nume}: {canal.descriere}\n"
            message += "-----------------------------------------------\n"
            message += "Pentru a te abona la un canal, scrie: /abonare nume_canal\nPentru a crea un canal, scrie: /creare nume_canal descriere_canal"
        client.send(message)

    def send_help(self, client):
        message = "-------------------Comenzile disponibile-------------------\n"
        for endpoint, description in self.endpoints.items():
            message += f"{endpoint}: {description}\n"
        message += "----------------------------------------------------------------"
        client.send(message)
