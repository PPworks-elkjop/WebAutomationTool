"""
Detailed check of what store data we're getting
"""

from vusion_api_helper import VusionAPIHelper
import json

helper = VusionAPIHelper()
success, data = helper.get_store_data('LAB', 'elkjop_se_lab.lab5')

print("Full Store Data:")
print("=" * 60)
print(json.dumps(data, indent=2))
