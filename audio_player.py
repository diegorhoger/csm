import sounddevice as sd
import matplotlib.pyplot as plt
import numpy as np
import torch
import torchaudio

class AudioPlayer:
    def __init__(self, sample_rate=24000):
        self.sample_rate = sample_rate
        
    def play_and_plot(self, audio_tensor):
        # Convert tensor to numpy array if needed
        if isinstance(audio_tensor, torch.Tensor):
            audio = audio_tensor.cpu().numpy()
        else:
            audio = audio_tensor
            
        # Create time array for x-axis
        time = np.arange(len(audio)) / self.sample_rate
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Plot waveform
        ax1.plot(time, audio)
        ax1.set_title('Waveform')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Amplitude')
        ax1.grid(True)
        
        # Plot spectrogram
        ax2.specgram(audio, Fs=self.sample_rate, NFFT=1024)
        ax2.set_title('Spectrogram')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Frequency (Hz)')
        ax2.grid(True)
        
        # Adjust layout
        plt.tight_layout()
        
        # Play audio
        sd.play(audio, self.sample_rate)
        sd.wait()  # Wait until audio is finished playing
        
        # Show plot
        plt.show()
        
    def save_and_play(self, audio_tensor, filename="output.wav"):
        # Save audio to file
        if isinstance(audio_tensor, torch.Tensor):
            torchaudio.save(filename, audio_tensor.unsqueeze(0), self.sample_rate)
        else:
            # Convert numpy array to tensor if needed
            audio_tensor = torch.from_numpy(audio_tensor)
            torchaudio.save(filename, audio_tensor.unsqueeze(0), self.sample_rate)
            
        print(f"Audio saved to {filename}")
        
        # Play the saved file
        audio, sr = torchaudio.load(filename)
        if sr != self.sample_rate:
            audio = torchaudio.functional.resample(audio, orig_freq=sr, new_freq=self.sample_rate)
        
        self.play_and_plot(audio.squeeze().numpy()) 