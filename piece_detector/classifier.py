import model.cnn as cnn
import torch
from util import *

class PieceClassifier:
    model=None
    img_size=-1
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

    def __init__(self, weights_path="model/model.pt", img_size=70):
        print("---\n")
        self.model = cnn.LeNet5(13).to(self.device)
        self.model.load_state_dict(torch.load(weights_path))

        self.img_size = img_size

        print(self.model.eval())
        print("classifier initiated")
        print("\n---")
        return
    
    #Takes in BGR images
    def predict(self, imgs):
        x = resize(imgs, self.img_size)
        x = splitAndSwap(x)
        x = torch.from_numpy(x).to(self.device).to(torch.float)
        preds = self.model(x)
        return torch.argmax(preds.data,1)
    
    def getLabelNames(self, preds):
        names = []
        for pred in preds:
            names.append(self.label_names[pred.item()])
        return names
    
def main():
    classifier = PieceClassifier()

    img = cv.imread("model/orig_pieces/image4.jpg")
    preds = classifier.predict([img])
    print(classifier.getLabelNames(preds))

    return

if __name__ == "__main__":
    main()