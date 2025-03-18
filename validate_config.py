import yaml
import os
from jsonschema import validate, ValidationError
from datetime import datetime

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "short_description": {"type": "string", "maxLength": 140},
        "description": {"type": "string", "pattern": "^templates/.*\\.html$"},
        "evaluation_details": {"type": "string", "pattern": "^templates/.*\\.html$"},
        "terms_and_conditions": {"type": "string", "pattern": "^templates/.*\\.html$"},
        "image": {"type": "string", "pattern": ".+\\.(jpg|jpeg|png)$"},
        "submission_guidelines": {"type": "string", "pattern": "^templates/.*\\.html$"},
        "evaluation_script": {"type": "string"},
        "leaderboard": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "minimum": 1},
                    "schema": {
                        "type": "object",
                        "properties": {
                            "labels": {"type": "array", "items": {"type": "string"}},
                            "default_order_by": {"type": "string"},
                            "metadata": {"type": "object"}
                        },
                        "required": ["labels", "default_order_by"]
                    }
                },
                "required": ["id", "schema"]
            }
        },
        "challenge_phases": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "minimum": 1},
                    "codename": {"type": "string"},
                    "test_annotation_file": {"type": "string"}
                },
                "required": ["id", "codename", "test_annotation_file"]
            }
        }
    },
    "required": [
        "title",
        "description",
        "submission_guidelines",
        "evaluation_script",
        "leaderboard",
        "challenge_phases"
    ]
}

def validate_config():
    try:
        with open("challenge_config.yml") as f:
            config = yaml.safe_load(f)
        
        validate(instance=config, schema=SCHEMA)
        
        for field in ["description", "evaluation_details", "terms_and_conditions", "submission_guidelines"]:
            if not os.path.exists(config[field]):
                raise ValidationError(f"Missing template file: {config[field]}")
                
        for phase in config["challenge_phases"]:
            if not os.path.exists(phase["test_annotation_file"]):
                raise ValidationError(f"Missing annotation file: {phase['test_annotation_file']}")

        print("✅ Config validation successful!")
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        return False

if __name__ == "__main__":
    if not validate_config():
        exit(1)