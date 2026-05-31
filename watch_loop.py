import threading
import time


class WatchLoop:
    """
    Periodic capture + dedup gate. Runs in a daemon thread.

    capture_fn() -> PIL.Image
    should_forward_fn(pil_image) -> bool  (False = duplicate / skip)
    on_forward(pil_image) -> None — e.g. queue for AI / store / log.
    """

    def __init__(self, capture_fn, should_forward_fn, on_forward, interval_ms=500):
        self.capture_fn = capture_fn
        self.should_forward_fn = should_forward_fn
        self.on_forward = on_forward
        self.interval_ms = interval_ms

        self._running = False
        self._thread = None

        self.metrics = {
            "frames_seen": 0,
            "frames_skipped": 0,
            "frames_forwarded": 0,
            "last_error": None,
        }

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _run(self):
        while self._running:
            t0 = time.perf_counter()
            try:
                frame = self.capture_fn()
                self.metrics["frames_seen"] += 1

                if not self.should_forward_fn(frame):
                    self.metrics["frames_skipped"] += 1
                else:
                    self.metrics["frames_forwarded"] += 1
                    self.on_forward(frame)
            except Exception as e:
                self.metrics["last_error"] = repr(e)

            elapsed_ms = (time.perf_counter() - t0) * 1000
            sleep_ms = max(0, self.interval_ms - elapsed_ms)
            time.sleep(sleep_ms / 1000.0)


if __name__ == "__main__":
    from dedup import FrameGate
    from screen import screen_capture_image

    gate = FrameGate(max_hamming=6)

    def forward(img):
        print("forward:", img.size)

    loop = WatchLoop(
        capture_fn=lambda: screen_capture_image(1),
        should_forward_fn=gate.should_forward,
        on_forward=forward,
        interval_ms=500,
    )
    loop.start()
    try:
        input("Capturing… Enter to stop.\n")
    finally:
        loop.stop()
        print("metrics:", loop.metrics)
