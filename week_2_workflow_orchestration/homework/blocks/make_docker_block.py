from prefect.infrastructure import DockerContainer

docker_block = DockerContainer(
    image="timovanniedek/prefect:zoom-2-homework",
    image_pull_policy="ALWAYS",
    auto_remove=True
)

docker_block.save("2-homework-img", overwrite=True)
