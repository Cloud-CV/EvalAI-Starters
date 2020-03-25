## How to create a challenge on EvalAI?

If you are looking for a simple challenge configuration that you can replicate to create a challenge on EvalAI, then you are at the right place. Follow the instructions given below to get started.

## Directory Structure

``` 
.
├── README.md
├── annotations                                 # Contains the annotations for Dataset splits
│   ├── test_annotations_devsplit.json          # Annotations of dev split
│   └── test_annotations_testsplit.json         # Annotations for test split
├── challenge_data                              # Contains scripts to test the evalautaion script locally
│   ├── challenge_1                             # Contains evaluation script for the challenge
|        ├── __init__.py                        # Imports the main.py file for evaluation
|        └── main.py                            # Challenge evaluation script
│   └── __init__.py                             # Imports the modules which involve evaluation script loading
├── challenge_config.yaml                       # Configuration file to define challenge setup
├── evaluation_script                           # Contains the evaluation script
│   ├── __init__.py                             # Imports the modules that involve annotations loading etc
│   └── main.py                                 # Contains the main `evaluate()` method
├── logo.jpg                                    # Logo image of the challenge
├── submission.json                             # Sample submission file
├── run.sh                                      # Script to create the challenge configuration zip to be uploaded on EvalAI website
└── templates                                   # Contains challenge related HTML templates
    ├── challenge_phase_1_description.html      # Challenge Phase 1 description template
    ├── challenge_phase_2_description.html      # Challenge Phase 2 description template
    ├── description.html                        # Challenge description template
    ├── evaluation_details.html                 # Contains description about how submissions will be evalauted for each challenge phase
    ├── submission_guidelines.html              # Contains information about how to make submissions to the challenge
    └── terms_and_conditions.html               # Contains terms and conditions related to the challenge
├── worker                                      # Contains the scripts to test evaluation script locally
│   ├── __init__.py                             # Imports the module that ionvolves loading evaluation script
│   └── run.py                                  # Contains the code to run the evaluation locally
```

## Test your evaluation script locally

In order to test the evaluation script locally before uploading it to [EvalAI](https://evalai.cloudcv.org/) server, please follow the below instructions -

1. Copy the evaluation script i.e `__init__.py` , `main.py` and other relevant files from `evaluation_script/` directory to `challenge_data/challenge_1/` directory.

2. Now, edit `challenge_phase` name, `annotation file` name and `submission file` name in the `worker/run.py` file to the challenge phase codename (which you want to test for), annotation file name in the `annotations/` folder (for specific phase) and corresponding submission file respectively.

3. Run the command `python -m worker.run` from the directory where `annotations/`  `challenge_data/` and `worker/` directories are present. If the command runs successfully, then the evaluation script works locally and will work on the server as well.

## Steps involved

1. Fork this repository.

2. Read [EvalAI challenge creation documentation](https://evalai.readthedocs.io/en/latest/configuration.html) to know more about how you want to structure your challenge. Once you are ready, start making changes in the yaml file, HTML templates, evaluation script according to your need.

3. Once you are done making changes, run the command `./run.sh` to generate the `challenge_config.zip` 

4. Upload the `challenge_config.zip` on [EvalAI](https://evalai.cloudcv.org) to create a challenge on EvalAI. Challenge will be available publicly once EvalAI Admin approves the challenge.

## Facing problems in creating a challenge?

Please feel free to open issues on our [GitHub Repository](https://github.com/Cloud-CV/EvalAI-Starter/issues) or contact us at team@cloudcv.org if you have issues.

