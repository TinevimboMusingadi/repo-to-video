"""Procedural ambient music generator for developer explainer videos."""

from pathlib import Path
import numpy as np
import soundfile as sf
from scipy import signal


class ProceduralMusicGenerator:
    """Generates royalty-free ambient synth music tailored to video duration."""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate

    def generate_ambient_track(self, duration_sec: float, output_path: Path) -> Path:
        """
        Synthesizes a lush, warm ambient synth pad progression.
        Duration will match or slightly exceed duration_sec.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        sr = self.sample_rate
        total_samples = int(sr * duration_sec)
        t_total = np.linspace(0, duration_sec, total_samples, endpoint=False)

        # Chord progression in Hz:
        # Chord 1: Dm9 (D3, F3, A3, C4, E4)
        # Chord 2: BbMaj7 (Bb2, D3, F3, A3)
        # Chord 3: Gm9 (G2, Bb2, D3, F3, A3)
        # Chord 4: Asus4 / Am7 (A2, D3, E3, G3, C4)
        chords = [
            [146.83, 174.61, 220.00, 261.63, 329.63],
            [116.54, 146.83, 174.61, 220.00],
            [98.00, 116.54, 146.83, 174.61, 220.00],
            [110.00, 146.83, 164.81, 196.00, 261.63]
        ]

        chord_duration = 5.0  # seconds per chord
        num_repeats = int(np.ceil(duration_sec / (len(chords) * chord_duration))) + 1
        
        full_audio = np.zeros(total_samples, dtype=np.float32)

        chord_idx = 0
        current_time = 0.0

        while current_time < duration_sec:
            chord_notes = chords[chord_idx % len(chords)]
            dur = min(chord_duration, duration_sec - current_time + 1.0)
            n_samples = int(dur * sr)
            t_chord = np.linspace(0, dur, n_samples, endpoint=False)

            chord_signal = np.zeros(n_samples, dtype=np.float32)

            # Generate warm detuned pad
            for freq in chord_notes:
                for detune in [-0.4, 0.0, 0.4]:
                    phase = np.random.uniform(0, 2 * np.pi)
                    chord_signal += (0.04 * np.sin(2 * np.pi * (freq + detune) * t_chord + phase))

            # Add gentle 16th-note bell arpeggio on top
            arp_step = 0.25  # 120 bpm 1/8th notes
            for step_i in range(int(dur / arp_step)):
                step_start = int(step_i * arp_step * sr)
                note_freq = chord_notes[step_i % len(chord_notes)] * 2.0  # octave up
                decay_len = min(int(0.35 * sr), n_samples - step_start)
                if decay_len > 0:
                    t_env = np.linspace(0, decay_len / sr, decay_len, endpoint=False)
                    env = np.exp(-12.0 * t_env)
                    bell = 0.02 * np.sin(2 * np.pi * note_freq * t_env) * env
                    chord_signal[step_start:step_start + decay_len] += bell

            # Apply smooth ADSR envelope to chord (crossfade)
            attack_len = int(0.8 * sr)
            release_len = int(0.8 * sr)
            envelope = np.ones(n_samples, dtype=np.float32)
            if n_samples > attack_len:
                envelope[:attack_len] = np.linspace(0, 1, attack_len)
            if n_samples > release_len:
                envelope[-release_len:] = np.linspace(1, 0, release_len)
            chord_signal *= envelope

            # Blend into full audio buffer
            start_sample = int(current_time * sr)
            end_sample = min(start_sample + n_samples, total_samples)
            slice_len = end_sample - start_sample
            if slice_len > 0:
                full_audio[start_sample:end_sample] += chord_signal[:slice_len]

            current_time += chord_duration - 0.5  # 0.5s overlap crossfade
            chord_idx += 1

        # Smooth lowpass filter (warm analog feel)
        try:
            sos = signal.butter(4, 1100, "low", fs=sr, output="sos")
            filtered = signal.sosfilt(sos, full_audio)
        except Exception:
            filtered = full_audio

        # Normalize to -6 dB headroom
        peak = np.max(np.abs(filtered)) + 1e-6
        normalized = (filtered / peak) * 0.5

        sf.write(str(output_path), normalized, sr)
        return output_path
