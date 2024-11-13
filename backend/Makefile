protos:
	python -m grpc_tools.protoc \
		-Iservice_pb2=../protos \
		--python_out=. \
		--pyi_out=. \
		--grpc_python_out=. \
		--js_out=import_style=commonjs,binary:./ \
		../protos/service.proto
