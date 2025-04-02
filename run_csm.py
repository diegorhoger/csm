import os
os.environ["DISABLE_TRITON"] = "1"
os.environ["NO_TORCH_COMPILE"] = "1"
import torch
import torchaudio
from generator import load_csm_1b, Segment
from audio_player import AudioPlayer

def main():
    # Select the best available device, skipping MPS due to float64 limitations
    if torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"
    print(f"Using device: {device}")

    # Load model
    generator = load_csm_1b(device)
    
    # Initialize audio player
    player = AudioPlayer(sample_rate=generator.sample_rate)

    # Generate conversation with Marcus Aurelius quote
    conversation = [
        {
            "text": "Let me share with you one of my favorite quotes from Marcus Aurelius's Meditations.",
            "speaker_id": 0
        },
        {
            "text": "Yes, please do! I'd love to hear it.",
            "speaker_id": 1
        },
        {
            "text": "Very well. Here it is: 'The happiness of your life depends upon the quality of your thoughts: therefore, guard accordingly, and take care that you entertain no notions unsuitable to virtue and reasonable nature.'",
            "speaker_id": 0
        },
        {
            "text": "That's profound! Could you explain what it means to you?",
            "speaker_id": 1
        },
        {
            "text": "Of course. Marcus Aurelius is teaching us that our thoughts shape our reality. By maintaining positive, virtuous thoughts and aligning them with reason and nature, we create the foundation for a fulfilling life.",
            "speaker_id": 0
        }
    ]

    # Generate each utterance
    generated_segments = []

    for utterance in conversation:
        print(f"Generating: {utterance['text']}")
        audio_tensor = generator.generate(
            text=utterance['text'],
            speaker=utterance['speaker_id'],
            context=generated_segments,
            max_audio_length_ms=30_000,  # Increased max audio length for longer phrases
        )
        generated_segments.append(Segment(text=utterance['text'], speaker=utterance['speaker_id'], audio=audio_tensor))
        
        # Play and visualize each segment as it's generated
        print(f"Playing segment from speaker {utterance['speaker_id']}:")
        player.play_and_plot(audio_tensor)

    # Concatenate all generations
    all_audio = torch.cat([seg.audio for seg in generated_segments], dim=0)
    
    # Save the full conversation
    player.save_and_play(all_audio, "full_conversation.wav")
    print("Successfully generated and saved full_conversation.wav")

if __name__ == "__main__":
    main() 