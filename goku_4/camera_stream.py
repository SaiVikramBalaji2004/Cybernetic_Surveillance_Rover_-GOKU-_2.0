import cv2
import numpy as np
import logging
import time
import signal

logger = logging.getLogger('GOKU.Camera')

class CameraStream:
    def __init__(self):
        self.cap = None
        self.use_picamera = False
        self._picamera2 = None
        self._initialized = False

    def initialize(self):
        if self._initialized:
            return self.cap is not None

        try:
            from picamera2 import Picamera2
            self._picamera2 = Picamera2
            self.cap = Picamera2()
            config = self.cap.create_video_configuration(
                main={"size": (640, 480), "format": "RGB888"}
            )
            self.cap.configure(config)
            self.use_picamera = True
            logger.info("Picamera2 initialized (Pi 5 CSI)")
            self._initialized = True
            return True
        except Exception as e:
            logger.warning(f"Picamera2 failed: {e}")
            self.cap = None
            self.use_picamera = False

        try:
            for idx in [0]:
                self.cap = cv2.VideoCapture(idx)
                if self.cap.isOpened():
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.use_picamera = False
                    logger.info(f"OpenCV camera initialized on index {idx}")
                    self._initialized = True
                    return True
                self.cap.release()
                self.cap = None
        except Exception as e2:
            logger.warning(f"OpenCV camera failed: {e2}")

        logger.warning("No camera available, continuing without camera")
        self._initialized = True
        return False

    def start(self):
        if not self._initialized:
            return False
        if self.use_picamera and self.cap:
            try:
                self.cap.start()
                time.sleep(0.5)
                logger.info("Picamera2 started")
                return True
            except Exception as e:
                logger.error(f"Camera start error: {e}")
                return False
        elif self.cap:
            logger.info("OpenCV camera ready")
            return True
        logger.info("No camera to start")
        return False

    def stop(self):
        if self.use_picamera and self.cap:
            try:
                self.cap.stop()
            except Exception:
                pass
        elif self.cap:
            self.cap.release()
        self.cap = None
        logger.info("Camera stopped")

    def get_frame(self):
        if not self.cap:
            return None
        try:
            if self.use_picamera:
                return self.cap.capture_array()
            else:
                for _ in range(3):
                    ret, frame = self.cap.read()
                    if ret:
                        return frame
                    time.sleep(0.1)
                return None
        except Exception as e:
            if "Remote I/O" not in str(e) and "queue" not in str(e).lower():
                logger.error(f"Frame capture error: {e}")
            return None

    def capture_frame_as_bytes(self, max_retries=3):
        if not self.cap:
            return None
        for attempt in range(max_retries):
            frame = self.get_frame()
            if frame is None:
                logger.debug(f"Frame capture failed, retry {attempt+1}/{max_retries}")
                time.sleep(0.3)
                continue
            try:
                if self.use_picamera:
                    if frame.ndim == 3 and frame.shape[2] == 4:
                        img = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                    elif frame.ndim == 3 and frame.shape[2] == 3:
                        img = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    else:
                        img = frame
                else:
                    img = frame
                _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 85])
                jpeg_bytes = buffer.tobytes()
                logger.debug(f"Frame captured: {len(jpeg_bytes)} bytes")
                return jpeg_bytes
            except Exception as e:
                logger.error(f"Frame encode error: {e}")
                time.sleep(0.3)
        return None

camera_stream = CameraStream()
