from setuptools import setup, find_packages

setup(
	name='kayci',
	version='0.0.1',
	author='Mike Lang',
	author_email='mikelang3000@gmail.com',
	description='A kubernetes-native CI system',
	packages=find_packages(),
	install_requires=[
		'argh',
		'gevent',
	],
)
