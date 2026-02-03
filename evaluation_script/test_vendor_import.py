import importlib.util
import importlib
import sys

print('Before importing evaluation_script: zhipuai importable =', importlib.util.find_spec('zhipuai') is not None)

# Importing the package triggers evaluation_script/__init__.py which adds vendor/ to sys.path
import evaluation_script

print('After importing evaluation_script: zhipuai importable =', importlib.util.find_spec('zhipuai') is not None)

from zhipuai import ZhipuAI, greet

obj = ZhipuAI()
print('ZhipuAI.name =', obj.name)
print('greet() =', greet())
