import random
import json
from collections import OrderedDict
import torch
import numpy as np
import torch.nn as nn
import torch.nn as nn
import torch
import os 
from torchvision import transforms,datasets

class Network(nn.Module):
    def __init__(self, num_classes=10, init_weights=False):
        super(Network, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 48, kernel_size=11, stride=4, padding=2),  
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2),                  
            nn.Conv2d(48, 128, kernel_size=5, padding=2),          
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2),                  
            nn.Conv2d(128, 192, kernel_size=3, padding=1),          
            nn.ReLU(inplace=True),
            nn.Conv2d(192, 128, kernel_size=3, padding=1),        
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2),                
        )
        self.classifier = nn.Sequential(
            nn.Dropout(p=0.5),
            nn.Linear(32 * 4, 1024),
            nn.ReLU(inplace=True),
            nn.Linear(1024, num_classes),
        )
        if init_weights:
            self._initialize_weights()

    def forward(self, x):
        x = self.features(x)
        x = torch.flatten(x, start_dim=1)
        x = self.classifier(x)
        return x

    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)


def jsontonet(jsonfile,net):
    with open(jsonfile) as f:
        jsondata = f.read()
    dictkk =json.loads(jsondata)
    dd = OrderedDict()
    for k,v in dictkk.items():
        if isinstance(v, list):
            v = torch.tensor(np.asarray(v))
            dd[k] = v
    net.load_state_dict(dd)
    return net

def evaluate(test_annotation_file, user_submission_file, phase_codename, **kwargs):
    print("Starting Evaluation.....")
    """
    Evaluates the submission for a particular challenge phase and returns score
    Arguments:

        `test_annotations_file`: Path to test_annotation_file on the server
        `user_submission_file`: Path to file submitted by the user
        `phase_codename`: Phase to which submission is made

        `**kwargs`: keyword arguments that contains additional submission
        metadata that challenge hosts can use to send slack notification.
        You can access the submission metadata
        with kwargs['submission_metadata']

        Example: A sample submission metadata can be accessed like this:
        >>> print(kwargs['submission_metadata'])
        {
            'status': u'running',
            'when_made_public': None,
            'participant_team': 5,
            'input_file': 'https://abc.xyz/path/to/submission/file.json',
            'execution_time': u'123',
            'publication_url': u'ABC',
            'challenge_phase': 1,
            'created_by': u'ABC',
            'stdout_file': 'https://abc.xyz/path/to/stdout/file.json',
            'method_name': u'Test',
            'stderr_file': 'https://abc.xyz/path/to/stderr/file.json',
            'participant_team_name': u'Test Team',
            'project_url': u'http://foo.bar',
            'method_description': u'ABC',
            'is_public': False,
            'submission_result_file': 'https://abc.xyz/path/result/file.json',
            'id': 123,
            'submitted_at': u'2017-03-20T19:22:03.880652Z'
        }
    """
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    net = Network()
    net = jsontonet(user_submission_file,net)
    net.eval()
    net.to(device)

    
    print("using {} device.".format(device))

    data_transform = {
        "test": transforms.Compose([transforms.Resize((64, 64)), 
                                   transforms.ToTensor(),
                                   transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])}
    image_path = os.path.abspath(os.path.join(os.getcwd(), "Augtest"))  # get data root path
    assert os.path.exists(image_path), "{} path does not exist.".format(image_path)
    test_dataset = datasets.ImageFolder(image_path,
                                            transform=data_transform["test"])
    test_num = len(test_dataset)
    batch_size = 4
    nw = min([os.cpu_count(), batch_size if batch_size > 1 else 0, 8])
    test_loader = torch.utils.data.DataLoader(test_dataset,
                                                  batch_size=batch_size, shuffle=False,
                                                  num_workers=nw)
    print("using {} images for testing.".format(test_num))

  
    
    acc = 0.0  # accumulate accurate number / epoch
    with torch.no_grad():
        #test_bar = tqdm(test_loader, file=sys.stdout)
        for test_data in test_loader:
            test_images, test_labels = test_data
            outputs = net(test_images.to(device))
            predict_y = torch.max(outputs, dim=1)[1]
            acc += torch.eq(predict_y, test_labels.to(device)).sum().item()

    test_accurate = acc / test_num

    output = {}
    if phase_codename == "dev":
        print("Evaluating for Dev Phase")
        output["result"] = [
            {
                "train_split": {
                    # "Metric1": random.randint(0, 99),
                    # "Metric2": random.randint(0, 99),
                    # "Metric3": random.randint(0, 99),
                    # "Total": random.randint(0, 99),
                    "Accuracy":test_accurate
                }
            }
        ]
        # To display the results in the result file
        output["submission_result"] = output["result"][0]["train_split"]
        print("Completed evaluation for Dev Phase")
    elif phase_codename == "test":
        print("Evaluating for Test Phase")
        output["result"] = [
            {
                "train_split": {
                    # "Metric1": random.randint(0, 99),
                    # "Metric2": random.randint(0, 99),
                    # "Metric3": random.randint(0, 99),
                    # "Total": random.randint(0, 99),
                    "Accuracy":test_accurate
                }
            },
            {
                "test_split": {
                    # "Metric1": random.randint(0, 99),
                    # "Metric2": random.randint(0, 99),
                    # "Metric3": random.randint(0, 99),
                    # "Total": random.randint(0, 99),
                    "Accuracy":test_accurate
                }
            },
        ]
        # To display the results in the result file
        output["submission_result"] = output["result"][0]
        print("Completed evaluation for Test Phase")
    return output


if __name__ == "__main__":
    evaluate('annotations/test_annotations_devsplit.json','network.json',"dev")
