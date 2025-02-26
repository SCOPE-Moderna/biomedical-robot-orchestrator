from invoke import task

@task
def protos(c):
    # Generate Python code from proto files
    c.run("python -m grpc_tools.protoc -I../protos --python_out=./node_connector_pb2 --pyi_out=./node_connector_pb2 --grpc_python_out=./node_connector_pb2 ../protos/*.proto")
    # Fix imports
    c.run("python -m protoletariat -o ./node_connector_pb2 --in-place protoc --proto-path=../protos ../protos/*.proto")
