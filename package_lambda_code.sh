#!/bin/bash

python3 setup.py bdist_wheel

docker run -it -v $PWD/python-packages:/python-packages -v $PWD/dist:/dist python:3.6 bash -c "pip install dist/invokust-0.6-py3-none-any.whl --target=/python-packages"

zip -q -r lambda_locust.zip lambda_locust.py locustfile_example.py python-packages