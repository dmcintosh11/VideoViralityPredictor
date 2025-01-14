import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from torchvision.models.video import r2plus1d_18, R2Plus1D_18_Weights
from torchvision.transforms import Compose, Lambda, Normalize
import torchvision.transforms.functional as TF
from torchvision.transforms.functional import InterpolationMode
import os
import random
from torchvision.io import read_video
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_curve, auc, precision_recall_curve, confusion_matrix

class VideoDataset(torch.utils.data.Dataset):
    """
    Custom Dataset class for loading video data and associated labels.
    """
    def __init__(self, dataframe, variable, transform=None, clip_length=500):
        self.video_paths = ['./TikTokVideos/' + filename for filename in dataframe['filename']]
        self.labels = torch.tensor(dataframe[variable].tolist(), dtype=torch.float32)
        self.transform = transform
        self.clip_length = clip_length

    def __len__(self):
        return len(self.video_paths)

    def __getitem__(self, idx):
        video_path = self.video_paths[idx]
        label = self.labels[idx]

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        vid, _, _ = read_video(video_path, pts_unit='sec')
        vid = vid.permute(0, 3, 1, 2)

        if vid.size(0) >= self.clip_length:
            start_index = random.randint(0, vid.size(0) - self.clip_length)
            vid = vid[start_index:start_index + self.clip_length]
        else:
            pad_size = self.clip_length - vid.size(0)
            pad = vid[-1].unsqueeze(0).repeat(pad_size, 1, 1, 1)
            vid = torch.cat((vid, pad), dim=0)

        vid = vid.float() / 255.0

        if self.transform:
            vid = self.transform(vid)

        vid = vid.permute(1, 0, 2, 3)
        return vid, label, video_path

class BaseEvaluator:
    """
    Base evaluator class for loading the model, preparing data, and making predictions.
    """
    def __init__(self, model_path, dataframe_path, variable, batch_size=4):
        self.model = self.load_model(model_path)
        self.dataframe_path = dataframe_path
        self.batch_size = batch_size
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        self.test_loader = self.prepare_data(variable)
        self.model.eval()

    def load_model(self, model_path):
        """
        Load the pre-trained model and modify the final fully connected layer.
        """
        weights = R2Plus1D_18_Weights.KINETICS400_V1
        model = r2plus1d_18(weights=weights)
        model.fc = nn.Sequential(
            nn.Linear(model.fc.in_features, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )
        model.load_state_dict(torch.load(model_path))
        return model

    def prepare_data(self, variable):
        """
        Prepare the test data loader.
        """
        df = pd.read_csv('data_with_virality_scores.csv')

        # Split the dataset into training, validation, and test sets
        train_df, temp_df = train_test_split(df, test_size=0.3, random_state=42)
        val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42)

        transform = Compose([
            Lambda(lambda x: TF.resize(x, [128, 171], InterpolationMode.BILINEAR)),
            Lambda(lambda x: TF.center_crop(x, [112, 112])),
            Lambda(lambda x: x.float() / 255.0),
            Normalize(mean=[0.43216, 0.394666, 0.37645], std=[0.22803, 0.22145, 0.216989])
        ])
        test_dataset = VideoDataset(test_df, transform=transform, variable=variable)
        test_loader = DataLoader(test_dataset, batch_size=self.batch_size, shuffle=False, num_workers=4)
        return test_loader

    def predict(self):
        """
        Generate predictions using the model.
        """
        actuals, predictions, video_paths = [], [], []
        with torch.no_grad():
            for inputs, labels, paths in self.test_loader:
                inputs, labels = inputs.to(self.device), labels.to(self.device)
                outputs = self.model(inputs)
                predicted = outputs.squeeze(1)
                actuals.extend(labels.cpu().numpy())
                predictions.extend(predicted.cpu().numpy())
                video_paths.extend(paths)
        return np.array(actuals), np.array(predictions), video_paths

