#!/bin/bash
echo "format.sh"

echo "============================"
echo "Running black..."
black .

echo "============================"
echo "Running isort..."
isort **/*.py

echo "============================"
echo "Running flake8..."
flake8 crypto/
