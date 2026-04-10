import espnow
import json

class SERVER:
    def __init__(self, *, timeout :int = 5) -> None:
        self.esp = espnow.ESPNow()
        self.timeout = timeout

    def configure(self, *, timeout :int = 5) -> None:
        self.timeout = timeout

    def send_message(self, peer :str, data :str) -> bool:
        """
        Send a string

        Args:

            peer (str): client's mac address

            data (str): Data to be sent

        Returns:

            bool: Confirmation flag (`True` if data was received, `False` otherwise)
        """

        ack :bool = self.esp.send(peer, data)
        return ack

    def receive_message(self, recv_timeout :int = 5) -> list | None:
        """
        Receive a string

        Args:

            recv_timeout (int, optional): Reception timeout. Defaults to 5.

        Returns:

            list | None: `[<sender's mac address (str)>, <message (str)>]` | `None` if no message is received
        """

        received = self.esp.recv(recv_timeout)
        if received[0] is None:
            return
        return received

    def send_txt(self, peer :str, filename :str) -> bool:
        """
        Parse and send a `.txt` file as a `string`

        Args:

            peer (str): client's mac address

            filename (str): Filepath of the desired file to be sent with file name and extension

        Returns:

            sent (bool): Confirmation flag (`True` if data was received, `False` otherwise)
        """

        with open(filename, "r") as f:
            data :str = str(f.readlines())
        sent :bool = self.send_message(peer, data)
        return sent

    def send_json(self, peer :str, filename :str, *, indent :int = 4) -> bool:
        """
        Parse and send a `.json` file as a `string`

        Args:

            peer (str): client's mac address

            filename (str): Filepath of the desired file to be sent with file name and extension

            indent (int, optional): Desired indent of the resulting parsed `string` (for formatting purposes). Defaults to 4.

        Returns:

            sent (bool): Confirmation flag (`True` if data was received, `False` otherwise)
        """

        with open(filename, "r") as f:
            unparsed = json.load(f)
        parsed :str = json.dumps(unparsed, indent=indent)
        sent :bool = self.send_message(peer, parsed)
        return sent

    def receive_to_txt(self, target_file :str, mode :str = "a") -> bool:
        """
        Write received `string` into a `.txt` file.

        **Will not write or create file if no data is received**

        Args:

            target_file (str): Filepath of the destination file for the received data with file name and extension.

            mode (str, optional): Editing mode

                - `r` - Read only

                - `w` - Write only (truncates file before writing)

                - `x` - Create a new file and open it for writing (raises `FileExistsError` if file already exists)

                - `a` - Append to the end of the file (default)

                - `b` - Binary mode

                - `t` - Text mode

                - `+` - Update (read and write)

            Read `open()`_ for more information

        Returns:

            received (bool): Confirmation flag (`True` if data was received, `False` otherwise)

        .. _open(): https://docs.python.org/3/library/functions.html#open
        """

        if ".txt" not in target_file:
            raise SyntaxError("File format must be .txt")
        try:
            data :list | None = self.receive_message()
            if data is None:
                return False
            data_list :list[str] = str(data[-1]).split("\n")
            if data_list[-1] == "":
                data_list = data_list[:-1]
            with open(target_file, mode) as f:
                f.writelines(data_list)
            return True
        except SyntaxError:
            raise

    def receive_to_json(self, target_file :str, mode :str = "a") -> bool:
        """
        Write received `string` into a `.json` file.

        **Will not write or create file if no data is received**

        Args:

            target_file (str): Filepath of the destination file for the received data with file name and extension.

            mode (str, optional): Editing mode

                - `r` - Read only

                - `w` - Write only (truncates file before writing)

                - `x` - Create a new file and open it for writing (raises `FileExistsError` if file already exists)

                - `a` - Append to the end of the file (default)

                - `b` - Binary mode

                - `t` - Text mode

                - `+` - Update (read and write)

            Read `open()`_ for more information

        Returns:

            received (bool): Confirmation flag (`True` if data was received, `False` otherwise)

        .. _open(): https://docs.python.org/3/library/functions.html#open
        """

        if ".json" not in target_file:
            raise SyntaxError("File format must be .json")
        try:
            received :bool = False
            data :list | None = self.receive_message()
            if data is None:
                return received
            mac :str = str(data[0])
            message = json.loads(str(data[-1]))
            unparsed :dict = {"mac": mac, "message": message}
            with open(target_file, mode) as f:
                json.dump(unparsed, f)
            return not received
        except SyntaxError:
            raise

    def receive_to_dict(self) -> dict:
        """
        Unparses received `string` into a `dict` object

        Args:

            None:

        Returns:

            unparsed (dict): `dictionary` object containing unparsed equivalent of the received `.json`
        """

        data :list | None = self.receive_message()
        if data is None:
            return {}
        mac :str = str(data[0])
        message = json.loads(str(data[-1]))
        unparsed :dict = {"mac": mac, "message": message}
        return unparsed
