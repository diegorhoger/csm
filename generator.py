from dataclasses import dataclass
from typing import List, Tuple
import os
os.environ['DISABLE_TRITON'] = '1'
os.environ['NO_TORCH_COMPILE'] = '1'
import os
from openai import OpenAI
import torch
import torchaudio
from huggingface_hub import hf_hub_download
from models import Model
from moshi.models import loaders
from watermarking import CSM_1B_GH_WATERMARK, load_watermarker, watermark


@dataclass
class Segment:
    speaker: int
    text: str
    # (num_samples,), sample_rate = 24_000
    audio: torch.Tensor


class Generator:
    def __init__(
        self,
        model: Model,
    ):
        self._model = model
        self._model.setup_caches(1)

        # Initialize OpenAI client only if API key is available
        self.client = None
        if os.getenv("OPENAI_API_KEY"):
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        device = next(model.parameters()).device
        mimi_weight = hf_hub_download(loaders.DEFAULT_REPO, loaders.MIMI_NAME)
        mimi = loaders.get_mimi(mimi_weight, device=device)
        mimi.set_num_codebooks(32)
        self._audio_tokenizer = mimi

        self._watermarker = load_watermarker(device=device)

        self.sample_rate = mimi.sample_rate
        self.device = device

    def _get_gpt4_response(self, context: List[Segment], text: str, speaker: int) -> str:
        # Return the input text directly since we're not using GPT-4
        return text

    def _tokenize_audio(self, audio: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        assert audio.ndim == 1, "Audio must be single channel"

        frame_tokens = []
        frame_masks = []

        audio = audio.to(self.device)
        audio_tokens = self._audio_tokenizer.encode(audio.unsqueeze(0).unsqueeze(0))[0]
        eos_frame = torch.zeros(audio_tokens.size(0), 1).to(self.device)
        audio_tokens = torch.cat([audio_tokens, eos_frame], dim=1)

        audio_frame = torch.zeros(audio_tokens.size(1), 33).long().to(self.device)
        audio_frame_mask = torch.zeros(audio_tokens.size(1), 33).bool().to(self.device)
        audio_frame[:, :-1] = audio_tokens.transpose(0, 1)
        audio_frame_mask[:, :-1] = True

        frame_tokens.append(audio_frame)
        frame_masks.append(audio_frame_mask)

        return torch.cat(frame_tokens, dim=0), torch.cat(frame_masks, dim=0)

    def _tokenize_text(self, text: str, speaker: int) -> Tuple[torch.Tensor, torch.Tensor]:
        # Create initial frame for text with 33 dimensions (32 codebooks + 1 text token)
        frame_tokens = torch.zeros(1, 1, 33).long().to(self.device)
        frame_mask = torch.zeros(1, 1, 33).bool().to(self.device)
        frame_mask[..., -1] = True
        frame_tokens[..., -1] = speaker  # Set speaker ID
        return frame_tokens, frame_mask

    @torch.inference_mode()
    def generate(
        self,
        text: str,
        speaker: int,
        context: List[Segment],
        max_audio_length_ms: float = 90_000,
        temperature: float = 0.9,
        topk: int = 50,
    ) -> torch.Tensor:
        # Use the exact input text instead of generating a response
        print(f"Processing text: {text}")
        
        # Process the text for audio generation
        self._model.reset_caches()

        # Tokenize text
        frame_tokens, frame_mask = self._tokenize_text(text, speaker)
        
        # Generate audio frame by frame
        max_generation_len = int(max_audio_length_ms / 80)
        tokens = []
        
        for i in range(max_generation_len):
            input_pos = torch.arange(i + 1, device=self.device).unsqueeze(0)
            try:
                frame = self._model.generate_frame(
                    frame_tokens,
                    frame_mask,
                    input_pos,
                    temperature=temperature,
                    topk=topk,
                )
                if frame.size(1) != 32:  # Ensure frame has correct number of codebooks
                    print(f"Warning: Frame {i} has incorrect size {frame.size(1)}, expected 32")
                    continue
                    
                tokens.append(frame)
                
                # Update frame tokens with generated audio
                new_frame = torch.zeros(1, 1, 33).long().to(self.device)
                new_frame[..., :32] = frame
                new_frame[..., -1] = speaker
                frame_tokens = torch.cat([frame_tokens, new_frame], dim=1)
                frame_mask = torch.cat([frame_mask, torch.ones(1, 1, 33).bool().to(self.device)], dim=1)
            except Exception as e:
                print(f"Error generating frame {i}: {e}")
                break
            
        if not tokens:
            print("No audio frames were generated. Returning silence.")
            return torch.zeros(24000, device=self.device)
            
        # Concatenate all frames
        audio_tokens = torch.cat(tokens, dim=0)
        
        # Decode audio tokens to waveform
        try:
            audio = self._audio_tokenizer.decode(audio_tokens.unsqueeze(0)).squeeze(0).squeeze(0)
        except Exception as e:
            print(f"Error decoding audio: {e}")
            return torch.zeros(24000, device=self.device)

        # Apply watermark
        audio, wm_sample_rate = watermark(self._watermarker, audio, self.sample_rate, CSM_1B_GH_WATERMARK)
        audio = torchaudio.functional.resample(audio, orig_freq=wm_sample_rate, new_freq=self.sample_rate)

        return audio


def load_csm_1b(device: str = "cuda") -> Generator:
    model = Model.from_pretrained("sesame/csm-1b")
    model.to(device=device, dtype=torch.bfloat16)

    generator = Generator(model)
    return generator