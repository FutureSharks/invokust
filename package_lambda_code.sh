#!/bin/bash

rm -rf python-packages

python3 setup.py bdist_wheel

docker run -it -v $PWD/python-packages:/python-packages -v $PWD/dist:/dist python:3.7 bash -c "pip install dist/invokust-*.whl --target=/python-packages"

zip -q -r lambda_locust.zip lambda_locust.py locustfile_example.py python-packages
