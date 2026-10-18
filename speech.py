"""Bounded, cancellable Piper synthesis with Qt audio playback."""
from __future__ import annotations

import os
import queue
import shutil
import tempfile
import threading
import wave
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from reader_core import Sentence, Voice


class VoiceEngine:
    def __init__(self):
        self.voice = None
        self.path = None

    def load(self, path: Path):
        if self.path != path:
            from piper import PiperVoice
            self.voice = PiperVoice.load(str(path))
            self.path = path
        return self.voice

    def write(self, text, target, voice: Voice, speed=1.0, speaker=0, pause_after=0):
        from piper import SynthesisConfig
        model = self.load(voice.path)
        config = SynthesisConfig(length_scale=1.0 / speed, speaker_id=speaker)
        with wave.open(str(target), "wb") as stream:
            model.synthesize_wav(text, stream, syn_config=config)
            if pause_after:
                stream.writeframes(b"\0\0" * int(model.config.sample_rate*pause_after))


class Speech(QObject):
    sentence_started = Signal(int)
    status = Signal(str)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.output = QAudioOutput(self)
        self.output.setVolume(0.8)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.output)
        self.player.mediaStatusChanged.connect(self._media_status)
        self.player.errorOccurred.connect(self._audio_error)
        self.timer = QTimer(self)
        self.timer.setInterval(35)
        self.timer.timeout.connect(self._poll)
        self.timer.start()
        self.active = False
        self.paused = False
        self.waiting = False
        self.items = queue.Queue(maxsize=3)
        self.cancel = threading.Event()
        self.thread = None
        self.index = 0
        self.current_file = None
        self.folder = None
        # One inference thread at a time; a cancelled generation must finish before a new model load.
        self.engine = VoiceEngine()
        self.lock = threading.Lock()
        self.retired = []

    def start(self, parts: list[Sentence], voice: Voice, index=0, speed=1.0, speaker=0):
        self.stop()
        self.active, self.paused, self.waiting = True, False, True
        self.index = index
        folder = Path(tempfile.mkdtemp(prefix="piper-reader-"))
        self.folder = folder
        items = self.items = queue.Queue(maxsize=3)
        cancel = self.cancel = threading.Event()

        def put(item):
            while not cancel.is_set():
                try:
                    items.put(item, timeout=0.1)
                    return True
                except queue.Full:
                    pass
            return False

        def produce():
            try:
                with self.lock:
                    if cancel.is_set():
                        return
                    for i in range(index, len(parts)):
                        if cancel.is_set():
                            break
                        path = folder / f"{i}.wav"
                        self.engine.write(parts[i].spoken if parts[i].spoken is not None else parts[i].text, path, voice, speed, speaker, parts[i].pause_after)
                        if not put(("audio", i, path)):
                            break
                    if not cancel.is_set():
                        put(("end", 0, None))
            except Exception as error:
                put(("error", 0, str(error)))

        self.thread = threading.Thread(target=produce, daemon=True, name="Piper synthesis")
        self.thread.start()
        self.status.emit("Preparing speech…")

    def _poll(self):
        self._clean_retired()
        if not self.active or self.paused or not self.waiting:
            return
        try:
            kind, index, payload = self.items.get_nowait()
        except queue.Empty:
            return
        if kind == "end":
            self.stop()
            self.status.emit("Finished reading")
            self.finished.emit()
        elif kind == "error":
            self.stop()
            self.failed.emit(payload)
        else:
            self.waiting = False
            self.index = index
            self.current_file = payload
            self.player.setSource(QUrl.fromLocalFile(str(payload)))
            self.player.play()
            self.sentence_started.emit(index)
            self.status.emit("Reading")

    def _media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia and self.active:
            self.player.setSource(QUrl())
            if self.current_file:
                try:
                    self.current_file.unlink(missing_ok=True)
                except OSError:
                    pass  # Windows audio decoders may release the handle slightly later.
                self.current_file = None
            self.waiting = True

    def _audio_error(self, *args):
        if self.active:
            message = self.player.errorString()
            self.stop()
            self.failed.emit(f"Audio playback failed: {message}")

    def toggle_pause(self):
        if not self.active:
            return
        self.paused = not self.paused
        if self.paused:
            self.player.pause()
            self.status.emit("Paused")
        else:
            if not self.waiting:
                self.player.play()
            self.status.emit("Preparing speech…" if self.waiting else "Reading")

    def stop(self):
        self.active = False
        self.cancel.set()
        self.player.stop()
        self.player.setSource(QUrl())
        if self.folder:
            self.retired.append((self.thread, self.folder))
        self.folder = None
        self.current_file = None
        self.paused = False
        self.waiting = False
        self._clean_retired()

    def _clean_retired(self):
        pending = []
        for thread, folder in self.retired:
            if thread and thread.is_alive():
                pending.append((thread, folder))
            else:
                shutil.rmtree(folder, ignore_errors=True)
        self.retired = pending


def export_audio(parts, voice, target: Path, speed, speaker, progress, cancelled):
    """Stream chunks to a temporary WAV; never replace a destination on cancellation."""
    from piper import SynthesisConfig
    engine = VoiceEngine()
    model = engine.load(voice.path)
    fd, name = tempfile.mkstemp(dir=target.parent, suffix=".wav")
    os.close(fd)
    try:
        with wave.open(name, "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(model.config.sample_rate)
            for i, part in enumerate(parts):
                if cancelled():
                    return False
                config = SynthesisConfig(length_scale=1 / speed, speaker_id=speaker)
                for chunk in model.synthesize(part.spoken if part.spoken is not None else part.text, syn_config=config):
                    if cancelled():
                        return False
                    stream.writeframesraw(chunk.audio_int16_bytes)
                if part.pause_after:
                    stream.writeframesraw(b"\0\0"*int(model.config.sample_rate*part.pause_after))
                progress(i + 1, len(parts), f"Exporting sentence {i + 1} of {len(parts)}")
        if cancelled():
            return False
        os.replace(name, target)
        return True
    finally:
        Path(name).unlink(missing_ok=True)
