'''
Python module that loads and handles the prediction and saliency map from the selected model

'''

import torch
import torch.nn as nn
import torchvision.models as models
from torchvision import transforms
import numpy as np
import matplotlib.pyplot as plt
import cv2
from PIL import Image
import pydicom

AlexNetModel = {
    "saggital1": "./models/alexnet_saggitalt1_model.pth",
    "axial":"./models/alexnet_axial_t2_model.pth",
    "saggital2": "./models/alexnet_sagittal_t2.pth"
}

ResNetModel = {
    "saggital1": "./models/resnet_saggitalt1_model.pth",
    "axial":"./models/resnet_axial_t2_model.pth",
    "saggital2": "./models/resnet_sagittal_t2.pth"
}

class CustomAlexNet(nn.Module):
    def __init__(self, num_levels=5, num_classes=3):
        self.num_levels = num_levels
        self.num_classes = num_classes
        super(CustomAlexNet, self).__init__()
        self.model = models.alexnet(weights=None)  # Load AlexNet
        num_ftrs = self.model.classifier[-1].in_features
        self.model.classifier[-1] = nn.Linear(num_ftrs, num_levels * num_classes)  # Modify to output all levels

    def forward(self, x):
        x = self.model(x)
        return x.view(-1, self.num_levels, self.num_classes)  # Reshape to (batch, levels, classes

class CustomResNet(nn.Module):
    def __init__(self, num_levels=5, num_classes=3):
        self.num_levels = num_levels
        self.num_classes = num_classes
        super(CustomResNet, self).__init__()
        self.model = models.resnet18(weights=None)  # Load ResNet-18; you could use resnet50 or other versions as well
        num_ftrs = self.model.fc.in_features
        self.model.fc = nn.Linear(num_ftrs, num_levels * num_classes)  # Modify the output layer for all levels

    def forward(self, x):
        x = self.model(x)
        return x.view(-1, self.num_levels, self.num_classes)  # Reshape to (batch, levels, classe

# Image Transformer
transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.Grayscale(num_output_channels=3),
    transforms.ToTensor(),
])

def load_dicom_image(dicom_path):
    """Load and preprocess a DICOM image."""
    dicom = pydicom.dcmread(dicom_path)
    image = dicom.pixel_array

    # Normalize image to 0-255 if needed
    if np.max(image) > 255:
        image = (image / np.max(image)) * 255.0
    
    image = image.astype(np.uint8)  # Convert to uint8 for PIL compatibility
    image = transform(image)  # Apply transformations
    image = image.unsqueeze(0)  # Add batch dimension
    return image

def predict_image(model, dicom_path, device):
    """Get predictions for each level from a DICOM image."""
    model.eval()  # Set model to evaluation mode
    Levels = ["L1/L2","L2/L3","L3/L4","L4/L5","L5/S1"]
    Classes = ["Normal/Mid","Moderate","Severe"]
    image = load_dicom_image(dicom_path).to(device)  # Load and move to device

    with torch.no_grad():
        outputs = model(image)  # Forward pass
        probabilities = torch.softmax(outputs, dim=2)  # Apply softmax along classes dimension

        predictions = {}
        for level_idx, level_probs in enumerate(probabilities.squeeze(0)):
            class_idx = torch.argmax(level_probs).item()
            confidence = level_probs[class_idx].item()
            predictions[Levels[level_idx]] = {
                'Class': Classes[class_idx],
                'Confidence': confidence
            }

    return predictions

def load_dicom_raw_image(dicom_path):
    dicom = pydicom.dcmread(dicom_path)
    image = dicom.pixel_array

    # Normalize to 0-255 if necessary and convert to uint8
    if np.max(image) > 255:
        image = (image / np.max(image)) * 255.0
    image = image.astype(np.uint8)

    # Ensure the image is 2D or 3D by removing any extra dimensions
    if image.ndim == 4 and image.shape[0] == 1:
        image = np.squeeze(image, axis=0)
    elif image.ndim == 4 and image.shape[-1] == 1:
        image = np.squeeze(image, axis=-1)
    
    return image

