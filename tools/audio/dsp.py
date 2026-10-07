"""Shared audio helpers: WAV I/O, BS.1770 loudness and true-peak estimates."""

import wave

import numpy as np
from scipy import signal

SR = 44100


def read_wav(path: str) -> np.ndarray:
    """-> float array of shape (n, channels) in [-1, 1]"""
    with wave.open(path, "rb") as w:
        ch, width, sr = w.getnchannels(), w.getsampwidth(), w.getframerate()
        raw = w.readframes(w.getnframes())
    assert sr == SR, f"{path}: expected {SR} Hz, got {sr}"
    if width == 2:
        data = np.frombuffer(raw, "<i2").astype(np.float64) / 32768.0
    elif width == 4:
        data = np.frombuffer(raw, "<i4").astype(np.float64) / 2147483648.0
    else:
        raise ValueError(f"{path}: unsupported sample width {width}")
    return data.reshape(-1, ch)


def write_wav(path: str, x: np.ndarray) -> None:
    if x.ndim == 1:
        x = x[:, None]
    pcm = np.clip(np.round(x * 32767.0), -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def _k_weight(x: np.ndarray) -> np.ndarray:
    # ITU-R BS.1770-4 pre-filter + RLB high-pass, coefficients re-derived for SR
    f0, g, q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    k = np.tan(np.pi * f0 / SR)
    vh = 10 ** (g / 20)
    vb = vh ** 0.4996667741545416
    a0 = 1 + k / q + k * k
    b1 = [(vh + vb * k / q + k * k) / a0, 2 * (k * k - vh) / a0, (vh - vb * k / q + k * k) / a0]
    a1 = [1, 2 * (k * k - 1) / a0, (1 - k / q + k * k) / a0]
    f0, q = 38.13547087602444, 0.5003270373238773
    k = np.tan(np.pi * f0 / SR)
    a0 = 1 + k / q + k * k
    b2 = [1, -2, 1]
    a2 = [1, 2 * (k * k - 1) / a0, (1 - k / q + k * k) / a0]
    return signal.lfilter(b2, a2, signal.lfilter(b1, a1, x, axis=0), axis=0)


def lufs(x: np.ndarray) -> float:
    """Integrated loudness (gated), BS.1770."""
    if x.ndim == 1:
        x = x[:, None]
    y = _k_weight(x)
    block, hop = int(0.4 * SR), int(0.1 * SR)
    if len(y) < block:
        y = np.pad(y, ((0, block - len(y)), (0, 0)))
    powers = np.array([
        np.sum(np.mean(y[i:i + block] ** 2, axis=0))
        for i in range(0, len(y) - block + 1, hop)
    ])
    loud = -0.691 + 10 * np.log10(powers + 1e-20)
    gated = powers[loud > -70]
    if len(gated) == 0:
        return -70.0
    rel = -0.691 + 10 * np.log10(np.mean(gated)) - 10
    gated = powers[(loud > -70) & (loud > rel)]
    return float(-0.691 + 10 * np.log10(np.mean(gated)))


def true_peak_db(x: np.ndarray) -> float:
    up = signal.resample_poly(x, 4, 1, axis=0)
    return float(20 * np.log10(np.max(np.abs(up)) + 1e-12))


def db(gain_db: float) -> float:
    return 10 ** (gain_db / 20)
