import espnow
import json

class SERVER:
    def __init__(self, *, timeout: int=5) -> None:
        self.esp = espnow.ESPNow()
        self.timeout = timeout
    
    def configure(self, *, timeout: int=5) -> None:
        self.timeout = timeout
    
    def send_message(self, peer: str, data: str) -> bool:
        ack: bool = self.esp.send(peer, data)
        return ack
    
    def receive_message(self, recv_timeout :int= 5) -> list | None:
        received = self.esp.recv(recv_timeout)
        if received[0] == None: return
        return received
    
    def send_txt(self, peer: str, filename: str) -> bool:
        with open(filename, 'r') as f:
            data: str = str(f.readlines())
        sent: bool = self.send_message(peer, data)
        return sent
    
    def send_json(self, peer: str, filename: str, *, indent: int=4) -> bool:
        with open(filename, 'r') as f:
            unparsed = json.load(f)
        parsed: str = json.dumps(unparsed, indent=indent)
        sent: bool = self.send_message(peer, parsed)
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