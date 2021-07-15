import sys
import subprocess
import os

__current_dir__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

# implement pip as a subprocess:
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'beautifulsoup4'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'django'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'matplotlib'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'mpld3'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'nltk'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'numpy'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pandas'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyculiarity'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'scipy'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'sqlalchemy'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'scikit-learn'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'sklearn'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'regex'])



# process output with an API in the subprocess module:
reqs = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'])
installed_packages = [r.decode().split('==')[0] for r in reqs.split()]

print(installed_packages)