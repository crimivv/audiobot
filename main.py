import os
import sys
from time import sleep
from pydub import AudioSegment
from pydub.effects import normalize, low_pass_filter, high_pass_filter, compress_dynamic_range

# --- Helper Functions ---
def print_progress_bar(percent, length=30):
    filled = int(length * percent // 100)
    bar = "█" * filled + "-" * (length - filled)
    sys.stdout.write(f"\rProgress: |{bar}| {percent:.0f}%")
    sys.stdout.flush()
    if percent >= 100:
        print()

def change_gain(audio, db, label="", step=None, total=None):
    audio = audio + db
    if label:
        if step and total:
            print(f"{label}: Step {step}/{total} applied gain {db} dB")
        else:
            print(f"{label}: applied gain {db} dB")
    return audio

def apply_amplify(audio, ratio, label=""):
    audio = audio.apply_gain(20 * (ratio / 100))
    if label:
        print(f"{label}: amplified by ratio {ratio}")
    return audio

def bass_and_treble(audio, bass_db=0, treble_db=0, gain_db=0, label=""):
    if bass_db != 0:
        audio = low_pass_filter(audio, 200) + bass_db
        if label:
            print(f"{label}: applied bass {bass_db} dB")
    if treble_db != 0:
        audio = high_pass_filter(audio, 3000) + treble_db
        if label:
            print(f"{label}: applied treble {treble_db} dB")
    if gain_db != 0 and label:
        print(f"{label}: applied gain {gain_db} dB")
    audio = audio + gain_db
    return audio

def apply_compressor(audio, threshold=-20, ratio=2, label=""):
    audio = compress_dynamic_range(audio, threshold=threshold, ratio=ratio)
    if label:
        print(f"{label}: compressor applied (threshold={threshold}, ratio={ratio})")
    return audio

def apply_distortion(audio, gain_db=20, label=""):
    audio = audio.apply_gain(gain_db).clip(-1.0, 1.0)
    if label:
        print(f"{label}: distortion applied (gain {gain_db} dB)")
    return audio

def duplicate(audio, times=1, label=""):
    combined = audio
    for i in range(times):
        combined = combined + audio
        if label:
            percent = int((i+1)/times*100)
            print(f"{label}: duplicated {i+1}/{times} ({percent}%)")
    return combined

# --- Macro 1 ---
def macro1(audio):
    print("Macro 1: Start")
    for i in range(5):
        audio = change_gain(audio, 1, label="Macro1 TrackGainInc", step=i+1, total=5)
    audio = apply_amplify(audio, 10, label="Macro1 Amplify")
    audio = bass_and_treble(audio, bass_db=-5, treble_db=0, gain_db=2, label="Macro1 Bass/Treble/Gain")
    audio = normalize(audio)
    print("Macro1: Normalize done")
    for i in range(2):
        audio = change_gain(audio, -1, label="Macro1 TrackGainDec", step=i+1, total=2)
    audio = bass_and_treble(audio, bass_db=0, treble_db=0, gain_db=3, label="Macro1 Bass/Treble/Gain 2")
    audio = normalize(audio)
    print("Macro 1: Complete")
    return audio

# --- Macro 2 ---
def macro2(audio):
    print("Macro 2: Start")
    audio = bass_and_treble(audio, bass_db=-5, treble_db=-5, gain_db=5, label="Macro2 Initial Bass/Treble/Gain")
    for i in range(5):
        audio = change_gain(audio, -1, label="Macro2 TrackGainDec", step=i+1, total=5)
    audio = apply_amplify(audio, 5, label="Macro2 Amplify")
    audio = bass_and_treble(audio, bass_db=5, treble_db=5, gain_db=0, label="Macro2 Bass/Treble/Gain 2")
    audio = normalize(audio)
    print("Macro2: Normalize done")
    audio = apply_compressor(audio, threshold=-60, ratio=1, label="Macro2 Compressor 1")
    audio = apply_compressor(audio, threshold=0, ratio=100, label="Macro2 Compressor 2")
    audio = apply_compressor(audio, threshold=-60, ratio=1, label="Macro2 Compressor 3")
    audio = apply_compressor(audio, threshold=-60, ratio=1, label="Macro2 Compressor 4")
    audio = apply_distortion(audio, gain_db=20, label="Macro2 Distortion")
    audio = duplicate(audio, times=5, label="Macro2 Duplicate")
    print("Macro 2: Complete")
    return audio

# --- Split Stereo / Delete Bottom / Duplicate Top ---
def split_delete_duplicate(audio):
    print("Split Stereo → Delete Bottom → Duplicate Top: Start")
    if audio.channels == 2:
        left = audio.split_to_mono()[0]
        print("Stereo split: kept top track (left channel)")
    else:
        left = audio
        print("Already mono: no split needed")
    duplicated = duplicate(left, times=1, label="Split/Delete/Duplicate")
    print("Split/Delete/Duplicate: Complete")
    return duplicated

# --- Export MP3 directly with progress bar ---
def export_mp3_with_progress(audio, filename):
    audio = audio.set_channels(1).set_frame_rate(44100)
    total_ms = len(audio)
    chunk_length = max(1, total_ms // 100)  # 1% chunks

    combined = AudioSegment.silent(duration=0)
    print("Exporting MP3 with progress:")
    for i in range(100):
        start = i * chunk_length
        end = start + chunk_length
        if end > total_ms:
            end = total_ms
        combined += audio[start:end]
        print_progress_bar(i+1)
        sleep(0.01)

    combined.export(filename, format="mp3", bitrate="192k", tags={})
    print("MP3 export complete")

# --- Main Processing ---
def process_all_audio():
    supported_formats = (".wav", ".mp3", ".flac", ".ogg", ".m4a")
    files = [f for f in os.listdir() if f.lower().endswith(supported_formats)]
    if not files:
        print("No audio files found!")
        return

    for file in files:
        print(f"\nProcessing file: {file}")
        audio = AudioSegment.from_file(file)

        # Step 1: Macro 1
        audio = macro1(audio)

        # Step 2: Split Stereo → Delete Bottom → Duplicate Top
        audio = split_delete_duplicate(audio)

        # Step 3: Macro 2
        audio = macro2(audio)

        # Step 4: Export MP3 directly with progress bar
        mp3_file = f"{os.path.splitext(file)[0]}_final.mp3"
        export_mp3_with_progress(audio, mp3_file)

        print(f"Finished processing {file}: {mp3_file}")

if __name__ == "__main__":
    process_all_audio()
    print("\nAll files processed successfully!")