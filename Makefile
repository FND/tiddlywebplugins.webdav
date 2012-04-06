.PHONY: test clean

test:
	py.test -x -s test

clean:
	find . -name "*.pyc" | xargs rm || true
