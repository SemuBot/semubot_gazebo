cmake_minimum_required(VERSION 3.16)
project(semubot_gazebo)

find_package(ament_cmake REQUIRED)
find_package(ros_gz_sim REQUIRED)

install(
  DIRECTORY launch worlds config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
