
COOKIE_DIR = .make

$(COOKIE_DIR)/setup:
	mkdir -p $(COOKIE_DIR)
	poetry install
	touch $(COOKIE_DIR)/setup

setup: $(COOKIE_DIR)/setup

test: setup
	poetry run pytest tests

pretty: setup
	poetry run black

.PHONY: test pretty
