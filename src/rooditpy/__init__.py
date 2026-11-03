import sqlite3
from neonize.client import NewClient
from neonize.events import ConnectedEv, MessageEv

class Client:
    def __init__(self) -> None:
        conn = sqlite3.connect("./data/karma.db")
        conn.execute("""
                          CREATE TABLE IF NOT EXISTS karma (
                              id TEXT PRIMARY KEY,
                              name TEXT NOT NULL UNIQUE,
                              points INTEGER NOT NULL
                          )
                          """)
        conn.commit()
        conn.close()
        
        self.prev_actions = {}
        
        self.client = NewClient("./data/session.db")

        @self.client.event(ConnectedEv)
        def on_connected(client: NewClient, _: ConnectedEv) -> None:
            print("Connected!")
        
        @self.client.event(MessageEv)
        def on_message(client: NewClient, message: MessageEv) -> None:
            if message.Info.Type == "reaction" and message.Info.MessageSource.Sender.User != message.Message.reactionMessage.key.participant:
                conn = sqlite3.connect("./data/karma.db")
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                                    SELECT EXISTS (
                                        SELECT 1 FROM karma
                                        WHERE id = ?
                                    )
                                    """,
                                    (message.Message.reactionMessage.key.participant,))
                
                # User is in db
                if cursor.fetchone():
                    match message.Message.reactionMessage.text.strip():
                        case "⬆" | "⬆️":
                            conn.execute("""
                                            UPDATE karma
                                            SET points = points + 1
                                            WHERE id = ?
                                            """,
                                            (message.Message.reactionMessage.key.participant,))
                        case "⬇" | "⬇️":
                            conn.execute("""
                                            UPDATE karma
                                            SET points = points - 1
                                            WHERE id = ?
                                            """,
                                            (message.Message.reactionMessage.key.participant,))
                        case "":
                            if self.prev_actions.get(message.Info.MessageSource.Sender.User) != None:
                                if self.prev_actions[message.Info.MessageSource.Sender.User] == "⬆" or self.prev_actions[message.Info.MessageSource.Sender.User] == "⬆️":
                                    conn.execute("""
                                            UPDATE karma
                                            SET points = points - 1
                                            WHERE id = ?
                                            """,
                                            (message.Message.reactionMessage.key.participant,))
                                elif self.prev_actions[message.Info.MessageSource.Sender.User] == "⬇" or self.prev_actions[message.Info.MessageSource.Sender.User] == "⬇️":
                                    conn.execute("""
                                            UPDATE karma
                                            SET points = points + 1
                                            WHERE id = ?
                                            """,
                                            (message.Message.reactionMessage.key.participant,))
                    
                    self.prev_actions[message.Info.MessageSource.Sender.User] = message.Message.reactionMessage.text
                else:
                    print(f"New user detected: {message.Message.reactionMessage.key.participant}")
                
                conn.commit()
                conn.close()
                
            elif message.Info.Type == "text":
                text = message.Message.conversation or message.Message.extendedTextMessage.text
                
                if text == "!karma":
                        conn = sqlite3.connect("./data/karma.db")
                        conn.row_factory = sqlite3.Row
                        
                        cursor = conn.execute("SELECT * FROM karma ORDER BY points DESC")
                        
                        final_str = ""
                        total_points = 0
                        total_karma = 0
                        for person in cursor.fetchall():
                            final_str += f"{person["name"]} has {person["points"]} karma,\n"
                            total_karma += person["points"]
                            total_points += abs(person["points"])
                        final_str = final_str.strip().removesuffix(",")
                        final_str += f"\n\nThere is a total karma of {total_karma} out of a total of {total_points} votes."
                            
                        client.reply_message(final_str, message)
                
                if message.Info.MessageSource.IsFromMe:
                    if text == "!reset":
                        conn = sqlite3.connect("./data/karma.db")
                        conn.execute("UPDATE karma SET points = 0")
                        conn.commit()
                        conn.close()
                        
                        client.reply_message("Reset karma.", message)
                    elif "!setkarma" in text:
                        data = text.split(" ")
                        try:
                            target = text.removeprefix(f"{data[0]} {data[1]} ") # type: ignore
                            conn = sqlite3.connect("./data/karma.db")
                            conn.execute("""
                                        UPDATE karma
                                        SET points = ?
                                        WHERE name = ?
                                        """,
                                        (data[1], target,))
                            conn.commit()
                            conn.close()
                            
                            client.reply_message(f"Set {target} to {data[1]} points.", message)
                        except:
                            client.reply_message("Invalid command", message)
    
    def start(self):
        self.client.connect()
    
    def stop(self):
        self.client.disconnect()
    
def main():
    client = Client()
    try:
        client.start()
    finally:
        client.stop()