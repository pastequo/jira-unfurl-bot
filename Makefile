CONTAINER_CMD := $(or $(CONTAINER_CMD), $(shell command -v podman 2> /dev/null))
ifndef CONTAINER_CMD
CONTAINER_CMD := docker
endif

JIRA_UNFURL_BOT_IMAGE := $(or $(JIRA_UNFURL_BOT_IMAGE), "quay.io/edge-infrastructure/jira-unfurl-bot")
JIRA_UNFURL_BOT_TAG := $(or $(JIRA_UNFURL_BOT_TAG),latest)

build-image:
	$(CONTAINER_CMD) build $(CONTAINER_BUILD_EXTRA_PARAMS) -t $(JIRA_UNFURL_BOT_IMAGE):$(JIRA_UNFURL_BOT_TAG) .

install:
	pip install -r requirements.txt

lint-manifest:
	oc process --local=true -f openshift/template.yaml --param IMAGE_TAG=foobar | oc apply --dry-run=client -f -

.PHONY: install install-lint full-install format flake8 lint lint-manifest build-image
