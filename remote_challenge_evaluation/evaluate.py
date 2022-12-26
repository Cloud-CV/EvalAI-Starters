

def evaluate(user_submission_file, phase_codename, test_annotation_file=None, **kwargs):
    print("Starting Evaluation.....")
    """
    Evaluates the submission for a particular challenge phase and returns score
    Arguments:
        `user_submission_file`: Path to file submitted by the user
        `phase_codename`: Phase to which submission is made

        `test_annotations_file`: Path to test_annotation_file on the server
            We recommend setting a default `test_annotation_file` or using `phase_codename`
            to select the appropriate file. For example, you could load test annotation file
            for current phase as:
            ```
            test_annotation_file = json.loads(open("{phase_codename}_path", "r"))
            ```
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

    '''
    # Load test annotation file for current phase
    test_annotation_file = json.loads(open("{phase_codename}_path", "r"))
    '''
    output = {}
    if phase_codename == "dev":
        print("Evaluating for Dev Phase")
        output["result"] = [
            {
                "split": "train_split",
                "show_to_participant": True,
                "accuracies": {"Metric1": 90},
            },
        ]
        print("Completed evaluation for Dev Phase")
    elif phase_codename == "test":
        print("Evaluating for Test Phase")
        output["result"] = [
            {
                "split": "train_split",
                "show_to_participant": True,
                "accuracies": {"Metric1": 90},
            },
            {
                "split": "test_split",
                "show_to_participant": False,
                "accuracies": {"Metric1": 50, "Metric2": 40},
            },
        ]
        print("Completed evaluation for Test Phase")
    return output
