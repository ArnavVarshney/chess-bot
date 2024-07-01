import torch
import torch.nn as nn
import torchvision.transforms as transforms
import os
import pandas as pd
from torch.utils.data import Dataset
from torchvision.io import read_image

#Global var
batch_size = 64
num_classes = 13
learning_rate = 0.001
num_epochs = 20

# Device will determine whether to run the training on GPU or CPU.
device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')

label_names={
    0:"black_bishop",
    1:"black_king",
    2:"black_knight",
    3:"black_pawn",
    4:"black_queen",
    5:"black_rook",
    6:"empty",
    7:"white_bishop",
    8:"white_king",
    9:"white_knight",
    10:"white_pawn",
    11:"white_queen",
    12:"white_rook",
}

class LeNet5(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.layer1 = nn.Sequential(
            nn.Conv2d(3, 6, kernel_size=5, stride=1, padding=0),
            nn.BatchNorm2d(6),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size = 2, stride = 2))
        self.layer2 = nn.Sequential(
            nn.Conv2d(6, 16, kernel_size=5, stride=1, padding=0),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size = 2, stride = 2))
        self.fc = nn.Linear(3136, 64)
        self.relu = nn.ReLU()
        self.fc1 = nn.Linear(64, 84)
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(84, num_classes)
        
    def forward(self, x):
        out = self.layer1(x)
        out = self.layer2(out)
        out = out.reshape(out.size(0), -1)
        out = self.fc(out)
        out = self.relu(out)
        out = self.fc1(out)
        out = self.relu1(out)
        out = self.fc2(out)
        return out

class ChessPieceDataset(Dataset):
    def __init__(self, annotations_file, img_dir, transform=None, target_transform=None):
        self.img_labels = pd.read_csv(annotations_file)
        self.img_dir = img_dir
        self.transform = transform
        self.target_transform = target_transform

    def __len__(self):
        return len(self.img_labels)

    def __getitem__(self, idx):
        img_path = os.path.join(self.img_dir, self.img_labels.iloc[idx, 0])
        image = read_image(img_path)
        label = torch.tensor(list(self.img_labels.iloc[idx, 1:]))
        if self.transform:
            image = self.transform(image)
        if self.target_transform:
            label = self.target_transform(label)
        return image, label

def train(train_loader, model, cost, optimizer):
    total_step = len(train_loader)
    for epoch in range(num_epochs):
        for i, (images, labels) in enumerate(train_loader):  
            images = images.to(device).to(torch.float)
            labels = labels.to(device).to(torch.float)
            
            #Forward pass
            outputs = model(images)
            loss = cost(outputs, labels)
                
            # Backward and optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
                    
            print ('Epoch [{}/{}], Step [{}/{}], Loss: {:.4f}' 
                            .format(epoch+1, num_epochs, i+1, total_step, loss.item()))
    
    print("Finished training")

    #Save the thing
    torch.save(model.state_dict(), "model.pt")
    print("Model saved at model.pt")
    return 

def validate(test_loader, model):
    with torch.no_grad():
        correct = 0
        total = 0
        for images, labels in test_loader:
            images = images.to(device).to(torch.float)

            labels = torch.argmax(labels.to(device).to(torch.float), dim=1)
            outputs = model(images)

            predicted = torch.argmax(outputs.data, dim=1)

            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        print('Accuracy of the network: {} %'.format(100 * correct / total))
    return

def main():
    train_dataset = ChessPieceDataset("overhead_pieces/train/_classes.csv","overhead_pieces/train")
    test_dataset = ChessPieceDataset("overhead_pieces/test/_classes.csv","overhead_pieces/test")

    train_loader = torch.utils.data.DataLoader(dataset = train_dataset,
                                            batch_size = batch_size,
                                            shuffle = True)
    test_loader = torch.utils.data.DataLoader(dataset = test_dataset,
                                            batch_size = batch_size,
                                            shuffle = True)
    
    model = LeNet5(num_classes).to(device)
    #Setting the loss function
    cost = nn.CrossEntropyLoss()
    #Setting the optimizer with the model parameters and learning rate
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    train(train_loader, model, cost, optimizer)
    validate(test_loader, model)
    return 

if __name__ == "__main__":
    main()
