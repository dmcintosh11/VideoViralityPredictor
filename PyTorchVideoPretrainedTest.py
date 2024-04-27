#%%
import torch
from torch.utils.data import Dataset, DataLoader
import json
from torchvision.transforms import Compose, Lambda
from torchvision.transforms._transforms_video import (
    CenterCropVideo,
    NormalizeVideo,
)
from pytorchvideo.data.encoded_video import EncodedVideo
from pytorchvideo.transforms import (
    ApplyTransformToKey,
    ShortSideScale,
    UniformTemporalSubsample,
    UniformCropVideo
)
from typing import Dict
import pandas as pd

# Device on which to run the model
# Set to cuda to load on GPU
device = "cuda"

# Pick a pretrained model and load the pretrained weights
model_name = "slowfast_r50"
model = torch.hub.load("facebookresearch/pytorchvideo", model=model_name, pretrained=True)

# Set to eval mode and move to desired device
model = model.to(device)
model = model.eval()

print("Model is loaded")
print(model)
print()
print("Model attributes: ", dir(model))
#print("Model parameters: ", model.parameters)
print("Model Final Block: ", model.blocks[6])
print("Model Final Block attributes: ", dir(model.blocks[6]))
print("Model Final Block proj: ", model.blocks[6].proj)



#FOUBD HOW TO CHOP OFF THIS FINAL LAYER
head_block = model.blocks[6]

# Check the input features to the proj layer, which we need to preserve
in_features = head_block.proj.in_features

# Replace the proj layer with a new one that outputs a single value
head_block.proj = torch.nn.Linear(in_features, 1)

print("New model head: ", model.blocks[6].proj)



video_dir = "./TikTokVideos/"


video_csv = pd.read_csv("video_data.csv")

X_col = 'filename'
y_col = 'diggCount'

#Set up the video paths and target values
video_paths = video_csv[X_col].apply(lambda x: video_dir + x)
target = video_csv[y_col]
    
    
    
    
    
# ####################
# # SlowFast transform
# ####################

side_size = 256
mean = [0.45, 0.45, 0.45]
std = [0.225, 0.225, 0.225]
crop_size = 256
num_frames = 32
sampling_rate = 2
frames_per_second = 30
alpha = 4

class PackPathway(torch.nn.Module):
    """
    Transform for converting video frames as a list of tensors.
    """
    def __init__(self):
        super().__init__()

    def forward(self, frames: torch.Tensor):
        fast_pathway = frames
        # Perform temporal sampling from the fast pathway.
        slow_pathway = torch.index_select(
            frames,
            1,
            torch.linspace(
                0, frames.shape[1] - 1, frames.shape[1] // alpha
            ).long(),
        )
        frame_list = [slow_pathway, fast_pathway]
        return frame_list

transform =  ApplyTransformToKey(
    key="video",
    transform=Compose(
        [
            UniformTemporalSubsample(num_frames),
            Lambda(lambda x: x/255.0),
            NormalizeVideo(mean, std),
            ShortSideScale(
                size=side_size
            ),
            CenterCropVideo(crop_size),
            PackPathway()
        ]
    ),
)

# # The duration of the input clip is also specific to the model.
clip_duration = (num_frames * sampling_rate)/frames_per_second





# Custom dataset class
class VideoDataset(Dataset):
    def __init__(self, video_paths, targets, transform=None):
        self.video_paths = video_paths
        self.targets = targets
        self.transform = transform

    def __len__(self):
        return len(self.video_paths)

    def __getitem__(self, idx):
        video_path = self.video_paths[idx]
        video = EncodedVideo.from_path(video_path)
        video_data = video.get_clip(start_sec=0, end_sec=video.duration)
        if self.transform:
            video_data = self.transform(video_data)
        target = self.targets[idx]
        return video_data, target

print("VideoDataset class created")

# Create the dataset and data loader
dataset = VideoDataset(video_paths, target, transform)
data_loader = DataLoader(dataset, batch_size=8, shuffle=True)

print("DataLoader created")

# Loss function and optimizer
criterion = torch.nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)

# Training loop
print("Starting training loop...")
num_epochs = 10
for epoch in range(num_epochs):
    print(f"Epoch {epoch+1}\n-------------------------------")
    for batch_idx, (videos, targets) in enumerate(data_loader):
        print("Batch ", batch_idx)
        
        videos = [vid.to(device) for vid in videos]
        targets = targets.to(device).float()

        # Forward pass
        outputs = model(videos)
        loss = criterion(outputs.squeeze(), targets)

        # Backward pass and optimization
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # Print progress
        if (batch_idx + 1) % 10 == 0:
            print(f"Epoch [{epoch+1}/{num_epochs}], Batch [{batch_idx+1}/{len(data_loader)}], Loss: {loss.item():.4f}")

print("Training completed!")