import irc.bot
import threading
import time

# Bot 1 configuration
server1 = "irc.oftc.net"
channel1 = "#debian-offtopic"
nickname1 = "debianoffportal"
password1 = "password1"

# Bot 2 configuration
server2 = "irc.libera.chat"
channel2 = "#debian-offtopic"
nickname2 = "debianoffportal"
password2 = "password2"

class IRCBot(irc.bot.SingleServerIRCBot):
    def __init__(self, server, channel, nickname, password, target_server, target_channel):
        server_info = irc.bot.ServerSpec(server, 6667, nickname)
        irc.bot.SingleServerIRCBot.__init__(self, [server_info], nickname, nickname)
        self.channel = channel
        self.nickname = nickname
        self.password = password
        self.target_server = target_server
        self.target_channel = target_channel
        self.connected = False

    def on_welcome(self, connection, event):
        # Send NickServ identify message after a 5 second delay
        if self.password:
            threading.Timer(5.0, self.identify, [connection]).start()

    def identify(self, connection):
        connection.privmsg("NickServ", f"IDENTIFY {self.nickname} {self.password}")
        # Wait for 5 seconds before joining the channel to ensure identification is processed
        threading.Timer(5.0, self.join_channel, [connection]).start()

    def join_channel(self, connection):
        connection.join(self.channel)
        self.connected = True

    def on_pubmsg(self, connection, event):
        nick = event.source.nick
        message = event.arguments[0]

        # Only forward the message if it's from the source channel
        if event.target == self.channel:
            self.pass_message(nick, message)

    def pass_message(self, nick, message):
        pass  # Override this method in subclasses

class MessagePasser(threading.Thread):
    def __init__(self, source_bot, target_bot):
        threading.Thread.__init__(self)
        self.source_bot = source_bot
        self.target_bot = target_bot

    def run(self):
        while True:
            nick, message = self.source_bot.get_message()
            if nick and message:
                self.target_bot.print_message(nick, message)

class BotWithMessageBuffer(IRCBot):
    def __init__(self, server, channel, nickname, password, target_server, target_channel):
        super().__init__(server, channel, nickname, password, target_server, target_channel)
        self.message_buffer = []

    def pass_message(self, nick, message):
        self.message_buffer.append((nick, message))

    def get_message(self):
        if self.message_buffer:
            return self.message_buffer.pop(0)
        return None, None

    def print_message(self, nick, message):
        if self.connected:
            self.connection.privmsg(self.target_channel, f"<{nick}> {message}")

def main():
    bot1 = BotWithMessageBuffer(server1, channel1, nickname1, password1, server2, channel2)
    bot2 = BotWithMessageBuffer(server2, channel2, nickname2, password2, server1, channel1)
    message_passer1 = MessagePasser(bot1, bot2)
    message_passer2 = MessagePasser(bot2, bot1)

    # Start bots and message passers
    bot1_thread = threading.Thread(target=bot1.start)
    bot2_thread = threading.Thread(target=bot2.start)
    message_passer1.start()
    message_passer2.start()

    bot1_thread.start()
    bot2_thread.start()

    # Wait for each bot to finish
    bot1_thread.join()
    bot2_thread.join()

if __name__ == "__main__":
    main()