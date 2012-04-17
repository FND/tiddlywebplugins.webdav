.PHONY: test clean

test: clean
	py.test -x -s test/test_compile.py test

clean:
	find . -name "*.pyc" | xargs rm || true
	rm -r test/__pycache__ || true
