
echo
echo "============================="
echo "=========== isort ==========="
echo "============================="
echo

isort --py 313 --diff --color --profile black custom_components
isort --py 313 --color --profile black custom_components

echo
echo "============================="
echo "=========== black ==========="
echo "============================="
echo

black -l 200 -t py313 --diff --color custom_components
black -l 200 -t py313 custom_components

echo
echo "============================="
echo "=========== pylint =========="
echo "============================="
echo

pylint --output-format=colorized --max-line-length 200 custom_components
