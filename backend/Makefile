protos:
	# Generate python code from proto files
	python -m grpc_tools.protoc \
		-I../protos \
		--python_out=./node_connector_pb2 \
		--pyi_out=./node_connector_pb2 \
		--grpc_python_out=./node_connector_pb2 \
		../protos/*.proto;
	# Fix imports (add `from . import ...`)
	python -m protoletariat \
		-o ./node_connector_pb2 \
		--in-place \
		protoc --proto-path=../protos ../protos/*.proto
