import MultiPyVu as mpv
import threading

class PPMS:
    """
    Class for controlling PPMS via MultiPyVu.

    Initialization parameters:
    host: String, IP address of the PPMS.
    port: Integer, port number of the PPMS. Default is 5000.

    Attributes:
    ._port: Integer, port number of the PPMS.
    ._host: String, IP address of the PPMS.
    ._lock: Threading lock for thread-safe access
    """
    type = "PPMS"

    def __init__(self, host, port=5000):
        self._port = port
        self._host = host
        self._lock = threading.RLock()  # 使用可重入锁防止死锁

        try:
            self.client = mpv.Client(self._host, self._port)
            self.client.open()
            print("PPMS connected")
            print("PPMS线程安全访问已启用 - 支持多线程并发数据读取")
        except Exception as e:
            print(f"Error: {e}")
            print("Test failed, PPMS is not connected.")
            raise ConnectionError(f"无法连接到PPMS {self._host}:{self._port} - {str(e)}")

    def reset(self, host, port):
        """
        Reset the connection to the PPMS.
        host: String, IP address of the PPMS.
        port: Integer, port number of the PPMS. Default is 5000.
        """
        with self._lock:
            self._port = port
            self._host = host

    def get_temperature_field(self):
        """
        Get the temperature and field from the PPMS.
        Returns:
        T: Float, temperature in Kelvin.
        sT: status of the temperature
        F: Float, field in Oe.
        sF: status of the field
        
        Thread-safe method using lock to prevent concurrent socket access.
        """
        with self._lock:
            try:
                T, sT = self.client.get_temperature()
                F, sF = self.client.get_field()
                return T, sT, F, sF
            except Exception as e:
                # 在锁内重新抛出异常，确保锁被正确释放
                raise e
    
    def close(self):
        with self._lock:
            self.client.close_client()
            print("PPMS closed")