def compute_saliency_map(model, input_image, device):
    """
    Computes a combined saliency map for all levels in a multi-level model.
    """
    model.eval()
    input_image = input_image.to(device)
    input_image.requires_grad_()

    # Forward pass
    outputs = model(input_image)  # Shape should be (batch, levels, classes)

    # Initialize saliency map with the same shape as input but reduced to one channel
    saliency_map = torch.zeros(input_image.shape[2:], device=device)

    Levels = ["L1/L2", "L2/L3", "L3/L4", "L4/L5", "L5/S1"]

    for level_idx in range(outputs.shape[1]):
        # Get the predicted class for this level
        level_output = outputs[0, level_idx]  # Get output for the current level
        target_class = level_output.argmax().item()  # Use the predicted class for saliency

        # Get the score for the target class
        score = level_output[target_class]
        
        # Zero out previous gradients
        model.zero_grad()
        
        # Backpropagate to get the gradient of the target score w.r.t. the input image
        score.backward(retain_graph=True)

        # Accumulate the gradients for each level into the saliency map
        saliency_map += input_image.grad.data.abs()[0, 0] * 0.2  # Accumulate across levels for combined saliency

    # Normalize saliency map
    saliency_map = (saliency_map - saliency_map.min()) / (saliency_map.max() - saliency_map.min())
    return saliency_map.cpu().numpy()

def overlay_saliency_on_image(saliency_map, original_image):
    # Resize saliency map to match the original image size (if necessary)
    if saliency_map.shape != original_image.shape:
        saliency_map = np.interp(saliency_map, (saliency_map.min(), saliency_map.max()), (0, 1))
        saliency_map = np.array(Image.fromarray((saliency_map * 255).astype(np.uint8)).resize(original_image.shape[::-1]))

    # Normalize original image for better contrast in overlay
    original_image = (original_image - original_image.min()) / (original_image.max() - original_image.min())

    # Overlay: set saliency map as red and blend with original grayscale image
    overlay = np.stack([saliency_map, np.zeros_like(saliency_map), np.zeros_like(saliency_map)], axis=-1)
    blended = np.stack([original_image] * 3, axis=-1) + 0.01 * overlay
    
    return blended

def process_image(cnn,model,image_path):
    """_summary_

    Args:
        cnn (string): model to use wether :
            res: ResNet
            alex: AlexNet
        model (string): type of model from the cnn:
            saggital1
            axial 
            saggital2
        image_path (string): path to the .dcm file of the MRI

    Raises:
        ValueError: cnn not valid: if the cnn spcecified is not an option
        ValueError: model not valid: if the model spcecified is not an option

    Returns:
        _type_: dict :
        has the predictions for each level , the severity and confidency given on the following format for each
        { Level : {
                'Class': str of the severity,
                'Confidence': float of the confidence of the diagnosis
            }
        }
        , 
        numpy.array  : NumPy array with the information of the image with the saliency map
    """
    Model = None
    dic = None
    if cnn == "res":
        #ResNet predictions
        Model = CustomResNet()
        dic = ResNetModel
    elif cnn == "alex":
        #AlexNet predictions
        Model = CustomAlexNet()
        dic = AlexNetModel
    else:
        raise ValueError(f"{cnn} cnn is not valid")
    if model not in dic.keys():
        raise ValueError(f"{model} model is not valid")
    Model.load_state_dict(torch.load(dic[model]))
    # Set the model to evaluation mode (important for inference)
    Model.eval()
    # Move to GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    Model.to(device)
    predictions = predict_image(Model, image_path,device)
    #get the classes predictions from the image
    
    # Get the saliency map
    raw_image = load_dicom_raw_image(image_path)
    input_image = transform(raw_image).unsqueeze(0)  # Add batch dimension

    # Generate saliency map
    saliency_map = compute_saliency_map(Model, input_image, device)
    overlayed_image = overlay_saliency_on_image(saliency_map, raw_image)
    
    return predictions ,overlayed_image
