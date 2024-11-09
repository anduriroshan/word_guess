from setuptools import find_packages, setup


HYPEN_E_DOT = '-e .'

def get_requirements(file_path):
    '''
    input : file path of requirements
    output: list of elements in requirements text file
    '''
    with open(file_path, 'r') as file:
        requirements = [req.strip() for req in file.readlines()]
        if HYPEN_E_DOT in requirements:
            requirements.remove(HYPEN_E_DOT)
    return requirements

setup(
    name = 'Word_guess',
    version = '0.0.1',
    author= 'Anduri Roshan',
    author_email='roshanandhuri@gmail.com',
    packages= find_packages(),
    install_required = get_requirements('requirements.txt')
)