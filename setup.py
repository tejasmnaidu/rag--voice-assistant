# setup.py

from setuptools import setup, find_packages

setup(
    name='ai-voice-rag-assistant',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'speechrecognition',
        'pygame',
        'openai',
        'groq',
        'deepgram-sdk',
        'python-dotenv',
        'colorama',
        'requests'
    ],
    entry_points={
        'console_scripts': [
            'jarvis=run_voice_assistant:main'
        ]
    },
    author='Tejas M Naidu',
    author_email='tejasmnaidu072@gmail.com',
    description='AI Voice Assistant using speech recognition, Retrieval-Augmented Generation (RAG), and text-to-speech.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/tejas-m-naidu',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Artificial Intelligence'
    ],
    python_requires='>=3.10',
    include_package_data=True,
)