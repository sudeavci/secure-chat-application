import threading
from SocketHandler import SocketHandler
from Actions import Actions  # ensure we can reference Actions for enums if needed

PREFIX = '/'

class HandleThreads:
    def __init__(self, display_chat=None, button_action=None):
        self.display_chat = display_chat
        self.button_action = button_action

    def start_receiver(self):
        threading.Thread(target=self._receive, daemon=True).start()

    def start_sender(self, msg):
        threading.Thread(target=self._send, args=(msg,), daemon=True).start()

    def _receive(self):
        """
        Sunucudan gelen TCP mesajlarını dinler.
        /users ve SERVER: Connected users formatlarını yakalar.
        Ayrıca, sunucu tarafından yeni bir kullanıcının katıldığı veya
        ayrıldığı bildirimi geldiğinde otomatik /users isteği atar.
        """
        while getattr(self.display_chat.user, "connected", False):
            try:
                message = SocketHandler.get_msg(self.display_chat.user.tcp_socket)
                if message is None:
                    continue

                # 1) /users CSV yanıtı
                if message.startswith("/users "):
                    users_csv = message[len("/users "):].strip()
                    self.display_chat.update_user_list(users_csv)
                    continue

                # 2) SERVER: Connected users: CSV yanıtı
                if message.startswith("SERVER: Connected users:"):
                    users_csv = message.split("Connected users:")[1].strip()
                    self.display_chat.update_user_list(users_csv)
                    continue

                # 3) Sunucudan "X katıldı" veya "X ayrıldı" gibi bildirimi yakalayalım
                #    (Connected users dışındaki SERVER: bildirimleri)
                if message.startswith("SERVER:"):
                    self.display_chat.update_chat_display(message)
                    # Güncel kullanıcı listesini iste
                    self._send(PREFIX + "users")
                    continue

                # 4) True/False komutları
                if message in ("True", "False"):
                    self.display_chat.user.get_msg(message)
                else:
                    # 5) Normal sohbet mesajı
                    self.display_chat.update_chat_display(message)

            except Exception as exc:
                print(f"Receive thread error: {exc}")
                if self.button_action:
                    self.button_action.handle_disconnect()
                break

        try:
            self.display_chat.window.destroy()
        except:
            pass

    def _send(self, msg):
        """
        Mesaj gönderimi: komutsa action_received,
        değilse normal sohbete.
        """
        try:
            self.display_chat.text_cons.config(state="disabled")
        except:
            pass

        if msg.startswith(PREFIX):
            # Komut olarak TCP üzerinden sunucuya ilet
            self.display_chat.user.action_received(msg)
        else:
            # Metin mesajı: önce enum (MESSAGE_ALL), sonra payload
            out = f"{self.display_chat.name}: {msg}"
            # 1) Sunucuya enum gönder
            self.display_chat.user.send_msg_to_all()
            # 2) Sunucuya asıl metni gönder
            SocketHandler.send_msg(out, self.display_chat.user.tcp_socket)
