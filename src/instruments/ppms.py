import MultiPyVu as mpv

class PPMS:
    """
    Class for controlling PPMS via MultiPyVu.

    Initialization parameters:
    host: String, IP address of the PPMS.
    port: Integer, port number of the PPMS. Default is 5000.

    Attributes:
    ._port: Integer, port number of the PPMS.
    ._host: String, IP address of the PPMS.
    """
    type = "PPMS"

    def __init__(self, host, port=5000):
        self._port = port
        self._host = host

        self.test()

    def reset(self, host, port):
        """
        Reset the connection to the PPMS.
        host: String, IP address of the PPMS.
        port: Integer, port number of the PPMS. Default is 5000.
        """
        self._port = port
        self._host = host

    def test(self):
        """
        Test the connection to the PPMS.
        Raises ConnectionError if connection fails.
        """
        print(f"Testing connection to PPMS at {self._host}:{self._port}...")
        try:
            with mpv.Client(self._host, self._port) as client:
                print(client.get_temperature())
                print(client.get_field())
            print("Test successful, PPMS is connected.")
        except Exception as e:
            print(f"Error: {e}")
            print("Test failed, PPMS is not connected.")
            # 抛出ConnectionError以便上层处理
            raise ConnectionError(f"无法连接到PPMS {self._host}:{self._port} - {str(e)}")

    def get_temperature_field(self):
        """
        Get the temperature and field from the PPMS.
        Returns:
        T: Float, temperature in Kelvin.
        sT: status of the temperature
        F: Float, field in Oe.
        sF: status of the field
        """
        with mpv.Client(self._host, self._port) as client:
            T, sT = client.get_temperature()
            F, sF = client.get_field()

        return T, sT, F, sF
    
    def close(self):
        pass



