set -e
TEST_DIR="tests"

echo "Current working directory: $(pwd)"

cd "$(dirname "$0")/../../"

echo "Running integration tests..."
pytest --junitxml=test-results/results.xml $TEST_DIR -s
echo "All tests passed!"
