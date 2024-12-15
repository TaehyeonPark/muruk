set -e
TEST_DIR="tests"

echo "Current working directory: $(pwd)"

cd "$(dirname "$0")/../../"

echo "Running mutation tests..."
mutatest -s $TEST_DIR -t "pytest" -r 314
echo "All tests passed!"
