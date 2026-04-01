.PHONY: lint pre-commit clean build publish publish-test check install_dev

lint:
	python -m pyright

pre-commit:
	pre-commit run --all-files --show-diff-on-failure

# Remove previous build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build dist *.egg-info

# Build sdist and wheel
build: clean
	@echo "Building distributions..."
	python -m build

# Check built artifacts
check:
	@echo "Checking distributions..."
	twine check dist/*

# Upload to TestPyPI first
publish-test: build check
	@echo "Uploading to TestPyPI..."
	twine upload --repository testpypi dist/*

# Upload to official PyPI
publish: build check
	@echo "Uploading to PyPI..."
	twine upload dist/*

install_dev:
	uv pip install -e .
