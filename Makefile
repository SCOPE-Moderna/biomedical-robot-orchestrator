.PHONY: backend
.PHONY: protos

backend:
	python -m backend.main

protos:
ifeq ($(OS),Windows_NT)
	cd backend && make protos-win
	cd nodes && yarn protos-win
else
	cd backend && make protos
	cd nodes && yarn protos
endif
