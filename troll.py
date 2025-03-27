from utilities.split_data import postprocess_output
import json
processed_output = postprocess_output()
print(json.dumps(processed_output, indent=4))x