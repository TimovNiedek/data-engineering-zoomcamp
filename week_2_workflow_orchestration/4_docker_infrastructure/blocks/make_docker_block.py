from prefect.infrastructure import DockerContainer

docker_block = DockerContainer(
    image_name="timovanniedek/prefect:zoom-2.2.6",
    image_pull_policy="ALWAYS",
    auto_remove=True
)

docker_block.save("zoom", overwrite=True)
