import imagehash


'''
uses difference hashing to figure out it we pass the image to ai.py or not. This way we
can compare the "fingerprints" of the images even when its really small changes. 

we can use either percentage or raw distance in figuring out if we should pass it or not, via the if else statement we just 
need to change the parameters.

'''


class FrameGate:
    def __init__(self, pct_threshold=0.10, max_hamming=None, hash_size=8):
        # If max_hamming is set, use raw Hamming distance;
        # otherwise forward when (distance / hash_bits) > pct_threshold.
        if max_hamming is not None:
            self._by_hamming = True
            self._max_hamming = max_hamming
        else:
            self._by_hamming = False
            self._pct_threshold = pct_threshold
        self._hash_size = hash_size
        self._last = None

    def should_forward(self, image):
        h = imagehash.dhash(image, hash_size=self._hash_size)
        if self._last is None:
            self._last = h
            return True

        distance = h - self._last
        self._last = h

        if self._by_hamming:
            return distance > self._max_hamming

        max_bits = h.hash.size
        if max_bits == 0:
            return True
        return (distance / max_bits) > self._pct_threshold

    def reset(self):
        self._last = None
