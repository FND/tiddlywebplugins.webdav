.PHONY: test clean

test: clean
	py.test -x -s test

clean:
	find . -name "*.pyc" | xargs rm || true
	rm -r test/__pycache__ || true
