import torch
import pydicom
import numpy as np
from PIL import Image
import torchvision.transforms as transforms
from torch.nn import Module
import os

class NewModel(Module):
    def __init__(self, num_classes=3):
        super(NewModel, self).__init__()
        self.conv_layers = torch.nn.Sequential(
            torch.nn.Conv2d(3, 32, kernel_size=3, stride=1, padding=1),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(kernel_size=2, stride=2),
            torch.nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(kernel_size=2, stride=2)
        )
        self.flatten = torch.nn.Flatten()
        
        # Calculate flattened size
        with torch.no_grad():
            dummy_input = torch.zeros(1, 3, 224, 224)
            flattened_size = self.conv_layers(dummy_input).view(1, -1).size(1)
            
        self.fc_layers = torch.nn.Sequential(
            torch.nn.Linear(flattened_size, 128),
            torch.nn.ReLU(),
            torch.nn.Linear(128, num_classes)
        )

    def forward(self, x):
        x = self.conv_layers(x)
        x = self.flatten(x)
        x = self.fc_layers(x)
        return x

def load_dicom(path):
    """Load and preprocess DICOM image"""
    dc = pydicom.dcmread(path)
    data = dc.pixel_array
    data = data - np.min(data)
    if np.max(data) != 0:
        data = data / np.max(data)
    data = (data * 255).astype(np.uint8)
    return data

def predict_image(model_path, image_path, device='cpu'):
    """
    Make prediction for a single image
    
    Args:
        model_path (str): Path to the .pth model file
        image_path (str): Path to the DICOM image
        device (str): 'cuda' or 'cpu'
        
    Returns:
        prediction (int): Predicted class (0: Normal/Mild, 1: Moderate, 2: Severe)
        probabilities (list): Prediction probabilities for each class
    """
    # Set device
    device = torch.device(device)
    
    # Load model
    model = NewModel()
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    
    # Define transforms (same as training)
    transform = transforms.Compose([
        transforms.Lambda(lambda x: (x * 255).astype(np.uint8)),
        transforms.ToPILImage(),
        transforms.Resize((224, 224)),
        transforms.Grayscale(num_output_channels=3),
        transforms.ToTensor(),
    ])
    
    # Load and preprocess image
    image = load_dicom(image_path)
    image = transform(image).unsqueeze(0).to(device)
    
    # Make prediction
    with torch.no_grad():
        outputs = model(image)
        probabilities = torch.softmax(outputs, dim=1)
        prediction = torch.argmax(probabilities, dim=1).item()
        probabilities = probabilities.squeeze().cpu().numpy()
    
    severity_map = {0: "Normal/Mild", 1: "Moderate", 2: "Severe"}
    
    return severity_map[prediction], probabilities

def predict_directory(model_path, directory_path, device='cpu'):
    """
    Make predictions for all DICOM images in a directory
    
    Args:
        model_path (str): Path to the .pth model file
        directory_path (str): Path to directory containing DICOM images
        device (str): 'cuda' or 'cpu'
        
    Returns:
        dict: Dictionary with image filenames as keys and predictions as values
    """
    results = {}
    
    for filename in os.listdir(directory_path):
        if filename.endswith('.dcm'):
            image_path = os.path.join(directory_path, filename)
            prediction, probabilities = predict_image(model_path, image_path, device)
            results[filename] = {
                'prediction': prediction,
                'probabilities': {
                    'Normal/Mild': float(probabilities[0]),
                    'Moderate': float(probabilities[1]),
                    'Severe': float(probabilities[2])
                }
            }
    
    return results

# Example usage
if __name__ == "__main__":
    # For single image prediction
    model_path = "path/to/your/model.pth"
    image_path = "path/to/your/image.dcm"
    
    prediction, probabilities = predict_image(model_path, image_path)
    print(f"Prediction: {prediction}")
    print(f"Probabilities: Normal/Mild: {probabilities[0]:.3f}, "
          f"Moderate: {probabilities[1]:.3f}, "
          f"Severe: {probabilities[2]:.3f}")
    
    # For directory prediction
    directory_path = "path/to/your/image/directory"
    results = predict_directory(model_path, directory_path)
    
    # Print results
    for filename, result in results.items():
        print(f"\nFile: {filename}")
        print(f"Prediction: {result['prediction']}")
        print("Probabilities:", result['probabilities'])