class ClassificationEvaluator(BaseEvaluator):
    """
    Evaluator class for classification tasks.
    """
    def evaluate(self):
        """
        Evaluate the classification model using various metrics and plot results.
        """
        actuals, predicted_probs, video_paths = self.predict()
        predicted_labels = (predicted_probs > 0.5).astype(int)
        accuracy = accuracy_score(actuals, predicted_labels)
        precision = precision_score(actuals, predicted_labels)
        recall = recall_score(actuals, predicted_labels)
        f1 = f1_score(actuals, predicted_labels)
        roc_auc = roc_auc_score(actuals, predicted_probs)

        print(f"Accuracy: {accuracy}, Precision: {precision}, Recall: {recall}, F1 Score: {f1}, ROC-AUC: {roc_auc}")

        # ROC Curve
        fpr, tpr, _ = roc_curve(actuals, predicted_probs)
        roc_auc_value = auc(fpr, tpr)
        plt.figure(figsize=(6, 4))
        plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc_value:.2f})')
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver Operating Characteristic')
        plt.legend(loc="lower right")
        plt.savefig('Graphics/ROC_Curve.png')
        plt.close()

        # Confusion Matrix
        cm = confusion_matrix(actuals, predicted_labels)
        plt.figure(figsize=(6, 4))
        sns.heatmap(cm, annot=True, fmt="d", cmap='Blues', xticklabels=['Non-Viral', 'Viral'], yticklabels=['Non-Viral', 'Viral'])
        plt.xlabel('Predicted Label')
        plt.ylabel('True Label')
        plt.title('Confusion Matrix')
        plt.savefig('Graphics/Confusion_Matrix.png')
        plt.close()

        # Precision-Recall Curve
        precision, recall, thresholds = precision_recall_curve(actuals, predicted_probs)
        plt.figure(figsize=(6, 4))
        plt.plot(recall, precision, marker='.', label='Precision-Recall curve')
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title('Precision-Recall Curve')
        plt.legend()
        plt.savefig('Graphics/Precision_Recall_Curve.png')
        plt.close()

        # F1 Score by Threshold
        f1_scores = 2 * (precision * recall) / (precision + recall + 1e-12)
        plt.figure(figsize=(6, 4))
        plt.plot(thresholds, f1_scores[:-1], label='F1 Score')
        plt.xlabel('Threshold')
        plt.ylabel('F1 Score')
        plt.title('F1 Score by Threshold')
        plt.legend()
        plt.savefig('Graphics/F1_Score_by_Threshold.png')
        plt.close()

        return accuracy, precision, recall, f1, roc_auc

class RegressionModelEvaluator(BaseEvaluator):
    """
    Evaluator class for regression tasks.
    """
    def predict(self):
        """
        Generate predictions for regression tasks.
        """
        actuals, predictions, video_paths = [], [], []
        with torch.no_grad():
            for inputs, labels, paths in self.test_loader:
                inputs, labels = inputs.to(self.device), labels.to(self.device)
                outputs = self.model(inputs)
                predicted = outputs.squeeze(1)
                actuals.extend(labels.cpu().numpy())
                predictions.extend(predicted.cpu().numpy())
                video_paths.extend(paths)
        return np.array(actuals), np.array(predictions), video_paths

    def evaluate(self):
        """
        Evaluate the regression model and report metrics.
        """
        self.actuals, self.predictions, self.video_paths = self.predict()
        mse = np.mean((self.actuals - self.predictions) ** 2)
        rmse = np.sqrt(mse)
        mae = F.l1_loss(torch.tensor(self.predictions), torch.tensor(self.actuals), reduction='mean').item()

        sorted_indices = np.argsort(np.abs(self.actuals - self.predictions))
        print("Best 3 Videos (smallest prediction error):")
        for i in sorted_indices[:3]:
            print(f'Video Path: {self.video_paths[i]}, Actual: {self.actuals[i]}, Predicted: {self.predictions[i]}')
        print("Worst 3 Videos (largest prediction error):")
        for i in sorted_indices[-3:]:
            print(f'Video Path: {self.video_paths[i]}, Actual: {self.actuals[i]}, Predicted: {self.predictions[i]}')


        return mse, rmse, mae

# Assuming model paths and data paths are set correctly
classification_evaluator = ClassificationEvaluator('Models/Classification_Final.pth', 'data_with_virality_scores.csv', 'is_viral')
classification_evaluator.evaluate()

regression_evaluator = RegressionModelEvaluator('Models/regression_redo.pth', 'data_with_virality_scores.csv', 'virality_score')
regression_evaluator.evaluate()
