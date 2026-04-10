import espnow
import json

class CLIENT:
    def __init__(self) -> None:
        self.esp = espnow.ESPNow()
    
    def configure(self, timeout=5) -> None:
        self.timeout: int = timeout

    def connect(self, peer: str) -> None:
        self.peer: str = peer
        self.esp.active(True)
        self.esp.add_peer(self.peer)

    def send_message(self, data: str) -> bool:
        ack: bool = self.esp.send(self.peer, data)
        return ack
            
    def receive_message(self, recv_timeout :int= 5) -> list | None:
        received = self.esp.recv(recv_timeout)
        if received[0] == None: return
        return received
    
    def send_txt(self, filename: str) -> bool:
        with open(filename, 'r') as f:
            data: str = str(f.readlines())
        sent: bool = self.send_message(data)
        return sent
    
    def send_json(self, filename: str, *, indent: int=4) -> bool:
        with open(filename, 'r') as f:
            unparsed = json.load(f)
        parsed: str = json.dumps(unparsed, indent=indent)
        sent: bool = self.send_message(parsed)
        return sent
    
    def receive_to_txt(self, target_file: str, mode: str='a') -> bool:
        if ".txt" not in target_file: raise SyntaxError("File format must be .txt")
        try:
            data: list | None = self.receive_message()
            if data == None: return False
            data_list: list[str] = str(data[-1]).split("\n")
            if data_list[-1] == "": data_list = data_list[:-1]
            with open(target_file, mode) as f:
                f.writelines(data_list)
            return True
        except SyntaxError:
            raise
    
    def receive_to_json(self, target_file: str, mode: str='a') -> bool:
        if ".json" not in target_file: raise SyntaxError("File format must be .json")
        try:
            data: list | None = self.receive_message()
            if data == None: return False
            mac: str = str(data[0])
            message = json.loads(str(data[-1]))
            unparsed: dict = {
                "mac": mac,
                "message": message
            }
            with open(target_file, mode) as f:
                json.dump(unparsed, f)
            return True
        except SyntaxError:
            raise
    
    def receive_to_dict(self) -> dict:
        data: list | None = self.receive_message()
        if data == None: return {}
        mac: str = str(data[0])
        message = json.loads(str(data[-1]))
        unparsed: dict = {
            "mac": mac,
            "message": message
        }
        return unparsed