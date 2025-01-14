import pandas as pd
from sklearn.preprocessing import RobustScaler, MinMaxScaler
import numpy as np

def calculate_virality_score(data):
    """
    Calculate the virality score for the given data.
    
    Args:
    data (pd.DataFrame): DataFrame containing engagement metrics ('diggCount', 'playCount', 'shareCount', 'commentCount').

    Returns:
    np.array: Normalized virality scores.
    """
    # Handle missing values and perform logarithmic transformation
    data = data.dropna()
    data = np.log1p(data)
    
    # Scale the data using RobustScaler to handle outliers
    scaler = RobustScaler()
    scaled_data = scaler.fit_transform(data)
    
    # Assign weights to engagement metrics
    weights = {'diggCount': 0.4, 'playCount': 0.3, 'shareCount': 0.2, 'commentCount': 0.1}
    
    # Calculate the weighted sum of scaled engagement metrics
    virality_score = np.sum(scaled_data * list(weights.values()), axis=1)
    
    # Normalize the virality score using MinMaxScaler
    normalizer = MinMaxScaler()
    normalized_virality_score = normalizer.fit_transform(virality_score.reshape(-1, 1)).flatten()
    
    return normalized_virality_score

def main():
    """
    Main function to read the dataset, calculate virality scores, and save the updated dataset.
    """
    # Read the dataset from the CSV file
    df = pd.read_csv('video_data_binary_virality_cleaned.csv')

    # Calculate the virality score and add it to the DataFrame
    df['virality_score'] = calculate_virality_score(df[['diggCount', 'playCount', 'shareCount', 'commentCount']])
    
    # Save the updated DataFrame to a new CSV file
    df.to_csv('data_with_virality_scores.csv', index=False)

if __name__ == "__main__":
    main()
